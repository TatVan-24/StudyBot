"""
Rank Probe (Bilingual): eval_wiki_s3_features_001
--------------------------------------------------
Run the same rank probe for both Vietnamese and English query
to isolate whether language gap is the root cause.

Output: idea/demo/rank_probe_bilingual.md
"""
import json
import os
import sqlite3
import sys
import numpy as np
from pathlib import Path
from datetime import datetime

sys.path.append(str(Path(__file__).resolve().parent.parent.parent))

from src.indexer.embedding import EmbeddingEngine

INDEX_PATH   = "d:/Personal Project/AWS StudyBot/evaluation/index/m3_index.db"
TARGET_CHUNK = "sha256:57d9ec5ae0af2744"
REPORT_PATH  = "d:/Personal Project/AWS StudyBot/idea/demo/rank_probe_bilingual.md"

QUERIES = [
    ("Vietnamese (original)", "Nhung tinh nang cot loi (core features) cua Amazon S3 la gi?"),
    ("English (control)",     "What are the core features of Amazon S3?"),
]

# ── Load all embeddings once ─────────────────────────────────────────────────
print("Loading index...")
with sqlite3.connect(INDEX_PATH) as conn:
    rows = conn.execute(
        "SELECT chunk_id, source_block_ids, text, vector FROM embeddings"
    ).fetchall()
total_chunks = len(rows)
print(f"  Total chunks: {total_chunks}")

parsed = []
for chunk_id, raw_sids, text, raw_vec in rows:
    vec = np.frombuffer(raw_vec, dtype=np.float32)
    parsed.append((chunk_id, json.loads(raw_sids), text, vec))

all_vecs = np.vstack([p[3] for p in parsed])   # (N, 768)

# ── Engine ───────────────────────────────────────────────────────────────────
print("Initializing embedding engine...")
engine = EmbeddingEngine()

# ── Probe function ───────────────────────────────────────────────────────────
def run_probe(query_label, query_text):
    q_vec  = engine.encode([query_text])[0]
    scores = all_vecs @ q_vec
    order  = np.argsort(scores)[::-1]

    ranked = [(float(scores[i]), parsed[i][0], parsed[i][1], parsed[i][2])
              for i in order]

    target_rank = target_score = target_sids = target_text = None
    for rank, (score, chunk_id, sids, text) in enumerate(ranked, 1):
        if chunk_id == TARGET_CHUNK:
            target_rank, target_score, target_sids, target_text = rank, score, sids, text
            break

    boundaries = {}
    for k in [1, 5, 10, 20, 50, 100, 150, 200]:
        if k <= len(ranked):
            boundaries[k] = ranked[k - 1]

    return {
        "label": query_label, "query": query_text,
        "q_norm": float(np.linalg.norm(q_vec)),
        "target_rank": target_rank, "target_score": target_score,
        "target_sids": target_sids, "target_text": target_text,
        "top10": ranked[:10], "boundaries": boundaries,
        "total": total_chunks,
    }

results = []
for label, query in QUERIES:
    print(f"\nProbing [{label}]: {query}")
    r = run_probe(label, query)
    if r["target_rank"]:
        print(f"  rank={r['target_rank']}/{r['total']}  score={r['target_score']:.4f}")
    else:
        print("  TARGET NOT FOUND IN INDEX")
    results.append(r)

# ── Build report ─────────────────────────────────────────────────────────────
os.makedirs(os.path.dirname(REPORT_PATH), exist_ok=True)

lines = []
w = lines.append

w("# Rank Probe - Bilingual Comparison")
w("")
w(f"> Case: `eval_wiki_s3_features_001`  |  Target chunk: `{TARGET_CHUNK}`")
w(f"> Generated: {datetime.utcnow().strftime('%Y-%m-%dT%H:%M:%SZ')}")
w(f"> Index total chunks: {total_chunks}")
w("")

