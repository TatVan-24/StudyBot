import json
import os
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
    print("Loading model...")
    model = SentenceTransformer(EMBEDDING_MODEL_NAME)
    
    print("Loading blocks and chunks...")
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
        
    print("Computing index representations...")
    dense_vecs = model.encode(texts, normalize_embeddings=True)
    tokenized_corpus = [tokenize(t) for t in texts]
    bm25_index = BM25Okapi(tokenized_corpus)
    
    cases = []
    with open(DATASET_PATH, 'r', encoding='utf-8') as f:
        for line in f:
            if not line.strip(): continue
            cases.append(json.loads(line))
            
    results_md = ["# RCA: M5 Step 1 (test-v3.jsonl) Diagnostics\n"]
    results_md.append("Analyzing failures using Frozen Baseline (minmax_0.4)\n---\n")
    
    print("Evaluating cases...")
    for case in cases:
        case_id = case['case_id']
        query_text = case['query']['text']
        tags = case.get('tags', [])
        
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
        
        top_k = 10
        top_indices = np.argsort(mm_score)[::-1][:top_k]
        
        # Check first hit rank
        first_hit_rank = -1
        full_rank = -1
        target_hit_count = 0
        sorted_indices = np.argsort(mm_score)[::-1]
        
        for rank, idx in enumerate(sorted_indices, start=1):
            if chunks[idx]['source_block_ids'].intersection(target_blocks):
                target_hit_count += 1
                if first_hit_rank == -1:
                    first_hit_rank = rank
                if target_hit_count == len(target_blocks):
                    full_rank = rank
                    break
                    
        mrr_first = 1.0 / first_hit_rank if first_hit_rank > 0 else 0.0
        
        if mrr_first >= 0.65:
            failure_type = "Success (Rank 1)"
        elif mrr_first >= 0.5:
            failure_type = "Near Failure (Rank 2)"
        else:
            failure_type = "Critical Failure (Zero-Hit / Rank >= 3)"
            
        results_md.append(f"## {case_id} (Tags: {', '.join(tags)})")
        results_md.append(f"**Status:** {failure_type}")
        results_md.append(f"**First Hit Rank:** {first_hit_rank}")
        results_md.append(f"**Query:** {query_text}")
        results_md.append(f"**Target Blocks:** {len(target_blocks)}\n")
        
        results_md.append("### Top 3 Retrieved Chunks (Distractors vs Targets)")
        for rank, idx in enumerate(top_indices[:3], start=1):
            chunk = chunks[idx]
            is_target = len(chunk['source_block_ids'].intersection(target_blocks)) > 0
            badge = "✅ TARGET" if is_target else "❌ DISTRACTOR"
            results_md.append(f"#### Rank {rank}: {badge}")
            results_md.append(f"Score: {mm_score[idx]:.4f} (Dense: {dense_scores[idx]:.4f} | BM25: {bm25_scores[idx]:.4f})")
            text_snippet = chunk['text'][:500] + ("..." if len(chunk['text']) > 500 else "")
            results_md.append(f"```text\n{text_snippet}\n```\n")
            
        if first_hit_rank > 3:
            results_md.append(f"### First Target Chunk (Found at Rank {first_hit_rank})")
            if first_hit_rank > 0:
                idx = sorted_indices[first_hit_rank - 1]
                chunk = chunks[idx]
                results_md.append(f"Score: {mm_score[idx]:.4f} (Dense: {dense_scores[idx]:.4f} | BM25: {bm25_scores[idx]:.4f})")
                text_snippet = chunk['text'][:500] + ("..." if len(chunk['text']) > 500 else "")
                results_md.append(f"```text\n{text_snippet}\n```\n")
            else:
                results_md.append("Target blocks not found in index or not retrieved!\n")
                
        results_md.append("---\n")
        
    out_path = f"{ROOT}/results/rca_m5_cases_output.md"
    with open(out_path, "w", encoding='utf-8') as f:
        f.write("\n".join(results_md))
        
    print(f"Done. RCA output saved to {out_path}")

if __name__ == "__main__":
    main()
