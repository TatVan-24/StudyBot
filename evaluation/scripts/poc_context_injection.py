import json
import os
import sqlite3
import numpy as np
from sentence_transformers import SentenceTransformer

dev_v2_path = "d:/Personal Project/AWS StudyBot/evaluation/datasets/development-v2.jsonl"
blocks_path = "d:/Personal Project/AWS StudyBot/evaluation/bundle_all/blocks.jsonl"
db_path = "d:/Personal Project/AWS StudyBot/evaluation/index/m3_index.db"
report_path = "d:/Personal Project/AWS StudyBot/idea/demo/poc_context_injection_report.md"

DOC_TITLES = {
    "pdf_aws_001": "AWS Cloud Computing Whitepaper",
    "txt_aiops_001": "AIOps and Observability Guide",
    "wiki_06_markdown_sample": "AWS Storage Overview"
}

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
    c.execute('SELECT chunk_id, document_id, text, heading_context, source_block_ids FROM embeddings')
    rows = c.fetchall()
    conn.close()
    
    chunks = []
    for r in rows:
        chunk_id, doc_id, text, hc_str, sbi_str = r
        heading_context = json.loads(hc_str) if hc_str else []
        source_block_ids = json.loads(sbi_str) if sbi_str else []
        
        doc_title = DOC_TITLES.get(doc_id, "")
        context_parts = [doc_title] + heading_context
        full_context = " > ".join([p for p in context_parts if p])
        context_text = f"{full_context}\n\n{text}" if full_context else text
        
        chunks.append({
            "chunk_id": chunk_id,
            "document_id": doc_id,
            "baseline_text": text,
            "context_text": context_text,
            "source_block_ids": set(source_block_ids)
        })
    return chunks

def evaluate_ranking(query_vec, chunk_vecs, chunks, target_blocks, k_list=[1, 5, 10, 15, 20, 50, 100, 1000]):
    scores = np.dot(chunk_vecs, query_vec)
    sorted_indices = np.argsort(scores)[::-1]
    
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
            coverage_at_k[rank] = {
                "retrieved_count": len(retrieved_blocks),
                "total_targets": num_targets,
                "coverage_pct": len(retrieved_blocks) / num_targets
            }
            
    for k in k_list:
        if k not in coverage_at_k:
            coverage_at_k[k] = {
                "retrieved_count": len(retrieved_blocks),
                "total_targets": num_targets,
                "coverage_pct": len(retrieved_blocks) / num_targets
            }
            
    return {
        "first_relevant_rank": first_relevant_rank if first_relevant_rank else 9999,
        "full_coverage_rank": full_coverage_rank if full_coverage_rank else 9999,
        "coverage_at_k": coverage_at_k,
        "total_targets": num_targets
    }

def main():
    print("Loading model...")
    model = SentenceTransformer('sentence-transformers/paraphrase-multilingual-mpnet-base-v2')
    
    print("Loading blocks and chunks...")
    blocks_by_doc = load_blocks()
    chunks = load_chunks()
    
    print("Embedding chunks...")
    baseline_texts = [c['baseline_text'] for c in chunks]
    context_texts = [c['context_text'] for c in chunks]
    
    baseline_vecs = model.encode(baseline_texts, normalize_embeddings=True)
    context_vecs = model.encode(context_texts, normalize_embeddings=True)
    
    cases = []
    with open(dev_v2_path, 'r', encoding='utf-8') as f:
        for line in f:
            cases.append(json.loads(line))
            
    results = {}
    queries = {}
    
    print("Evaluating cases...")
    for case in cases:
        case_id = case['case_id']
        query_text = case['query']['text']
        queries[case_id] = query_text
        
        target_blocks = set()
        for ev in case.get('evidence', []):
            doc_id = ev['document_id']
            gt_locator = ev['locator']
            for b in blocks_by_doc.get(doc_id, []):
                if match_locator(gt_locator, b):
                    target_blocks.add(b['block_id'])
                    
        if not target_blocks:
            print(f"Warning: {case_id} resolved to 0 blocks.")
            continue
            
        query_vec = model.encode(query_text, normalize_embeddings=True)
        
        res_baseline = evaluate_ranking(query_vec, baseline_vecs, chunks, target_blocks)
        res_context = evaluate_ranking(query_vec, context_vecs, chunks, target_blocks)
        
        results[case_id] = {
            "baseline": res_baseline,
            "context": res_context
        }
    
    print("Generating report...")
    os.makedirs(os.path.dirname(report_path), exist_ok=True)
    with open(report_path, 'w', encoding='utf-8') as f:
        f.write("# Context-aware embedding representation POC\n\n")
        f.write("**Intervention**: `embedding_input = document_title + heading_context + chunk.text`\n\n")
        
        f.write("## 1. Rank Comparison & Delta\n\n")
        f.write("| Case ID | Baseline First Rank | Context First Rank | Delta Rank | Baseline Full Rank | Context Full Rank |\n")
        f.write("|---------|---------------------|--------------------|------------|--------------------|-------------------|\n")
        for case_id, res in results.items():
            b = res['baseline']
            c = res['context']
            delta = c['first_relevant_rank'] - b['first_relevant_rank']
            delta_str = f"+{delta}" if delta > 0 else str(delta)
            f.write(f"| {case_id} | {b['first_relevant_rank']} | {c['first_relevant_rank']} | {delta_str} | {b['full_coverage_rank']} | {c['full_coverage_rank']} |\n")
            
        f.write("\n## 2. Coverage Curves (Per Case)\n\n")
        k_list = [1, 5, 10, 15, 20, 50, 100, 1000]
        
        for case_id, res in results.items():
            f.write(f"### {case_id}\n")
            f.write(f"- **Query**: {queries[case_id]}\n")
            f.write(f"- **Total evidence blocks**: {res['baseline']['total_targets']}\n\n")
            f.write("| K | Baseline Retrieved | Baseline Coverage | Context Retrieved | Context Coverage |\n")
            f.write("|---|--------------------|-------------------|-------------------|------------------|\n")
            for k in k_list:
                b_cov = res['baseline']['coverage_at_k'][k]
                c_cov = res['context']['coverage_at_k'][k]
                f.write(f"| {k} | {b_cov['retrieved_count']}/{b_cov['total_targets']} | {b_cov['coverage_pct']:.2%} | {c_cov['retrieved_count']}/{c_cov['total_targets']} | {c_cov['coverage_pct']:.2%} |\n")
            f.write("\n")
            
        f.write("## 3. Aggregate Comparison\n\n")
        f.write("| Metric | Baseline Mean | Context Mean |\n")
        f.write("|--------|---------------|--------------|\n")
        for k in k_list:
            b_mean = np.mean([r['baseline']['coverage_at_k'][k]['coverage_pct'] for r in results.values()])
            c_mean = np.mean([r['context']['coverage_at_k'][k]['coverage_pct'] for r in results.values()])
            f.write(f"| Mean Coverage@{k} | {b_mean:.2%} | {c_mean:.2%} |\n")
            
    print(f"Report saved to {report_path}")

if __name__ == '__main__':
    main()