# Summary table
w("## Summary")
w("")
w("| Query | Language | Target Rank | Target Score | Score@Rank100 | Delta |")
w("|---|---|---:|---:|---:|---:|")
for r in results:
    s100 = r["boundaries"].get(100, (None,))[0]
    if r["target_rank"] is None:
        w(f"| {r['query'][:60]} | {r['label']} | NOT IN INDEX | - | - | - |")
    elif s100:
        delta = (s100 - r["target_score"]) if r["target_rank"] > 100 else 0.0
        w(f"| {r['query'][:60]} | {r['label']} | {r['target_rank']} | {r['target_score']:.4f} | {s100:.4f} | {delta:+.4f} |")
    else:
        w(f"| {r['query'][:60]} | {r['label']} | {r['target_rank']} | {r['target_score']:.4f} | - | - |")
w("")

# Per-query section
for r in results:
    w("---")
    w("")
    w(f"## [{r['label']}]")
    w("")
    w(f"**Query**: *{r['query']}*")
    w(f"**Vector norm**: {r['q_norm']:.4f}")
    w("")

    w("### Target Chunk")
    w("")
    w("```")
    if r["target_rank"] is None:
        w(f"[!!!] '{TARGET_CHUNK}' NOT FOUND in index. INGESTION FAILURE.")
    else:
        w(f"chunk_id     : {TARGET_CHUNK}")
        w(f"actual rank  : {r['target_rank']} / {r['total']}")
        w(f"score        : {r['target_score']:.4f}")
        w(f"source_blocks: {r['target_sids']}")
        w(f"text (120ch) : {repr(r['target_text'][:120]) if r['target_text'] else 'N/A'}")
    w("```")
    w("")

    w("### Score Landscape (Boundary Ranks)")
    w("")
    w("| Rank | Score | chunk_id | Text (70ch) |")
    w("|---:|---:|---|---|")
    for k, (score, chunk_id, sids, text) in r["boundaries"].items():
        marker = " <- TARGET" if chunk_id == TARGET_CHUNK else ""
        w(f"| {k} | {score:.4f} | `{chunk_id}`{marker} | {repr(text[:70])} |")
    w("")

    w("### Top-10 (What Won)")
    w("")
    w("| Rank | Score | chunk_id | Source Blocks | Text (80ch) |")
    w("|---:|---:|---|---|---|")
    for rank, (score, chunk_id, sids, text) in enumerate(r["top10"], 1):
        w(f"| {rank} | {score:.4f} | `{chunk_id}` | `{sids}` | {repr(text[:80])} |")
    w("")

# Verdict
w("---")
w("")
w("## Verdict")
w("")
vi, en = results[0], results[1]
if vi["target_rank"] is None and en["target_rank"] is None:
    w("Both queries: TARGET NOT IN INDEX. ROOT CAUSE: **INGESTION FAILURE**.")
elif vi["target_rank"] is None or en["target_rank"] is None:
    w("One query found target, one did not. Check manually.")
else:
    s100_vi = vi["boundaries"].get(100, (None,))[0]
    s100_en = en["boundaries"].get(100, (None,))[0]
    w("| Metric | Vietnamese | English |")
    w("|---|---|---|")
    w(f"| Target rank | {vi['target_rank']} | {en['target_rank']} |")
    w(f"| Target score | {vi['target_score']:.4f} | {en['target_score']:.4f} |")
    if s100_vi and s100_en:
        w(f"| Score @ rank 100 | {s100_vi:.4f} | {s100_en:.4f} |")
        w(f"| Delta | {s100_vi - vi['target_score']:+.4f} | {s100_en - en['target_score']:+.4f} |")
    w("")
    vi_r, en_r = vi["target_rank"], en["target_rank"]
    if en_r < vi_r:
        w(f"English rank ({en_r}) is {vi_r - en_r} positions better than Vietnamese ({vi_r}).")
        w("")
        w("**Conclusion: Cross-lingual semantic gap is a contributing factor.**")
    elif en_r == vi_r:
        w(f"Both queries produce rank {vi_r}. Language gap is NOT the root cause.")
        w("")
        w("**Conclusion: Investigate chunking boundary or distractor competition.**")
    else:
        w(f"Vietnamese ({vi_r}) ranks better than English ({en_r}). Unexpected - investigate further.")

with open(REPORT_PATH, "w", encoding="utf-8") as f:
    f.write("\n".join(lines) + "\n")

print(f"\nReport written: {REPORT_PATH}")
