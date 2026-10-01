"""Eval harness cho 200 cases.

Usage:
    python src/tests/eval/run_eval.py --session-id <uuid>
    python src/tests/eval/run_eval.py --session-id <uuid> --limit 5
    python src/tests/eval/run_eval.py --session-id <uuid> --resume
"""
import argparse
import csv
import json
import sys
import time
from collections import Counter
from datetime import datetime, timezone
from pathlib import Path

import requests

# ── Config ────────────────────────────────────────────────────────────
API_BASE = "http://127.0.0.1:8000"
USER_ID = "eval-user-200"  # default, override bằng --user-id
TIMEOUT = 90

EVAL_DIR = Path(__file__).parent
CASES_FILE = EVAL_DIR / "cases_200.jsonl"
RESULTS_FILE = EVAL_DIR / "results_200.jsonl"
REPORT_MD = EVAL_DIR / "report_200.md"
REPORT_CSV = EVAL_DIR / "report_200.csv"
LOG_DIR = Path("_data/logs")

VALID_STATUSES = {"acceptance", "ambiguous", "rejection", "refusal"}


# ── I/O ───────────────────────────────────────────────────────────────
def load_cases(path):
    return [json.loads(l) for l in path.read_text(encoding="utf-8").splitlines() if l.strip()]


def load_done_ids(path):
    if not path.exists():
        return set()
    ids = set()
    for line in path.read_text(encoding="utf-8").splitlines():
        if line.strip():
            try:
                ids.add(json.loads(line)["case_id"])
            except Exception:
                continue
    return ids


# ── HTTP call ─────────────────────────────────────────────────────────
def call_query(session_id, query):
    t0 = time.time()
    try:
        r = requests.post(
            f"{API_BASE}/query",
            json={"session_id": session_id, "user_id": USER_ID, "query": query},
            timeout=TIMEOUT,
        )
        latency = int((time.time() - t0) * 1000)
        if r.ok:
            return r.json(), latency, None
        return None, latency, f"HTTP {r.status_code}: {r.text[:200]}"
    except Exception as e:
        latency = int((time.time() - t0) * 1000)
        return None, latency, f"Exception: {type(e).__name__}: {str(e)[:200]}"


# ── Stage checks ──────────────────────────────────────────────────────
def stage_response_ok(response, error):
    return {"pass": error is None, "error": error}


def stage_retrieval(response, expected):
    """Dùng citations + scores làm proxy cho retrieval."""
    if not response:
        return {"pass": False, "reason": "no response"}
    meta = response.get("metadata", {})
    citations = meta.get("citations") or []
    scores = meta.get("scores") or {}
    top1 = scores.get("retrieval_top1")

    # acceptance → cần ít nhất 1 citation
    if expected == "acceptance":
        ok = len(citations) >= 1 and top1 is not None
    else:
        # rejection/refusal/ambiguous → không bắt buộc
        ok = True

    return {
        "pass": ok,
        "n_citations": len(citations),
        "top1_score": top1,
    }


def stage_generation(response):
    if not response:
        return {"pass": False}
    answer = response.get("metadata", {}).get("answer", "") or ""
    ok = len(answer.strip()) > 0 and "Lỗi khi gọi mô hình" not in answer
    return {"pass": ok, "answer_len": len(answer)}


def stage_check2(response, expected):
    if not response:
        return {"pass": False}
    meta = response.get("metadata", {})
    citations = meta.get("citations") or []
    status = meta.get("status", "")
    reason = (meta.get("reason") or "").lower()

    if citations:
        return {"status": "VALID", "n_citations": len(citations), "pass": True}

    # MISSING — OK cho rejection/refusal
    if expected in ("rejection", "refusal"):
        return {"status": "MISSING", "pass": True}

    # acceptance mà MISSING → fail
    return {"status": "MISSING", "pass": False, "reason": reason[:100]}


def stage_check3(response):
    if not response:
        return {"pass": False}
    status = response.get("metadata", {}).get("status", "")
    ok = status in VALID_STATUSES
    return {"pass": ok, "status": status}


