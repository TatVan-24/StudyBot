"""Vector store adapters. Pick via VECTOR_BACKEND env var.

Interface:
    ingest(doc_id, text, metadata=None) -> None
    search(query, top_k=5, filter=None) -> list[dict] (each has 'text', 'doc_id', 'score', 'metadata')
"""
import re
from collections import Counter
from typing import Optional


class BedrockKBVector:
    """Production: Bedrock Knowledge Base abstracts the vector store backend.

    Group still chooses the underlying vector store (OpenSearch Serverless, S3 Vectors,
    Aurora pgvector, Pinecone) when creating the KB in AWS console — that choice
    is invisible to this code.

    NOTE: KB ingestion is async via StartIngestionJob, normally triggered by S3 events.
    For simplicity, this adapter is search-only — ingestion happens through the
    Bedrock console or S3 → KB sync pipeline you set up separately.
    """

    def __init__(self, kb_id: str, region: str):
        import boto3
        if not kb_id:
            raise ValueError("VECTOR_BEDROCK_KB_ID must be set for Bedrock KB backend")
        self.kb_id = kb_id
        self.agent_runtime = boto3.client("bedrock-agent-runtime", region_name=region)

    def ingest(self, doc_id: str, text: str, metadata: Optional[dict] = None) -> None:
        # Ingestion is typically S3-event driven. Trigger a manual sync if needed
        # via StartIngestionJob — but the doc must already be in the KB's S3 source.
        # This adapter assumes upstream code uploaded to S3 already.
        pass

    def search(self, query: str, top_k: int = 5, filter: Optional[dict] = None) -> list:
        kwargs = {
            "knowledgeBaseId": self.kb_id,
            "retrievalQuery": {"text": query},
            "retrievalConfiguration": {
                "vectorSearchConfiguration": {"numberOfResults": top_k}
            },
        }
        if filter:
            kwargs["retrievalConfiguration"]["vectorSearchConfiguration"]["filter"] = {
                "andAll": [{"equals": {"key": k, "value": v}} for k, v in filter.items()]
            }
        resp = self.agent_runtime.retrieve(**kwargs)
        return [
            {
                "text": r.get("content", {}).get("text", ""),
                "doc_id": r.get("metadata", {}).get("doc_id", ""),
                "score": r.get("score", 0.0),
                "metadata": r.get("metadata", {}),
            }
            for r in resp.get("retrievalResults", [])
        ]


class LocalVector:
    """M6 Phase 1: Real RAG Ingestion & Retrieval Pipeline (Dense Only).
    
    Replaces dummy keyword matching with actual MPNet + SQLiteVectorStore
    using our custom Parser and Chunker from M1-M4.
    """

    def __init__(self):
        import os
        import time
        print("[M6] Initializing LocalVector (Integration Skeleton)...")
        start_time = time.time()
        
        from sentence_transformers import SentenceTransformer
        self.model = SentenceTransformer('sentence-transformers/paraphrase-multilingual-mpnet-base-v2')
        
        # Load Vector Store — isolated to m6_index.db (NEVER touch m3_index.db)
        from indexer.vector_store import SQLiteVectorStore
        os.makedirs("_data", exist_ok=True)
        self.vector_store = SQLiteVectorStore(db_path="_data/m6_index.db")
        
        # StructureAwareChunker inherits BaseChunker.__init__(tokenizer=None)
        # max_tokens is NOT a constructor arg — it is passed via config dict at .chunk() call time
        from chunker.chunker import StructureAwareChunker
        self.chunker = StructureAwareChunker()
        
        elapsed = time.time() - start_time
        print(f"[M6] LocalVector initialized in {elapsed:.2f} seconds.")

    def ingest(self, doc_id: str, text: str, metadata: Optional[dict] = None) -> None:
        print(f"[M6] Ingesting document: {doc_id}")
        
        # 1. Parse raw text into blocks using M1 TXT Parser
        from parser.text.txt_parser import build_blocks, to_parsed_blocks
        
        lines = []
        for line_number, raw_line in enumerate(text.splitlines(), start=1):
            lines.append({"line_number": line_number, "text": raw_line})
            
        raw_blocks = build_blocks(lines)
        parsed_blocks = to_parsed_blocks(raw_blocks, doc_id)
        
        if not parsed_blocks:
            print("[M6] Warning: Parser produced no blocks.")
            return

        # 2. Chunk using M2 StructureAwareChunker
        # max_tokens is a config dict key, NOT a constructor argument
        chunk_config = {"max_tokens": 512, "parse_job_id": ""}
        bundle = self.chunker.chunk(parsed_blocks, doc_id, "txt", chunk_config)
        
        if not bundle.chunks:
            print("[M6] Warning: No chunks produced.")
            return

        # 3. Convert ChunkBundle (list of Chunk dataclass) → list[dict] for SQLiteVectorStore
        chunks_as_dicts = []
        for c in bundle.chunks:
            chunks_as_dicts.append({
                "chunk_id": c.chunk_id,
                "chunk_index": c.chunk_index,
                "document_id": c.document_id,
                "text": c.text,
                "source_block_ids": c.source_block_ids,
                "heading_context": c.heading_context,
                "token_count": c.token_count,
            })
        
        # 4. Embed chunks with MPNet
        import numpy as np
        texts_to_embed = [c["text"] for c in chunks_as_dicts]
        vectors_np = np.array(
            self.model.encode(texts_to_embed, normalize_embeddings=True),
            dtype=np.float32
        )
        
        # 5. Persist to m6_index.db (NEVER overwrites m3_index.db)
        from indexer.schema import IndexMeta
        from datetime import datetime, timezone
        
        meta = IndexMeta(
            model_name="paraphrase-multilingual-mpnet-base-v2",
            revision="main",
            dimension=768,
            max_seq_length=512,
            normalization="L2",
            index_version="v1.0",
            created_at=datetime.now(timezone.utc).isoformat()
        )
        self.vector_store.upsert_index(meta, chunks_as_dicts, vectors_np)
        print(f"[M6] Ingested {len(chunks_as_dicts)} chunks into m6_index.db")

    def search(self, query: str, top_k: int = 5, filter: Optional[dict] = None) -> list:
        # 1. Embed query with same MPNet model
        query_vector = self.model.encode([query], normalize_embeddings=True)[0]
        
        # 2. Dense cosine search in SQLite
        search_results = self.vector_store.search(query_vector, top_k=top_k)
        
        # 3. Format → API output contract: list[{text, doc_id, score, metadata}]
        results = []
        for r in search_results:
            results.append({
                "text": r.text,
                "doc_id": r.document_id,
                "score": r.score,
                "metadata": {
                    "chunk_id": r.chunk_id,
                    "chunk_index": r.chunk_index,
                    "source_block_ids": r.source_block_ids,
                    "heading_context": r.heading_context,
                    "token_count": r.token_count
                }
            })
            
        return results
