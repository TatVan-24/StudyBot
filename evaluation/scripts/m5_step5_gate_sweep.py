"""
m5_step5_gate_sweep.py
======================
Reads raw CE + Baseline scores (generating them once if needed), then sweeps
over Gate parameters (T=BGE score threshold, R=Baseline-rank threshold) to
find the trade-off between A/B rescue and Strong-Anchor regression.

Input  : evaluation/index/m3_index.db
         evaluation/bundle_all/blocks.jsonl
         evaluation/datasets/test-v3.jsonl
Output : evaluation/results/m5_step5_raw_scores.json  (cached, generated once)
         Printed trade-off table
"""

import json
import os
import re
import sqlite3
import sys

import numpy as np
from rank_bm25 import BM25Okapi
from tqdm import tqdm

# ── Paths ──────────────────────────────────────────────────────────────────
ROOT         = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))   # .../evaluation
DB_PATH      = os.path.join(ROOT, "index",      "m3_index.db")
BLOCKS_PATH  = os.path.join(ROOT, "bundle_all", "blocks.jsonl")
DATASET_PATH = os.path.join(ROOT, "datasets",   "test-v3.jsonl")
RAW_DATA_PATH = os.path.join(ROOT, "results",   "m5_step5_raw_scores.json")

CE_MODEL_NAME    = "BAAI/bge-reranker-v2-m3"
DENSE_MODEL_NAME = "sentence-transformers/paraphrase-multilingual-mpnet-base-v2"


# ── Helpers (copied exactly from Step 3) ───────────────────────────────────

def tokenize(text: str) -> list:
    return re.findall(r"\w+", text.lower())


def min_max_norm(scores: np.ndarray) -> np.ndarray:
    lo, hi = np.min(scores), np.max(scores)
    if hi > lo:
        return (scores - lo) / (hi - lo)
    return np.zeros_like(scores)


def match_locator(gt_locator: dict, block: dict) -> bool:
    block_locator = block.get("locator", {})
    gt_type = gt_locator.get("type")
    bl_type = block_locator.get("type")

    if gt_type in ("markdown", "text_span", "txt") and bl_type in ("markdown", "text_span", "text", "txt"):
        gs, ge = gt_locator.get("start_line"), gt_locator.get("end_line")
        bs, be = block_locator.get("start_line"), block_locator.get("end_line")
        if None not in (gs, ge, bs, be):
            return max(gs, bs) <= min(ge, be)

    if gt_type in ("page", "pdf") and bl_type == "pdf":
        gt_page = gt_locator.get("pdf_page")
        if gt_page is None:
            locs = gt_locator.get("locations", [])
            if locs:
                gt_page = locs[0].get("pdf_page")
        for loc in block_locator.get("locations", []):
            if loc.get("pdf_page") == gt_page:
                return True

    return False


# ── Phase 1: generate raw scores (only once) ───────────────────────────────

