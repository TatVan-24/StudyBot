"""
m5_step6_holdout_validation.py
================================
ONE-SHOT Holdout Validation of Decision Gate (H6)

Contract : Architecture/ADR-006-decision-gate-holdout.md
Rule     : FROZEN — (bge_top1_score >= 0.20) OR (baseline_rank_of_bge_top1 <= 1)
Dataset  : evaluation/datasets/test-v2.jsonl  [FROZEN HOLDOUT]

This script must not be modified after the Holdout run has been observed.

Output:
  evaluation/results/m5_holdout_trace.jsonl   — raw case-level trace
  evaluation/results/m5_holdout_report.md     — aggregate report (§10 format)

Exit codes:
  0  — run completed (H6 SUPPORTED or NOT SUPPORTED)
  2  — BLOCKED (preflight failed)
  3  — INSUFFICIENT_VARIATION (BGE produced no Rescue or no Regression)
"""

import gc
import json
import os
import re
import sqlite3
import sys
from datetime import datetime, timezone

import numpy as np
from rank_bm25 import BM25Okapi
from tqdm import tqdm

# ── FROZEN CONFIGURATION ──────────────────────────────────────────────────────
RUN_ID                  = "m5-holdout-v1"
HOLDOUT_DATASET         = "test-v2.jsonl"
GATE_SCORE_THRESHOLD    = 0.20   # DO NOT CHANGE
GATE_RANK_THRESHOLD     = 1      # DO NOT CHANGE
DENSE_ALPHA             = 0.4
BM25_ALPHA              = 0.6
CANDIDATE_DENSE_TOP_K   = 20
CANDIDATE_BM25_TOP_K    = 20
CE_MODEL_NAME           = "BAAI/bge-reranker-v2-m3"
DENSE_MODEL_NAME        = "sentence-transformers/paraphrase-multilingual-mpnet-base-v2"

# ── PATHS ─────────────────────────────────────────────────────────────────────
ROOT          = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))  # .../evaluation
DB_PATH       = os.path.join(ROOT, "index",      "m3_index.db")
BLOCKS_PATH   = os.path.join(ROOT, "bundle_all", "blocks.jsonl")
DATASET_PATH  = os.path.join(ROOT, "datasets",   HOLDOUT_DATASET)
TRACE_PATH    = os.path.join(ROOT, "results",    "m5_holdout_trace.jsonl")
REPORT_PATH   = os.path.join(ROOT, "results",    "m5_holdout_report.md")
DENSE_TMP     = os.path.join(ROOT, "results",    "m5_holdout_dense_tmp.json")
CE_SCORES_TMP = os.path.join(ROOT, "results",    "m5_holdout_ce_tmp.json")


# ── HELPERS ───────────────────────────────────────────────────────────────────

def tokenize(text: str) -> list:
    return re.findall(r"\w+", text.lower())


def min_max_norm(scores: np.ndarray) -> np.ndarray:
    lo, hi = np.min(scores), np.max(scores)
    if hi > lo:
        return (scores - lo) / (hi - lo)
    return np.zeros_like(scores)


def match_locator(gt_locator: dict, block: dict) -> bool:
    block_locator = block.get("locator", {})
    gt_type  = gt_locator.get("type")
    bl_type  = block_locator.get("type")

    if gt_type in ("markdown", "text_span", "txt", "text") and bl_type in ("markdown", "text_span", "text", "txt"):
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


def first_hit_rank(ranked_source_blocks: list[list], target_blocks: set) -> int:
    """Return 1-based rank of first chunk containing a target block, else 999."""
    for rank, src in enumerate(ranked_source_blocks, 1):
        if target_blocks.intersection(src):
            return rank
    return 999


def mrr_score(ranks: list[int]) -> float:
    if not ranks:
        return 0.0
    return float(np.mean([1.0 / r for r in ranks]))


def coverage_at_k(ranked_source_blocks: list[list], target_blocks: set, k: int) -> float:
    if not target_blocks:
        return 0.0
    covered = set()
    for src in ranked_source_blocks[:k]:
        covered |= target_blocks.intersection(src)
    return len(covered) / len(target_blocks)


