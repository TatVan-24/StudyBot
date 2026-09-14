import json
import sqlite3
import numpy as np
import re
import os
from sentence_transformers import SentenceTransformer
from rank_bm25 import BM25Okapi

db_path = "d:/Personal Project/AWS StudyBot/evaluation/index/m3_index.db"
dev_v2_path = "d:/Personal Project/AWS StudyBot/evaluation/datasets/development-v2.jsonl"
blocks_path = "d:/Personal Project/AWS StudyBot/evaluation/bundle_all/blocks.jsonl"
output_path = "d:/Personal Project/AWS StudyBot/idea/demo/case9_raw_trace.md"

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

def main():
    print("Loading chunks...")
    conn = sqlite3.connect(db_path)
    c = conn.cursor()
    c.execute('SELECT chunk_id, document_id, text, source_block_ids FROM embeddings')
    rows = c.fetchall()
    conn.close()
    
    chunks = []
    texts = []
    for r in rows:
        chunks.append({
            "chunk_id": r[0],
            "text": r[2],
            "source_block_ids": set(json.loads(r[3]) if r[3] else [])
        })
        texts.append(r[2])
        
    print("Loading blocks & resolving target...")
    blocks_by_doc = {}
    with open(blocks_path, 'r', encoding='utf-8') as f:
        for line in f:
            b = json.loads(line)
            blocks_by_doc.setdefault(b.get('document_id'), []).append(b)
            
    target_case = None
    with open(dev_v2_path, 'r', encoding='utf-8') as f:
        for line in f:
            case = json.loads(line)
            if case['case_id'] == "eval_wiki_s3_features_001":
                target_case = case
                break
                
    target_blocks = set()
    for ev in target_case.get('evidence', []):
        for b in blocks_by_doc.get(ev['document_id'], []):
            if match_locator(ev['locator'], b):
                target_blocks.add(b['block_id'])

    print("Embedding Dense...")
    model = SentenceTransformer('sentence-transformers/paraphrase-multilingual-mpnet-base-v2')
    dense_vecs = model.encode(texts, normalize_embeddings=True)
    
    print("Indexing BM25...")
    tokenized_corpus = [tokenize(t) for t in texts]
    bm25_index = BM25Okapi(tokenized_corpus)
    
    query_text = target_case['query']['text']
    
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
    
    # Hybrid RRF
    rrf_scores = np.zeros(len(chunks))
    for i in range(len(chunks)):
        rrf_scores[i] = (1.0 / (60 + dense_ranks[i])) + (1.0 / (60 + bm25_ranks[i]))
    
    hybrid_sorted_indices = np.argsort(rrf_scores)[::-1]
    
    # Generate Output
    print("Writing output...")
    os.makedirs(os.path.dirname(output_path), exist_ok=True)
    with open(output_path, 'w', encoding='utf-8') as f:
        f.write("# Case 9 Raw Trace (Top 24 Hybrid RRF)\n\n")
        f.write(f"**Query**: {query_text}\n\n")
        
        f.write("| Rank RRF | Chunk | Dense Rank | Dense Score | BM25 Rank | BM25 Score | RRF Score | Target? | Chunk Text Snippet |\n")
        f.write("|---:|---|---:|---:|---:|---:|---:|:---:|---|\n")
        
        for rank in range(1, 25): # Top 24
            idx = hybrid_sorted_indices[rank-1]
            c = chunks[idx]
            is_target = "✅" if c['source_block_ids'].intersection(target_blocks) else "❌"
            
            snippet = c['text'].replace('\n', ' ')[:60] + "..."
            
            f.write(f"| {rank} | `{c['chunk_id'][:8]}` | {dense_ranks[idx]} | {dense_scores[idx]:.4f} | {bm25_ranks[idx]} | {bm25_scores[idx]:.4f} | {rrf_scores[idx]:.5f} | {is_target} | {snippet} |\n")
            
    print(f"Done! Trace written to {output_path}")

if __name__ == '__main__':
    main()
