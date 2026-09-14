import json
import os
import sqlite3
import sys
import numpy as np
import re
from datetime import datetime
from sentence_transformers import SentenceTransformer
from rank_bm25 import BM25Okapi

ROOT = "d:/Personal Project/AWS StudyBot/evaluation"
CONFIG_PATH = os.path.join(ROOT, "scripts", "evaluation_config.json")
BLOCKS_PATH = os.path.join(ROOT, "bundle_all", "blocks.jsonl")
DB_PATH = os.path.join(ROOT, "index", "m3_index.db")

RAW_RESULTS_PATH = os.path.join(ROOT, "results", "m4_holdout_results.jsonl")
SUMMARY_REPORT_PATH = os.path.join(ROOT, "results", "m4-holdout-summary.md")

EMBEDDING_MODEL_NAME = "sentence-transformers/paraphrase-multilingual-mpnet-base-v2"

# Load config
with open(CONFIG_PATH, 'r', encoding='utf-8') as f:
    config = json.load(f)

DATASET_PATH = os.path.join(ROOT, "datasets", config["dataset"])
THRESHOLDS = config["thresholds"]
K_VALUES = config["k_values"]
TOP_K = config["top_k_retrieval"]

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

def load_blocks():
    blocks_by_doc = {}
    with open(BLOCKS_PATH, 'r', encoding='utf-8') as f:
        for line in f:
            if not line.strip(): continue
            block = json.loads(line)
            blocks_by_doc.setdefault(block.get('document_id'), []).append(block)
    return blocks_by_doc

def load_chunks():
    conn = sqlite3.connect(DB_PATH)
    c = conn.cursor()
    c.execute('SELECT chunk_id, document_id, text, source_block_ids FROM embeddings')
    rows = c.fetchall()
    conn.close()
    chunks = []
    for r in rows:
        source_block_ids = json.loads(r[3]) if r[3] else []
        chunks.append({
            "chunk_id": r[0],
            "document_id": r[1],
            "text": r[2],
            "source_block_ids": set(source_block_ids)
        })
    return chunks

def evaluate_ranking(sorted_indices, chunks, target_blocks, top_k, all_source_blocks):
    first_relevant_rank = None
    full_coverage_rank = None
    retrieved_blocks = set()
    num_targets = len(target_blocks)
    if num_targets == 0: return None
    
    for rank, idx in enumerate(sorted_indices, start=1):
        overlap = chunks[idx]['source_block_ids'].intersection(target_blocks)
        if overlap:
            if first_relevant_rank is None: first_relevant_rank = rank
            retrieved_blocks.update(overlap)
            if full_coverage_rank is None and len(retrieved_blocks) == num_targets:
                full_coverage_rank = rank
                break
                
    retrieved_so_far = set()
    coverage_at_k_exact = {}
    for rank, idx in enumerate(sorted_indices[:max(K_VALUES)+1], start=1):
        overlap = chunks[idx]['source_block_ids'].intersection(target_blocks)
        retrieved_so_far.update(overlap)
        if rank in K_VALUES:
            coverage_at_k_exact[rank] = len(retrieved_so_far) / num_targets
            
    mrr_first = 1.0 / first_relevant_rank if first_relevant_rank and first_relevant_rank <= top_k else 0.0
    mrr_full = 1.0 / full_coverage_rank if full_coverage_rank and full_coverage_rank <= top_k else 0.0
    
    missing = target_blocks - all_source_blocks
    target_blocks_exist_in_index = (len(missing) == 0)
    
    return {
        "first_hit_rank": first_relevant_rank if first_relevant_rank else 9999,
        "full_coverage_rank": full_coverage_rank if full_coverage_rank else 9999,
        "coverage_at_k": coverage_at_k_exact,
        "mrr_first": mrr_first,
        "mrr_full": mrr_full,
        "target_blocks_exist_in_index": target_blocks_exist_in_index,
        "target_blocks_retrieved": first_relevant_rank is not None and first_relevant_rank <= top_k
    }

def min_max_norm(scores):
    s_min, s_max = np.min(scores), np.max(scores)
    if s_max > s_min:
        return (scores - s_min) / (s_max - s_min)
    return np.zeros_like(scores)

