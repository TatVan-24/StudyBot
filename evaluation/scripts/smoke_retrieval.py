import os
import sys
from pathlib import Path
sys.path.append(str(Path(__file__).resolve().parent.parent.parent))

import json
from src.indexer.embedding import EmbeddingEngine
from src.indexer.vector_store import SQLiteVectorStore

def run_smoke_retrieval():
    db_path = Path("evaluation/index/m3_index.db")
    if not db_path.exists():
        print(f"Index not found at {db_path}. Run run_m3_indexing.py first.")
        return
        
    print("Loading Embedding Engine...")
    engine = EmbeddingEngine()
    
    print("Connecting to Vector Store...")
    store = SQLiteVectorStore(str(db_path))
    
    meta = store.load_meta()
    if meta:
        print(f"Loaded Index Meta: Model={meta.model_name}, Dimension={meta.dimension}")
    else:
        print("Warning: No index metadata found.")

    queries = [
        "Data Observability Pipeline có những thành phần nào?",
        "Feature Store dùng để làm gì trong ML?"
    ]
    
    for i, q in enumerate(queries):
        print(f"\n--- Query {i+1}: '{q}' ---")
        
        # Encode query (must be exactly the same process as chunks)
        # engine.encode() returns L2 normalized vectors
        q_vector = engine.encode([q])[0]
        
        top_k = 3
        results = store.search(q_vector, top_k=top_k)
        
        assert len(results) == top_k, f"FAIL: Expected {top_k} results, got {len(results)}"
        
        print(f"Top {len(results)} Results:")
        for rank, res in enumerate(results, 1):
            assert -1.0001 <= res.score <= 1.0001, f"FAIL: Score {res.score} out of bounds"
            
            # Print minimal info
            print(f"  [{rank}] Score: {res.score:.4f} | Chunk ID: {res.chunk_id}")
            print(f"       Trace: document={res.document_id}, block_ids={len(res.source_block_ids)}")
            print(f"       Text: {res.text[:100]}...")

if __name__ == "__main__":
    run_smoke_retrieval()