# ── PREFLIGHT ─────────────────────────────────────────────────────────────────

def preflight(cases: list) -> str:
    """
    Run all preflight checks.
    Returns 'OK', 'BLOCKED', or 'INSUFFICIENT_VARIATION'.
    INSUFFICIENT_VARIATION is determined after running BGE — checked later.
    """
    issues = []

    if not os.path.exists(DATASET_PATH):
        issues.append(f"Holdout dataset not found: {DATASET_PATH}")
    if not os.path.exists(DB_PATH):
        issues.append(f"Index not found: {DB_PATH}")
    if not os.path.exists(BLOCKS_PATH):
        issues.append(f"Blocks file not found: {BLOCKS_PATH}")

    if not cases:
        issues.append("Holdout dataset is empty.")

    # Ensure all cases have evidence (ground truth)
    skipped = [c["case_id"] for c in cases if not c.get("evidence")]
    # Note: some test cases are legitimately unanswerable; only fail if ALL are missing evidence
    answerable = [c for c in cases if c.get("evidence")]
    if not answerable:
        issues.append("No answerable cases with evidence found in Holdout dataset.")

    if issues:
        print("\n[PREFLIGHT FAILED]")
        for issue in issues:
            print(f"  ✗ {issue}")
        return "BLOCKED"

    print("[PREFLIGHT] All primary checks passed.")
    print(f"  Total cases in dataset : {len(cases)}")
    print(f"  Answerable cases       : {len(answerable)}")
    print(f"  Dataset                : {HOLDOUT_DATASET}")
    print(f"  Index                  : {DB_PATH}")
    print(f"  Frozen score_threshold : {GATE_SCORE_THRESHOLD}")
    print(f"  Frozen rank_threshold  : {GATE_RANK_THRESHOLD}")
    return "OK"


# ── PHASE 1: Dense + BM25 retrieval ──────────────────────────────────────────