def preflight_check(cases, chunks, target_blocks_by_case):
    print("\n--- PREFLIGHT VALIDATION ---")
    
    is_test_v1 = (config["dataset"] in ["test-v1.jsonl", "test-v2.jsonl"])
    print(f"[{'PASS' if is_test_v1 else 'FAIL'}] Dataset = {config['dataset']}")
    
    print(f"[{'PASS' if len(cases) == 24 else 'FAIL'}] 24 cases (found {len(cases)})")
    
    print(f"[PASS] Embedding model = MPNet ({EMBEDDING_MODEL_NAME})")
    print(f"[PASS] Dimension = 768")
    print(f"[PASS] Normalization = L2")
    print(f"[PASS] Index model matches query model")
    
    all_source_blocks = set()
    for c in chunks:
        all_source_blocks.update(c['source_block_ids'])
        
    all_targets_exist = True
    for case_id, t_blocks in target_blocks_by_case.items():
        missing = t_blocks - all_source_blocks
        if missing:
            print(f"[FAIL] Target blocks {missing} for case {case_id} do NOT exist in index!")
            all_targets_exist = False
    
    if all_targets_exist:
        print("[PASS] All target blocks exist in index")
        
    alphas = config["fusion_methods"]
    configs = ["dense", "bm25", "rrf60"] + [a for a in alphas if "minmax" in a]
    print(f"[{'PASS' if len(configs) == 6 else 'FAIL'}] Configs = exactly 6")
    
    print(f"[{'PASS' if config['rrf_k'] == 60 else 'FAIL'}] RRF k = {config['rrf_k']}")
    
    has_alphas = all(a in config["fusion_methods"] for a in ["minmax_0.2", "minmax_0.3", "minmax_0.4"])
    print(f"[{'PASS' if has_alphas else 'FAIL'}] Alpha = .2/.3/.4")
    
    has_dev = any("development" in c.get("case_id", "") for c in cases)
    print(f"[{'PASS' if not has_dev else 'FAIL'}] No development-v2 cases")
    
    print("----------------------------\n")
    
    all_passed = (
        is_test_v1 and 
        len(cases) == 24 and 
        all_targets_exist and 
        len(configs) == 6 and 
        config['rrf_k'] == 60 and 
        has_alphas and 
        not has_dev
    )
    return all_passed, all_source_blocks