def build_raw_data():
    """Run Dense + BM25 retrieval + CE scoring and cache to JSON."""
    print("Raw data not found — generating now (CE on CPU, expect 20-30 min)…")
    import gc
    import torch
    from sentence_transformers import SentenceTransformer, CrossEncoder, util
    from transformers import AutoModelForSequenceClassification, AutoTokenizer

    os.environ["HF_HUB_OFFLINE"]    = "1"
    os.environ["TRANSFORMERS_OFFLINE"] = "1"

    # ── Load test cases ────────────────────────────────────────────────────
    cases = []
    with open(DATASET_PATH, encoding="utf-8") as f:
        for line in f:
            if line.strip():
                cases.append(json.loads(line))

    # ── Load blocks index (for target resolution) ─────────────────────────
    blocks_by_doc: dict[str, list] = {}
    with open(BLOCKS_PATH, encoding="utf-8") as f:
        for line in f:
            if line.strip():
                b = json.loads(line)
                blocks_by_doc.setdefault(b.get("document_id"), []).append(b)

    # ── Load corpus from SQLite ────────────────────────────────────────────
    print("Loading corpus from SQLite…")
    conn = sqlite3.connect(DB_PATH)
    rows = conn.execute("SELECT chunk_id, document_id, text, source_block_ids FROM embeddings").fetchall()
    conn.close()

    chunks = []
    for chunk_id, doc_id, text, src_raw in rows:
        src = json.loads(src_raw) if src_raw else []
        chunks.append({"chunk_id": chunk_id, "text": text, "source_block_ids": set(src)})
    del rows
    corpus_texts = [c["text"] for c in chunks]

    # ── Dense model & embeddings ───────────────────────────────────────────
    print("Loading Dense Model…")
    dense_model = SentenceTransformer(DENSE_MODEL_NAME, local_files_only=True)
    dense_embs  = dense_model.encode(corpus_texts, normalize_embeddings=True,
                                     convert_to_tensor=True, show_progress_bar=True)

    query_texts = [c["query"]["text"] for c in cases]
    query_embs  = dense_model.encode(query_texts, normalize_embeddings=True,
                                     convert_to_tensor=True, show_progress_bar=True)

    # ── BM25 ───────────────────────────────────────────────────────────────
    print("Building BM25 index…")
    bm25 = BM25Okapi([tokenize(t) for t in corpus_texts])

    # ── Dense + BM25 Main loop ─────────────────────────────────────────────
    raw_cases = []
    print("Processing Dense & BM25 for cases…")
    for q_idx, case in enumerate(tqdm(cases)):
        case_id    = case["case_id"]
        query_text = case["query"]["text"]

        # Resolve target blocks
        target_blocks: set[str] = set()
        for ev in case.get("evidence", []):
            for blk in blocks_by_doc.get(ev["document_id"], []):
                if match_locator(ev["locator"], blk):
                    target_blocks.add(blk["block_id"])

        # Scores
        dense_scores = util.cos_sim(query_embs[q_idx], dense_embs)[0].cpu().numpy()
        bm25_scores  = np.array(bm25.get_scores(tokenize(query_text)))

        dense_sorted = np.argsort(dense_scores)[::-1]
        bm25_sorted  = np.argsort(bm25_scores)[::-1]

        # Global fusion — group assignment
        dense_mm  = min_max_norm(dense_scores)
        bm25_mm   = min_max_norm(bm25_scores)
        fusion_global = 0.4 * dense_mm + 0.6 * bm25_mm
        global_sorted = np.argsort(fusion_global)[::-1]

        first_hit_global, target_idx = -1, -1
        for rank, idx in enumerate(global_sorted, start=1):
            if chunks[idx]["source_block_ids"].intersection(target_blocks):
                first_hit_global, target_idx = rank, idx
                break

        if first_hit_global == 1:
            group = "Strong Anchors"
        else:
            if target_idx == -1:
                group = "Group C"
            else:
                d_rank = int(np.where(dense_sorted == target_idx)[0][0]) + 1
                b_rank = int(np.where(bm25_sorted  == target_idx)[0][0]) + 1
                best   = min(d_rank, b_rank)
                group  = "Group A" if best <= 10 else ("Group B" if best <= 20 else "Group C")

        if group == "Group C":
            continue

        # Candidate pool (Top20 Dense ∪ Top20 BM25)
        pool_indices = list(set(dense_sorted[:20].tolist()) | set(bm25_sorted[:20].tolist()))

        # Baseline: local MinMax fusion
        pd = dense_scores[pool_indices];  pd_mm = min_max_norm(pd)
        pb = bm25_scores[pool_indices];   pb_mm = min_max_norm(pb)
        pool_fusion = 0.4 * pd_mm + 0.6 * pb_mm
        baseline_order = np.argsort(pool_fusion)[::-1]
        baseline_pool  = [pool_indices[i] for i in baseline_order]

        raw_cases.append({
            "case_id":   case_id,
            "query_text": query_text,
            "group":     group,
            "target_blocks": list(target_blocks),
            "baseline_pool": baseline_pool,
            "chunks_source_blocks": [list(chunks[idx]["source_block_ids"]) for idx in baseline_pool],
            "baseline_chunks": [{"text": chunks[idx]["text"]} for idx in baseline_pool]
        })

    # ── Isolate CE Inference to avoid PyTorch Segfault ───────────────────
    print("Saving intermediate Dense results...")
    tmp_path = "evaluation/results/m5_step5_dense_results.json"
    with open(tmp_path, "w", encoding="utf-8") as f:
        json.dump(raw_cases, f)
        
    print("Freeing Dense model from RAM to prevent OOM…")
    del dense_model
    del dense_embs
    del query_embs
    del bm25
    del corpus_texts
    del raw_cases
    gc.collect()
    torch.cuda.empty_cache() if torch.cuda.is_available() else None

    print("Spawning fresh subprocess for CE inference (to prevent memory corruption)...")
    import subprocess
    import sys
    ret = subprocess.run([sys.executable, "evaluation/scripts/m5_step5_ce_runner.py"])
    if ret.returncode != 0:
        print("CE Subprocess failed!")
        sys.exit(1)
        
    # Remove temp file
    if os.path.exists(tmp_path):
        os.remove(tmp_path)


