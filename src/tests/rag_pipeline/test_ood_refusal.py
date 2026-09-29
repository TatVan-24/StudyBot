"""OOD test cho Truthful Refusal Gate.

Chạy 10 query OOD + 3 query in-domain, verify:
  - log_only mode: in ra top1_score + lexical_ratio (distribution analysis)
  - strict mode  : phân loại truthful_refusal vs false_refusal (threshold test)

Usage:
  python src/tests/rag_pipeline/test_ood_refusal.py --mode log_only
  python src/tests/rag_pipeline/test_ood_refusal.py --mode strict
"""
import argparse
import json
import statistics
import sys
from datetime import datetime, timezone
from pathlib import Path

# Fix path to allow importing src (mirror harness convention)
sys.path.append(str(Path(__file__).parent.parent.parent.parent))

from src.backend.app import userstore, vector_store
from src.backend import refusal

OUTPUT_DIR  = Path("outputs")
OOD_JSONL   = OUTPUT_DIR / "ood_refusal_results.jsonl"   # per-query log
OOD_SUMMARY = OUTPUT_DIR / "ood_refusal_summary.json"    # aggregate


# ── 10 query OOD (ngoài domain: Qdrant, RAG, LLM agent, AIOps) ─────────────
OOD_QUERIES = [
    "How does TCP three-way handshake work?",
    "Explain Kubernetes Pods and Deployments.",
    "How does Redis Cluster distribute keys?",
    "Explain PostgreSQL transaction isolation levels.",
    "How does LoRA reduce LLM fine-tuning cost?",
    "What is CUDA kernel scheduling?",
    "Explain Git rebase versus merge.",
    "How does AWS Lambda pricing work?",
    "Explain JWT refresh token storage best practices.",
    "How does Terraform state locking work?",
]

# ── 3 query in-domain (để so sánh score distribution) ───────────────────────
IN_DOMAIN_QUERIES = [
    "What is a vector database?",
    "How does HNSW work?",
    "Why is reducing alert noise important in AIOps?",
]

# LLM refuse answer (simulate — vì script này chỉ test retrieval + classify,
# không gọi LLM thật để tiết kiệm quota)
SIMULATED_REFUSE = (
    "Tôi không tìm thấy đủ thông tin trong tài liệu để trả lời câu hỏi này."
)


def run_query(query: str, label: str, session_id: str, mode: str) -> dict:
    chunks = vector_store.search(query, top_k=3, session_id=session_id)

    # Remap chunk_id (mirror handlers.py logic)
    for c in chunks:
        if "metadata" in c and "chunk_id" in c["metadata"]:
            c["doc_id"] = c["metadata"]["chunk_id"]

    cls = refusal.classify(SIMULATED_REFUSE, query, chunks)

    top1  = chunks[0].get("score", 0.0) if chunks else 0.0
    n_chk = len(chunks)
    diag  = cls["diagnostics"]

    print(f"[{label}] {query[:60]}")
    print(f"       n_chunks={n_chk}  top1={top1:.4f}")
    print(f"       label={cls['label']}  "
          f"refused={cls['refused']}  "
          f"sufficient={cls['context_sufficient']}")
    print(f"       top1_score={diag['top1_score']}  "
          f"lex={diag['lexical_ratio']}  "
          f"low_score_would={diag['low_score_would_trigger']}  "
          f"no_overlap_would={diag['no_overlap_would_trigger']}")
    print("-" * 80)

    result = {
        "ts": datetime.now(timezone.utc).isoformat(),
        "mode": mode,
        "query_type": label,
        "query": query,
        "n_chunks": n_chk,
        "label": cls["label"],
        "refused": cls["refused"],
        "context_sufficient": cls["context_sufficient"],
        "top1_score": diag["top1_score"],
        "lexical_ratio": diag["lexical_ratio"],
        "low_score_would_trigger": diag["low_score_would_trigger"],
        "no_overlap_would_trigger": diag["no_overlap_would_trigger"],
    }

    # Append to JSONL log
    OUTPUT_DIR.mkdir(parents=True, exist_ok=True)
    with open(OOD_JSONL, "a", encoding="utf-8") as f:
        f.write(json.dumps(result, ensure_ascii=False) + "\n")

    return result


