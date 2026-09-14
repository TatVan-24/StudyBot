"""
M4 Diagnostic — Retrieval Depth Sweep

Purpose:
    Map retrieval behavior per case at extended K depths to identify
    WHERE in the ranking relevant evidence appears.
    This is a diagnostic experiment, NOT a change to the M4 baseline contract.

Baseline:      K = [1, 3, 5, 10]   → run_retrieval_eval.py
Diagnostic:    K = [1, 3, 5, 10, 20, 50, 100]  ← this script

Output:
    evaluation/results/m4_depth_sweep.jsonl     Raw per-case curves
    evaluation/results/m4-depth-sweep.md        Curve report
"""

import json
import sys
import os
import datetime
from pathlib import Path
from typing import List, Dict, Any, Set

sys.path.append(str(Path(__file__).resolve().parent.parent.parent))

from src.indexer.embedding import EmbeddingEngine
from src.indexer.vector_store import SQLiteVectorStore
from evaluation.scripts.validate_resolution import load_blocks, match_locator

DEV_V2_PATH  = "d:/Personal Project/AWS StudyBot/evaluation/datasets/development-v2.jsonl"
INDEX_PATH   = "d:/Personal Project/AWS StudyBot/evaluation/index/m3_index.db"
SWEEP_OUTPUT = "d:/Personal Project/AWS StudyBot/evaluation/results/m4_depth_sweep.jsonl"
REPORT_PATH  = "d:/Personal Project/AWS StudyBot/evaluation/results/m4-depth-sweep.md"

SWEEP_K = [1, 3, 5, 10, 20, 50, 100]
MAX_SWEEP_K = max(SWEEP_K)


# ── Core helpers (same D1/D2/D3 contract as baseline) ─────────────────────────

def resolve_ground_truth(case: Dict[str, Any], blocks_by_doc: Dict[str, List[Dict]]) -> Set[str]:
    target_block_ids = set()
    for ev in case.get('evidence', []):
        doc_id     = ev.get('document_id')
        gt_locator = ev.get('locator')
        for b in blocks_by_doc.get(doc_id, []):
            if match_locator(gt_locator, b):
                target_block_ids.add(b['block_id'])
    return target_block_ids


def compute_coverage_curve(target_block_ids: Set[str], retrieved_chunks: List[Any], k_values: List[int]) -> Dict:
    """
    Compute cumulative Coverage@K for each K in k_values.
    Returns a dict with per-K coverage, first_hit_rank, full_coverage_rank.
    """
    cumulative = set()
    coverage_at_k = {}
    first_hit_rank = -1
    full_coverage_rank = -1
    total = len(target_block_ids)

    for rank, chunk in enumerate(retrieved_chunks, 1):
        chunk_block_ids  = set(chunk.source_block_ids)
        provided         = target_block_ids.intersection(chunk_block_ids)
        cumulative.update(provided)
        current_coverage = len(cumulative) / total if total > 0 else 0.0

        if provided and first_hit_rank == -1:
            first_hit_rank = rank
        if current_coverage == 1.0 and full_coverage_rank == -1:
            full_coverage_rank = rank

        if rank in k_values:
            coverage_at_k[rank] = round(current_coverage, 6)

    # Forward-fill for K values that might exceed len(retrieved)
    prev = 0.0
    for k in k_values:
        if k not in coverage_at_k:
            coverage_at_k[k] = prev
        else:
            prev = coverage_at_k[k]

    return {
        "coverage_curve": {str(k): coverage_at_k[k] for k in k_values},
        "first_hit_rank": first_hit_rank,
        "full_coverage_rank": full_coverage_rank,
        "uncovered_block_ids": list(target_block_ids - cumulative),
    }


# ── Report generator ──────────────────────────────────────────────────────────

def ascii_curve(coverage_curve: Dict[str, float]) -> str:
    """Render a simple ASCII bar chart of the coverage curve."""
    ks = sorted(int(k) for k in coverage_curve)
    rows = []
    rows.append(f"{'K':>6}  {'Coverage':>8}  Bar")
    rows.append("-" * 50)
    for k in ks:
        cov = coverage_curve[str(k)]
        bar = "█" * int(cov * 30)
        rows.append(f"{k:>6}  {cov*100:>7.1f}%  {bar}")
    return "\n".join(rows)