def stage_contract(response):
    if not response:
        return {"pass": False, "missing": ["*"]}
    meta = response.get("metadata", {})
    required = ["status", "answer", "citations", "metrics"]
    missing = [f for f in required if f not in meta]
    return {"pass": len(missing) == 0, "missing": missing}


def stage_log(query, since_iso):
    today = datetime.now(timezone.utc).strftime("%Y-%m-%d")
    # Thay đổi logic lấy log cho tương thích project directory structure
    project_root = Path(__file__).parent.parent.parent.parent
    log_dir = project_root / "_data" / "logs"
    log_file = log_dir / f"{today}.jsonl"
    
    if not log_file.exists():
        return {"pass": False, "reason": "no log file"}
    try:
        # Đọc từ cuối lên 200 dòng để nhanh
        lines = log_file.read_text(encoding="utf-8").splitlines()[-200:]
        for line in reversed(lines):
            try:
                rec = json.loads(line)
                if rec.get("query") == query and rec.get("timestamp", "") >= since_iso:
                    return {"pass": True}
            except Exception:
                continue
    except Exception as e:
        return {"pass": False, "reason": str(e)[:100]}
    return {"pass": False, "reason": "no matching record"}


# ── Run one case ──────────────────────────────────────────────────────
def run_case(case, session_id):
    ts_start = datetime.now(timezone.utc).isoformat()

    response, latency, error = call_query(session_id, case["query"])
    meta = (response or {}).get("metadata", {}) or {}
    actual_status = meta.get("status")

    stages = {
        "response_ok": stage_response_ok(response, error),
        "retrieval":   stage_retrieval(response, case["expected_status"]),
        "generation":  stage_generation(response),
        "check2":      stage_check2(response, case["expected_status"]),
        "check3":      stage_check3(response),
        "contract":    stage_contract(response),
        "log":         stage_log(case["query"], ts_start),
    }

    passed = (actual_status == case["expected_status"])

    fail_stage = None
    for name in ["response_ok", "retrieval", "generation", "check2", "check3", "contract", "log"]:
        if stages[name].get("pass") is False:
            fail_stage = name
            break

    return {
        "case_id": case["case_id"],
        "source": case["source"],
        "language": case.get("language", "vi"), # fallback to vi if language is missing
        "query": case["query"],
        "expected_status": case["expected_status"],
        "actual_status": actual_status,
        "pass": passed,
        "stages": stages,
        "latency_ms": latency,
        "reason": meta.get("reason"),
        "fail_stage": fail_stage,
    }