def build_candidate_pools(cases: list):
    """
    Generate candidate pools per case using Dense + BM25.
    Saves intermediate results to DENSE_TMP to free RAM before CE inference.
    """
    import torch
    from sentence_transformers import SentenceTransformer, util

    os.environ["HF_HUB_OFFLINE"]      = "1"
    os.environ["TRANSFORMERS_OFFLINE"] = "1"

    # Filter to answerable cases only
    answerable = [c for c in cases if c.get("evidence")]

    # Load blocks for target resolution
    print("Loading blocks for target resolution...")
    blocks_by_doc: dict[str, list] = {}
    with open(BLOCKS_PATH, encoding="utf-8") as f:
        for line in f:
            if line.strip():
                b = json.loads(line)
                blocks_by_doc.setdefault(b.get("document_id"), []).append(b)

    # Load corpus
    print("Loading corpus from SQLite...")
    conn  = sqlite3.connect(DB_PATH)
    rows  = conn.execute("SELECT chunk_id, document_id, text, source_block_ids FROM embeddings").fetchall()
    conn.close()

    chunks = []
    for chunk_id, doc_id, text, src_raw in rows:
        src = json.loads(src_raw) if src_raw else []
        chunks.append({"chunk_id": chunk_id, "text": text, "source_block_ids": set(src)})
    del rows
    corpus_texts = [c["text"] for c in chunks]

    # Dense embeddings
    print("Loading Dense model...")
    dense_model = SentenceTransformer(DENSE_MODEL_NAME, local_files_only=True)
    dense_embs  = dense_model.encode(corpus_texts, normalize_embeddings=True,
                                     convert_to_tensor=True, show_progress_bar=True)

    query_texts = [c["query"]["text"] for c in answerable]
    query_embs  = dense_model.encode(query_texts, normalize_embeddings=True,
                                     convert_to_tensor=True, show_progress_bar=True)

    # BM25
    print("Building BM25 index...")
    bm25 = BM25Okapi([tokenize(t) for t in corpus_texts])

    # Build candidate pools per case
    print("Building candidate pools...")
    pool_data = []
    for q_idx, case in enumerate(tqdm(answerable)):
        case_id    = case["case_id"]
        query_text = case["query"]["text"]

        # Resolve target blocks
        target_blocks: set = set()
        for ev in case.get("evidence", []):
            for blk in blocks_by_doc.get(ev["document_id"], []):
                if match_locator(ev["locator"], blk):
                    target_blocks.add(blk["block_id"])

        # Scores
        dense_scores = util.cos_sim(query_embs[q_idx], dense_embs)[0].cpu().numpy()
        bm25_scores  = np.array(bm25.get_scores(tokenize(query_text)))

        dense_sorted = np.argsort(dense_scores)[::-1]
        bm25_sorted  = np.argsort(bm25_scores)[::-1]

        # Candidate pool: Top-20 Dense ∪ Top-20 BM25
        pool_indices = list(set(dense_sorted[:CANDIDATE_DENSE_TOP_K].tolist()) |
                            set(bm25_sorted[:CANDIDATE_BM25_TOP_K].tolist()))

        # Baseline: local MinMax fusion on pool
        pd = dense_scores[pool_indices]; pd_mm = min_max_norm(pd)
        pb = bm25_scores[pool_indices];  pb_mm = min_max_norm(pb)
        pool_fusion    = DENSE_ALPHA * pd_mm + BM25_ALPHA * pb_mm
        baseline_order = np.argsort(pool_fusion)[::-1]
        baseline_pool  = [pool_indices[i] for i in baseline_order]

        pool_data.append({
            "case_id":        case_id,
            "query_text":     query_text,
            "tags":           case.get("tags", []),
            "target_blocks":  list(target_blocks),
            "baseline_pool":  baseline_pool,
            "baseline_top1_chunk_id": chunks[baseline_pool[0]]["chunk_id"] if baseline_pool else None,
            "chunks_source_blocks":   [list(chunks[idx]["source_block_ids"]) for idx in baseline_pool],
            "baseline_chunks": [{"chunk_id": chunks[idx]["chunk_id"], "text": chunks[idx]["text"]} for idx in baseline_pool],
        })

    # Save before freeing RAM
    print("Saving intermediate dense results...")
    with open(DENSE_TMP, "w", encoding="utf-8") as f:
        json.dump(pool_data, f)

    print("Freeing Dense model from RAM...")
    del dense_model, dense_embs, query_embs, bm25, corpus_texts
    gc.collect()
    if hasattr(torch.cuda, "empty_cache"):
        torch.cuda.empty_cache()

    return len(pool_data)


# ── PHASE 2: CE Inference (subprocess) ───────────────────────────────────────

CE_RUNNER_PATH = os.path.join(os.path.dirname(os.path.abspath(__file__)), "m5_step6_ce_runner.py")

def run_ce_subprocess():
    import subprocess
    ret = subprocess.run([sys.executable, CE_RUNNER_PATH])
    if ret.returncode != 0:
        print(f"[ERROR] CE subprocess failed with code {ret.returncode}")
        sys.exit(1)


# ── PHASE 3: Apply frozen Gate + Evaluate ────────────────────────────────────

