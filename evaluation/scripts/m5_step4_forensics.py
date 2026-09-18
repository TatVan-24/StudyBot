import json
import sqlite3
import numpy as np
import re
import gc
import torch
from sentence_transformers import SentenceTransformer, CrossEncoder
from rank_bm25 import BM25Okapi

ROOT = "d:/Personal Project/AWS StudyBot/evaluation"
DB_PATH = f"{ROOT}/index/m3_index.db"
BLOCKS_PATH = f"{ROOT}/bundle_all/blocks.jsonl"
DATASET_PATH = f"{ROOT}/datasets/test-v3.jsonl"
EMBEDDING_MODEL_NAME = "sentence-transformers/paraphrase-multilingual-mpnet-base-v2"
CROSS_ENCODER_MODEL_NAME = "BAAI/bge-reranker-v2-m3"

def tokenize(text: str) -> list:
    return re.findall(r"\w+", text.lower())

def match_locator(gt_locator, block):
    block_locator = block.get('locator', {})
    if gt_locator.get('type') in ['markdown', 'text_span', 'txt'] and block_locator.get('type') in ['markdown', 'text_span', 'text', 'txt']:
        gt_start = gt_locator.get('start_line')
        gt_end = gt_locator.get('end_line')
        bl_start = block_locator.get('start_line')
        bl_end = block_locator.get('end_line')
        if gt_start is not None and gt_end is not None and bl_start is not None and bl_end is not None:
            if max(gt_start, bl_start) <= min(gt_end, bl_end): return True
    if gt_locator.get('type') in ['page', 'pdf'] and block_locator.get('type') == 'pdf':
        gt_page = gt_locator.get('pdf_page')
        if gt_page is None:
            locations = gt_locator.get('locations', [])
            if locations:
                gt_page = locations[0].get('pdf_page')
        for loc in block_locator.get('locations', []):
            if loc.get('pdf_page') == gt_page: return True
    return False

def min_max_norm(scores):
    s_min = np.min(scores)
    s_max = np.max(scores)
    if s_max > s_min:
        return (scores - s_min) / (s_max - s_min)
    return np.zeros_like(scores)

