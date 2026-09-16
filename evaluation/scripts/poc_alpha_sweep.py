import json
import os
import sqlite3
import numpy as np
import re
from sentence_transformers import SentenceTransformer
from rank_bm25 import BM25Okapi

# Constants
dev_v2_path = "d:/Personal Project/AWS StudyBot/evaluation/datasets/development-v2.jsonl"
blocks_path = "d:/Personal Project/AWS StudyBot/evaluation/bundle_all/blocks.jsonl"
db_path = "d:/Personal Project/AWS StudyBot/evaluation/index/m3_index.db"
report_path = "d:/Personal Project/AWS StudyBot/idea/demo/poc_alpha_sweep_report.md"

def tokenize(text: str) -> list:
    return re.findall(r"\w+", text.lower())

def match_locator(gt_locator, block):
    block_locator = block.get('locator', {})
    if gt_locator.get('type') in ['markdown', 'text_span'] and block_locator.get('type') in ['markdown', 'text_span', 'text', 'txt']:
        gt_start = gt_locator.get('start_line')
        gt_end = gt_locator.get('end_line')
        bl_start = block_locator.get('start_line')
        bl_end = block_locator.get('end_line')
        if gt_start is not None and gt_end is not None and bl_start is not None and bl_end is not None:
            if max(gt_start, bl_start) <= min(gt_end, bl_end): return True
    if gt_locator.get('type') == 'page' and block_locator.get('type') == 'pdf':
        gt_page = gt_locator.get('pdf_page')
        for loc in block_locator.get('locations', []):
            if loc.get('pdf_page') == gt_page: return True
    return False

def load_blocks():
    blocks_by_doc = {}
    with open(blocks_path, 'r', encoding='utf-8') as f:
        for line in f:
            block = json.loads(line)
            blocks_by_doc.setdefault(block.get('document_id'), []).append(block)
    return blocks_by_doc

def load_chunks():
    conn = sqlite3.connect(db_path)
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

def evaluate_ranking(sorted_indices, chunks, target_blocks, k_list=[10, 50]):
    first_relevant_rank = None
    full_coverage_rank = None
    retrieved_blocks = set()
    num_targets = len(target_blocks)
    if num_targets == 0: return None
    
    coverage_at_k = {}
    for rank, idx in enumerate(sorted_indices, start=1):
        overlap = chunks[idx]['source_block_ids'].intersection(target_blocks)
        if overlap:
            if first_relevant_rank is None: first_relevant_rank = rank
            retrieved_blocks.update(overlap)
            if full_coverage_rank is None and len(retrieved_blocks) == num_targets:
                full_coverage_rank = rank
        if rank in k_list:
            coverage_at_k[rank] = len(retrieved_blocks) / num_targets
            
    for k in k_list:
        if k not in coverage_at_k:
            coverage_at_k[k] = len(retrieved_blocks) / num_targets
            
    return {
        "first_relevant_rank": first_relevant_rank if first_relevant_rank else 9999,
        "full_coverage_rank": full_coverage_rank if full_coverage_rank else 9999,
        "coverage_at_k": coverage_at_k
    }

def min_max_norm(scores):
    s_min, s_max = np.min(scores), np.max(scores)
    if s_max > s_min:
        return (scores - s_min) / (s_max - s_min)
    return np.zeros_like(scores)

def format_delta(val, base):
    delta = val - base
    if delta > 0: return f"+{delta:.4f}"
    if delta < 0: return f"{delta:.4f}"
    return "0.0000"