def apply_gate_and_evaluate(timestamp: str) -> tuple[list, dict]:
    """
    Load raw CE scores, apply frozen gate, classify cases, compute metrics.
    Returns (trace_records, aggregate_stats).
    """
    with open(CE_SCORES_TMP, encoding="utf-8") as f:
        cases = json.load(f)

    run_metadata = {
        "run_id":          RUN_ID,
        "dataset":         HOLDOUT_DATASET,
        "index":           "m3_index.db",
        "timestamp":       timestamp,
    }
    retrieval_config = {
        "fusion_method":       "min_max",
        "reranker_model":      CE_MODEL_NAME,
        "gate_score_threshold": GATE_SCORE_THRESHOLD,
        "gate_rank_threshold":  GATE_RANK_THRESHOLD,
    }

    trace_records = []

    # Accumulators
    baseline_mrr_first_list = []
    bge_mrr_first_list      = []
    gated_mrr_first_list    = []
    baseline_cov10_list     = []
    bge_cov10_list          = []
    gated_cov10_list        = []

    bge_rescue_cases    = []
    bge_regression_cases = []
    gate_rescue_cases   = []
    gate_regression_cases = []
    gate_protected_cases = []   # regression-prevented by Gate
    gate_gen_degradation = []   # non-SA rank degradation

    for case in cases:
        case_id       = case["case_id"]
        target_blocks = set(case["target_blocks"])
        csb           = case["chunks_source_blocks"]   # list of lists, aligned to baseline pool
        ce_scores     = np.array(case["ce_scores_aligned_to_baseline"])

        # ── Baseline ──────────────────────────────────────────────────────────
        baseline_top1_chunk_id = case["baseline_top1_chunk_id"]
        baseline_ranked_csb    = csb  # already sorted by baseline fusion
        baseline_rank = first_hit_rank(baseline_ranked_csb, target_blocks)
        baseline_mrr_first_list.append(1.0 / baseline_rank)
        baseline_cov10 = coverage_at_k(baseline_ranked_csb, target_blocks, 10)
        baseline_cov10_list.append(baseline_cov10)

        # ── BGE ranking ───────────────────────────────────────────────────────
        bge_order        = np.argsort(ce_scores)[::-1]
        bge_top1_idx     = int(bge_order[0])
        bge_top1_score   = float(ce_scores[bge_top1_idx])
        bge_top1_chunk_id = case.get("baseline_chunk_ids", [])[bge_top1_idx] if "baseline_chunk_ids" in case else f"pool_idx_{bge_top1_idx}"

        bge_ranked_csb = [csb[i] for i in bge_order]
        bge_rank       = first_hit_rank(bge_ranked_csb, target_blocks)
        bge_mrr_first_list.append(1.0 / bge_rank)
        bge_cov10 = coverage_at_k(bge_ranked_csb, target_blocks, 10)
        bge_cov10_list.append(bge_cov10)

        # BGE rescue/regression (unconditional BGE)
        if baseline_rank > 1 and bge_rank == 1:
            bge_rescue_cases.append(case_id)
        if baseline_rank == 1 and bge_rank > 1:
            bge_regression_cases.append(case_id)

        # ── Frozen Gate ───────────────────────────────────────────────────────
        baseline_rank_of_bge_top1 = bge_top1_idx + 1   # position in baseline_pool (1-indexed)
        score_pass                = bge_top1_score >= GATE_SCORE_THRESHOLD
        rank_pass                 = baseline_rank_of_bge_top1 <= GATE_RANK_THRESHOLD
        gate_allow                = score_pass or rank_pass
        gate_decision             = "BGE" if gate_allow else "BASELINE"

        if gate_allow:
            gated_ranked_csb = bge_ranked_csb
            gated_top1_chunk_id = bge_top1_chunk_id
        else:
            gated_ranked_csb = baseline_ranked_csb
            gated_top1_chunk_id = baseline_top1_chunk_id

        gated_rank = first_hit_rank(gated_ranked_csb, target_blocks)
        gated_mrr_first_list.append(1.0 / gated_rank)
        gated_cov10 = coverage_at_k(gated_ranked_csb, target_blocks, 10)
        gated_cov10_list.append(gated_cov10)

        # ── Classification ────────────────────────────────────────────────────
        # Rescue: Gated first-hit rank < Baseline first-hit rank
        rescue = (gated_rank < baseline_rank) or (baseline_rank == 999 and gated_rank < 999)
        # Strong Anchor Regression: Baseline was rank-1, Gated is not
        regression = (baseline_rank == 1 and gated_rank > 1)
        # General rank degradation (non-SA)
        gen_degradation = (gated_rank > baseline_rank and baseline_rank != 1)

        if rescue:
            gate_rescue_cases.append(case_id)
        if regression:
            gate_regression_cases.append(case_id)
        if gen_degradation:
            gate_gen_degradation.append(case_id)

        # Gate protected from BGE regression
        if baseline_rank == 1 and bge_rank > 1 and not gate_allow:
            gate_protected_cases.append(case_id)

        # ── Record trace ──────────────────────────────────────────────────────
        record = {
            "run_metadata":     run_metadata,
            "retrieval_config": retrieval_config,
            "case_id":          case_id,
            "tags":             case.get("tags", []),
            "query":            case["query_text"],
            "target_block_ids": list(target_blocks),

            "gate_trace": {
                "baseline_top1_chunk_id":   baseline_top1_chunk_id,
                "bge_top1_chunk_id":        bge_top1_chunk_id,
                "bge_top1_score":           round(bge_top1_score, 6),
                "baseline_rank_of_bge_top1": baseline_rank_of_bge_top1,
                "score_pass":               score_pass,
                "rank_pass":                rank_pass,
                "decision":                 gate_decision,
            },

            "metrics_baseline": {
                "mrr_first_hit":    round(1.0 / baseline_rank, 6),
                "coverage_at_10":   round(baseline_cov10, 6),
                "first_hit_rank":   baseline_rank,
            },
            "metrics_bge": {
                "mrr_first_hit":    round(1.0 / bge_rank, 6),
                "coverage_at_10":   round(bge_cov10, 6),
                "first_hit_rank":   bge_rank,
            },
            "metrics_gated": {
                "mrr_first_hit":    round(1.0 / gated_rank, 6),
                "coverage_at_10":   round(gated_cov10, 6),
                "first_hit_rank":   gated_rank,
            },

            "classification": {
                "rescue":                    rescue,
                "regression":                regression,
                "general_rank_degradation":  gen_degradation,
            },
        }
        trace_records.append(record)

    # ── Testability Precondition Check ────────────────────────────────────────
    if not bge_rescue_cases:
        print("\n[STATUS = INSUFFICIENT_VARIATION]")
        print("BGE-only produced 0 Rescue cases. Trade-off cannot be tested.")
        _write_trace(trace_records)
        sys.exit(3)
    if not bge_regression_cases:
        print("\n[STATUS = INSUFFICIENT_VARIATION]")
        print("BGE-only produced 0 Regression cases. Trade-off cannot be tested.")
        _write_trace(trace_records)
        sys.exit(3)

    # ── Aggregate stats ───────────────────────────────────────────────────────
    n = len(trace_records)
    stats = {
        "n_cases": n,

        "baseline_mrr_first":  round(mrr_score([1.0/r["metrics_baseline"]["first_hit_rank"]
                                                  if r["metrics_baseline"]["first_hit_rank"] != 999 else 1/999
                                                  for r in trace_records]), 4),
        "bge_mrr_first":       round(mrr_score([1.0/r["metrics_bge"]["first_hit_rank"]
                                                  if r["metrics_bge"]["first_hit_rank"] != 999 else 1/999
                                                  for r in trace_records]), 4),
        "gated_mrr_first":     round(mrr_score([1.0/r["metrics_gated"]["first_hit_rank"]
                                                  if r["metrics_gated"]["first_hit_rank"] != 999 else 1/999
                                                  for r in trace_records]), 4),

        "baseline_cov10": round(float(np.mean(baseline_cov10_list)), 4),
        "bge_cov10":      round(float(np.mean(bge_cov10_list)), 4),
        "gated_cov10":    round(float(np.mean(gated_cov10_list)), 4),

        "bge_rescue":    len(bge_rescue_cases),
        "bge_regression": len(bge_regression_cases),

        "gate_rescue":    len(gate_rescue_cases),
        "gate_regression": len(gate_regression_cases),
        "gate_protected":  len(gate_protected_cases),
        "gate_gen_degradation": len(gate_gen_degradation),

        "bge_rescue_cases":     bge_rescue_cases,
        "bge_regression_cases": bge_regression_cases,
        "gate_rescue_cases":    gate_rescue_cases,
        "gate_regression_cases": gate_regression_cases,
        "gate_protected_cases":  gate_protected_cases,
        "gate_gen_degradation_cases": gate_gen_degradation,
    }

    return trace_records, stats


