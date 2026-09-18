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
            
    total_failed_cases = 0
    in_top_10 = 0
    in_top_20 = 0
    out_of_top_20 = 0
    
    print("=== GATE B: Target Candidate Availability Analysis ===")
    
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
                
        # Only analyze failed cases (First Rank > 1)
        if first_hit_rank > 1:
            total_failed_cases += 1
            if target_idx != -1:
                d_rank = np.where(dense_sorted_indices == target_idx)[0][0] + 1
                b_rank = np.where(bm25_sorted_indices == target_idx)[0][0] + 1
                
                best_rank = min(d_rank, b_rank)
                
                if best_rank <= 10:
                    in_top_10 += 1
                    status = "TOP-10"
                elif best_rank <= 20:
                    in_top_20 += 1
                    status = "TOP-20"
                else:
                    out_of_top_20 += 1
                    status = "OUT (>20)"
                    
                print(f"{case_id}: Fusion #{first_hit_rank} | Dense #{d_rank} | BM25 #{b_rank} | => {status}")
            else:
                out_of_top_20 += 1
                print(f"{case_id}: ZERO HIT => OUT (>20)")
                
    print("\n=== GATE B SUMMARY ===")
    print(f"Total Failed Cases (Near Fails + Critical Fails): {total_failed_cases}")
    print(f"Target in Top 10 (Dense or BM25): {in_top_10} ({(in_top_10/total_failed_cases)*100:.1f}%)")
    print(f"Target in Top 11-20 (Dense or BM25): {in_top_20} ({(in_top_20/total_failed_cases)*100:.1f}%)")
    print(f"Target outside Top 20 (or Zero-Hit): {out_of_top_20} ({(out_of_top_20/total_failed_cases)*100:.1f}%)")
    
    total_in_20 = in_top_10 + in_top_20
    print(f"\n=> Tỷ lệ Target lọt vào Candidate Pool (Top 20): {total_in_20}/{total_failed_cases} ({(total_in_20/total_failed_cases)*100:.1f}%)")

if __name__ == "__main__":
    main()
