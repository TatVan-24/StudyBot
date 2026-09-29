"""
m6_step2_merge_diagnostic.py
============================
Injects a "gold_match" (1 or 0) diagnostic field into the M6 dev set,
without modifying the "ground_truth_label" (which is left for human annotation).

Reads: evaluation/datasets/m6_dev_sufficiency_ground_truth.jsonl
       evaluation/datasets/test-v3.jsonl
       evaluation/bundle_all/blocks.jsonl
       evaluation/index/m3_index.db
Writes (In-Place): evaluation/datasets/m6_dev_sufficiency_ground_truth.jsonl
"""

import copy
import json
import os
import sqlite3

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
DB_PATH = os.path.join(ROOT, "index", "m3_index.db")
BLOCKS_PATH = os.path.join(ROOT, "bundle_all", "blocks.jsonl")
DEV_DATASET_PATH = os.path.join(ROOT, "datasets", "test-v3.jsonl")
GROUND_TRUTH_PATH = os.path.join(ROOT, "datasets", "m6_dev_sufficiency_ground_truth.jsonl")


def match_locator(gt_locator: dict, block: dict) -> bool:
    block_locator = block.get("locator", {})
    gt_type = gt_locator.get("type")
    bl_type = block_locator.get("type")

    if gt_type in ("markdown", "text_span", "txt", "text") and bl_type in ("markdown", "text_span", "text", "txt"):
        gs, ge = gt_locator.get("start_line"), gt_locator.get("end_line")
        bs, be = block_locator.get("start_line"), block_locator.get("end_line")
        if None not in (gs, ge, bs, be):
            return max(gs, bs) <= min(ge, be)

    if gt_type in ("page", "pdf") and bl_type == "pdf":
        gt_page = gt_locator.get("pdf_page")
        if gt_page is None:
            locs = gt_locator.get("locations", [])
            if locs:
                gt_page = locs[0].get("pdf_page")
        for loc in block_locator.get("locations", []):
            if loc.get("pdf_page") == gt_page:
                return True

    return False


def main():
    # 1. Load test-v3.jsonl to get evidence for each query
    v3_cases = {}
    with open(DEV_DATASET_PATH, encoding="utf-8") as f:
        for line in f:
            if line.strip():
                c = json.loads(line)
                v3_cases[c["case_id"]] = c

    # 2. Load blocks.jsonl
    blocks_by_doc = {}
    with open(BLOCKS_PATH, encoding="utf-8") as f:
        for line in f:
            if line.strip():
                b = json.loads(line)
                blocks_by_doc.setdefault(b.get("document_id"), []).append(b)

    # 3. Load chunk_id -> source_block_ids mapping
    conn = sqlite3.connect(DB_PATH)
    rows = conn.execute("SELECT chunk_id, source_block_ids FROM embeddings").fetchall()
    conn.close()
    
    chunk_to_blocks = {}
    for chunk_id, src_raw in rows:
        chunk_to_blocks[chunk_id] = set(json.loads(src_raw)) if src_raw else set()

    # 4. Process the ground truth file
    records = []
    with open(GROUND_TRUTH_PATH, encoding="utf-8") as f:
        for line in f:
            if line.strip():
                records.append(json.loads(line))

    if len(records) != 35:
        print(f"[ERROR] Expected 35 records, found {len(records)}.")
        return

    out_records = []
    
    # Evaluate each record
    for rec in records:
        # Invariant check: Create a deep copy to ensure we don't mutate anything except adding gold_match
        new_rec = copy.deepcopy(rec)
        
        qid = new_rec["query_id"]
        v3_case = v3_cases.get(qid)
        
        if not v3_case:
            new_rec["gold_match"] = 0
        else:
            # Get target blocks for this query
            target_blocks = set()
            for ev in v3_case.get("evidence", []):
                for blk in blocks_by_doc.get(ev["document_id"], []):
                    if match_locator(ev["locator"], blk):
                        target_blocks.add(blk["block_id"])

            # Check if any retrieved chunk contains any target block
            is_match = False
            for chunk in new_rec.get("retrieved_context", []):
                cid = chunk["chunk_id"]
                if chunk_to_blocks.get(cid, set()).intersection(target_blocks):
                    is_match = True
                    break
            
            new_rec["gold_match"] = 1 if is_match else 0
            
        out_records.append(new_rec)

    # Verifications before writing
    assert len(out_records) == 35, "Record count changed!"
    qids = set(r["query_id"] for r in out_records)
    assert len(qids) == 35, "query_id is not unique!"
    
    for old, new in zip(records, out_records):
        assert old["query_id"] == new["query_id"], "query_id order changed!"
        assert old["query"] == new["query"], "query changed!"
        assert old["retrieved_context"] == new["retrieved_context"], "retrieved_context changed!"
        assert old["signals"] == new["signals"], "signals changed!"
        assert old["ground_truth_label"] is None, "ground_truth_label is not null in original!"
        assert new["ground_truth_label"] is None, "ground_truth_label changed from null!"
        assert "gold_match" in new, "gold_match field is missing!"
        assert new["gold_match"] in (0, 1), f"gold_match invalid value: {new['gold_match']}"

    # Write back in-place
    with open(GROUND_TRUTH_PATH, "w", encoding="utf-8") as f:
        for r in out_records:
            f.write(json.dumps(r, ensure_ascii=False) + "\n")
            
    print(f"[DONE] Injected 'gold_match' diagnostic into {len(out_records)} records.")
    print("[VERIFIED] Invariants maintained: 35 records, unique query_ids, no data mutated, ground_truth_label remains null.")


if __name__ == "__main__":
    main()