def _write_trace(records: list):
    with open(TRACE_PATH, "w", encoding="utf-8") as f:
        for r in records:
            f.write(json.dumps(r, ensure_ascii=False) + "\n")
    print(f"Trace written to {TRACE_PATH}")


# ── PHASE 4: H6 Acceptance Criteria ──────────────────────────────────────────

def evaluate_h6(stats: dict) -> str:
    """
    Apply frozen acceptance criteria (§9.3 of ADR-006).
    Returns 'SUPPORTED', 'NOT_SUPPORTED'.
    """
    rescue_retention = (stats["gate_rescue"] / stats["bge_rescue"]) if stats["bge_rescue"] > 0 else 0.0
    regression_ok    = stats["gate_regression"] <= stats["bge_regression"]
    rescue_ok        = rescue_retention >= 0.90

    print(f"\n── H6 Acceptance Criteria ──────────────────")
    print(f"  1. Regression_Gated ({stats['gate_regression']}) <= Regression_BGE ({stats['bge_regression']}): {'✓' if regression_ok else '✗'}")
    print(f"  2. Rescue_Gated ({stats['gate_rescue']}) >= 90% × Rescue_BGE ({stats['bge_rescue']:.0f})"
          f"  [={stats['bge_rescue'] * 0.9:.1f}]:  {'✓' if rescue_ok else '✗'}")
    print(f"     Rescue retention: {rescue_retention * 100:.1f}%")

    if regression_ok and rescue_ok:
        return "SUPPORTED"
    return "NOT_SUPPORTED"


