"""
m6_step1_prepare_ground_truth.py
=================================
Generate unannotated Ground Truth dataset for M6 Check 1 (Evidence Sufficiency).

Reads  : evaluation/datasets/test-v3.jsonl (Dev Set)
Writes : evaluation/datasets/m6_dev_sufficiency_ground_truth.jsonl
"""

import gc
import json
import os
import re
import sqlite3
import sys
import subprocess
from datetime import datetime, timezone

import numpy as np
from rank_bm25 import BM25Okapi
from tqdm import tqdm

# ── CONFIGURATION ─────────────────────────────────────────────────────────────
DATASET_FILE            = "test-v3.jsonl"
OUTPUT_FILE             = "m6_dev_sufficiency_ground_truth.jsonl"
GATE_SCORE_THRESHOLD    = 0.20
GATE_RANK_THRESHOLD     = 1
DENSE_ALPHA             = 0.4
BM25_ALPHA              = 0.6
CANDIDATE_DENSE_TOP_K   = 20
CANDIDATE_BM25_TOP_K    = 20
DENSE_MODEL_NAME        = "sentence-transformers/paraphrase-multilingual-mpnet-base-v2"

# ── PATHS ─────────────────────────────────────────────────────────────────────
ROOT          = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
DB_PATH       = os.path.join(ROOT, "index",      "m3_index.db")
DATASET_PATH  = os.path.join(ROOT, "datasets",   DATASET_FILE)
OUTPUT_PATH   = os.path.join(ROOT, "datasets",   OUTPUT_FILE)
DENSE_TMP     = os.path.join(ROOT, "results",    "m6_dev_dense_tmp.json")
CE_SCORES_TMP = os.path.join(ROOT, "results",    "m6_dev_ce_tmp.json")
CE_RUNNER     = os.path.join(os.path.dirname(os.path.abspath(__file__)), "m6_step1_ce_runner.py")


def tokenize(text: str) -> list:
    return re.findall(r"\w+", text.lower())


def min_max_norm(scores: np.ndarray) -> np.ndarray:
    lo, hi = np.min(scores), np.max(scores)
    if hi > lo:
        return (scores - lo) / (hi - lo)
    return np.zeros_like(scores)


def build_candidate_pools(cases: list):
    import torch
    from sentence_transformers import SentenceTransformer, util

    os.environ["HF_HUB_OFFLINE"]      = "1"
    os.environ["TRANSFORMERS_OFFLINE"] = "1"

    print("Loading corpus from SQLite...")
    conn = sqlite3.connect(DB_PATH)
    rows = conn.execute("SELECT chunk_id, document_id, text FROM embeddings").fetchall()
    conn.close()

    chunks = []
    for chunk_id, doc_id, text in rows:
        chunks.append({"chunk_id": chunk_id, "text": text})
    del rows
    corpus_texts = [c["text"] for c in chunks]

    print("Loading Dense model...")
    dense_model = SentenceTransformer(DENSE_MODEL_NAME, local_files_only=True)
    dense_embs  = dense_model.encode(corpus_texts, normalize_embeddings=True, convert_to_tensor=True, show_progress_bar=True)

    query_texts = [c["query"]["text"] for c in cases]
    query_embs  = dense_model.encode(query_texts, normalize_embeddings=True, convert_to_tensor=True, show_progress_bar=True)

    print("Building BM25 index...")
    bm25 = BM25Okapi([tokenize(t) for t in corpus_texts])

    print("Building candidate pools...")
    pool_data = []
    for q_idx, case in enumerate(tqdm(cases)):
        case_id    = case["case_id"]
        query_text = case["query"]["text"]

        dense_scores = util.cos_sim(query_embs[q_idx], dense_embs)[0].cpu().numpy()
        bm25_scores  = np.array(bm25.get_scores(tokenize(query_text)))

        dense_sorted = np.argsort(dense_scores)[::-1]
        bm25_sorted  = np.argsort(bm25_scores)[::-1]

        pool_indices = list(set(dense_sorted[:CANDIDATE_DENSE_TOP_K].tolist()) |
                            set(bm25_sorted[:CANDIDATE_BM25_TOP_K].tolist()))

        pd = dense_scores[pool_indices]; pd_mm = min_max_norm(pd)
        pb = bm25_scores[pool_indices];  pb_mm = min_max_norm(pb)
        pool_fusion = DENSE_ALPHA * pd_mm + BM25_ALPHA * pb_mm
        baseline_order = np.argsort(pool_fusion)[::-1]
        baseline_pool = [pool_indices[i] for i in baseline_order]

        baseline_chunks = []
        baseline_scores = []
        for i, idx in enumerate(baseline_order):
            real_idx = pool_indices[idx]
            baseline_chunks.append({
                "chunk_id": chunks[real_idx]["chunk_id"],
                "text": chunks[real_idx]["text"]
            })
            baseline_scores.append(float(pool_fusion[idx]))

        pool_data.append({
            "query_id": case_id,
            "query_text": query_text,
            "baseline_chunks": baseline_chunks,
            "baseline_fusion_scores": baseline_scores
        })

    with open(DENSE_TMP, "w", encoding="utf-8") as f:
        json.dump(pool_data, f)

    del dense_model, dense_embs, query_embs, bm25, corpus_texts
    gc.collect()
    if hasattr(torch.cuda, "empty_cache"):
        torch.cuda.empty_cache()