# ── Phase 2: sweep gate parameters ────────────────────────────────────────

def run_sweep():
    with open(RAW_DATA_PATH, encoding="utf-8") as f:
        raw_cases = json.load(f)
    print(f"Loaded {len(raw_cases)} cases.\n")

    # ── Precompute Baseline and BGE-only first_rank ───────────────────────
    def first_rank(chunks_source_blocks, target_blocks):
        ts = set(target_blocks)
        for rank, src in enumerate(chunks_source_blocks, 1):
            if ts.intersection(src):
                return rank
        return 999

    baseline_ranks: dict[str, int] = {}
    bge_ranks:      dict[str, int] = {}

    for case in raw_cases:
        tb  = case["target_blocks"]
        csb = case["chunks_source_blocks"]
        baseline_ranks[case["case_id"]] = first_rank(csb, tb)

        ce   = np.array(case["ce_scores_aligned_to_baseline"])
        order = np.argsort(ce)[::-1]
        bge_ranks[case["case_id"]] = first_rank([csb[i] for i in order], tb)

    def mrr(ranks_dict):
        return np.mean([1.0 / r for r in ranks_dict.values()])

    def evaluate(T: float, R: int):
        """
        Gate rule (OR logic — lenient):
          Allow BGE override IF:
            (a) BGE top-1 score >= T   (BGE is confident enough)
            OR
            (b) BGE top-1 is already near the top of Baseline (rank <= R)
                → safe fine-tuning, not risky pull from rank-20+
        """
        gate_ranks: dict[str, int] = {}
        rescue = regression = 0

        for case in raw_cases:
            ce      = np.array(case["ce_scores_aligned_to_baseline"])
            top1_idx = int(np.argmax(ce))
            top1_score       = float(ce[top1_idx])
            top1_base_rank   = top1_idx + 1      # position in baseline_pool (1-indexed)

            allow = (top1_score >= T) or (top1_base_rank <= R)
            final = bge_ranks[case["case_id"]] if allow else baseline_ranks[case["case_id"]]
            gate_ranks[case["case_id"]] = final

            base = baseline_ranks[case["case_id"]]
            if case["group"] == "Strong Anchors":
                if base == 1 and final > 1:
                    regression += 1
            elif case["group"] in ("Group A", "Group B"):
                if base > 1 and final == 1:
                    rescue += 1

        return rescue, regression, mrr(gate_ranks)

    # ── Reference rows ─────────────────────────────────────────────────────
    bge_rescue = sum(
        1 for c in raw_cases
        if c["group"] in ("Group A", "Group B")
        and baseline_ranks[c["case_id"]] > 1
        and bge_ranks[c["case_id"]] == 1
    )
    bge_reg = sum(
        1 for c in raw_cases
        if c["group"] == "Strong Anchors"
        and baseline_ranks[c["case_id"]] == 1
        and bge_ranks[c["case_id"]] > 1
    )

    header = f"{'Rule':<28} | {'Rescue':>8} | {'Regression':>12} | {'MRR First':>10}"
    sep    = "-" * len(header)
    print(header); print(sep)
    print(f"{'Baseline':<28} | {'—':>8} | {'0':>12} | {mrr(baseline_ranks):>10.4f}")
    print(f"{'BGE-only':<28} | {bge_rescue:>8} | {bge_reg:>12} | {mrr(bge_ranks):>10.4f}")
    print(sep)

    # ── Sweep ─────────────────────────────────────────────────────────────
    # T: BGE probability threshold (raw logits, typically range -10 to +10)
    T_values = [-2.0, -1.0, -0.5, 0.0, 0.1, 0.2, 0.3, 0.4, 0.5, 0.6, 0.8, 1.0]
    R_values = [1, 2, 3, 5, 10]

    for T in T_values:
        for R in R_values:
            res, reg, m = evaluate(T, R)
            label = f"Score>={T:.2f} OR Rank<={R}"
            print(f"{label:<28} | {res:>8} | {reg:>12} | {m:>10.4f}")

    print(sep)
    print("\nDecision criterion note: Choose based on your priority.")
    print("  - Minimize Regression → prefer high T, low R")
    print("  - Maximize Rescue     → prefer low T, high R")
    print("  - Balance             → look at Pareto front manually")


# ── Entry point ────────────────────────────────────────────────────────────

if __name__ == "__main__":
    if not os.path.exists(RAW_DATA_PATH):
        build_raw_data()
    run_sweep()
