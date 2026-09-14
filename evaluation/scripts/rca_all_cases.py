import json
import sqlite3
import numpy as np
import re
import os
from sentence_transformers import SentenceTransformer
from rank_bm25 import BM25Okapi

ROOT = "d:/Personal Project/AWS StudyBot/evaluation"
DB_PATH = f"{ROOT}/index/m3_index.db"
BLOCKS_PATH = f"{ROOT}/bundle_all/blocks.jsonl"
DATASET_PATH = f"{ROOT}/datasets/test-v2.jsonl"
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
                
    results_md = []
    results_md.append("# RCA: 24 Cases Diagnostics\n")
    
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
                    
        overlapping_chunks = []
        for idx, chunk in enumerate(chunks):
            if chunk['source_block_ids'].intersection(target_blocks):
                overlapping_chunks.append((idx, chunk))
                
        if not overlapping_chunks:
            results_md.append(f"## {case_id} \n- **Query:** {query_text}\n- **ERROR:** Target block not in any chunk!\n")
            continue
            
        results_md.append(f"## {case_id} (Tags: {', '.join(tags)})")
        results_md.append(f"**Query:** {query_text}")
        results_md.append(f"**Found {len(overlapping_chunks)} overlapping chunks:**\n")
        
        query_vec = model.encode(query_text, normalize_embeddings=True)
        tokenized_query = tokenize(query_text)
        
        dense_scores_all = np.dot(dense_vecs, query_vec)
        bm25_scores_all = bm25_index.get_scores(tokenized_query)
        
        for chunk_idx, chunk in overlapping_chunks:
            dense_score = np.dot(dense_vecs[chunk_idx], query_vec)
            bm25_score = bm25_index.get_scores(tokenized_query)[chunk_idx]
            
            dense_rank = (dense_scores_all > dense_score).sum() + 1
            bm25_rank = (bm25_scores_all > bm25_score).sum() + 1
            
            results_md.append(f"### Chunk ID: {chunk['chunk_id']}")
            results_md.append(f"```text\n{chunk['text']}\n```")
            results_md.append(f"- **Dense Score:** {dense_score:.4f} (Rank: {dense_rank})")
            results_md.append(f"- **BM25 Score:** {bm25_score:.4f} (Rank: {bm25_rank})\n")
            
        results_md.append("---\n")
        
    out_path = f"{ROOT}/results/rca_all_cases_output.md"
    with open(out_path, "w", encoding='utf-8') as f:
        f.write("\n".join(results_md))
        
    print(f"Done. RCA saved to {out_path}")

if __name__ == "__main__":
    main()
