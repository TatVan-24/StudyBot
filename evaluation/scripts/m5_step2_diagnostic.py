import json
import sqlite3
import numpy as np
import re
from sentence_transformers import SentenceTransformer
from rank_bm25 import BM25Okapi

ROOT = "d:/Personal Project/AWS StudyBot/evaluation"
DB_PATH = f"{ROOT}/index/m3_index.db"
BLOCKS_PATH = f"{ROOT}/bundle_all/blocks.jsonl"
DATASET_PATH = f"{ROOT}/datasets/test-v3.jsonl"
EMBEDDING_MODEL_NAME = "sentence-transformers/paraphrase-multilingual-mpnet-base-v2"

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
    model = SentenceTransformer(EMBEDDING_MODEL_NAME)
    
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
        
    dense_vecs = model.encode(texts, normalize_embeddings=True)
    tokenized_corpus = [tokenize(t) for t in texts]
    bm25_index = BM25Okapi(tokenized_corpus)
    
    cases = []
    with open(DATASET_PATH, 'r', encoding='utf-8') as f:
        for line in f:
            if not line.strip(): continue
            cases.append(json.loads(line))
            
    out_lines = ["# M5 Step 2 Diagnostic Output\n"]
    
    for case in cases:
        case_id = case['case_id']
        query_text = case['query']['text']
        
        target_blocks = set()
        for ev in case.get('evidence', []):
            for b in blocks_by_doc.get(ev['document_id'], []):
                if match_locator(ev['locator'], b):
                    target_blocks.add(b['block_id'])
                    
        query_vec = model.encode(query_text, normalize_embeddings=True)
        tokenized_query = tokenize(query_text)
        
        dense_scores = np.dot(dense_vecs, query_vec)
        bm25_scores = bm25_index.get_scores(tokenized_query)
        
        dense_mm = min_max_norm(dense_scores)
        bm25_mm = min_max_norm(bm25_scores)
        mm_score = 0.4 * dense_mm + 0.6 * bm25_mm
        
        sorted_indices = np.argsort(mm_score)[::-1]
        dense_sorted_indices = np.argsort(dense_scores)[::-1]
        bm25_sorted_indices = np.argsort(bm25_scores)[::-1]
        
        first_hit_rank = -1
        target_idx = -1
        for rank, idx in enumerate(sorted_indices, start=1):
            if chunks[idx]['source_block_ids'].intersection(target_blocks):
                first_hit_rank = rank
                target_idx = idx
                break
                
        if first_hit_rank == 1:
            continue # Skip Strong Anchors
            
        out_lines.append(f"## {case_id}")
        out_lines.append(f"**Query:** {query_text}")
        out_lines.append(f"**Fusion Rank:** {first_hit_rank}")
        
        if target_idx != -1:
            d_rank = np.where(dense_sorted_indices == target_idx)[0][0] + 1
            b_rank = np.where(bm25_sorted_indices == target_idx)[0][0] + 1
            out_lines.append(f"**Target Candidate Availability (Gate A):** Dense Rank: {d_rank} | BM25 Rank: {b_rank}")
            out_lines.append(f"**Target Scores:** Fusion: {mm_score[target_idx]:.4f} | Dense_mm: {dense_mm[target_idx]:.4f} | BM25_mm: {bm25_mm[target_idx]:.4f}")
            
            # Sibling Analysis (Distractors Above Target)
            if 1 < first_hit_rank <= 20:
                out_lines.append("\n### Sibling Competition Analysis (Distractors Above Target)")
                for r_idx in range(first_hit_rank - 1):
                    d_idx = sorted_indices[r_idx]
                    d_d_rank = np.where(dense_sorted_indices == d_idx)[0][0] + 1
                    d_b_rank = np.where(bm25_sorted_indices == d_idx)[0][0] + 1
                    
                    fusion_margin = mm_score[d_idx] - mm_score[target_idx]
                    dense_margin = dense_mm[d_idx] - dense_mm[target_idx]
                    bm25_margin = bm25_mm[d_idx] - bm25_mm[target_idx]
                    
                    out_lines.append(f"\n#### Distractor Rank {r_idx + 1}")
                    out_lines.append(f"Fusion Margin: +{fusion_margin:.4f} | Dense Margin: {dense_margin:+.4f} | BM25 Margin: {bm25_margin:+.4f}")
                    out_lines.append(f"Ranks: Dense {d_d_rank} | BM25 {d_b_rank}")
                    
                    # Pattern check
                    if d_d_rank < d_rank and d_b_rank > b_rank:
                        pattern = "Dense gây nhiễu (kéo Distractor lên)"
                    elif d_b_rank < b_rank and d_d_rank > d_rank:
                        pattern = "BM25 gây nhiễu (kéo Distractor lên)"
                    elif d_d_rank < d_rank and d_b_rank < b_rank:
                        pattern = "Cả hai đều kéo Distractor lên"
                    else:
                        pattern = "Fusion Alpha/MinMax artifact"
                    out_lines.append(f"**Pattern:** {pattern}")
                    snippet = chunks[d_idx]['text'][:200].replace('\n', ' ') + "..."
                    out_lines.append(f"> {snippet}")
        else:
            out_lines.append("**Target Candidate Availability (Gate A):** TARGET NOT RETRIEVED (ZERO-HIT)")
            
        out_lines.append("\n---\n")

    out_path = f"{ROOT}/results/m5_step2_diagnostic.md"
    with open(out_path, "w", encoding='utf-8') as f:
        f.write("\n".join(out_lines))
        
    print(f"Done. Diagnostic saved to {out_path}")

if __name__ == "__main__":
    main()