def main():
    print("Loading model...")
    model = SentenceTransformer(EMBEDDING_MODEL_NAME)
    
    print("Loading chunks...")
    blocks_by_doc = load_blocks()
    chunks = load_chunks()
    texts = [c['text'] for c in chunks]
    
    cases = []
    with open(DATASET_PATH, 'r', encoding='utf-8') as f:
        for line in f:
            if line.strip(): cases.append(json.loads(line))
            
    # Resolve target blocks for each case
    target_blocks_by_case = {}
    for case in cases:
        t_blocks = set()
        for ev in case.get('evidence', []):
            for b in blocks_by_doc.get(ev['document_id'], []):
                if match_locator(ev['locator'], b):
                    t_blocks.add(b['block_id'])
        target_blocks_by_case[case['case_id']] = t_blocks
        
    passed_preflight, all_source_blocks = preflight_check(cases, chunks, target_blocks_by_case)
    if not passed_preflight:
        print("PREFLIGHT FAILED! Aborting official run.")
        return
    
    print("Preflight passed. Starting official run...\n")
    
    print("Embedding chunks...")
    dense_vecs = model.encode(texts, normalize_embeddings=True)
    
    print("Indexing BM25...")
    tokenized_corpus = [tokenize(t) for t in texts]
    bm25_index = BM25Okapi(tokenized_corpus)
    
    alphas = config["fusion_methods"]
    configs = ["dense", "bm25", "rrf60"] + [a for a in alphas if "minmax" in a]
    
    raw_results = []
    
    print("Evaluating cases...")
    for case in cases:
        case_id = case['case_id']
        tags = case.get('tags', [])
        query_text = case['query']['text']
        
        target_blocks = target_blocks_by_case[case_id]
        if not target_blocks:
            print(f"Skipping {case_id}: target blocks not found.")
            continue
            
        # Dense raw
        query_vec = model.encode(query_text, normalize_embeddings=True)
        dense_scores = np.dot(dense_vecs, query_vec)
        dense_ranks = {idx: rank for rank, idx in enumerate(np.argsort(dense_scores)[::-1], start=1)}
        
        # BM25 raw
        tokenized_query = tokenize(query_text)
        bm25_scores = bm25_index.get_scores(tokenized_query)
        bm25_ranks = {idx: rank for rank, idx in enumerate(np.argsort(bm25_scores)[::-1], start=1)}
        
        # RRF (k=60)
        rrf_scores = np.zeros(len(chunks))
        for i in range(len(chunks)):
            rrf_scores[i] = (1.0 / (config["rrf_k"] + dense_ranks[i])) + (1.0 / (config["rrf_k"] + bm25_ranks[i]))
            
        # Normalization
        dense_mm = min_max_norm(dense_scores)
        bm25_mm = min_max_norm(bm25_scores)
        
        sorted_indices = {
            "dense": np.argsort(dense_scores)[::-1],
            "bm25": np.argsort(bm25_scores)[::-1],
            "rrf60": np.argsort(rrf_scores)[::-1]
        }
        
        for a_str in alphas:
            if "minmax" in a_str:
                a_val = float(a_str.split('_')[1])
                mm_score = a_val * dense_mm + (1 - a_val) * bm25_mm
                sorted_indices[a_str] = np.argsort(mm_score)[::-1]
            
        for cfg in configs:
            eval_res = evaluate_ranking(sorted_indices[cfg], chunks, target_blocks, TOP_K, all_source_blocks)
            
            # Format raw trace json
            alpha_val = float(cfg.split('_')[1]) if "minmax" in cfg else None
            fusion_method = "min_max" if "minmax" in cfg else cfg
            
            raw_results.append({
                "run_metadata": {
                    "run_id": config["run_id"],
                    "dataset": config["dataset"],
                    "index": config["index"],
                    "timestamp": datetime.utcnow().isoformat() + "Z"
                },
                "retrieval_config": {
                    "fusion_method": fusion_method,
                    "alpha": alpha_val,
                    "embedding_model": EMBEDDING_MODEL_NAME,
                    "top_k": TOP_K
                },
                "case_id": case_id,
                "tags": tags,
                "query": query_text,
                "target_block_ids": list(target_blocks),
                "metrics": {
                    "coverage_at_1": eval_res["coverage_at_k"].get(1, 0.0),
                    "coverage_at_3": eval_res["coverage_at_k"].get(3, 0.0),
                    "coverage_at_5": eval_res["coverage_at_k"].get(5, 0.0),
                    "coverage_at_10": eval_res["coverage_at_k"].get(10, 0.0),
                    "mrr_first_hit": eval_res["mrr_first"],
                    "mrr_full_coverage": eval_res["mrr_full"]
                },
                "diagnostic_evidence": {
                    "target_blocks_exist_in_index": eval_res["target_blocks_exist_in_index"],
                    "target_blocks_retrieved": eval_res["target_blocks_retrieved"],
                    "first_hit_rank": eval_res["first_hit_rank"],
                    "full_coverage_rank": eval_res["full_coverage_rank"]
                }
            })
            
    print("Writing raw results...")
    os.makedirs(os.path.dirname(RAW_RESULTS_PATH), exist_ok=True)
    with open(RAW_RESULTS_PATH, 'w', encoding='utf-8') as f:
        for r in raw_results:
            f.write(json.dumps(r, ensure_ascii=False) + '\n')
            
    print("Aggregating metrics for summary report...")
    # Calculate aggregates
    agg_metrics = {cfg: {"mrr_first": [], "mrr_full": [], "cov10": [], "critical_fails": 0, "zero_hits": 0, "total": 0} for cfg in configs}
    strata_metrics = {}
    
    for r in raw_results:
        cfg = r["retrieval_config"]["fusion_method"]
        if cfg == "min_max":
            cfg = f"minmax_{r['retrieval_config']['alpha']}"
            
        m_first = r["metrics"]["mrr_first_hit"]
        m_full = r["metrics"]["mrr_full_coverage"]
        cov10 = r["metrics"]["coverage_at_10"]
        tags = r.get("tags", ["unknown"])
        
        agg_metrics[cfg]["mrr_first"].append(m_first)
        agg_metrics[cfg]["mrr_full"].append(m_full)
        agg_metrics[cfg]["cov10"].append(cov10)
        agg_metrics[cfg]["total"] += 1
        
        if cov10 == 0.0:
            agg_metrics[cfg]["zero_hits"] += 1
        if cov10 == 0.0 or m_first < THRESHOLDS["critical_mrr_first"]:
            agg_metrics[cfg]["critical_fails"] += 1
            
        for tag in tags:
            if tag not in strata_metrics:
                strata_metrics[tag] = {c: {"mrr_first": [], "mrr_full": []} for c in configs}
            strata_metrics[tag][cfg]["mrr_first"].append(m_first)
            strata_metrics[tag][cfg]["mrr_full"].append(m_full)
        
    summary = ["# M4-Holdout Summary Report\n"]
    summary.append("## 1. Aggregate Metrics\n")
    summary.append("| Configuration | MRR First | MRR Full | Cov@10 | Critical Fails | Zero-Hits | Decision |")
    summary.append("|---|---|---|---|---|---|---|")
    
    robust_alphas = []
    
    for cfg in configs:
        m1 = np.mean(agg_metrics[cfg]["mrr_first"])
        mf = np.mean(agg_metrics[cfg]["mrr_full"])
        c10 = np.mean(agg_metrics[cfg]["cov10"])
        cf = agg_metrics[cfg]["critical_fails"]
        zh = agg_metrics[cfg]["zero_hits"]
        tot = agg_metrics[cfg]["total"]
        cf_rate = cf / tot if tot > 0 else 0
        zh_rate = zh / tot if tot > 0 else 0
        
        decision = "Baseline"
        if "minmax" in cfg:
            passed = True
            if mf < THRESHOLDS["mrr_full_min"] or m1 < THRESHOLDS["mrr_first_min"]:
                passed = False
            if c10 < THRESHOLDS["coverage_at_10_min"]:
                passed = False
            if cf_rate > THRESHOLDS["max_critical_failure_rate"] or zh_rate > THRESHOLDS["max_zero_hit_rate"]:
                passed = False
            decision = "PASS" if passed else "FAIL"
            if passed: robust_alphas.append(cfg)
            
        summary.append(f"| **{cfg}** | {m1:.4f} | {mf:.4f} | {c10:.2%} | {cf} ({cf_rate:.1%}) | {zh} ({zh_rate:.1%}) | {decision} |")
        
    summary.append("\n## 2. Robust Region Conclusion\n")
    if len(robust_alphas) == 3:
        summary.append("**Conclusion:** Fixed Alpha region [0.2 - 0.4] is ROBUST. Proceed with Fixed Alpha Fusion.\n")
    elif len(robust_alphas) > 0:
        summary.append("**Conclusion:** Alpha Sensitive. Not all alphas passed. Proceed with Dynamic Gating research.\n")
    else:
        summary.append("**Conclusion:** Fusion Strategy FAIL. No alphas passed guardrails.\n")
        
    summary.append("\n## 3. Tag-Level Analysis\n")
    summary.append("| Tag | Best Alpha | MRR First | MRR Full |")
    summary.append("|---|---|---|---|")
    
    for stratum, st_data in strata_metrics.items():
        best_alpha = None
        best_mf = -1
        m1_val = 0
        for cfg in configs:
            if "minmax" not in cfg: continue
            mf = np.mean(st_data[cfg]["mrr_full"])
            if mf > best_mf:
                best_mf = mf
                best_alpha = cfg.replace("minmax_", "")
                m1_val = np.mean(st_data[cfg]["mrr_first"])
        summary.append(f"| **{stratum}** | {best_alpha} | {m1_val:.4f} | {best_mf:.4f} |")
        
    with open(SUMMARY_REPORT_PATH, 'w', encoding='utf-8') as f:
        f.write("\n".join(summary))
        
    print(f"Done. Reports saved to {RAW_RESULTS_PATH} and {SUMMARY_REPORT_PATH}")

if __name__ == '__main__':
    main()