def pattern_label(curve: Dict[str, float], full_coverage_rank: int) -> str:
    """Classify the curve shape into a retrieval pattern."""
    cov10  = curve.get("10",  0.0)
    cov50  = curve.get("50",  0.0)
    cov100 = curve.get("100", 0.0)

    if cov10 == 1.0:
        return "EARLY_FULL  — full coverage within Top-10 (strong retrieval)"
    if cov10 == 0.0 and cov50 == 0.0 and cov100 == 0.0:
        return "TOTAL_MISS  — no relevant evidence in Top-100 (embedding/representation issue)"
    if cov10 == 0.0 and cov100 > 0:
        return "DEEP_HIT    — evidence only appears past Rank-10 (ranking/alignment issue)"
    if cov10 < 0.5 and cov100 >= 1.0:
        return "PLATEAU_LOW — coverage plateaus low early, then completes deep (redundancy + tail gap)"
    if cov10 > 0.0 and cov100 < 1.0:
        return "PARTIAL     — partial retrieval, evidence missing even at Top-100"
    return "UNKNOWN"


def generate_depth_report(path: str, sweep_results: list, embed_model: str, run_ts: str):
    lines = []
    w = lines.append

    w("# M4 — Retrieval Depth Sweep\n")
    w("> **Diagnostic experiment** — NOT a modification to the M4 baseline contract.")
    w("> Baseline: K = [1, 3, 5, 10] | Sweep: K = [1, 3, 5, 10, 20, 50, 100]\n")

    w("## 1. Configuration\n")
    w(f"| Item | Value |")
    w(f"|---|---|")
    w(f"| Embedding model | {embed_model} |")
    w(f"| Retrieval scope | Global Search (D5) |")
    w(f"| Sweep K values | {SWEEP_K} |")
    w(f"| Run timestamp | {run_ts} |")
    w(f"| Cases evaluated | {len(sweep_results)} |")
    w("")

    w("## 2. Pattern Summary\n")
    w("| Case | Target Blocks | Pattern | First Hit | Full Cov Rank |")
    w("|---|---:|---|---:|---:|")
    for r in sweep_results:
        diag = r["diagnostic"]
        fhr  = f"#{diag['first_hit_rank']}" if diag['first_hit_rank'] > 0 else "—"
        fcr  = f"#{diag['full_coverage_rank']}" if diag['full_coverage_rank'] > 0 else "—"
        w(f"| {r['case_id']} | {r['total_target_blocks']} | {r['pattern']} | {fhr} | {fcr} |")
    w("")

    w("## 3. Per-Case Coverage Curves\n")
    for r in sweep_results:
        curve = r["diagnostic"]["coverage_curve"]
        w(f"### `{r['case_id']}`\n")
        w(f"- Query: *{r['query'][:100]}*")
        w(f"- Target blocks: {r['total_target_blocks']}")
        w(f"- Pattern: **{r['pattern']}**")
        w(f"- First relevant chunk: Rank #{r['diagnostic']['first_hit_rank']}" if r['diagnostic']['first_hit_rank'] > 0 else "- First relevant chunk: **None in Top-100**")
        if r['diagnostic']['full_coverage_rank'] > 0:
            w(f"- Full coverage at: Rank #{r['diagnostic']['full_coverage_rank']}")
        else:
            w(f"- Full coverage: **Not achieved in Top-100**")
            if r['diagnostic']['uncovered_block_ids']:
                w(f"- Uncovered blocks: `{r['diagnostic']['uncovered_block_ids'][:5]}`")
        w("")
        w("```")
        w(ascii_curve(curve))
        w("```")
        w("")

    w("## 4. Root-Cause Investigation Guide\n")
    w("Based on the pattern observed per case:\n")
    w("| Pattern | Investigation Priority |")
    w("|---|---|")
    w("| TOTAL_MISS | Query ↔ Target embedding similarity; chunk boundary; ingestion |")
    w("| DEEP_HIT | Ranking / semantic alignment / distractor competition |")
    w("| PARTIAL | Evidence granularity; multi-block span vs chunk size |")
    w("| PLATEAU_LOW | Redundancy in top results; evidence fragmented across corpus |")
    w("| EARLY_FULL | No issue — use as control case |")
    w("")
    w("> **Next step**: Pick 1 TOTAL_MISS and 1 DEEP_HIT case.")
    w("> Read `query text`, `target block text`, and `top-3 retrieved chunk text` side-by-side.")
    w("> Only after text-level inspection should a root-cause hypothesis be formed.")

    with open(path, 'w', encoding='utf-8') as f:
        f.write('\n'.join(lines) + '\n')


