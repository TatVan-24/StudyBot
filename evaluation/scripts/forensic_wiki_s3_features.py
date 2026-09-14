"""
Forensic Investigation: eval_wiki_s3_features_001
-------------------------------------------------
Input:   Query + Target blocks (text from blocks.jsonl)
Output:  Top-100 returned chunks (with text) vs target blocks
Goal:    Understand WHY this case is TOTAL_MISS
"""
import json
import sys
from pathlib import Path

sys.path.append(str(Path(__file__).resolve().parent.parent.parent))

from src.indexer.embedding import EmbeddingEngine
from src.indexer.vector_store import SQLiteVectorStore
from evaluation.scripts.validate_resolution import load_blocks, match_locator

BLOCKS_PATH = "d:/Personal Project/AWS StudyBot/evaluation/bundle_all/blocks.jsonl"
INDEX_PATH  = "d:/Personal Project/AWS StudyBot/evaluation/index/m3_index.db"
CASE_ID     = "eval_wiki_s3_features_001"
TOP_K       = 100

# ── Load the specific case ─────────────────────────────────────────────────────
case = None
with open("d:/Personal Project/AWS StudyBot/evaluation/datasets/development-v2.jsonl", encoding="utf-8") as f:
    for line in f:
        c = json.loads(line)
        if c["case_id"] == CASE_ID:
            case = c
            break

assert case, f"Case {CASE_ID} not found"

print("=" * 70)
print("INPUT — QUERY")
print("=" * 70)
print(f"  Case ID  : {case['case_id']}")
print(f"  Category : {case['category']}")
print(f"  Language : {case['query']['language']}")
print(f"  Query    : {case['query']['text']}")
print(f"  Scope    : {case['scope']['document_ids']}")
print()
print("  Evidence Locator:")
for ev in case["evidence"]:
    print(f"    doc_id  = {ev['document_id']}")
    print(f"    locator = {json.dumps(ev['locator'])}")
    print(f"    note    = {ev.get('evidence_note','')}")
print()

# ── Resolve target blocks ──────────────────────────────────────────────────────
blocks_by_doc = load_blocks()

target_block_ids = set()
for ev in case.get("evidence", []):
    doc_id = ev.get("document_id")
    gt_locator = ev.get("locator")
    for b in blocks_by_doc.get(doc_id, []):
        if match_locator(gt_locator, b):
            target_block_ids.add(b["block_id"])

print("=" * 70)
print(f"INPUT — TARGET BLOCKS ({len(target_block_ids)} resolved)")
print("=" * 70)

all_blocks = {}
with open(BLOCKS_PATH, encoding="utf-8") as f:
    for line in f:
        b = json.loads(line)
        all_blocks[b["block_id"]] = b

if not target_block_ids:
    print("  [!] 0 blocks resolved — locator mismatch problem")
else:
    for bid in sorted(target_block_ids):
        b = all_blocks.get(bid)
        if b:
            print(f"\n  block_id   : {bid}")
            print(f"  block_type : {b.get('block_type')}")
            print(f"  locator    : {json.dumps(b.get('locator', {}))}")
            print(f"  text       : {repr(b.get('text',''))}")
        else:
            print(f"\n  [!] block_id {bid} NOT FOUND in blocks.jsonl")

print()

# ── Check which chunks in index reference these blocks ────────────────────────
import sqlite3
print("=" * 70)
print("INDEX CHECK — chunks containing target block_ids")
print("=" * 70)
with sqlite3.connect(INDEX_PATH) as conn:
    rows = conn.execute("SELECT chunk_id, source_block_ids, text FROM embeddings").fetchall()

target_chunks = []
for chunk_id, raw_sids, text in rows:
    sids = set(json.loads(raw_sids))
    overlap = sids & target_block_ids
    if overlap:
        target_chunks.append((chunk_id, list(overlap), text))

if not target_chunks:
    print("  [!!!] NO chunks in the index contain any of the target block_ids")
    print("        → The target blocks were NEVER indexed. Ingestion failure.")
else:
    print(f"  {len(target_chunks)} chunk(s) in index contain target blocks:\n")
    for chunk_id, evidence_bids, text in target_chunks:
        print(f"  chunk_id        : {chunk_id}")
        print(f"  provided_blocks : {evidence_bids}")
        print(f"  text (first 200): {repr(text[:200])}")
        print()

# ── Run actual retrieval Top-100 ───────────────────────────────────────────────
print("=" * 70)
print(f"RETRIEVAL — Top-{TOP_K} Results")
print("=" * 70)

engine = EmbeddingEngine()
store  = SQLiteVectorStore(INDEX_PATH)

q_vector = engine.encode([case["query"]["text"]])[0]
results  = store.search(q_vector, top_k=TOP_K)

print(f"  Query vector dim : {q_vector.shape[0]}")
print(f"  Results returned : {len(results)}")
print()

for r in results:
    is_target = bool(set(r.source_block_ids) & target_block_ids)
    marker = "  [HIT] " if is_target else "        "
    print(f"{marker}Rank {r.chunk_index if hasattr(r,'chunk_index') else '?':>3}  score={r.score:.4f}  chunk={r.chunk_id}")
    print(f"         source_blocks = {r.source_block_ids}")
    print(f"         text (80ch)   = {repr(r.text[:80])}")
    if is_target:
        print(f"         [MATCH] provided = {list(set(r.source_block_ids) & target_block_ids)}")
    print()
