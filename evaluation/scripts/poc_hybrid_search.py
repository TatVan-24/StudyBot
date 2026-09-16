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
report_path = "d:/Personal Project/AWS StudyBot/idea/demo/poc_hybrid_search_report.md"

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
            if max(gt_start, bl_start) <= min(gt_end, bl_end):
                return True
                
    if gt_locator.get('type') == 'page' and block_locator.get('type') == 'pdf':
        gt_page = gt_locator.get('pdf_page')
        locations = block_locator.get('locations', [])
        for loc in locations:
            if loc.get('pdf_page') == gt_page:
                return True
    return False

def load_blocks():
    blocks_by_doc = {}
    with open(blocks_path, 'r', encoding='utf-8') as f:
        for line in f:
            block = json.loads(line)
            doc_id = block.get('document_id')
            if doc_id not in blocks_by_doc:
                blocks_by_doc[doc_id] = []
            blocks_by_doc[doc_id].append(block)
    return blocks_by_doc

def load_chunks():
    conn = sqlite3.connect(db_path)
    c = conn.cursor()
    c.execute('SELECT chunk_id, document_id, text, source_block_ids FROM embeddings')
    rows = c.fetchall()
    conn.close()
    
    chunks = []
    for r in rows:
        chunk_id, doc_id, text, sbi_str = r
        source_block_ids = json.loads(sbi_str) if sbi_str else []
        chunks.append({
            "chunk_id": chunk_id,
            "document_id": doc_id,
            "text": text,
            "source_block_ids": set(source_block_ids)
        })
    return chunks

def evaluate_ranking(sorted_indices, chunks, target_blocks, k_list=[1, 5, 10, 20, 50, 100, 1000]):
    first_relevant_rank = None
    full_coverage_rank = None
    retrieved_blocks = set()
    num_targets = len(target_blocks)
    
    if num_targets == 0:
        return None
        
    coverage_at_k = {}
    
    for rank, idx in enumerate(sorted_indices, start=1):
        c = chunks[idx]
        overlap = c['source_block_ids'].intersection(target_blocks)
        if overlap:
            if first_relevant_rank is None:
                first_relevant_rank = rank
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

