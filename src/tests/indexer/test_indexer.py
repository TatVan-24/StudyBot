import pytest
import numpy as np
import os
import sqlite3
from typing import List
from src.indexer.schema import IndexMeta, SearchResult
from src.indexer.embedding import EmbeddingEngine
from src.indexer.vector_store import SQLiteVectorStore

def test_index_meta_schema():
    meta = IndexMeta(
        model_name="test-model",
        revision="abc1234",
        dimension=128,
        max_seq_length=256,
        normalization="L2",
        index_version="1.0",
        created_at="2026-09-02T00:00:00Z"
    )
    assert meta.model_name == "test-model"
    assert meta.dimension == 128

def test_sqlite_vector_store_workflow(tmp_path):
    db_path = str(tmp_path / "test_index.db")
    store = SQLiteVectorStore(db_path)
    
    meta = IndexMeta(
        model_name="test-model",
        revision="abc1234",
        dimension=4,
        max_seq_length=256,
        normalization="L2",
        index_version="1.0",
        created_at="2026-09-02T00:00:00Z"
    )
    
    chunks = [
        {"chunk_id": "c1", "chunk_index": 1, "document_id": "doc1", "text": "hello world", "source_block_ids": ["b1"], "heading_context": ["h1"], "token_count": 2},
        {"chunk_id": "c2", "chunk_index": 2, "document_id": "doc2", "text": "test document", "source_block_ids": ["b2"], "heading_context": ["h2"], "token_count": 2}
    ]
    
    # Fake vectors
    v1 = np.array([1.0, 0.0, 0.0, 0.0], dtype=np.float32)
    v2 = np.array([0.0, 1.0, 0.0, 0.0], dtype=np.float32)
    vectors = np.vstack([v1, v2])
    
    # 1. Upsert
    store.upsert_index(meta, chunks, vectors)
    
    # 2. Check Meta
    loaded_meta = store.load_meta()
    assert loaded_meta is not None
    assert loaded_meta.model_name == "test-model"
    assert loaded_meta.dimension == 4
    
    # 3. Check Count Atomicity
    with sqlite3.connect(db_path) as conn:
        cursor = conn.execute("SELECT COUNT(*) FROM embeddings")
        assert cursor.fetchone()[0] == 2
        
    # 4. Search
    query = np.array([1.0, 0.0, 0.0, 0.0], dtype=np.float32)
    results = store.search(query, top_k=1)
    
    assert len(results) == 1
    assert results[0].chunk_id == "c1"
    assert results[0].score == 1.0
    
    # 5. Search with scoping (filter)
    query2 = np.array([0.0, 1.0, 0.0, 0.0], dtype=np.float32)
    results_scoped = store.search(query2, top_k=2, filter_dict={"document_id": "doc2"})
    assert len(results_scoped) == 1
    assert results_scoped[0].chunk_id == "c2"

def test_sqlite_vector_store_search_validation(tmp_path):
    db_path = str(tmp_path / "test_val.db")
    store = SQLiteVectorStore(db_path)
    meta = IndexMeta(model_name="m", revision="r", dimension=4, max_seq_length=2, normalization="L2", index_version="1", created_at="")
    store.upsert_index(meta, [], np.array([]))
    
    # Query with wrong dimension
    with pytest.raises(AssertionError):
        store.search(np.array([1.0, 0.0]), top_k=1)

# Note: We do not extensively test EmbeddingEngine with network requests here to avoid 
# CI issues. Real tests on embedding engine are covered in run_m3_indexing.py tests 
# or can be mocked.
