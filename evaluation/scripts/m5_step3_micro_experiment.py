import json
import sqlite3
import numpy as np
import re
from sentence_transformers import SentenceTransformer, CrossEncoder
from rank_bm25 import BM25Okapi

import argparse
import sys

ROOT = "d:/Personal Project/AWS StudyBot/evaluation"
DB_PATH = f"{ROOT}/index/m3_index.db"
BLOCKS_PATH = f"{ROOT}/bundle_all/blocks.jsonl"
DATASET_PATH = f"{ROOT}/datasets/test-v3.jsonl"
EMBEDDING_MODEL_NAME = "sentence-transformers/paraphrase-multilingual-mpnet-base-v2"

# Parse args to allow user to specify the model
parser = argparse.ArgumentParser()
parser.add_argument("--ce-model", type=str, default="BAAI/bge-reranker-m3", help="HuggingFace model name for Cross-Encoder")
args = parser.parse_args()
CROSS_ENCODER_MODEL_NAME = args.ce_model

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

def calculate_metrics(sorted_indices, target_blocks, chunks):
    ranks = []
    for rank, idx in enumerate(sorted_indices, start=1):
        if chunks[idx]['source_block_ids'].intersection(target_blocks):
            ranks.append(rank)
            
    if not ranks:
        return {
            "first_rank": -1,
            "full_rank": -1,
            "mrr_first": 0.0,
            "mrr_full": 0.0,
            "cov_1": 0, "cov_3": 0, "cov_5": 0, "cov_10": 0
        }
        
    first_rank = ranks[0]
    mrr_first = 1.0 / first_rank
    
    # Coverage calculation (how many distinct target blocks found?)
    found_blocks = set()
    cov_1, cov_3, cov_5, cov_10 = 0, 0, 0, 0
    full_rank = -1
    
    target_len = len(target_blocks)
    
    for rank, idx in enumerate(sorted_indices, start=1):
        found = chunks[idx]['source_block_ids'].intersection(target_blocks)
        for b in found:
            found_blocks.add(b)
        
        pct = len(found_blocks) / target_len
        if rank == 1: cov_1 = pct
        if rank == 3: cov_3 = pct
        if rank == 5: cov_5 = pct
        if rank == 10: cov_10 = pct
            
        if len(found_blocks) == target_len and full_rank == -1:
            full_rank = rank
            
    if len(found_blocks) < target_len:
        # Pad remaining coverage to end
        if 1 > len(sorted_indices): cov_1 = cov_1
        if 3 > len(sorted_indices): cov_3 = len(found_blocks)/target_len
        if 5 > len(sorted_indices): cov_5 = len(found_blocks)/target_len
        if 10 > len(sorted_indices): cov_10 = len(found_blocks)/target_len
            
    mrr_full = 1.0 / full_rank if full_rank != -1 else 0.0
            
    return {
        "first_rank": first_rank,
        "full_rank": full_rank,
        "mrr_first": mrr_first,
        "mrr_full": mrr_full,
        "cov_1": cov_1, "cov_3": cov_3, "cov_5": cov_5, "cov_10": cov_10
    }

