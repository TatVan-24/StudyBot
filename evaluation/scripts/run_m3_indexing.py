import os
import sys
from pathlib import Path
sys.path.append(str(Path(__file__).resolve().parent.parent.parent))

import json
import datetime
import numpy as np
from src.indexer.embedding import EmbeddingEngine
from src.indexer.vector_store import SQLiteVectorStore
from src.indexer.schema import IndexMeta

def run_indexing():
    input_file = Path("evaluation/runs/m2-final/chunks_structure.jsonl")
    blocks_file = Path("evaluation/bundle_all/blocks.jsonl")
    
    db_dir = Path("evaluation/index")
    db_dir.mkdir(parents=True, exist_ok=True)
    db_path = db_dir / "m3_index.db"
    manifest_path = db_dir / "m3_manifest.json"
    
    # 1. Load chunks & blocks
    chunks = []
    with open(input_file, "r", encoding="utf-8") as f:
        for line in f:
            if line.strip():
                chunks.append(json.loads(line))
                
    valid_block_ids = set()
    with open(blocks_file, "r", encoding="utf-8") as f:
        for line in f:
            if line.strip():
                b = json.loads(line)
                valid_block_ids.add(b["block_id"])
                
    print(f"Loaded {len(chunks)} chunks and {len(valid_block_ids)} source blocks.")
    
    # 2. Init Engine
    print("Initializing Embedding Engine...")
    engine = EmbeddingEngine()
    
    print(f"Model={engine.model_name} dim={engine.dimension} max_seq={engine.max_seq_length}")
    
    # Check max_seq_length logic (sanity check against readme brochure)
    if engine.max_seq_length > 512:
        print("FAIL: max_seq_length exceeds expected 512, might cause unexpected OOM or silent truncation.")
        sys.exit(1)
        
    print("Initializing Vector Store...")
    if db_path.exists():
        db_path.unlink()
    store = SQLiteVectorStore(str(db_path))
    
    # 3. Fail-fast verification test
    print("Testing fail-fast mechanism (Expected to fail)...")
    long_text = "test word " * 1000
    try:
        engine.encode([long_text])
        print("FAIL: Engine did not fail-fast on long text!")
        sys.exit(1)
    except ValueError as e:
        print(f"PASS: Fail-fast activated correctly: {e}")

    # 4. Encode and store
    print("Encoding chunks...")
    texts = [c["text"] for c in chunks]
    vectors = engine.encode(texts)
    
    norms = np.linalg.norm(vectors, axis=1)
    if not np.allclose(norms, 1.0, atol=1e-5):
        print("FAIL: Vectors are not L2 normalized!")
        sys.exit(1)
    else:
        print("PASS: Vectors are strictly L2 normalized.")
        
    print("Storing chunks in SQLite...")
    meta = IndexMeta(
        model_name=engine.model_name,
        revision=engine.revision,
        dimension=engine.dimension,
        max_seq_length=engine.max_seq_length,
        normalization="L2",
        index_version="1.0",
        created_at=os.environ.get("M3_EXECUTION_TIME", datetime.datetime.now(datetime.timezone.utc).isoformat())
    )
    
    store.upsert_index(meta, chunks, vectors)
    
    # Export Manifest
    with open(manifest_path, "w", encoding="utf-8") as f:
        f.write(meta.model_dump_json(indent=2))
    
    # 5. Verification Checklist
    print("\n--- Verification Checklist ---")
    
    # Dimension
    if engine.dimension == meta.dimension:
        print(f"PASS: Dimension == {engine.dimension}")
    else:
        print(f"FAIL: Dimension == {engine.dimension} (Expected {meta.dimension})")
        sys.exit(1)
        
    # Count Invariants & Set equality
    import sqlite3
    with sqlite3.connect(db_path) as conn:
        cursor = conn.execute("SELECT chunk_id FROM embeddings")
        db_rows = cursor.fetchall()
        db_ids = set([r[0] for r in db_rows])
        
    chunk_ids = set([c["chunk_id"] for c in chunks])
    
    if len(db_ids) == len(chunk_ids) == 1972 and db_ids == chunk_ids:
        print(f"PASS: index_count == chunk_count == 1972, and chunk_ids match exactly.")
    else:
        print(f"FAIL: index_count={len(db_ids)}, chunk_count={len(chunk_ids)}. DB ids match: {db_ids == chunk_ids}")
        sys.exit(1)
        
    # Traceability check
    all_traceable = True
    for c in chunks:
        if not all(bid in valid_block_ids for bid in c["source_block_ids"]):
            all_traceable = False
            break
            
    if all_traceable:
        print("PASS: All source_block_ids are fully traceable to blocks.jsonl.")
    else:
        print("FAIL: Some source_block_ids cannot be found in blocks.jsonl!")
        sys.exit(1)
        
    # Determinism / Rebuild Diff Check
    print("Running determinism check...")
    vectors_rebuild = engine.encode(texts)
    diff = np.abs(vectors - vectors_rebuild).max()
    if diff < 1e-6:
        print(f"PASS: Rebuild determinism verified. Max diff: {diff:.8e}")
    else:
        print(f"FAIL: Rebuild yielded different vectors! Max diff: {diff:.8e}")
        sys.exit(1)

if __name__ == "__main__":
    run_indexing()

