"""
test_handlers_phase3.py
=======================
Test handlers.py Phase 3 trực tiếp, không qua HTTP.

Run (với server đang chạy):
    $env:PYTHONPATH = "D:\Personal Project\AWS StudyBot;D:\Personal Project\AWS StudyBot\src"
    python src/tests/rag_pipeline/test_handlers_phase3.py
"""
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[3]))
sys.path.insert(0, str(Path(__file__).resolve().parents[3] / "src"))

from src.backend.adapters import factory
from src.backend import handlers


def sep(title=""):
    print("\n" + "=" * 60)
    if title:
        print(f"  {title}")
        print("=" * 60)


def main():
    sep("PHASE 3 HANDLER TEST")

    # ── Init adapters (dùng factory = giống server) ─────────────────────────
    print("\n[INIT] Loading adapters (reuses existing DB)...")
    ai_client   = factory.make_ai()
    storage     = factory.make_storage()
    userstore   = factory.make_userstore()
    vector_store = factory.make_vector()
    print("  OK")

    USER_ID = "test_user_phase3"
    KWARGS = dict(
        ai_client=ai_client,
        userstore=userstore,
        vector_store=vector_store,
        vector_backend="local",
        bedrock_kb_id="",
    )

    # ── Test 1: Upload → auto-create session ─────────────────────────────────
    sep("Test 1: Upload → auto-create session")
    upload_result = handlers.handle_upload(
        user_id=USER_ID,
        filename="test_vector.txt",
        data=(
            "Vector Database là hệ thống lưu trữ vector embedding. "
            "Collection tương đương Table trong SQL. "
            "Point tương đương Row. "
            "Payload là metadata dạng JSON gắn vào mỗi vector."
        ).encode("utf-8"),
        storage=storage,
        userstore=userstore,
        vector_store=vector_store,
    )
    print(f"  Response: {upload_result}")

    assert "session_id" in upload_result, "❌ Missing session_id"
    assert "doc_id" in upload_result,     "❌ Missing doc_id"
    session_id = upload_result["session_id"]
    print(f"  ✅ Session auto-created: {session_id}")

    # ── Test 2: Upload vào session đã tạo ────────────────────────────────────
    sep("Test 2: Upload vào existing session")
    upload2 = handlers.handle_upload(
        user_id=USER_ID,
        filename="test_vector2.txt",
        data=b"HNSW la thuat toan index cho vector search.",
        storage=storage,
        userstore=userstore,
        vector_store=vector_store,
        session_id=session_id,
    )
    print(f"  Response: {upload2}")
    assert upload2.get("session_id") == session_id, "❌ session_id không match"
    print(f"  ✅ Doc added to existing session")

    # ── Test 3: Query → acceptance ────────────────────────────────────────────
    sep("Test 3: Query → acceptance (grounded answer)")
    q_result = handlers.handle_query(
        session_id=session_id,
        user_id=USER_ID,
        query="Collection trong Vector Database là gì?",
        **KWARGS,
    )
    print(f"  Session ID:    {q_result.get('session_id')}")
    print(f"  User ID:       {q_result.get('user_id')}")
    meta = q_result.get("metadata", {})
    print(f"  Status:        {meta.get('status')}")
    print(f"  Answer:        {str(meta.get('answer', ''))[:100]}...")
    print(f"  Strategy:      {meta.get('strategy')}")
    print(f"  Scores:        {meta.get('scores')}")
    print(f"  Metrics:       {meta.get('metrics')}")
    print(f"  Citations:     {meta.get('citations', [])[:2]}")

    # Verify Contract 8.2
    required_top = ["session_id", "user_id", "metadata"]
    required_meta = ["status", "answer", "strategy", "scores", "citations", "metrics"]
    for f in required_top:
        assert f in q_result, f"❌ Top-level field missing: {f}"
    for f in required_meta:
        assert f in meta, f"❌ metadata field missing: {f}"
    print("  ✅ Output Contract 8.2 OK")

    # ── Test 4: Query session không tồn tại ──────────────────────────────────
    sep("Test 4: Session không tồn tại → rejection")
    bad_session = handlers.handle_query(
        session_id="non_existent_session_xyz",
        user_id=USER_ID,
        query="Test",
        **KWARGS,
    )
    print(f"  Status: {bad_session['metadata']['status']}")
    print(f"  Reason: {bad_session['metadata'].get('reason')}")
    assert bad_session["metadata"]["status"] == "rejection", "❌ Phải là rejection"
    assert "not found" in bad_session["metadata"].get("reason", "").lower(), "❌ Reason phải mention not found"
    print("  ✅ Session-not-found handled correctly (skip_log=True)")

    # ── Test 5: handle_list_sessions ─────────────────────────────────────────
    sep("Test 5: List sessions")
    list_result = handlers.handle_list_sessions(USER_ID, userstore)
    print(f"  Sessions: {len(list_result['sessions'])} found")
    assert any(s["session_id"] == session_id for s in list_result["sessions"]), "❌ Session không có trong list"
    print("  ✅ List sessions OK")

    # ── Test 6: handle_get_session ────────────────────────────────────────────
    sep("Test 6: Get session detail")
    get_result = handlers.handle_get_session(session_id, USER_ID, userstore)
    print(f"  Session:   {get_result.get('session', {}).get('title')}")
    print(f"  Documents: {get_result.get('documents')}")
    print(f"  Turns:     {len(get_result.get('turns', []))}")
    assert "session" in get_result,   "❌ Missing session"
    assert "documents" in get_result, "❌ Missing documents"
    assert "turns" in get_result,     "❌ Missing turns"
    print("  ✅ Get session OK")

    # ── Test 7: handle_delete_session ─────────────────────────────────────────
    sep("Test 7: Delete session")
    del_result = handlers.handle_delete_session(session_id, USER_ID, userstore)
    print(f"  Delete result: {del_result}")
    assert del_result.get("status") == "deleted", "❌ Delete failed"

    # Verify không còn trong list
    after_delete = handlers.handle_list_sessions(USER_ID, userstore)
    remaining = [s for s in after_delete["sessions"] if s["session_id"] == session_id]
    assert not remaining, "❌ Session vẫn còn sau khi delete"
    print("  ✅ Delete session + verify removed OK")

    # ── Kết quả ───────────────────────────────────────────────────────────────
    sep("✅ ALL TESTS PASSED → Ready for Phase 4 (app.py)")


if __name__ == "__main__":
    try:
        main()
    except Exception as e:
        import traceback
        print(f"\n❌ EXCEPTION: {type(e).__name__}: {e}")
        traceback.print_exc()
        sys.exit(1)
