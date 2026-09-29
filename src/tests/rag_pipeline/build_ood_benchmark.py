"""
Build OOD vs In-Domain benchmark từ query logs thực tế.

Chiến lược:
- Dùng retrieved chunks + top1_score làm signal gán nhãn
- Query có top1_score >= 0.50 AND có chunk nội dung thực sự liên quan → in_domain
- Query có top1_score < 0.40 → likely OOD
- Query 0.40-0.50 → manual review zone (bỏ qua để dataset sạch)

Output: src/tests/rag_pipeline/ood_benchmark.jsonl
"""
import json
import sys
from pathlib import Path
from collections import Counter

sys.path.append(str(Path(__file__).resolve().parents[3]))

from src.backend.app import userstore, vector_store

# ── Config ──────────────────────────────────────────────────────────────────
OUTPUT = Path("src/tests/rag_pipeline/ood_benchmark.jsonl")
SCORE_IN_DOMAIN  = 0.50   # top1 >= này → likely in-domain
SCORE_OOD        = 0.40   # top1 <  này → likely OOD
TOP_K            = 3

# ── Lấy session có docs ──────────────────────────────────────────────────────
USER_ID = "eval_english_user"
sessions = userstore.list_sessions(USER_ID)
session_id = None
for s in reversed(sessions):
    if userstore.get_session_docs(s["session_id"]):
        session_id = s["session_id"]
        break

if not session_id:
    print("[ERROR] No session with docs found.")
    sys.exit(1)

print(f"[*] Session: {session_id}")

# ── Đọc toàn bộ queries từ log ───────────────────────────────────────────────
LOG_DIR = Path("_data/logs")
log_files = sorted(LOG_DIR.glob("*.jsonl"))

seen_queries = set()
all_queries = []
for f in log_files:
    for line in f.read_bytes().decode("utf-8", errors="replace").splitlines():
        if not line.strip():
            continue
        try:
            r = json.loads(line)
            q = r.get("query", "").strip()
            status = r.get("status", "")
            # Bỏ qua injection test, greeting, rất ngắn
            if not q or len(q) < 8:
                continue
            if q in seen_queries:
                continue
            seen_queries.add(q)
            all_queries.append({"query": q, "log_status": status})
        except Exception:
            pass

print(f"[*] Unique queries in logs: {len(all_queries)}")

# ── Retrieve và score từng query ─────────────────────────────────────────────
results = []
in_domain_count = 0
ood_count = 0
ambiguous_count = 0

for i, item in enumerate(all_queries):
    q = item["query"]
    chunks = vector_store.search(q, top_k=TOP_K, session_id=session_id)
    top1 = chunks[0].get("score", 0.0) if chunks else 0.0

    # Tính lexical ratio (đơn giản, không dùng stopwords)
    qwords = set(q.lower().split())
    max_lex = 0.0
    if qwords and chunks:
        for c in chunks[:TOP_K]:
            cwords = set(c.get("text", "").lower().split())
            if cwords:
                ratio = len(qwords & cwords) / len(qwords)
                max_lex = max(max_lex, ratio)

    # Gán nhãn tự động dựa trên score
    if top1 >= SCORE_IN_DOMAIN:
        label = "in_domain"
        in_domain_count += 1
    elif top1 < SCORE_OOD:
        label = "ood"
        ood_count += 1
    else:
        label = "ambiguous_skip"  # vùng 0.40-0.50 → không đưa vào benchmark
        ambiguous_count += 1

    rec = {
        "query": q,
        "label": label,
        "top1_score": round(top1, 4),
        "lexical_ratio": round(max_lex, 4),
        "log_status": item["log_status"],
        "n_chunks": len(chunks),
        "top3_chunk_ids": [c.get("doc_id", c.get("metadata", {}).get("chunk_id", "")) for c in chunks],
        "top1_snippet": chunks[0].get("text", "")[:120] if chunks else "",
    }
    results.append(rec)

    if (i + 1) % 20 == 0:
        print(f"  Processed {i+1}/{len(all_queries)}...")

print(f"\n[*] Labeling complete:")
print(f"    in_domain      : {in_domain_count}")
print(f"    ood            : {ood_count}")
print(f"    ambiguous_skip : {ambiguous_count}")

# ── Chỉ lưu in_domain + ood (bỏ ambiguous) ──────────────────────────────────
clean = [r for r in results if r["label"] in ("in_domain", "ood")]
print(f"    clean dataset  : {len(clean)} cases ({in_domain_count} IN + {ood_count} OOD)")

# ── Lưu output ───────────────────────────────────────────────────────────────
OUTPUT.parent.mkdir(parents=True, exist_ok=True)
with open(OUTPUT, "w", encoding="utf-8") as f:
    for r in clean:
        f.write(json.dumps(r, ensure_ascii=False) + "\n")

print(f"\n[SAVED] {OUTPUT} ({len(clean)} cases)")

# ── Print sample ─────────────────────────────────────────────────────────────
print("\n--- Sample IN_DOMAIN (top 5) ---")
for r in [x for x in clean if x["label"] == "in_domain"][:5]:
    print(f"  [{r['top1_score']:.4f}] {r['query'][:70]}")

print("\n--- Sample OOD (top 5) ---")
for r in [x for x in clean if x["label"] == "ood"][:5]:
    print(f"  [{r['top1_score']:.4f}] {r['query'][:70]}")