def print_stats(title: str, results: list[dict]):
    top1_vals = [r["top1_score"] for r in results]
    lex_vals  = [r["lexical_ratio"]  for r in results]
    labels    = [r["label"] for r in results]
    low_score = sum(1 for r in results if r["low_score_would_trigger"])
    no_lex    = sum(1 for r in results if r["no_overlap_would_trigger"])

    print(f"\n{title} (n={len(results)})")
    print(f"  top1_score : mean={statistics.mean(top1_vals):.4f}  "
          f"min={min(top1_vals):.4f}  max={max(top1_vals):.4f}")
    print(f"  lex_ratio  : mean={statistics.mean(lex_vals):.4f}  "
          f"min={min(lex_vals):.4f}  max={max(lex_vals):.4f}")
    print(f"  would-trigger low_score : {low_score}/{len(results)}")
    print(f"  would-trigger no_overlap: {no_lex}/{len(results)}")
    print(f"  labels     : {labels}")


def main():
    parser = argparse.ArgumentParser(
        description="OOD test for Truthful Refusal Gate"
    )
    parser.add_argument(
        "--mode",
        choices=["log_only", "strict"],
        default="log_only",
        help="log_only: chỉ zero_hit trigger | strict: dùng score + lex threshold",
    )
    args = parser.parse_args()

    # Override CONFIG mode
    refusal.CONFIG["log_only"] = (args.mode == "log_only")
    mode_label = args.mode
    print(f"[*] Truthful Refusal Gate — mode={mode_label}")
    print(f"    score_threshold={refusal.CONFIG['score_threshold']}  "
          f"lexical_min_ratio={refusal.CONFIG['lexical_min_ratio']}")
    print("=" * 80)

    # Resolve session (lấy session đầu tiên có docs của eval user)
    USER_ID = "eval_english_user"
    sessions = userstore.list_sessions(USER_ID)
    session_id = None
    for s in reversed(sessions):
        if userstore.get_session_docs(s["session_id"]):
            session_id = s["session_id"]
            break

    if not session_id:
        print(f"[ERROR] Không tìm thấy session nào có docs cho user: {USER_ID}")
        print("        Hãy chạy trace_eval_harness.py trước để tạo session.")
        sys.exit(1)

    print(f"[*] Session: {session_id}")
    print(f"[*] Per-query log : {OOD_JSONL}")
    print(f"[*] Summary       : {OOD_SUMMARY}\n")

    run_ts = datetime.now(timezone.utc).isoformat()

    # ── In-domain queries ───────────────────────────────────────────────────
    print("### IN-DOMAIN QUERIES ###")
    print("(Kỳ vọng: top1 cao, lex cao, label=false_refusal do simulate refuse)\n")
    in_results = []
    for q in IN_DOMAIN_QUERIES:
        in_results.append(run_query(q, "IN", session_id, mode_label))

    # ── OOD queries ─────────────────────────────────────────────────────────
    print("\n### OOD QUERIES ###")
    if mode_label == "strict":
        print("(Kỳ vọng: top1 thấp / lex thấp → label=truthful_refusal)\n")
    else:
        print("(Kỳ vọng: label=false_refusal vì log_only, nhưng low_score_would/no_overlap_would=True)\n")

    ood_results = []
    for q in OOD_QUERIES:
        ood_results.append(run_query(q, "OOD", session_id, mode_label))

    # ── Summary ─────────────────────────────────────────────────────────────
    print("\n" + "=" * 80)
    print(f"SUMMARY — mode={mode_label}")
    print("=" * 80)

    print_stats("IN-DOMAIN", in_results)
    print_stats("OOD      ", ood_results)

    # ── Threshold guidance ──────────────────────────────────────────────────
    guidance = {}
    if mode_label == "log_only":
        in_top1_mean = statistics.mean(r["top1_score"] for r in in_results)
        ood_top1_mean = statistics.mean(r["top1_score"] for r in ood_results)
        in_lex_mean  = statistics.mean(r["lexical_ratio"] for r in in_results)
        ood_lex_mean = statistics.mean(r["lexical_ratio"] for r in ood_results)

        print("\n[THRESHOLD GUIDANCE]")
        mid_top1 = round((in_top1_mean + ood_top1_mean) / 2, 4)
        mid_lex  = round((in_lex_mean  + ood_lex_mean)  / 2, 4)
        print(f"  Midpoint top1  : ({in_top1_mean:.4f} + {ood_top1_mean:.4f}) / 2 = {mid_top1}")
        print(f"  Midpoint lex   : ({in_lex_mean:.4f}  + {ood_lex_mean:.4f}) / 2  = {mid_lex}")
        print(f"  Current config : score_threshold={refusal.CONFIG['score_threshold']}  "
              f"lexical_min_ratio={refusal.CONFIG['lexical_min_ratio']}")

        delta_top1 = round(in_top1_mean - ood_top1_mean, 4)
        delta_lex  = round(in_lex_mean  - ood_lex_mean,  4)
        print(f"\n  \u0394 top1 (in - ood) = {delta_top1}  {'\u2190 Good separation' if delta_top1 > 0.10 else '\u2190 Poor separation'}")
        print(f"  \u0394 lex  (in - ood) = {delta_lex }  {'\u2190 Good separation' if delta_lex  > 0.10 else '\u2190 Poor separation'}")
        print("\n  \u2192 N\u1ebfu separation t\u1ed1t: ch\u1ea1y l\u1ea1i v\u1edbi --mode strict \u0111\u1ec3 test threshold.")
        print("  \u2192 N\u1ebfu separation k\u00e9m: c\u1ea7n th\u00eam data ho\u1eb7c \u0111\u1ed5i signal kh\u00e1c.")

        guidance = {
            "in_top1_mean": round(in_top1_mean, 4),
            "ood_top1_mean": round(ood_top1_mean, 4),
            "delta_top1": delta_top1,
            "mid_top1": mid_top1,
            "in_lex_mean": round(in_lex_mean, 4),
            "ood_lex_mean": round(ood_lex_mean, 4),
            "delta_lex": delta_lex,
            "mid_lex": mid_lex,
            "top1_good_separation": delta_top1 > 0.10,
            "lex_good_separation": delta_lex > 0.10,
        }

    # ── Save summary JSON ───────────────────────────────────────────────────
    def _stat(vals):
        return {
            "mean": round(statistics.mean(vals), 4),
            "min":  round(min(vals), 4),
            "max":  round(max(vals), 4),
        }

    summary = {
        "ts": run_ts,
        "mode": mode_label,
        "session_id": session_id,
        "in_domain": {
            "n": len(in_results),
            "top1": _stat([r["top1_score"] for r in in_results]),
            "lex":  _stat([r["lexical_ratio"] for r in in_results]),
            "labels": [r["label"] for r in in_results],
        },
        "ood": {
            "n": len(ood_results),
            "top1": _stat([r["top1_score"] for r in ood_results]),
            "lex":  _stat([r["lexical_ratio"] for r in ood_results]),
            "labels": [r["label"] for r in ood_results],
        },
        "threshold_config": {
            "score_threshold": refusal.CONFIG["score_threshold"],
            "lexical_min_ratio": refusal.CONFIG["lexical_min_ratio"],
            "log_only": refusal.CONFIG["log_only"],
        },
        "guidance": guidance,
    }

    with open(OOD_SUMMARY, "w", encoding="utf-8") as f:
        json.dump(summary, f, ensure_ascii=False, indent=2)

    print(f"\n[SAVED] Per-query log  \u2192 {OOD_JSONL}")
    print(f"[SAVED] Summary JSON   \u2192 {OOD_SUMMARY}")
    print()


if __name__ == "__main__":
    main()