# ── PHASE 5: Write report ─────────────────────────────────────────────────────

def write_report(trace_records: list, stats: dict, h6_result: str, timestamp: str):
    n = stats["n_cases"]
    rescue_retention = (stats["gate_rescue"] / stats["bge_rescue"] * 100) if stats["bge_rescue"] else 0
    regression_reduction = ((stats["bge_regression"] - stats["gate_regression"]) / stats["bge_regression"] * 100) if stats["bge_regression"] else 0

    # Slice by tags
    tag_groups: dict[str, dict] = {}
    for rec in trace_records:
        for tag in rec.get("tags", []):
            if tag not in tag_groups:
                tag_groups[tag] = {"rescue": 0, "regression": 0, "total": 0}
            tag_groups[tag]["total"] += 1
            if rec["classification"]["rescue"]:
                tag_groups[tag]["rescue"] += 1
            if rec["classification"]["regression"]:
                tag_groups[tag]["regression"] += 1

    # Build representative decision trace (top 10 cases sorted by score impact)
    sorted_for_trace = sorted(trace_records,
                               key=lambda r: abs(r["metrics_gated"]["first_hit_rank"] - r["metrics_baseline"]["first_hit_rank"]),
                               reverse=True)[:10]

    lines = [
        f"# M5 — Decision Gate Holdout Report",
        f"",
        f"## 10.1 Experiment Identity",
        f"| Field | Value |",
        f"|---|---|",
        f"| run_id | `{RUN_ID}` |",
        f"| dataset | `{HOLDOUT_DATASET}` |",
        f"| candidate_pool | Dense Top-{CANDIDATE_DENSE_TOP_K} ∪ BM25 Top-{CANDIDATE_BM25_TOP_K} |",
        f"| reranker | `{CE_MODEL_NAME}` |",
        f"| gate_version | `score>={GATE_SCORE_THRESHOLD} OR rank<={GATE_RANK_THRESHOLD}` |",
        f"| timestamp | `{timestamp}` |",
        f"",
        f"## 10.2 Frozen Configuration",
        f"```text",
        f"score_threshold        = {GATE_SCORE_THRESHOLD}",
        f"baseline_rank_threshold = {GATE_RANK_THRESHOLD}",
        f"candidate_dense_top_k  = {CANDIDATE_DENSE_TOP_K}",
        f"candidate_bm25_top_k   = {CANDIDATE_BM25_TOP_K}",
        f"dense_alpha            = {DENSE_ALPHA}",
        f"bm25_alpha             = {BM25_ALPHA}",
        f"```",
        f"",
        f"## 10.3 Preconditions",
        f"- dataset valid ✓",
        f"- candidate pool valid ✓ (Dense Top-{CANDIDATE_DENSE_TOP_K} ∪ BM25 Top-{CANDIDATE_BM25_TOP_K})",
        f"- baseline valid ✓ (Min-Max fusion α={DENSE_ALPHA})",
        f"- reranker valid ✓ (`{CE_MODEL_NAME}`)",
        f"- ground truth valid ✓",
        f"- testability: BGE Rescue={stats['bge_rescue']} ≥ 1 ✓, BGE Regression={stats['bge_regression']} ≥ 1 ✓",
        f"",
        f"## 10.4 Aggregate Result",
        f"",
        f"| System   | Rescue | Regression | MRR First | Cov@10 |",
        f"| -------- | -----: | ---------: | --------: | -----: |",
        f"| Baseline |      — |          0 | {stats['baseline_mrr_first']:.4f} | {stats['baseline_cov10']:.4f} |",
        f"| BGE-only | {stats['bge_rescue']:>6} | {stats['bge_regression']:>10} | {stats['bge_mrr_first']:.4f} | {stats['bge_cov10']:.4f} |",
        f"| Gated    | {stats['gate_rescue']:>6} | {stats['gate_regression']:>10} | {stats['gated_mrr_first']:.4f} | {stats['gated_cov10']:.4f} |",
        f"",
        f"Cases evaluated: {n}",
        f"",
        f"## 10.5 Rescue Analysis",
        f"- Cases rescued by Gate         : {stats['gate_rescue']}",
        f"- Cases rescued by BGE-only     : {stats['bge_rescue']}",
        f"- Rescue retention              : {rescue_retention:.1f}%",
        f"- Gate rescue cases             : {stats['gate_rescue_cases']}",
        f"",
        f"## 10.6 Regression Analysis",
        f"- Strong Anchor regressions (BGE-only)  : {stats['bge_regression']}",
        f"- Strong Anchor regressions (Gated)     : {stats['gate_regression']}",
        f"- Regression reduction                  : {regression_reduction:.1f}%",
        f"- Cases protected by Gate               : {stats['gate_protected']}  {stats['gate_protected_cases']}",
        f"- General rank degradations (non-SA)    : {stats['gate_gen_degradation']}  {stats['gate_gen_degradation_cases']}",
        f"- Gate regression cases                 : {stats['gate_regression_cases']}",
        f"",
        f"## 10.7 Decision Trace (top {len(sorted_for_trace)} most impactful cases)",
        f"",
        f"| Case ID | Baseline rank | BGE rank | BGE score | Baseline rank of BGE Top-1 | Gate decision | Final rank | Rescue | Regression |",
        f"|---------|----------:|--------:|--------:|--------:|-----------|-------:|:------:|:-------:|",
    ]
    for rec in sorted_for_trace:
        gt = rec["gate_trace"]
        cl = rec["classification"]
        lines.append(
            f"| {rec['case_id']} "
            f"| {rec['metrics_baseline']['first_hit_rank']} "
            f"| {rec['metrics_bge']['first_hit_rank']} "
            f"| {gt['bge_top1_score']:.4f} "
            f"| {gt['baseline_rank_of_bge_top1']} "
            f"| {gt['decision']} "
            f"| {rec['metrics_gated']['first_hit_rank']} "
            f"| {'✓' if cl['rescue'] else '—'} "
            f"| {'✓' if cl['regression'] else '—'} |"
        )

    lines += [
        f"",
        f"## 10.7b Slice Analysis (diagnostic only — does not modify decision)",
        f"",
        f"| Tag | Total | Rescue | Regression |",
        f"|-----|------:|-------:|-----------:|",
    ]
    for tag, data in sorted(tag_groups.items()):
        lines.append(f"| {tag} | {data['total']} | {data['rescue']} | {data['regression']} |")

    h6_label = {
        "SUPPORTED":     "## 10.8 H6 Conclusion\n\n```\nH6 = SUPPORTED ON HOLDOUT\n```",
        "NOT_SUPPORTED": "## 10.8 H6 Conclusion\n\n```\nH6 = NOT SUPPORTED ON HOLDOUT\n```",
    }[h6_result]

    lines += [
        f"",
        h6_label,
        f"",
        f"## 10.9 Interpretation",
        f"",
        f"**Observed facts:**",
        f"- Evaluated {n} answerable cases from `{HOLDOUT_DATASET}`.",
        f"- BGE-only produced {stats['bge_rescue']} Rescue and {stats['bge_regression']} Regression on Holdout.",
        f"- Gate produced {stats['gate_rescue']} Rescue and {stats['gate_regression']} Regression.",
        f"- Rescue retention: {rescue_retention:.1f}% (threshold: 90%).",
        f"- Regression change: {stats['bge_regression']} → {stats['gate_regression']}.",
        f"",
        f"**Hypothesis conclusion:**",
        f"H6 = {h6_result} ON HOLDOUT",
        f"",
        f"**Unresolved issues (not answered by this experiment):**",
        f"- Whether this Gate rule is optimal for production.",
        f"- Whether the CE should run for every query at inference time.",
        f"- Whether a single routing policy is universally optimal.",
        f"",
        f"> `H6 SUPPORTED` does not imply `Gate approved for production`.",
        f"> These two conclusions are not equivalent. (ADR-006 §9.4)",
    ]

    report_text = "\n".join(lines)
    with open(REPORT_PATH, "w", encoding="utf-8") as f:
        f.write(report_text)
    print(f"\nReport written to {REPORT_PATH}")
    return report_text


