"""
test_vector_phase2.py
=====================
Test LocalVector session isolation.

Run:
    $env:PYTHONPATH = "D:\Personal Project\AWS StudyBot;D:\Personal Project\AWS StudyBot\src"
    python src/tests/rag_pipeline/test_vector_phase2.py
"""

import os
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[3]))
sys.path.insert(0, str(Path(__file__).resolve().parents[3] / "src"))

from src.rag_pipeline.llm.adapters.vector import LocalVector


def clean_db():
    for f in ["_data/m6_index.db", "_data/m6_index.db-wal", "_data/m6_index.db-shm"]:
        p = Path(f)
        if p.exists():
            try:
                p.unlink()
                print(f"  Removed {f}")
            except PermissionError:
                print(f"  Warning: cannot remove {f} (in use)")


def test_session_isolation():
    print("=" * 60)
    print("TEST: Session Isolation")
    print("=" * 60)

    print("\n[1] Cleaning DB...")
    clean_db()

    print("\n[2] Initializing LocalVector...")
    vec = LocalVector()

    print("\n[3] Ingesting docs into 2 different sessions...")
    vec.ingest(
        doc_id="doc_vector_db",
        text=(
            "Vector Database là hệ thống lưu trữ vector. "
            "Collection tương đương Table trong SQL. "
            "Point tương đương Row. "
            "Payload là metadata dạng JSON."
        ),
        user_id="user_1",
        session_id="sess_vector",
    )

    vec.ingest(
        doc_id="doc_blockchain",
        text=(
            "Blockchain là sổ cái phân tán. "
            "Bitcoin là ứng dụng đầu tiên của blockchain. "
            "Hash là hàm một chiều dùng để bảo mật. "
            "Smart contract cho phép lập trình trên blockchain."
        ),
        user_id="user_1",
        session_id="sess_blockchain",
    )

    print("\n[4] Testing session isolation...")
    passed = True

    # Test 1
    print("\n--- Test 1: Search trong sess_vector ---")
    results = vec.search("Collection là gì?", session_id="sess_vector", top_k=5)
    doc_ids = [r["doc_id"] for r in results]
    print(f"  Returned: {doc_ids}")
    if results and all("vector_db" in did for did in doc_ids):
        print("  ✅ PASS")
    else:
        print("  ❌ FAIL: Cross-contamination detected")
        passed = False

    # Test 2
    print("\n--- Test 2: Search trong sess_blockchain ---")
    results = vec.search("Hash là gì?", session_id="sess_blockchain", top_k=5)
    doc_ids = [r["doc_id"] for r in results]
    print(f"  Returned: {doc_ids}")
    if results and all("blockchain" in did for did in doc_ids):
        print("  ✅ PASS")
    else:
        print("  ❌ FAIL: Cross-contamination detected")
        passed = False

    # Test 3: Cross-session query in wrong session
    print("\n--- Test 3: Bitcoin query bị giới hạn vào sess_vector ---")
    results = vec.search("Bitcoin là gì?", session_id="sess_vector", top_k=5)
    doc_ids = [r["doc_id"] for r in results]
    print(f"  Returned: {doc_ids}")
    if all("vector_db" in did for did in doc_ids):
        print("  ✅ PASS: Session scope enforced")
    else:
        print("  ❌ FAIL")
        passed = False

    # Test 4: Legacy — no session_id
    print("\n--- Test 4: Legacy mode (no session_id) ---")
    results = vec.search("Vector là gì?", top_k=10)
    print(f"  Total chunks returned: {len(results)}")
    if len(results) > 0:
        print("  ✅ PASS: Legacy mode works")
    else:
        print("  ❌ FAIL")
        passed = False

    # Test 5: Metadata format
    print("\n--- Test 5: Metadata format ---")
    results = vec.search("Vector DB", session_id="sess_vector", top_k=1)
    if results:
        r = results[0]
        required = ["text", "doc_id", "score", "metadata"]
        missing = [f for f in required if f not in r]
        if missing:
            print(f"  ❌ FAIL: Missing fields {missing}")
            passed = False
        else:
            meta = r["metadata"]
            required_meta = ["chunk_id", "chunk_index", "source_block_ids", "heading_context", "token_count"]
            missing_meta = [f for f in required_meta if f not in meta]
            if missing_meta:
                print(f"  ❌ FAIL: Missing metadata fields {missing_meta}")
                passed = False
            else:
                print(f"  ✅ PASS (score={r['score']:.4f}, chunk={meta['chunk_id'][:20]}...)")

    return passed


def main():
    print("\n" + "=" * 60)
    print("VECTOR.PY PHASE 2.2 TEST")
    print("=" * 60 + "\n")

    try:
        passed = test_session_isolation()
    except Exception as e:
        import traceback
        print(f"\n❌ EXCEPTION: {type(e).__name__}: {e}")
        traceback.print_exc()
        sys.exit(1)

    print("\n" + "=" * 60)
    if passed:
        print("✅ ALL TESTS PASSED → Ready for Phase 3 (handlers.py)")
    else:
        print("❌ SOME TESTS FAILED")
        sys.exit(1)
    print("=" * 60)


if __name__ == "__main__":
    main()
