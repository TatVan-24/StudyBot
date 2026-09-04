import sqlite3
import json
import numpy as np
from typing import List, Dict, Any, Optional
from .schema import IndexMeta, SearchResult

class SQLiteVectorStore:
    def __init__(self, db_path: str):
        self.db_path = db_path
        self._init_db()
        
    def _init_db(self):
        with sqlite3.connect(self.db_path) as conn:
            conn.execute("""
                CREATE TABLE IF NOT EXISTS index_meta (
                    model_name TEXT,
                    revision TEXT,
                    dimension INTEGER,
                    max_seq_length INTEGER,
                    normalization TEXT,
                    index_version TEXT,
                    created_at TEXT
                )
            """)
            conn.execute("""
                CREATE TABLE IF NOT EXISTS embeddings (
                    chunk_id TEXT PRIMARY KEY,
                    chunk_index INTEGER,
                    document_id TEXT,
                    text TEXT,
                    source_block_ids TEXT,
                    heading_context TEXT,
                    token_count INTEGER,
                    vector BLOB
                )
            """)
            
    def upsert_index(self, meta: IndexMeta, chunks: List[Dict[str, Any]], vectors: np.ndarray):
        with sqlite3.connect(self.db_path) as conn:
            cursor = conn.cursor()
            
            # Save meta
            cursor.execute("DELETE FROM index_meta")
            cursor.execute("""
                INSERT INTO index_meta 
                (model_name, revision, dimension, max_seq_length, normalization, index_version, created_at)
                VALUES (?, ?, ?, ?, ?, ?, ?)
            """, (meta.model_name, meta.revision, meta.dimension, meta.max_seq_length, meta.normalization, meta.index_version, meta.created_at))
            
            # Upsert embeddings
            for chunk, vector in zip(chunks, vectors):
                cursor.execute("""
                    INSERT OR REPLACE INTO embeddings 
                    (chunk_id, chunk_index, document_id, text, source_block_ids, heading_context, token_count, vector)
                    VALUES (?, ?, ?, ?, ?, ?, ?, ?)
                """, (
                    chunk['chunk_id'],
                    chunk.get('chunk_index', 0),
                    chunk['document_id'],
                    chunk['text'],
                    json.dumps(chunk.get('source_block_ids', [])),
                    json.dumps(chunk.get('heading_context', [])),
                    chunk.get('token_count', 0),
                    vector.astype(np.float32).tobytes()
                ))
            
    def load_meta(self) -> Optional[IndexMeta]:
        with sqlite3.connect(self.db_path) as conn:
            cursor = conn.execute("SELECT model_name, revision, dimension, max_seq_length, normalization, index_version, created_at FROM index_meta LIMIT 1")
            row = cursor.fetchone()
            if row:
                return IndexMeta(
                    model_name=row[0],
                    revision=row[1],
                    dimension=row[2],
                    max_seq_length=row[3],
                    normalization=row[4],
                    index_version=row[5],
                    created_at=row[6]
                )
            return None

    def search(self, query_vector: np.ndarray, top_k: int = 5, filter_dict: Optional[Dict[str, Any]] = None) -> List[SearchResult]:
        # query_vector must be L2 normalized and have shape (dimension,)
        meta = self.load_meta()
        if meta is None:
            return []
            
        assert query_vector.shape[0] == meta.dimension, f"Query dimension mismatch: {query_vector.shape[0]} != {meta.dimension}"
        
        with sqlite3.connect(self.db_path) as conn:
            query = "SELECT chunk_id, chunk_index, document_id, text, source_block_ids, heading_context, token_count, vector FROM embeddings"
            params = []
            
            if filter_dict:
                conditions = []
                for k, v in filter_dict.items():
                    conditions.append(f"{k} = ?")
                    params.append(v)
                query += " WHERE " + " AND ".join(conditions)
                
            cursor = conn.execute(query, params)
            rows = cursor.fetchall()
            
            if not rows:
                return []
                
            chunk_ids = []
            vectors = []
            metadata_map = {}
            for row in rows:
                chunk_id = row[0]
                chunk_index = row[1]
                chunk_ids.append(chunk_id)
                vector = np.frombuffer(row[7], dtype=np.float32)
                vectors.append(vector)
                
                metadata_map[chunk_id] = {
                    "chunk_index": chunk_index,
                    "document_id": row[2],
                    "text": row[3],
                    "source_block_ids": json.loads(row[4]),
                    "heading_context": json.loads(row[5]),
                    "token_count": row[6]
                }
                
            vectors_np = np.vstack(vectors)
            # Dot product search (equals cosine similarity since vectors are L2 normalized)
            scores = np.dot(vectors_np, query_vector)
            
            top_k = min(top_k, len(scores))
            top_indices = np.argsort(scores)[::-1][:top_k]
            
            results = []
            for idx in top_indices:
                chunk_id = chunk_ids[idx]
                score = float(scores[idx])
                
                # Validating range
                assert -1.0001 <= score <= 1.0001, f"Score {score} outside expected cosine similarity range"
                
                res_meta = metadata_map[chunk_id]
                results.append(SearchResult(
                    chunk_id=chunk_id,
                    chunk_index=res_meta["chunk_index"],
                    score=score,
                    document_id=res_meta["document_id"],
                    text=res_meta["text"],
                    source_block_ids=res_meta["source_block_ids"],
                    heading_context=res_meta["heading_context"],
                    token_count=res_meta["token_count"]
                ))
                
            return results
