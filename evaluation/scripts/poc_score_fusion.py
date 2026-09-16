import json
import os
import sqlite3
import numpy as np
import re
from sentence_transformers import SentenceTransformer
from rank_bm25 import BM25Okapi

dev_v2_path = "d:/Personal Project/AWS StudyBot/evaluation/datasets/development-v2.jsonl"
blocks_path = "d:/Personal Project/AWS StudyBot/evaluation/bundle_all/blocks.jsonl"
db_path = "d:/Personal Project/AWS StudyBot/evaluation/index/m3_index.db"
report_path = "d:/Personal Project/AWS StudyBot/idea/demo/poc_score_fusion_report.md"

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

def evaluate_ranking(sorted_indices, chunks, target_blocks, k_list=[1, 5, 10, 20, 50, 100, 1000]):
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
            
    alphas = [0.3, 0.5, 0.7]
    configs = ["dense", "bm25", "rrf60"]
    for a in alphas:
        configs.append(f"mm_{a}")
        configs.append(f"sat_{a}")
        
    results = {case['case_id']: {cfg: None for cfg in configs} for case in cases}
    deep_dive = {}
    
    print("Evaluating Score Fusion...")
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
            
        # Min-Max Normalization
        dense_mm = min_max_norm(dense_scores)
        bm25_mm = min_max_norm(bm25_scores)
        
        # Saturation Normalization
        bm25_nonzero = bm25_scores[bm25_scores > 0]
        k_m = np.median(bm25_nonzero) if len(bm25_nonzero) > 0 else 1.0
        if k_m == 0: k_m = 1.0
        bm25_sat = bm25_scores / (bm25_scores + k_m)
        dense_sat = dense_scores
        
        # Rankings
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
            
        # Evaluate
        for cfg in configs:
            results[case_id][cfg] = evaluate_ranking(sorted_indices[cfg], chunks, target_blocks)
            
        # Track traces
        if case_id in ["eval_txt_kafka_recovery_001", "eval_wiki_s3_features_001"]:
            case_traces = []
            for i, c in enumerate(chunks):
                if c['source_block_ids'].intersection(target_blocks):
                    trace_obj = {
                        "chunk_id": c["chunk_id"],
                        "dense_raw": float(dense_scores[i]),
                        "bm25_raw": float(bm25_scores[i]),
                        "dense_rank": dense_ranks[i],
                        "bm25_rank": bm25_ranks[i],
                        "rrf60_rank": np.where(sorted_indices["rrf60"] == i)[0][0] + 1
                    }
                    for a in alphas:
                        trace_obj[f"mm_{a}_rank"] = np.where(sorted_indices[f"mm_{a}"] == i)[0][0] + 1
                        trace_obj[f"sat_{a}_rank"] = np.where(sorted_indices[f"sat_{a}"] == i)[0][0] + 1
                    case_traces.append(trace_obj)
            deep_dive[case_id] = {"query": query_text, "traces": case_traces}

    print("Generating report...")
    os.makedirs(os.path.dirname(report_path), exist_ok=True)
    with open(report_path, 'w', encoding='utf-8') as f:
        f.write("# POC M4-D Score-based Fusion Report (Extended)\n\n")
        
        f.write("## 1. Aggregate MRR Comparison\n\n")
        f.write("| Metric | Dense | BM25 | RRF (k=60) | MM (a=0.3) | MM (a=0.5) | MM (a=0.7) | Sat (a=0.3) | Sat (a=0.5) | Sat (a=0.7) |\n")
        f.write("|---|---|---|---|---|---|---|---|---|---|\n")
        valid_cases = [cid for cid, res in results.items() if res["dense"] is not None]
        
        mrr_first_means = {}
        mrr_full_means = {}
        for cfg in configs:
            mrr_first_means[cfg] = np.mean([1.0 / results[cid][cfg]['first_relevant_rank'] for cid in valid_cases])
            mrr_full_means[cfg] = np.mean([1.0 / results[cid][cfg]['full_coverage_rank'] for cid in valid_cases])
            
        f.write("| MRR First | " + " | ".join([f"{mrr_first_means[c]:.4f}" for c in configs]) + " |\n")
        f.write("| MRR Full | " + " | ".join([f"{mrr_full_means[c]:.4f}" for c in configs]) + " |\n\n")

        f.write("## 2. Aggregate Coverage Comparison\n\n")
        k_list = [1, 5, 10, 20, 50, 100]
        f.write("| Metric | Dense | BM25 | RRF (k=60) | MM (a=0.3) | MM (a=0.5) | MM (a=0.7) | Sat (a=0.3) | Sat (a=0.5) | Sat (a=0.7) |\n")
        f.write("|---|---|---|---|---|---|---|---|---|---|\n")
        for k in k_list:
            means = {cfg: np.mean([results[cid][cfg]['coverage_at_k'][k] for cid in valid_cases]) for cfg in configs}
            f.write(f"| Coverage@{k} | " + " | ".join([f"{means[c]:.2%}" for c in configs]) + " |\n")
            
        f.write("\n## 3. First Relevant Rank Matrix\n\n")
        f.write("| Case | Dense | BM25 | RRF (k=60) | MM (0.3) | MM (0.5) | MM (0.7) | Sat (0.3) | Sat (0.5) | Sat (0.7) |\n")
        f.write("|---|---:|---:|---:|---:|---:|---:|---:|---:|---:|\n")
        for cid in valid_cases:
            ranks = [str(results[cid][cfg]['first_relevant_rank']) for cfg in configs]
            f.write(f"| {cid} | " + " | ".join(ranks) + " |\n")
            
        f.write("\n## 4. Full Coverage Rank Matrix\n\n")
        f.write("| Case | Dense | BM25 | RRF (k=60) | MM (0.3) | MM (0.5) | MM (0.7) | Sat (0.3) | Sat (0.5) | Sat (0.7) |\n")
        f.write("|---|---:|---:|---:|---:|---:|---:|---:|---:|---:|\n")
        for cid in valid_cases:
            ranks = [str(results[cid][cfg]['full_coverage_rank']) for cfg in configs]
            f.write(f"| {cid} | " + " | ".join(ranks) + " |\n")
            
        f.write("\n## 5. Alpha Sensitivity Deep Dive (Case 6 & Case 9)\n\n")
        for cid, info in deep_dive.items():
            f.write(f"### {cid}\n**Query**: {info['query']}\n\n")
            f.write("| Chunk ID | D Rank (Score) | B Rank (Score) | RRF Rank | MM 0.3 | MM 0.5 | MM 0.7 | Sat 0.3 | Sat 0.5 | Sat 0.7 |\n")
            f.write("|---|---|---|---:|---:|---:|---:|---:|---:|---:|\n")
            for t in info['traces']:
                cid_short = t['chunk_id'][:8]
                dr = f"{t['dense_rank']} ({t['dense_raw']:.3f})"
                br = f"{t['bm25_rank']} ({t['bm25_raw']:.3f})"
                rrf = t['rrf60_rank']
                mm = f"{t['mm_0.3_rank']} | {t['mm_0.5_rank']} | {t['mm_0.7_rank']}"
                sat = f"{t['sat_0.3_rank']} | {t['sat_0.5_rank']} | {t['sat_0.7_rank']}"
                f.write(f"| `{cid_short}` | {dr} | {br} | {rrf} | {mm} | {sat} |\n")
            f.write("\n")
            
    print(f"Report saved to {report_path}")

if __name__ == '__main__':
    main()