def main():
    import os
    os.environ["HF_HUB_OFFLINE"] = "1"
    os.environ["TRANSFORMERS_OFFLINE"] = "1"
    print("Forcing Hugging Face Offline Mode...")
    
    print("Loading Dense Model...")
    dense_model = SentenceTransformer(EMBEDDING_MODEL_NAME, local_files_only=True)
    
    blocks_by_doc = {}
    with open(BLOCKS_PATH, 'r', encoding='utf-8') as f:
        for line in f:
            if not line.strip(): continue
            b = json.loads(line)
            blocks_by_doc.setdefault(b.get('document_id'), []).append(b)
            
    conn = sqlite3.connect(DB_PATH)
    c = conn.cursor()
    c.execute('SELECT chunk_id, document_id, text, source_block_ids FROM embeddings')
    rows = c.fetchall()
    conn.close()
    
    chunks = []
    texts = []
    for r in rows:
        source_block_ids = json.loads(r[3]) if r[3] else []
        chunks.append({
            "chunk_id": r[0],
            "document_id": r[1],
            "text": r[2],
            "source_block_ids": set(source_block_ids)
        })
        texts.append(r[2])
        
    print("Encoding corpus...")
    dense_vecs = dense_model.encode(texts, normalize_embeddings=True)
    tokenized_corpus = [tokenize(t) for t in texts]
    bm25_index = BM25Okapi(tokenized_corpus)
    
    cases = []
    with open(DATASET_PATH, 'r', encoding='utf-8') as f:
        for line in f:
            if not line.strip(): continue
            cases.append(json.loads(line))
            
    strong_anchors_data = []
    
    print("Preparing Candidate Pools for Strong Anchors...")
    for case in cases:
        case_id = case['case_id']
        query_text = case['query']['text']
        
        target_blocks = set()
        for ev in case.get('evidence', []):
            for b in blocks_by_doc.get(ev['document_id'], []):
                if match_locator(ev['locator'], b):
                    target_blocks.add(b['block_id'])
                    
        query_vec = dense_model.encode(query_text, normalize_embeddings=True)
        tokenized_query = tokenize(query_text)
        
        dense_scores = np.dot(dense_vecs, query_vec)
        bm25_scores = bm25_index.get_scores(tokenized_query)
        
        dense_mm_global = min_max_norm(dense_scores)
        bm25_mm_global = min_max_norm(bm25_scores)
        fusion_global = 0.4 * dense_mm_global + 0.6 * bm25_mm_global
        
        global_sorted = np.argsort(fusion_global)[::-1]
        dense_sorted = np.argsort(dense_scores)[::-1]
        bm25_sorted = np.argsort(bm25_scores)[::-1]
        
        first_hit_global = -1
        target_idx = -1
        for rank, idx in enumerate(global_sorted, start=1):
            if chunks[idx]['source_block_ids'].intersection(target_blocks):
                first_hit_global = rank
                target_idx = idx
                break
                
        # Only keep Strong Anchors
        if first_hit_global == 1:
            top20_dense = dense_sorted[:20]
            top20_bm25 = bm25_sorted[:20]
            pool_indices = list(set(top20_dense).union(set(top20_bm25)))
            
            pool_dense_scores = dense_scores[pool_indices]
            pool_bm25_scores = bm25_scores[pool_indices]
            
            pool_dense_mm = min_max_norm(pool_dense_scores)
            pool_bm25_mm = min_max_norm(pool_bm25_scores)
            pool_fusion = 0.4 * pool_dense_mm + 0.6 * pool_bm25_mm
            
            strong_anchors_data.append({
                "case": case,
                "target_blocks": target_blocks,
                "pool_indices": pool_indices,
                "pool_dense_scores": pool_dense_scores,
                "pool_bm25_scores": pool_bm25_scores,
                "pool_minmax_scores": pool_fusion
            })
            
    print(f"Found {len(strong_anchors_data)} Strong Anchors.")
            
    print("Freeing Dense Model and Corpus Embeddings from RAM to prevent OOM...")
    del dense_model
    del dense_vecs
    gc.collect()
    if torch.cuda.is_available(): torch.cuda.empty_cache()
    
    print(f"Loading Cross-Encoder Model ({CROSS_ENCODER_MODEL_NAME}) in fp16...")
    cross_encoder = CrossEncoder(
        CROSS_ENCODER_MODEL_NAME,
        local_files_only=True,
        model_kwargs={"torch_dtype": torch.float16}
    )
    
    report_lines = [
        "# M5 Step 4: Strong Anchor Forensics Report\n",
        "This report investigates 13 Strong Anchor cases where the Baseline correctly ranked the target at #1, but the Cross-Encoder (BGE) may have altered the ranking.\n",
        "**Extraction Logic:** Union(Target chunks, Baseline Top-10, BGE Top-10).\n"
    ]
    
    print("Running BGE inference and generating report...")
    try:
        from tqdm import tqdm
        iterator = tqdm(strong_anchors_data, desc="Scoring Cases")
    except ImportError:
        iterator = strong_anchors_data
        
    for item in iterator:
        case = item["case"]
        case_id = case['case_id']
        query_text = case['query']['text']
        target_blocks = item["target_blocks"]
        pool_indices = item["pool_indices"]
        pool_minmax = item["pool_minmax_scores"]
        
        pool_sorted_local_idx = np.argsort(pool_minmax)[::-1]
        baseline_ranks = {pool_indices[local_idx]: rank for rank, local_idx in enumerate(pool_sorted_local_idx, start=1)}
        
        ce_pairs = [[query_text, chunks[idx]['text']] for idx in pool_indices]
        ce_scores = cross_encoder.predict(ce_pairs)
        
        ce_sorted_local_idx = np.argsort(ce_scores)[::-1]
        ce_ranks = {pool_indices[local_idx]: rank for rank, local_idx in enumerate(ce_sorted_local_idx, start=1)}
        
        target_indices = [idx for idx in pool_indices if chunks[idx]['source_block_ids'].intersection(target_blocks)]
        baseline_top10 = [pool_indices[i] for i in pool_sorted_local_idx[:10]]
        bge_top10 = [pool_indices[i] for i in ce_sorted_local_idx[:10]]
        
        union_indices = list(set(target_indices + baseline_top10 + bge_top10))
        union_indices.sort(key=lambda idx: ce_ranks[idx])
        
        baseline_target_rank = min([baseline_ranks[idx] for idx in target_indices]) if target_indices else -1
        bge_target_rank = min([ce_ranks[idx] for idx in target_indices]) if target_indices else -1
        
        report_lines.append(f"### Case: {case_id}")
        report_lines.append(f"**Query**: {query_text}\n")
        report_lines.append(f"**Candidate Pool:** {len(pool_indices)} chunks")
        report_lines.append(f"**Target chunks:** {len(target_indices)}")
        report_lines.append(f"**Baseline Target Rank:** {baseline_target_rank}")
        report_lines.append(f"**BGE Target Rank:** {bge_target_rank}\n")
        
        report_lines.append("| Chunk ID | Target? | Base Rank | BGE Rank | Dense | BM25 | MinMax | BGE Score | Text |")
        report_lines.append("|---|---:|---:|---:|---:|---:|---:|---:|---|")
        
        for idx in union_indices:
            local_idx = pool_indices.index(idx)
            is_target = "YES" if idx in target_indices else "NO"
            base_rank = baseline_ranks[idx]
            bge_rank = ce_ranks[idx]
            d_score = item["pool_dense_scores"][local_idx]
            b_score = item["pool_bm25_scores"][local_idx]
            m_score = item["pool_minmax_scores"][local_idx]
            c_score = ce_scores[local_idx]
            
            text_cleaned = chunks[idx]['text'].replace('\\n', ' ').replace('\n', '<br>').replace('|', '&#124;')
            chunk_id = chunks[idx]['chunk_id'][:12] + "..." # short ID
            
            report_lines.append(f"| {chunk_id} | {is_target} | {base_rank} | {bge_rank} | {d_score:.4f} | {b_score:.4f} | {m_score:.4f} | {c_score:.4f} | {text_cleaned} |")
            
        report_lines.append("\n---\n")
        
    output_path = f"{ROOT}/results/m5_step4_forensics_report.md"
    with open(output_path, "w", encoding="utf-8") as f:
        f.write("\n".join(report_lines))
        
    print(f"Forensics complete. Report saved to {output_path}")

if __name__ == "__main__":
    main()
