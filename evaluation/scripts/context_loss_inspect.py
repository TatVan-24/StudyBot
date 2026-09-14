"""
Context-Loss Inspection: wiki_06_markdown_sample
-------------------------------------------------
Hypothesis: Target chunk lacks "Amazon S3" entity anchor.
Test: Inspect block lineage + chunk text around target blocks.

No embedding, no model. Pure data inspection.
"""
import json
import sqlite3
import sys
from pathlib import Path

BLOCKS_PATH  = "d:/Personal Project/AWS StudyBot/evaluation/bundle_all/blocks.jsonl"
INDEX_PATH   = "d:/Personal Project/AWS StudyBot/evaluation/index/m3_index.db"
REPORT_PATH  = "d:/Personal Project/AWS StudyBot/idea/demo/context_loss_inspection.md"
DOC_ID       = "wiki_06_markdown_sample"
TARGET_CHUNK = "sha256:57d9ec5ae0af2744"

TARGET_BLOCK_IDS = {
    "wiki_06_markdown_sample_b_58d21ed73e8210ee76ad0b86600f151a",
    "wiki_06_markdown_sample_b_75c4ea1fd6d2e216eb1f05b89ecdd55f",
    "wiki_06_markdown_sample_b_c6672b8f15ea97c2ba1af94a4367b653",
}

# ── 1. Load all blocks for the wiki doc (sorted by block_index) ───────────────
wiki_blocks = []
with open(BLOCKS_PATH, encoding="utf-8") as f:
    for line in f:
        b = json.loads(line)
        if b.get("document_id") == DOC_ID:
            wiki_blocks.append(b)

wiki_blocks.sort(key=lambda b: b.get("block_index", 0))

# ── 2. Load all chunks whose source_block_ids touch target or neighbors ────────
with sqlite3.connect(INDEX_PATH) as conn:
    chunk_rows = conn.execute(
        "SELECT chunk_id, source_block_ids, text FROM embeddings"
    ).fetchall()

# Build: block_id → list of chunks that reference it
block_to_chunks = {}
for chunk_id, raw_sids, text in chunk_rows:
    for bid in json.loads(raw_sids):
        if bid.startswith(DOC_ID):
            block_to_chunks.setdefault(bid, []).append((chunk_id, text))

# Also pull target chunk directly
target_chunk_data = None
for chunk_id, raw_sids, text in chunk_rows:
    if chunk_id == TARGET_CHUNK:
        target_chunk_data = {"chunk_id": chunk_id, "source_block_ids": json.loads(raw_sids), "text": text}
        break

# ── 3. Find target blocks and their neighbors ─────────────────────────────────
target_indices = [i for i, b in enumerate(wiki_blocks) if b["block_id"] in TARGET_BLOCK_IDS]
if not target_indices:
    print("ERROR: Target blocks not found in blocks.jsonl for this doc_id.")
    sys.exit(1)

min_idx = max(0, min(target_indices) - 3)
max_idx = min(len(wiki_blocks) - 1, max(target_indices) + 3)
window  = wiki_blocks[min_idx:max_idx + 1]

# ── 4. Build report ────────────────────────────────────────────────────────────
import os
os.makedirs(os.path.dirname(REPORT_PATH), exist_ok=True)

lines = []
w = lines.append

w("# Context-Loss Inspection: wiki_06_markdown_sample")
w("")
w("> Hypothesis: target chunk lacks 'Amazon S3' entity anchor.")
w("> Test: block lineage + chunk text around target blocks.")
w("")

# Section 1: Block window
w("## 1. Block Lineage (±3 neighbors around target)")
w("")
w("| # | block_id (short) | block_type | locator | text | IS_TARGET | Has 'Amazon S3'? |")
w("|---:|---|---|---|---|:---:|:---:|")
for b in window:
    bid        = b["block_id"]
    bid_short  = bid.split("_b_")[-1][:12] + "..."
    btype      = b.get("block_type", "?")
    locator    = json.dumps(b.get("locator", {}), ensure_ascii=False)[:60]
    text       = b.get("text", "")
    text_short = repr(text[:80])
    is_target  = "YES" if bid in TARGET_BLOCK_IDS else ""
    has_s3     = "YES" if "Amazon S3" in text or "amazon s3" in text.lower() else "no"
    w(f"| {b.get('block_index','?')} | `{bid_short}` | {btype} | {locator} | {text_short} | {is_target} | {has_s3} |")
w("")

# Section 2: Target chunk full inspection
w("## 2. Target Chunk Full Text (sha256:57d9ec5ae0af2744)")
w("")
if target_chunk_data is None:
    w("> [!!!] TARGET CHUNK NOT FOUND IN INDEX — INGESTION FAILURE")
else:
    has_s3_in_chunk = "Amazon S3" in target_chunk_data["text"] or "amazon s3" in target_chunk_data["text"].lower()
    w(f"- chunk_id: `{target_chunk_data['chunk_id']}`")
    w(f"- source_block_ids: `{target_chunk_data['source_block_ids']}`")
    w(f"- Contains 'Amazon S3': **{'YES' if has_s3_in_chunk else 'NO'}**")
    w("")
    w("```")
    w(target_chunk_data["text"])
    w("```")
w("")

# Section 3: All chunks referencing target blocks
w("## 3. All Chunks Referencing Target Blocks")
w("")
seen_chunks = set()
for bid in sorted(TARGET_BLOCK_IDS):
    bid_short = bid.split("_b_")[-1][:16]
    w(f"### Block `{bid_short}...`")
    w("")
    chunks = block_to_chunks.get(bid, [])
    if not chunks:
        w("> No chunk references this block — block may not be indexed.")
    for chunk_id, text in chunks:
        if chunk_id not in seen_chunks:
            seen_chunks.add(chunk_id)
            has_s3 = "Amazon S3" in text or "amazon s3" in text.lower()
            w(f"- chunk_id: `{chunk_id}`  |  Contains 'Amazon S3': **{'YES' if has_s3 else 'NO'}**")
            w("```")
            w(text[:300])
            w("```")
    w("")

# Section 4: Verdict
w("## 4. Evidence Summary")
w("")

if target_chunk_data is None:
    w("- Target chunk NOT in index → **INGESTION FAILURE** — stop here.")
else:
    has_s3 = "Amazon S3" in target_chunk_data["text"] or "amazon s3" in target_chunk_data["text"].lower()
    if not has_s3:
        w("- Target chunk does NOT contain 'Amazon S3'.")
        w("- Entity anchor is missing from chunk representation.")
        w("")
        w("**Evidence supports hypothesis: CONTEXT-LOSS during chunking.**")
        w("")
        w("The chunk only contains the list items (`High durability`, etc.) without the")
        w("parent entity context (`Amazon S3`). Query asks about 'Amazon S3 core features'")
        w("but the chunk has no 'Amazon S3' signal → semantic alignment gap.")
        w("")
        w("**Next decision (not yet):** Investigate whether heading_context field in the")
        w("chunk schema captures this, or whether M2 chunker needs to prepend heading context.")
    else:
        w("- Target chunk DOES contain 'Amazon S3'.")
        w("- Context-loss hypothesis is NOT supported.")
        w("")
        w("**Redirect investigation to:** embedding representation, model behavior,")
        w("or distractor competition from other S3-related chunks.")

with open(REPORT_PATH, "w", encoding="utf-8") as f:
    f.write("\n".join(lines) + "\n")

print(f"Report written: {REPORT_PATH}")