# ── Reports ───────────────────────────────────────────────────────────
def write_markdown(results, path):
    total = len(results)
    passed = sum(1 for r in results if r["pass"])

    exp_dist = Counter(r["expected_status"] for r in results)
    act_dist = Counter(r["actual_status"] or "null" for r in results)

    latencies = sorted(r["latency_ms"] for r in results)
    p50 = latencies[len(latencies) // 2] if latencies else 0
    p95 = latencies[int(len(latencies) * 0.95)] if latencies else 0

    # Stage pass rates
    stage_names = ["response_ok", "retrieval", "generation", "check2", "check3", "contract", "log"]
    stage_pass = {s: sum(1 for r in results if r["stages"].get(s, {}).get("pass")) for s in stage_names}

    lines = []
    lines.append(f"# Eval Report — 200 Cases\n")
    lines.append(f"**Run at:** {datetime.now(timezone.utc).isoformat()}\n")
    lines.append(f"**Total:** {total}  ")
    lines.append(f"**Pass:** {passed}/{total} ({100*passed/total:.1f}%)\n")
    lines.append(f"**Latency:** P50={p50}ms  P95={p95}ms\n")

    lines.append("## Status Distribution\n")
    lines.append("| Status | Expected | Actual |")
    lines.append("|---|---|---|")
    for s in ["acceptance", "ambiguous", "rejection", "refusal", "null"]:
        lines.append(f"| {s} | {exp_dist.get(s, 0)} | {act_dist.get(s, 0)} |")

    lines.append("\n## Stage pass rate\n")
    lines.append("| Stage | Pass | % |")
    lines.append("|---|---|---|")
    for s in stage_names:
        p = stage_pass[s]
        lines.append(f"| {s} | {p}/{total} | {100*p/total:.1f}% |")

    lines.append("\n## By source\n")
    lines.append("| Source | n | Pass | % |")
    lines.append("|---|---|---|---|")
    for src in ["llm_gen", "log", "adversarial", "cross_doc"]:
        sub = [r for r in results if r.get("source") == src]
        p = sum(1 for r in sub if r["pass"])
        if sub:
            lines.append(f"| {src} | {len(sub)} | {p} | {100*p/len(sub):.1f}% |")

    lines.append("\n## By language\n")
    lines.append("| Lang | n | Pass | % |")
    lines.append("|---|---|---|---|")
    for lang in ["en", "vi"]:
        sub = [r for r in results if r.get("language") == lang]
        p = sum(1 for r in sub if r["pass"])
        if sub:
            lines.append(f"| {lang} | {len(sub)} | {p} | {100*p/len(sub):.1f}% |")

    lines.append(f"\n## Failures ({total - passed})\n")
    lines.append("| case_id | expected | actual | fail_stage | reason |")
    lines.append("|---|---|---|---|---|")
    for r in results:
        if not r["pass"]:
            reason = (r.get("reason") or "")[:60]
            lines.append(f"| {r['case_id']} | {r['expected_status']} | {r['actual_status']} | {r['fail_stage']} | {reason} |")

    path.write_text("\n".join(lines), encoding="utf-8")


def write_csv(results, path):
    fields = ["case_id", "source", "language", "query", "expected_status",
              "actual_status", "pass", "latency_ms", "fail_stage", "reason"]
    with path.open("w", encoding="utf-8", newline="") as f:
        w = csv.DictWriter(f, fieldnames=fields)
        w.writeheader()
        for r in results:
            w.writerow({k: r.get(k) for k in fields})


# ── Main ──────────────────────────────────────────────────────────────
def main():
    global USER_ID
    parser = argparse.ArgumentParser()
    parser.add_argument("--session-id", required=True)
    parser.add_argument("--user-id", default=USER_ID, help="User ID to bypass session authorization")
    parser.add_argument("--limit", type=int, default=None)
    parser.add_argument("--resume", action="store_true")
    args = parser.parse_args()
    
    USER_ID = args.user_id

    cases = load_cases(CASES_FILE)
    if args.limit:
        cases = cases[:args.limit]

    done_ids = load_done_ids(RESULTS_FILE) if args.resume else set()
    pending = [c for c in cases if c["case_id"] not in done_ids]

    print(f"Total cases: {len(cases)}")
    print(f"Pending: {len(pending)}")
    print(f"Session: {args.session_id}")
    print("=" * 70)

    # Health check
    try:
        r = requests.get(f"{API_BASE}/health", timeout=10)
        print(f"Backend health: {r.status_code} {r.json().get('status')}")
    except Exception as e:
        print(f"Backend unreachable: {e}")
        sys.exit(1)

    # Open results file in append mode if resume, else overwrite
    mode = "a" if args.resume else "w"
    out = RESULTS_FILE.open(mode, encoding="utf-8")

    all_results = []
    try:
        for i, case in enumerate(pending, 1):
            print(f"[{i}/{len(pending)}] {case['case_id']} ({case.get('source', '')}) — {case['query'][:50]}")
            r = run_case(case, args.session_id)
            all_results.append(r)
            out.write(json.dumps(r, ensure_ascii=False) + "\n")
            out.flush()

            marker = "✓" if r["pass"] else "✗"
            print(f"  {marker} expected={case['expected_status']} actual={r['actual_status']} ({r['latency_ms']}ms)")
    finally:
        out.close()

    # Reload all results (bao gồm các case đã chạy trước nếu resume)
    all_saved = [json.loads(l) for l in RESULTS_FILE.read_text(encoding="utf-8").splitlines() if l.strip()]

    write_markdown(all_saved, REPORT_MD)
    write_csv(all_saved, REPORT_CSV)

    print("=" * 70)
    print(f"Report: {REPORT_MD}")
    print(f"CSV:    {REPORT_CSV}")


if __name__ == "__main__":
    main()
