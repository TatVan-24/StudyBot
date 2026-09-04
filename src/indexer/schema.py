from typing import List, Optional, Any
from pydantic import BaseModel, Field

class IndexMeta(BaseModel):
    model_name: str
    revision: str
    dimension: int
    max_seq_length: int
    normalization: str
    index_version: str
    created_at: str

class SearchResult(BaseModel):
    chunk_id: str
    chunk_index: int
    score: float
    document_id: str
    text: str
    source_block_ids: List[str]
    heading_context: List[str]
    token_count: int