def main():
    print("Loading model...")
    model = SentenceTransformer('sentence-transformers/paraphrase-multilingual-mpnet-base-v2')
    
    print("Loading blocks and chunks...")
    blocks_by_doc = load_blocks()
    chunks = load_chunks()
    texts = [c['text'] for c in chunks]
    
    print("Embedding chunks (Dense)...")
    dense_vecs = model.encode(texts, normalize_embeddings=True)
    
    print("Indexing chunks (BM25)...")
    tokenized_corpus = [tokenize(t) for t in texts]
    bm25_index = BM25Okapi(tokenized_corpus)
    
    cases = []
    with open(dev_v2_path, 'r', encoding='utf-8') as f:
        for line in f:
            cases.append(json.loads(line))
            
    k_values = [1, 10, 60, 100]
    results = {}
    deep_dive = {}
    
    print("Evaluating cases...")
    for case in cases:
        case_id = case['case_id']
        query_text = case['query']['text']
        
        target_blocks = set()
        for ev in case.get('evidence', []):
            doc_id = ev['document_id']
            gt_locator = ev['locator']
            for b in blocks_by_doc.get(doc_id, []):
                if match_locator(gt_locator, b):
                    target_blocks.add(b['block_id'])
                    
        if not target_blocks:
            continue
            
        # Dense
        query_vec = model.encode(query_text, normalize_embeddings=True)
        dense_scores = np.dot(dense_vecs, query_vec)
        dense_sorted_indices = np.argsort(dense_scores)[::-1]
        dense_ranks = {idx: rank for rank, idx in enumerate(dense_sorted_indices, start=1)}
        
        # BM25
        tokenized_query = tokenize(query_text)
        bm25_scores = bm25_index.get_scores(tokenized_query)
        bm25_sorted_indices = np.argsort(bm25_scores)[::-1]
        bm25_ranks = {idx: rank for rank, idx in enumerate(bm25_sorted_indices, start=1)}
        
        case_res = {
            "dense": evaluate_ranking(dense_sorted_indices, chunks, target_blocks),
            "bm25": evaluate_ranking(bm25_sorted_indices, chunks, target_blocks)
        }
        
        traces = []
        
        for k in k_values:
            rrf_scores = np.zeros(len(chunks))
            for i in range(len(chunks)):
                rrf_scores[i] = (1.0 / (k + dense_ranks[i])) + (1.0 / (k + bm25_ranks[i]))
            hybrid_sorted_indices = np.argsort(rrf_scores)[::-1]
            hybrid_ranks = {idx: rank for rank, idx in enumerate(hybrid_sorted_indices, start=1)}
            case_res[f"hybrid_k{k}"] = evaluate_ranking(hybrid_sorted_indices, chunks, target_blocks)
            
            # Trace targets
            if case_id in ["eval_txt_kafka_recovery_001", "eval_wiki_s3_features_001"]:
                for i, c in enumerate(chunks):
                    if c['source_block_ids'].intersection(target_blocks):
                        traces.append({
                            "k_val": k,
                            "chunk_id": c["chunk_id"],
                            "dense_rank": dense_ranks[i],
                            "bm25_rank": bm25_ranks[i],
                            "hybrid_rank": hybrid_ranks[i]
                        })
                        
        results[case_id] = case_res
        if traces:
            deep_dive[case_id] = {
                "query": query_text,
                "traces": traces
            }

    print("Generating report...")
    os.makedirs(os.path.dirname(report_path), exist_ok=True)
    with open(report_path, 'w', encoding='utf-8') as f:
        f.write("# POC M4-B RRF K-Sweep Report\n\n")
        
        f.write("## 1. Aggregate Coverage Comparison\n\n")
        metrics_k = [1, 5, 10, 20, 50, 100]
        f.write("| Metric | Dense | BM25 | RRF (k=1) | RRF (k=10) | RRF (k=60) | RRF (k=100) |\n")
        f.write("|---|---|---|---|---|---|---|\n")
        for mk in metrics_k:
            d_mean = np.mean([r['dense']['coverage_at_k'][mk] for r in results.values()])
            b_mean = np.mean([r['bm25']['coverage_at_k'][mk] for r in results.values()])
            h1_mean = np.mean([r['hybrid_k1']['coverage_at_k'][mk] for r in results.values()])
            h10_mean = np.mean([r['hybrid_k10']['coverage_at_k'][mk] for r in results.values()])
            h60_mean = np.mean([r['hybrid_k60']['coverage_at_k'][mk] for r in results.values()])
            h100_mean = np.mean([r['hybrid_k100']['coverage_at_k'][mk] for r in results.values()])
            f.write(f"| Coverage@{mk} | {d_mean:.2%} | {b_mean:.2%} | {h1_mean:.2%} | {h10_mean:.2%} | {h60_mean:.2%} | {h100_mean:.2%} |\n")
            
        f.write("\n## 2. K-Sweep First Rank Matrix\n\n")
        f.write("| Case | Dense | BM25 | RRF (k=1) | RRF (k=10) | RRF (k=60) | RRF (k=100) |\n")
        f.write("|---|---:|---:|---:|---:|---:|---:|\n")
        for case_id, res in results.items():
            f.write(f"| {case_id} | {res['dense']['first_relevant_rank']} | {res['bm25']['first_relevant_rank']} | {res['hybrid_k1']['first_relevant_rank']} | {res['hybrid_k10']['first_relevant_rank']} | {res['hybrid_k60']['first_relevant_rank']} | {res['hybrid_k100']['first_relevant_rank']} |\n")
            
        f.write("\n## 3. Rank-Disagreement Deep Dive\n\n")
        for case_id, info in deep_dive.items():
            if case_id == "eval_txt_kafka_recovery_001":
                f.write("### Case 6 (Sibling Crowding / Exact Keyword Rescue)\n")
            elif case_id == "eval_wiki_s3_features_001":
                f.write("### Case 9 (Missing Entity Anchor)\n")
                
            f.write(f"**Query**: {info['query']}\n\n")
            f.write("| Chunk ID | Dense Rank | BM25 Rank | Hybrid Rank (k=1) | Hybrid Rank (k=10) | Hybrid Rank (k=60) | Hybrid Rank (k=100) |\n")
            f.write("|---|---:|---:|---:|---:|---:|---:|\n")
            
            # Group traces by chunk_id
            chunk_traces = {}
            for t in info['traces']:
                cid = t['chunk_id'][:12]
                if cid not in chunk_traces:
                    chunk_traces[cid] = {"dense": t["dense_rank"], "bm25": t["bm25_rank"], "hybrid": {}}
                chunk_traces[cid]["hybrid"][t["k_val"]] = t["hybrid_rank"]
                
            for cid, ranks in chunk_traces.items():
                f.write(f"| `{cid}` | {ranks['dense']} | {ranks['bm25']} | {ranks['hybrid'][1]} | {ranks['hybrid'][10]} | {ranks['hybrid'][60]} | {ranks['hybrid'][100]} |\n")
            f.write("\n")
            
    print(f"Report saved to {report_path}")

if __name__ == '__main__':
    main()
