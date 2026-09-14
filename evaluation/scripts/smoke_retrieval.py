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
        
        # --- MODEL DRIFT GUARD (Optimized Option B) ---
        # 1. Dimension Guard
        assert engine.dimension == meta.dimension, \
            f"Mismatched Dimensions! Index has {meta.dimension} but Model outputs {engine.dimension}"
            
        # 2. Normalized Name Guard
        def normalize_model_name(name: str) -> str:
            return name.strip("/").split("/")[-1].lower()
            
        assert normalize_model_name(meta.model_name) == normalize_model_name(engine.model_name), \
            f"Model Drift Detected! Index was built with '{meta.model_name}' but querying with '{engine.model_name}'"
    else:
        print("Warning: No index metadata found.")

    queries = [
        # Existing (TXT domain - txt_aiops_001)
        "Data Observability Pipeline có những thành phần nào?",
        "Feature Store dùng để làm gì trong ML?",
        # New (PDF domain - pdf_aws_001)
        "What are the core services of AWS cloud computing?",
        # New (MD domain - wiki_06_markdown_sample)
        "What is the main topic of the markdown sample document?",
    ]
    
    seen_documents = set()
    
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
            
            seen_documents.add(res.document_id)
            
    print(f"\nFound results from documents: {seen_documents}")
    assert len(seen_documents) >= 2, f"FAIL: Expected results from at least 2 distinct documents, but only saw {seen_documents}"
    print("PASS: Cross-document smoke retrieval successful!")

if __name__ == "__main__":
    run_smoke_retrieval()
