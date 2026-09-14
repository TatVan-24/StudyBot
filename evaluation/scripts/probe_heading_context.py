import sqlite3
import json

INDEX_PATH = "d:/Personal Project/AWS StudyBot/evaluation/index/m3_index.db"
CHUNK_ID = "sha256:57d9ec5ae0af2744"

def probe_heading_context():
    print("=" * 60)
    print(f"PROBE HEADING CONTEXT FOR: {CHUNK_ID}")
    print("=" * 60)

    with sqlite3.connect(INDEX_PATH) as conn:
        row = conn.execute("""
            SELECT document_id, text, source_block_ids, heading_context
            FROM embeddings
            WHERE chunk_id = ?
        """, (CHUNK_ID,)).fetchone()

    if not row:
        print("[!] Chunk not found in database.")
        return

    doc_id, text, source_block_ids, heading_context_raw = row
    
    print(f"document_id      : {doc_id}")
    print(f"source_block_ids : {source_block_ids}")
    print(f"text             :\n{text}")
    print("-" * 60)
    
    if heading_context_raw is None:
        print("heading_context  : NULL (Column exists but value is NULL)")
    else:
        try:
            heading_context = json.loads(heading_context_raw)
            print("heading_context  : (JSON Parsed)")
            print(json.dumps(heading_context, indent=2, ensure_ascii=False))
        except json.JSONDecodeError:
            print(f"heading_context  : (Raw String)\n{heading_context_raw}")

if __name__ == "__main__":
    probe_heading_context()