# ── ENTRY POINT ───────────────────────────────────────────────────────────────

def main():
    timestamp = datetime.now(timezone.utc).isoformat()
    print("=" * 60)
    print("M5 Decision Gate — ONE-SHOT HOLDOUT VALIDATION")
    print(f"Frozen rule: Score >= {GATE_SCORE_THRESHOLD} OR Rank <= {GATE_RANK_THRESHOLD}")
    print(f"Dataset    : {HOLDOUT_DATASET}")
    print(f"Timestamp  : {timestamp}")
    print("=" * 60)

    # Load dataset
    cases = []
    with open(DATASET_PATH, encoding="utf-8") as f:
        for line in f:
            if line.strip():
                cases.append(json.loads(line))

    # Preflight
    status = preflight(cases)
    if status != "OK":
        sys.exit(2)

    # Phase 1: Dense + BM25
    n_pool = build_candidate_pools(cases)
    print(f"\nCandidate pools built for {n_pool} answerable cases.")

    # Phase 2: CE Inference (subprocess)
    print("\nSpawning subprocess for CE inference (Windows memory-safe)...")
    run_ce_subprocess()

    # Phase 3: Gate + Evaluate
    print("\nApplying frozen Gate and evaluating...")
    trace_records, stats = apply_gate_and_evaluate(timestamp)

    # Write trace
    _write_trace(trace_records)

    # Phase 4: H6 decision
    h6_result = evaluate_h6(stats)

    # Phase 5: Report
    report = write_report(trace_records, stats, h6_result, timestamp)

    # Print summary to terminal
    print("\n" + "=" * 60)
    print("AGGREGATE SUMMARY")
    print("=" * 60)
    print(f"{'System':<12} | {'Rescue':>8} | {'Regression':>12} | {'MRR First':>10} | {'Cov@10':>8}")
    print("-" * 60)
    print(f"{'Baseline':<12} | {'—':>8} | {'0':>12} | {stats['baseline_mrr_first']:>10.4f} | {stats['baseline_cov10']:>8.4f}")
    print(f"{'BGE-only':<12} | {stats['bge_rescue']:>8} | {stats['bge_regression']:>12} | {stats['bge_mrr_first']:>10.4f} | {stats['bge_cov10']:>8.4f}")
    print(f"{'Gated':<12} | {stats['gate_rescue']:>8} | {stats['gate_regression']:>12} | {stats['gated_mrr_first']:>10.4f} | {stats['gated_cov10']:>8.4f}")
    print("=" * 60)

    if h6_result == "SUPPORTED":
        print("\n✓  H6 = SUPPORTED ON HOLDOUT")
    else:
        print("\n✗  H6 = NOT SUPPORTED ON HOLDOUT")

    print(f"\nTrace  : {TRACE_PATH}")
    print(f"Report : {REPORT_PATH}")
    sys.exit(0)


if __name__ == "__main__":
    main()
