"""
m6_step1_ce_runner.py
======================
Isolated CE inference subprocess for M6 Ground Truth Preparation.
Reads  : evaluation/results/m6_dev_dense_tmp.json
Writes : evaluation/results/m6_dev_ce_tmp.json
"""

import json
import os
import sys
import torch
from sentence_transformers import CrossEncoder
from tqdm import tqdm

os.environ["HF_HUB_OFFLINE"]      = "1"
os.environ["TRANSFORMERS_OFFLINE"] = "1"

IN_FILE  = "evaluation/results/m6_dev_dense_tmp.json"
OUT_FILE = "evaluation/results/m6_dev_ce_tmp.json"
CE_MODEL = "BAAI/bge-reranker-v2-m3"


def run():
    with open(IN_FILE, "r", encoding="utf-8") as f:
        cases = json.load(f)

    print(f"[CE Runner] Loading {CE_MODEL} (float32, CPU)...")
    ce = CrossEncoder(
        CE_MODEL,
        local_files_only=True,
    )

    print(f"[CE Runner] Running CE inference on {len(cases)} cases...")
    for case in tqdm(cases):
        pairs  = [[case["query_text"], chunk["text"]] for chunk in case["baseline_chunks"]]
        scores = ce.predict(pairs)
        case["ce_scores_aligned_to_baseline"] = scores.tolist()

        # Persist chunk_ids aligned to baseline pool
        case["baseline_chunk_ids"] = [chunk.get("chunk_id", f"idx_{i}") for i, chunk in enumerate(case["baseline_chunks"])]
        
        # We do NOT delete baseline_chunks here because we need the text for the ground truth context later.

    with open(OUT_FILE, "w", encoding="utf-8") as f:
        json.dump(cases, f, indent=2)
    print(f"[CE Runner] Saved CE scores to {OUT_FILE}")


if __name__ == "__main__":
    run()