# ── Main ──────────────────────────────────────────────────────────────────────

def main():
    if not os.path.exists(DEV_V2_PATH):
        print(f"[FAIL FAST] Dataset not found: {DEV_V2_PATH}")
        sys.exit(1)

    print("Loading blocks...")
    blocks_by_doc = load_blocks()
    print("Initializing Embedding Engine...")
    engine = EmbeddingEngine()
    print("Connecting to Vector Store...")
    store = SQLiteVectorStore(INDEX_PATH)

    # Embedding invariant check (same gate as baseline)
    index_meta = store.load_meta()
    if index_meta is None:
        print("[FAIL FAST] Index metadata missing.")
        sys.exit(1)
    mismatches = []
    if index_meta.model_name != engine.model_name:
        mismatches.append(f"  model: {index_meta.model_name!r} vs {engine.model_name!r}")
    if index_meta.dimension != engine.dimension:
        mismatches.append(f"  dim: {index_meta.dimension} vs {engine.dimension}")
    if index_meta.normalization != engine.normalization:
        mismatches.append(f"  norm: {index_meta.normalization!r} vs {engine.normalization!r}")
    if mismatches:
        print("[FAIL FAST] Embedding invariant violated:")
        for m in mismatches:
            print(m)
        sys.exit(1)
    print(f"[OK] Embedding invariant: model={index_meta.model_name!r}, dim={index_meta.dimension}")

    cases = []
    with open(DEV_V2_PATH, 'r', encoding='utf-8') as f:
        for line in f:
            cases.append(json.loads(line))

    print(f"\nRunning depth sweep (K={SWEEP_K}) for {len(cases)} cases...\n")

    run_ts = datetime.datetime.utcnow().isoformat() + "Z"
    sweep_results = []

    for i, case in enumerate(cases, 1):
        case_id    = case.get('case_id')
        query_text = case.get('query', {}).get('text')

        if not case_id or not query_text or 'evidence' not in case:
            print(f"[FAIL FAST] Invalid case: {case_id}")
            sys.exit(1)

        target_block_ids = resolve_ground_truth(case, blocks_by_doc)
        if not target_block_ids:
            print(f"[FAIL FAST] Case {case_id} resolved to 0 blocks.")
            sys.exit(1)

        q_vector  = engine.encode([query_text])[0]
        retrieved = store.search(q_vector, top_k=MAX_SWEEP_K)

        diag    = compute_coverage_curve(target_block_ids, retrieved, SWEEP_K)
        pattern = pattern_label(diag["coverage_curve"], diag["full_coverage_rank"])

        result = {
            "case_id": case_id,
            "query": query_text,
            "total_target_blocks": len(target_block_ids),
            "target_block_ids": list(target_block_ids),
            "pattern": pattern,
            "diagnostic": diag,
        }
        sweep_results.append(result)

        # Print compact curve to terminal
        curve = diag["coverage_curve"]
        cov_str = "  ".join(f"@{k}={float(curve[str(k)])*100:.0f}%" for k in SWEEP_K)
        print(f"[{i}/{len(cases)}] {case_id}")
        print(f"  {cov_str}")
        print(f"  Pattern: {pattern}")
        print()

    os.makedirs(os.path.dirname(SWEEP_OUTPUT), exist_ok=True)
    with open(SWEEP_OUTPUT, 'w', encoding='utf-8') as f:
        for r in sweep_results:
            f.write(json.dumps(r, ensure_ascii=False) + '\n')
    print(f"Exported raw sweep to {SWEEP_OUTPUT}")

    generate_depth_report(REPORT_PATH, sweep_results, index_meta.model_name, run_ts)
    print(f"Exported depth report to {REPORT_PATH}")


if __name__ == "__main__":
    main()