def main():
    print("Loading Dense Model...")
    dense_model = SentenceTransformer(EMBEDDING_MODEL_NAME)
    print("Loading Cross-Encoder Model...")
    cross_encoder = CrossEncoder(CROSS_ENCODER_MODEL_NAME)
    
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
            
    results_baseline = []
    results_ce = []
    
    group_a = []
    group_b = []
    group_c = []
    strong_anchors = []
    
    print("Running Micro-Experiment...")
    for case in cases:
        case_id = case['case_id']
        query_text = case['query']['text']
        
        target_blocks = set()
        for ev in case.get('evidence', []):
            for b in blocks_by_doc.get(ev['document_id'], []):
                if match_locator(ev['locator'], b):
                    target_blocks.add(b['block_id'])
                    
        # Global Retrieval
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
                
        # Group Assignment
        if first_hit_global == 1:
            group = "Strong Anchors"
            strong_anchors.append(case_id)
        else:
            d_rank = np.where(dense_sorted == target_idx)[0][0] + 1 if target_idx != -1 else 999
            b_rank = np.where(bm25_sorted == target_idx)[0][0] + 1 if target_idx != -1 else 999
            best_rank = min(d_rank, b_rank)
            
            if best_rank <= 10:
                group = "Group A"
                group_a.append(case_id)
            elif best_rank <= 20:
                group = "Group B"
                group_b.append(case_id)
            else:
                group = "Group C"
                group_c.append(case_id)
                
        if group == "Group C":
            # Skip evaluation for Group C
            continue
            
        # Build Candidate Pool (Top 20 Dense + Top 20 BM25)
        top20_dense = dense_sorted[:20]
        top20_bm25 = bm25_sorted[:20]
        pool_indices = list(set(top20_dense).union(set(top20_bm25)))
        
        # --- Control Baseline: MinMax 0.4 on Pool ---
        pool_dense_scores = dense_scores[pool_indices]
        pool_bm25_scores = bm25_scores[pool_indices]
        
        # Local normalization
        pool_dense_mm = min_max_norm(pool_dense_scores)
        pool_bm25_mm = min_max_norm(pool_bm25_scores)
        pool_fusion = 0.4 * pool_dense_mm + 0.6 * pool_bm25_mm
        
        # Sort pool by fusion score
        pool_sorted_local_idx = np.argsort(pool_fusion)[::-1]
        pool_sorted_global_idx = [pool_indices[i] for i in pool_sorted_local_idx]
        
        metrics_baseline = calculate_metrics(pool_sorted_global_idx, target_blocks, chunks)
        metrics_baseline['case_id'] = case_id
        metrics_baseline['group'] = group
        results_baseline.append(metrics_baseline)
        
        # --- Intervention: Cross-Encoder on Pool ---
        ce_pairs = [[query_text, chunks[idx]['text']] for idx in pool_indices]
        ce_scores = cross_encoder.predict(ce_pairs)
        
        ce_sorted_local_idx = np.argsort(ce_scores)[::-1]
        ce_sorted_global_idx = [pool_indices[i] for i in ce_sorted_local_idx]
        
        metrics_ce = calculate_metrics(ce_sorted_global_idx, target_blocks, chunks)
        metrics_ce['case_id'] = case_id
        metrics_ce['group'] = group
        results_ce.append(metrics_ce)
        
    # Aggregate and Print
    print("\n\n=== M5 Step 3 Micro-Experiment Results ===")
    
    def agg(res_list, group_filter):
        filtered = [r for r in res_list if r['group'] == group_filter]
        if not filtered: return None
        n = len(filtered)
        return {
            "mrr_first": sum(r['mrr_first'] for r in filtered) / n,
            "mrr_full": sum(r['mrr_full'] for r in filtered) / n,
            "cov_1": sum(r['cov_1'] for r in filtered) / n,
            "cov_3": sum(r['cov_3'] for r in filtered) / n,
            "cov_5": sum(r['cov_5'] for r in filtered) / n,
            "cov_10": sum(r['cov_10'] for r in filtered) / n,
        }

    for g in ["Group A", "Group B", "Strong Anchors"]:
        agg_b = agg(results_baseline, g)
        agg_ce = agg(results_ce, g)
        if not agg_b: continue
        
        print(f"\n--- {g} ---")
        print(f"{'Metric':<15} | {'MinMax Baseline':<20} | {'Cross-Encoder':<20} | {'Change':<10}")
        print("-" * 75)
        for k in ['mrr_first', 'mrr_full', 'cov_1', 'cov_3', 'cov_5', 'cov_10']:
            b_val = agg_b[k]
            ce_val = agg_ce[k]
            change = ce_val - b_val
            trend = "▲" if change > 0.01 else "▼" if change < -0.01 else "-"
            print(f"{k:<15} | {b_val:<20.4f} | {ce_val:<20.4f} | {change:+.4f} {trend}")

    # Save per-case results for offline analysis
    output_path = f"{ROOT}/results/m5_step3_per_case.json"
    with open(output_path, 'w', encoding='utf-8') as f:
        json.dump({
            "baseline": results_baseline,
            "cross_encoder": results_ce
        }, f, indent=2)
    print(f"\nSaved per-case results to {output_path}")
    print("Done.")
    
if __name__ == "__main__":
    main()
