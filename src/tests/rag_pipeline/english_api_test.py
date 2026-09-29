import json
import time
import requests
from pathlib import Path

# ── CONFIG ────────────────────────────────────────────────────────────────────
BASE_URL = "http://127.0.0.1:8000"
USER_ID = "eval_english_user"
DOCS_DIR = Path("_data/uploads/mixigaming@gmail.com")
CASES_PATH = Path("src/tests/rag_pipeline/english_benchmark.jsonl")
RESULTS_PATH = Path("src/tests/rag_pipeline/english_api_report.json")

def load_cases():
    with open(CASES_PATH, encoding="utf-8") as f:
        return [json.loads(line) for line in f if line.strip()]

def upload_doc(file_path: Path, session_id: str = None) -> dict:
    headers = {"X-User-Id": USER_ID}
    data = {}
    if session_id:
        data["session_id"] = session_id

    content_type = "application/pdf" if file_path.suffix == ".pdf" else "text/plain"
    with open(file_path, "rb") as f:
        files = {"file": (file_path.name, f, content_type)}
        resp = requests.post(
            f"{BASE_URL}/upload",
            files=files,
            data=data,
            headers=headers,
            timeout=120,
        )
    resp.raise_for_status()
    return resp.json()

def query(session_id: str, query_text: str) -> dict:
    payload = {
        "session_id": session_id,
        "user_id": USER_ID,
        "query": query_text,
    }
    resp = requests.post(
        f"{BASE_URL}/query",
        json=payload,
        timeout=120,
    )
    resp.raise_for_status()
    return resp.json()

def delete_session(session_id: str):
    headers = {"X-User-Id": USER_ID}
    try:
        requests.delete(f"{BASE_URL}/sessions/{session_id}", headers=headers, timeout=30)
    except Exception:
        pass

def setup_session() -> str:
    # Lấy danh sách PDF (lọc trùng lặp file name để tránh upload nhiều bản sao)
    docs = []
    seen = set()
    for ext in ["*.pdf", "*.md", "*.txt"]:
        for p in DOCS_DIR.rglob(ext):
            if p.name not in seen:
                seen.add(p.name)
                docs.append(p)

    if not docs:
        raise RuntimeError(f"Không tìm thấy file trong {DOCS_DIR}")

    print(f"[SETUP] Uploading {len(docs)} unique docs...")
    session_id = None

    for doc in docs:
        print(f"  → {doc.name}")
        resp = upload_doc(doc, session_id)
        session_id = resp["session_id"]

    print(f"[SETUP] Session ready: {session_id}\n")
    return session_id

def main():
    print("=" * 60)
    print("M6 Phase 2 — RE-EVAL (English Benchmark via API)")
    print("=" * 60 + "\n")

    cases = load_cases()
    if not cases:
        print("Không tìm thấy cases trong english_benchmark.jsonl")
        return

    cases = cases[110:] # Chỉ chạy 22 cases cuối (từ index 110 trở đi)

    try:
        requests.get(f"{BASE_URL}/health")
    except:
        print(f"Server không phản hồi ở {BASE_URL}. Hãy start uvicorn!")
        return

    session_id = setup_session()

    print(f"[RUN] Chạy {len(cases)} cases...\n")
    results = []

    for i, case in enumerate(cases, 1):
        cid = case["id"]
        expected_status = case["expected"]
        category = case.get("category", "")

        start = time.time()
        try:
            resp = query(session_id, case["query"])
            elapsed = time.time() - start

            metadata = resp.get("metadata", {})
            actual_status = metadata.get("status", "unknown")
            reason = metadata.get("reason", "")

            answer = resp.get("answer", "")
            if "Lỗi khi gọi mô hình" in answer or "429" in answer:
                actual_status = "PROVIDER_ERROR"
                reason = "Rate limit / Quota exhausted"

            passed = (actual_status == expected_status)

            results.append({
                "id": cid,
                "category": category,
                "query": case["query"],
                "expected_status": expected_status,
                "actual_status": actual_status,
                "pass": passed,
                "reason": reason,
                "elapsed_s": round(elapsed, 2),
            })

            time.sleep(12) # Tránh Rate Limit 5 request/phút

            mark = "✅" if passed else "❌"
            print(f"[{i:03d}/{len(cases)}] {cid} ({expected_status}) → {actual_status} {mark}")
            if not passed and reason:
                print(f"       reason: {reason}")

        except Exception as e:
            results.append({
                "id": cid,
                "category": category,
                "query": case["query"],
                "expected_status": expected_status,
                "actual_status": "ERROR",
                "pass": False,
                "error": str(e),
            })
            print(f"[{i:03d}/{len(cases)}] {cid} → ERROR: {e}")

    delete_session(session_id)

    print("\n" + "=" * 60)
    print("RESULTS")
    print("=" * 60)

    total = len(results)
    passed = sum(1 for r in results if r["pass"])
    accuracy = passed / total * 100 if total else 0

    print(f"\nTotal: {total} | PASS: {passed} | FAIL: {total - passed}")
    print(f"Accuracy: {accuracy:.1f}%\n")

    print("--- Per Category ---")
    categories = sorted(list(set(r["category"] for r in results)))
    for cat in categories:
        cat_cases = [r for r in results if r["category"] == cat]
        cat_pass = sum(1 for r in cat_cases if r["pass"])
        cat_acc = cat_pass / len(cat_cases) * 100
        print(f"  {cat:35s}: {cat_pass:2d}/{len(cat_cases):2d} ({cat_acc:5.1f}%)")

    failed = [r for r in results if not r["pass"]]
    if failed:
        print(f"\n--- Failed ({len(failed)}) ---")
        for r in failed:
            print(f"  {r['id']:8s} | exp: {r['expected_status']:10s} | act: {r['actual_status']:10s} | {r.get('reason','')[:60]}")

    with open(RESULTS_PATH, "w", encoding="utf-8") as f:
        json.dump({
            "summary": {
                "total": total,
                "passed": passed,
                "accuracy": round(accuracy, 1),
            },
            "results": results,
        }, f, ensure_ascii=False, indent=2)
    print(f"\n✓ Report: {RESULTS_PATH}")

if __name__ == "__main__":
    main()