def main():
    print("Loading model...")
    model = SentenceTransformer('sentence-transformers/paraphrase-multilingual-mpnet-base-v2')
    
    print("Loading chunks...")
    blocks_by_doc = load_blocks()
    chunks = load_chunks()
    texts = [c['text'] for c in chunks]
    
    print("Embedding chunks...")
    dense_vecs = model.encode(texts, normalize_embeddings=True)
    
    print("Indexing BM25...")
    tokenized_corpus = [tokenize(t) for t in texts]
    bm25_index = BM25Okapi(tokenized_corpus)
    
    cases = []
    with open(dev_v2_path, 'r', encoding='utf-8') as f:
        for line in f: cases.append(json.loads(line))
            
    alphas = [round(a, 1) for a in np.arange(0.0, 1.1, 0.1)]
    configs = ["dense", "bm25", "rrf60"]
    for a in alphas:
        configs.append(f"mm_{a}")
        configs.append(f"sat_{a}")
        
    results = {case['case_id']: {cfg: None for cfg in configs} for case in cases}
    
    print("Evaluating Alpha Sweep...")
    for case in cases:
        case_id = case['case_id']
        query_text = case['query']['text']
        
        target_blocks = set()
        for ev in case.get('evidence', []):
            for b in blocks_by_doc.get(ev['document_id'], []):
                if match_locator(ev['locator'], b):
                    target_blocks.add(b['block_id'])
        if not target_blocks: continue
            
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
            rrf_scores[i] = (1.0 / (60 + dense_ranks[i])) + (1.0 / (60 + bm25_ranks[i]))
            
        # Normalization
        dense_mm = min_max_norm(dense_scores)
        bm25_mm = min_max_norm(bm25_scores)
        
        bm25_nonzero = bm25_scores[bm25_scores > 0]
        k_m = np.median(bm25_nonzero) if len(bm25_nonzero) > 0 else 1.0
        if k_m == 0: k_m = 1.0
        bm25_sat = bm25_scores / (bm25_scores + k_m)
        dense_sat = dense_scores
        
        sorted_indices = {
            "dense": np.argsort(dense_scores)[::-1],
            "bm25": np.argsort(bm25_scores)[::-1],
            "rrf60": np.argsort(rrf_scores)[::-1]
        }
        
        for a in alphas:
            mm_score = a * dense_mm + (1 - a) * bm25_mm
            sat_score = a * dense_sat + (1 - a) * bm25_sat
            sorted_indices[f"mm_{a}"] = np.argsort(mm_score)[::-1]
            sorted_indices[f"sat_{a}"] = np.argsort(sat_score)[::-1]
            
        for cfg in configs:
            results[case_id][cfg] = evaluate_ranking(sorted_indices[cfg], chunks, target_blocks)
            
    print("Generating report...")
    os.makedirs(os.path.dirname(report_path), exist_ok=True)
    with open(report_path, 'w', encoding='utf-8') as f:
        f.write("# POC M4-E Alpha Robustness Sweep Report\n\n")
        f.write("> **Dataset Status:** Frozen\n")
        f.write(f"> **Evaluated Cases:** {len([c for c in cases if results[c['case_id']]['dense'] is not None])}\n\n")
        
        valid_cases = [cid for cid, res in results.items() if res["dense"] is not None]
        
        def compute_aggregate(cfg):
            mrr_first = np.mean([1.0 / results[cid][cfg]['first_relevant_rank'] for cid in valid_cases])
            mrr_full = np.mean([1.0 / results[cid][cfg]['full_coverage_rank'] for cid in valid_cases])
            cov10 = np.mean([results[cid][cfg]['coverage_at_k'][10] for cid in valid_cases])
            cov50 = np.mean([results[cid][cfg]['coverage_at_k'][50] for cid in valid_cases])
            return mrr_first, mrr_full, cov10, cov50
            
        baselines = {}
        for base in ["dense", "bm25", "rrf60"]:
            baselines[base] = compute_aggregate(base)
            
        f.write("## 1. Baselines\n\n")
        f.write("| Baseline | MRR First | MRR Full | Cov@10 | Cov@50 |\n")
        f.write("|---|---:|---:|---:|---:|\n")
        f.write(f"| Dense | {baselines['dense'][0]:.4f} | {baselines['dense'][1]:.4f} | {baselines['dense'][2]:.2%} | {baselines['dense'][3]:.2%} |\n")
        f.write(f"| BM25 | {baselines['bm25'][0]:.4f} | {baselines['bm25'][1]:.4f} | {baselines['bm25'][2]:.2%} | {baselines['bm25'][3]:.2%} |\n")
        f.write(f"| RRF (k=60) | {baselines['rrf60'][0]:.4f} | {baselines['rrf60'][1]:.4f} | {baselines['rrf60'][2]:.2%} | {baselines['rrf60'][3]:.2%} |\n\n")
        
        def write_decision_matrix(title, prefix):
            f.write(f"## {title} Alpha Decision Matrix\n\n")
            f.write("| Alpha | MRR First | MRR Full | Cov@10 | Cov@50 | Critical Failures (Manual) | Decision |\n")
            f.write("|---|---|---|---|---|---|---|\n")
            
            pareto_data = []
            for a in alphas:
                cfg = f"{prefix}_{a}"
                m1, mf, c10, c50 = compute_aggregate(cfg)
                # Show absolute and delta vs Dense
                d_m1 = format_delta(m1, baselines['dense'][0])
                d_mf = format_delta(mf, baselines['dense'][1])
                
                f.write(f"| {a:.1f} | **{m1:.4f}** ({d_m1}) | **{mf:.4f}** ({d_mf}) | {c10:.2%} | {c50:.2%} | [ ] | [ ] |\n")
                pareto_data.append((a, m1, mf))
                
            return pareto_data

        pareto_mm = write_decision_matrix("2. Min-Max", "mm")
        f.write("\n")
        pareto_sat = write_decision_matrix("3. Saturation", "sat")
        f.write("\n")
        
        f.write("## 4. Pareto View (Sorted by Primary Objective: MRR Full)\n\n")
        f.write("| Strategy | Alpha | MRR Full (Primary) | MRR First (Guardrail) |\n")
        f.write("|---|---|---:|---:|\n")
        
        combined_pareto = [("Min-Max", a, m1, mf) for a, m1, mf in pareto_mm] + [("Saturation", a, m1, mf) for a, m1, mf in pareto_sat]
        combined_pareto.sort(key=lambda x: x[3], reverse=True) # Sort by MRR Full desc
        
        for strat, a, m1, mf in combined_pareto:
            f.write(f"| {strat} | {a:.1f} | **{mf:.4f}** | {m1:.4f} |\n")
            
    print(f"Report saved to {report_path}")

if __name__ == '__main__':
    main()
