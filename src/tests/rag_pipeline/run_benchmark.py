import json
import time
import requests
from pathlib import Path

# ── CONFIG ────────────────────────────────────────────────────────────────────
BASE_URL = "http://127.0.0.1:8000"
USER_ID = "eval_benchmark_user"
DOCS_DIR = Path("_data/uploads/mixigaming@gmail.com")

def load_cases(file_path: Path, max_cases: int = None):
    with open(file_path, encoding="utf-8") as f:
        cases = [json.loads(line) for line in f if line.strip()]
    if max_cases:
        cases = cases[:max_cases]
    return cases

def upload_doc(file_path: Path, session_id: str = None) -> dict:
    headers = {"X-User-Id": USER_ID}
    data = {}
    if session_id:
        data["session_id"] = session_id
    content_type = "application/pdf" if file_path.suffix == ".pdf" else "text/plain"
    with open(file_path, "rb") as f:
        resp = requests.post(
            f"{BASE_URL}/upload",
            files={"file": (file_path.name, f, content_type)},
            data=data,
            headers=headers,
            timeout=120,
        )
    resp.raise_for_status()
    return resp.json()

def query(session_id: str, query_text: str) -> dict:
    resp = requests.post(
        f"{BASE_URL}/query",
        json={"session_id": session_id, "user_id": USER_ID, "query": query_text},
        timeout=120,
    )
    resp.raise_for_status()
    return resp.json()

def delete_session(session_id: str):
    try:
        requests.delete(f"{BASE_URL}/sessions/{session_id}", headers={"X-User-Id": USER_ID}, timeout=30)
    except:
        pass

def run_benchmark(cases_path: str, output_path: str, max_cases: int = None):
    print(f"\n============================================================")
    print(f"RUNNING BENCHMARK: {cases_path}")
    print(f"============================================================")

    cases = load_cases(Path(cases_path), max_cases)

    # 1. Upload Docs
    print("\n[SETUP] Uploading Docs...")
    session_id = None
    seen = set()
    for ext in ["*.pdf", "*.md", "*.txt"]:
        for p in DOCS_DIR.rglob(ext):
            if p.name not in seen:
                seen.add(p.name)
                res = upload_doc(p, session_id)
                session_id = res.get("session_id")
                print(f"  → Uploaded: {p.name}")

    if not session_id:
        print("Không tìm thấy document nào để upload!")
        return

    print(f"[SETUP] Session ready: {session_id}")

    # 2. Run Queries
    results = []
    print(f"\n[RUN] Running {len(cases)} cases...")

    for i, case in enumerate(cases, 1):
        cid = case["id"]
        # Map schema if Vietnamese benchmark (test_cases.jsonl)
        if "expected_class" in case:
            expected_status = case["expected_class"].lower()
            if expected_status == "grounded": expected_status = "acceptance"
            elif expected_status == "reject": expected_status = "rejection"
        else:
            expected_status = case["expected"]

        # Start timing
        t0 = time.time()
        try:
            resp = query(session_id, case["query"])
            elapsed = time.time() - t0

            meta = resp.get("metadata", {})
            actual_status = meta.get("status", "unknown")
            reason = meta.get("reason", "")
            citations = meta.get("citations", [])
            latencies = meta.get("metrics", {}).get("latency_ms", {})
            answer = resp.get("answer", "")

            # Identify Provider Error vs Check 2 vs Check 3
            provider_error = "Lỗi khi gọi mô hình" in answer or "429" in answer
            check2_fail = "Check 2 Failed" in reason
            check3_ambiguous = "ambiguous" in actual_status.lower() or "ambiguous" in reason.lower()
            check3_contradict = "contradiction" in actual_status.lower() or "contradict" in reason.lower()

            if provider_error:
                actual_status = "PROVIDER_ERROR"

            passed = (actual_status == expected_status)

            results.append({
                "id": cid,
                "expected": expected_status,
                "actual": actual_status,
                "pass": passed,
                "reason": reason,
                "provider_error": provider_error,
                "has_citation": len(citations) > 0,
                "check2_fail": check2_fail,
                "check3_ambiguous": check3_ambiguous,
                "check3_contradict": check3_contradict,
                "latency_retrieval": latencies.get("retrieval", 0),
                "latency_generation": latencies.get("generation", 0),
                "latency_total": latencies.get("total", int(elapsed*1000)),
            })

            mark = "✅" if passed else "❌"
            if provider_error: mark = "⚠️"

            print(f"[{i:03d}/{len(cases)}] {cid} ({expected_status}) → {actual_status} {mark} (cit:{len(citations)})")

        except Exception as e:
            results.append({
                "id": cid,
                "expected": expected_status,
                "actual": "HTTP_ERROR",
                "pass": False,
                "provider_error": True,
                "has_citation": False,
                "reason": str(e),
                "check2_fail": False,
                "check3_ambiguous": False,
                "check3_contradict": False,
            })
            print(f"[{i:03d}/{len(cases)}] {cid} → ERROR: {e}")

        # Groq OSS models rate limits are usually 30 RPM, 1K/day.
        # We can add a small sleep to be safe, e.g. 2s
        time.sleep(2)

    delete_session(session_id)

    # 3. Aggregating Metrics
    total = len(results)
    provider_errors = sum(1 for r in results if r["provider_error"])
    valid_calls = total - provider_errors

    passed = sum(1 for r in results if r["pass"] and not r["provider_error"])
    accuracy = (passed / valid_calls * 100) if valid_calls > 0 else 0

    cit_present = sum(1 for r in results if r["has_citation"])
    check2_fails = sum(1 for r in results if r["check2_fail"])
    check3_amb_cnt = sum(1 for r in results if r.get("check3_ambiguous", False))
    check3_contra_cnt = sum(1 for r in results if r.get("check3_contradict", False))

    report = {
        "summary": {
            "total_cases": total,
            "provider_errors": provider_errors,
            "valid_calls": valid_calls,
            "passed": passed,
            "accuracy_on_valid": round(accuracy, 2),
            "metrics": {
                "citation_present": f"{cit_present}/{valid_calls}",
                "check2_rejected": f"{check2_fails}/{valid_calls}",
                "check3_ambiguous": f"{check3_amb_cnt}/{valid_calls}",
                "check3_contradiction": f"{check3_contra_cnt}/{valid_calls}"
            }
        },
        "results": results
    }

    with open(output_path, "w", encoding="utf-8") as f:
        json.dump(report, f, ensure_ascii=False, indent=2)
    print(f"\n✓ Saved rich report to: {output_path}")

if __name__ == "__main__":
    # RUN ENGLISH BENCHMARK (132 cases)
    run_benchmark(
        cases_path="src/tests/rag_pipeline/english_benchmark.jsonl",
        output_path="src/tests/rag_pipeline/groq_english_full.json"
    )

    # RUN VIETNAMESE BENCHMARK (34 cases)
    run_benchmark(
        cases_path="src/tests/rag_pipeline/test_cases.jsonl",
        output_path="src/tests/rag_pipeline/groq_vietnamese_full.json"
    )
