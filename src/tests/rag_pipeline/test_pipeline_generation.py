import json
import re
from src.backend.app import userstore, ai_client
from src.backend.adapters import factory

vector_store = factory.make_vector()
USER_ID = "mixigaming@gmail.com"

# Tìm session có document gần đây nhất
sessions = userstore.list_sessions(USER_ID)
session_id = None
for s in reversed(sessions):
    if userstore.get_session_docs(s["session_id"]):
        session_id = s["session_id"]
        break

if not session_id:
    print("Không tìm thấy session nào có document.")
    exit(1)

print(f"Sử dụng session: {session_id}")

query = "Vector Database khác SQL truyền thống ở điểm cốt lõi nào?"
chunks = vector_store.search(query, top_k=5, session_id=session_id)

print("\n[1] Retrieved Chunks BEFORE Remap:")
for i, c in enumerate(chunks):
    doc_id = c.get("doc_id", "unknown")
    chunk_id = c.get("metadata", {}).get("chunk_id", "unknown")
    text = c.get("text", "")[:50].replace('\n', ' ')
    print(f"  [{i}] doc_id: {doc_id} | chunk_id: {chunk_id} | text: {text}...")

# Remap chunk_id for validators (GIỐNG HỆT HANDLERS.PY)
for c in chunks:
    if "metadata" in c and "chunk_id" in c["metadata"]:
        c["doc_id"] = c["metadata"]["chunk_id"]

print("\n[2] Calling generate_with_citations...")
res = ai_client.generate_with_citations(query, chunks)
answer = res.get("answer", "")

print("\n[3] RAW LLM ANSWER:")
print("-" * 40)
print(answer)
print("-" * 40)

print("\n[4] Citations extracted by AI Adapter:")
citations = res.get("citations", [])
print(f"  Count: {len(citations)}")
for cit in citations:
    print(f"  - {cit}")

# Extra Check: Tự chạy lại Regex để xem có hụt gì không
matches = re.findall(r"\[(.*?)\]", answer)
print(f"\n[5] Raw Regex Matches: {matches}")

print("\n[5.5] Scope Test (P0 Hypothesis):")
session_docs = userstore.get_session_docs(session_id)
session_doc_ids = session_docs
retrieved_doc_ids = list(set([c.get("doc_id", "unknown") for c in chunks]))

print(f"  Session doc IDs: {session_doc_ids}")
print(f"  Retrieved doc IDs: {retrieved_doc_ids}")

out_of_scope = [d for d in retrieved_doc_ids if d not in session_doc_ids and d != "unknown"]
if out_of_scope:
    print(f"  ⚠️ ALERT: Found out-of-scope docs in retrieval: {out_of_scope}")
else:
    print("  ✅ All retrieved docs belong to the current session.")

print("\n[6] Check 2 Execution:")
from src.backend import validators
check2_status = validators.check_2_citations(citations, chunks)
print(f"  Input citations: {len(citations)}")
print(f"  Input retrieved chunks: {len(chunks)}")
print(f"  Check 2 OUTPUT: {check2_status}")