def run_ce_subprocess():
    ret = subprocess.run([sys.executable, CE_RUNNER])
    if ret.returncode != 0:
        print(f"[ERROR] CE subprocess failed with code {ret.returncode}")
        sys.exit(1)


def generate_ground_truth():
    with open(CE_SCORES_TMP, encoding="utf-8") as f:
        cases = json.load(f)

    out_records = []
    
    for case in cases:
        ce_scores = np.array(case["ce_scores_aligned_to_baseline"])
        bge_order = np.argsort(ce_scores)[::-1]
        
        bge_top1_idx = int(bge_order[0])
        bge_top1_score = float(ce_scores[bge_top1_idx])
        
        bge_top2_score = float(ce_scores[bge_order[1]]) if len(bge_order) > 1 else bge_top1_score
        bge_score_gap = bge_top1_score - bge_top2_score

        baseline_rank_of_bge_top1 = bge_top1_idx + 1
        baseline_top1_score = case["baseline_fusion_scores"][0]

        # Apply M5 Frozen Gate
        score_pass = bge_top1_score >= GATE_SCORE_THRESHOLD
        rank_pass = baseline_rank_of_bge_top1 <= GATE_RANK_THRESHOLD
        gate_allow = score_pass or rank_pass
        gate_action = "BGE" if gate_allow else "BASELINE"

        # Select Final Evidence Chunk
        if gate_action == "BGE":
            final_chunk = case["baseline_chunks"][bge_top1_idx]
        else:
            final_chunk = case["baseline_chunks"][0]

        record = {
            "query_id": case["query_id"],
            "query": case["query_text"],
            "retrieved_context": [
                {
                    "chunk_id": final_chunk["chunk_id"],
                    "text": final_chunk["text"]
                }
            ],
            "signals": {
                "baseline_top1_score": round(baseline_top1_score, 4),
                "bge_top1_score": round(bge_top1_score, 4),
                "bge_top2_score": round(bge_top2_score, 4),
                "bge_score_gap": round(bge_score_gap, 4),
                "gate_action": gate_action,
                "baseline_rank_of_bge_top1": baseline_rank_of_bge_top1
            },
            "ground_truth_label": None,
            "label_rationale": "",
            "annotator": "",
            "annotated_at": ""
        }
        out_records.append(record)

    with open(OUTPUT_PATH, "w", encoding="utf-8") as f:
        for r in out_records:
            f.write(json.dumps(r, ensure_ascii=False) + "\n")
            
    print(f"\n[DONE] Generated {len(out_records)} records to {OUTPUT_PATH}")
    
    # Verifications
    print("\n--- Verifications ---")
    print(f"✓ {len(out_records)}/{len(cases)} queries processed")
    chunks_ok = all(len(r["retrieved_context"]) == 1 for r in out_records)
    print(f"✓ {len(out_records)}/{len(cases)} cases have exactly 1 final retrieved chunk: {chunks_ok}")
    signals_ok = all(len(r["signals"]) == 6 for r in out_records)
    print(f"✓ {len(out_records)}/{len(cases)} cases have complete raw signals: {signals_ok}")


def main():
    print("=" * 60)
    print("M6 Check 1 - Ground Truth Preparation")
    print("=" * 60)

    cases = []
    with open(DATASET_PATH, encoding="utf-8") as f:
        for line in f:
            if line.strip():
                cases.append(json.loads(line))

    build_candidate_pools(cases)
    print("\nSpawning CE runner subprocess...")
    run_ce_subprocess()
    print("\nGenerating final ground truth JSONL...")
    generate_ground_truth()


if __name__ == "__main__":
    main()
