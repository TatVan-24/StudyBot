from typing import List, Dict, Any, Optional
from dataclasses import dataclass, field
from enum import Enum
import hashlib
import json

class ChunkerStrategy(str, Enum):
    FIXED = "fixed"
    RECURSIVE = "recursive"
    SEMANTIC = "semantic"
    STRUCTURE_AWARE = "structure"
    TOKEN_AWARE = "token_aware"


@dataclass
class Chunk:
    schema_version: str = "1.0"
    chunk_id: str = ""
    document_id: str = ""
    chunk_index: int = 0

    text: str = ""
    char_count: int = 0
    token_count: int = 0

    source_type: str = ""
    source_block_ids: List[str] = field(default_factory=list)
    page_numbers: List[int] = field(default_factory=list)

    heading_context: List[str] = field(default_factory=list)
    block_types: List[str] = field(default_factory=list)

    chunker_strategy: ChunkerStrategy = ChunkerStrategy.FIXED
    chunker_config: Dict[str, Any] = field(default_factory=dict)

    def generate_chunk_id(self) -> str:
        """I1: Deterministic identity - hash(document_id, chunk_index, text)"""
        content = f"{self.document_id}:{self.chunk_index}:{self.text}"
        return f"sha256:{hashlib.sha256(content.encode()).hexdigest()[:16]}"

    def to_json(self) -> str:
        return json.dumps({
            "schema_version": self.schema_version,
            "chunk_id": self.chunk_id,
            "document_id": self.document_id,
            "chunk_index": self.chunk_index,
            "text": self.text,
            "char_count": self.char_count,
            "token_count": self.token_count,
            "source_type": self.source_type,
            "source_block_ids": self.source_block_ids,
            "page_numbers": self.page_numbers,
            "heading_context": self.heading_context,
            "block_types": self.block_types,
            "chunker_strategy": self.chunker_strategy.value,
            "chunker_config": self.chunker_config
        })


class ChunkBundle:
    """Output structure for chunks.jsonl"""
    def __init__(self, document_id: str, parse_job_id: str):
        self.document_id = document_id
        self.parse_job_id = parse_job_id
        self.chunks: List[Chunk] = []

    def add_chunk(self, chunk: Chunk) -> None:
        self.chunks.append(chunk)

    def to_jsonl(self) -> str:
        return "\n".join(chunk.to_json() for chunk in self.chunks)


class ChunkValidator:
    """Validation logic for chunk invariants"""
    @staticmethod
    def validate_invariants(chunk: Chunk, block_ids_in_blocks_jsonl: set) -> List[str]:
        errors = []
        
        # I2: Strict lineage - source_block_ids non-empty
        if not chunk.source_block_ids:
            errors.append("I2 Violation: source_block_ids cannot be empty")
        
        # I2: Each source_block_id must exist in blocks.jsonl
        for block_id in chunk.source_block_ids:
            if block_id not in block_ids_in_blocks_jsonl:
                errors.append(f"I2 Violation: source_block_id '{block_id}' not found in blocks.jsonl")
        
        # I4: Token count must be > 0
        if chunk.token_count <= 0:
            errors.append("I4 Violation: token_count must be > 0")
        
        # I5: chunk_index must be 1-based
        if chunk.chunk_index < 1:
            errors.append("I5 Violation: chunk_index must be >= 1")
        
        return errors