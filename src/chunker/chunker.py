"""Sample chunker implementations"""
from typing import List, Callable, Optional
import hashlib
import json

# tiktoken optional - imported lazily
_tiktoken_available = False
try:
    import tiktoken
    _tiktoken_available = True
except ImportError:
    pass


class ChunkerStrategy:
    FIXED = "fixed"
    RECURSIVE = "recursive"
    SEMANTIC = "semantic"
    STRUCTURE_AWARE = "structure"
    TOKEN_AWARE = "token_aware"


class Chunk:
    """Chunk dataclass - matches schema.py"""
    def __init__(
        self,
        schema_version: str = "1.0",
        chunk_id: str = "",
        document_id: str = "",
        chunk_index: int = 0,
        text: str = "",
        char_count: int = 0,
        token_count: int = 0,
        source_type: str = "",
        source_block_ids: Optional[List[str]] = None,
        page_numbers: Optional[List[int]] = None,
        heading_context: Optional[List[str]] = None,
        block_types: Optional[List[str]] = None,
        chunker_strategy: str = "fixed",
        chunker_config: Optional[dict] = None
    ):
        self.schema_version = schema_version
        self.chunk_id = chunk_id
        self.document_id = document_id
        self.chunk_index = chunk_index
        self.text = text
        self.char_count = char_count
        self.token_count = token_count
        self.source_type = source_type
        self.source_block_ids = source_block_ids or []
        self.page_numbers = page_numbers or []
        self.heading_context = heading_context or []
        self.block_types = block_types or []
        self.chunker_strategy = chunker_strategy
        self.chunker_config = chunker_config or {}

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
            "chunker_strategy": self.chunker_strategy,
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


class BaseChunker:
    """Base chunker abstract class"""
    def __init__(self, tokenizer: Optional[Callable[[str], List[int]]] = None):
        self.tokenizer = tokenizer or self._default_tokenizer()
    
    def _default_tokenizer(self) -> Callable[[str], List[int]]:
        """I4: Token-aware sizing - use tiktoken if available"""
        if _tiktoken_available:
            enc = tiktoken.get_encoding("cl100k_base")
            return enc
        return lambda text: text.split()

    def chunk(self, blocks: List[dict], document_id: str, source_type: str, config: dict) -> ChunkBundle:
        raise NotImplementedError


class FixedSizeChunker(BaseChunker):
    """Fixed-size chunking by token count"""
    
    def chunk(self, blocks: List[dict], document_id: str, source_type: str, config: dict) -> ChunkBundle:
        window_size = config.get("window_size", 512)
        overlap_ratio = config.get("overlap_ratio", 0.1)
        
        bundle = ChunkBundle(document_id, config.get("parse_job_id", ""))
        
        all_text = []
        all_block_ids = []
        all_heading_contexts = []
        all_block_types = []
        all_page_numbers = []
        
        for block in blocks:
            all_text.append(block.get("text", ""))
            all_block_ids.append(block.get("block_id", ""))
            heading_path = block.get("heading_path", [])
            heading_texts = [h.get("text", "") for h in heading_path]
            all_heading_contexts.append(heading_texts)
            all_block_types.append(block.get("block_type", ""))
            locator = block.get("locator", {})
            if locator.get("type") == "pdf":
                locations = locator.get("locations", [])
                pages = [loc.get("pdf_page", 0) for loc in locations if loc.get("pdf_page")]
                all_page_numbers.append(pages)
            else:
                all_page_numbers.append([])
        
        full_text = "\n\n".join(all_text)
        tokens = self.tokenizer.encode(full_text)
        
        window_tokens = window_size
        overlap_tokens = int(window_tokens * overlap_ratio)
        
        chunk_index = 1
        for i in range(0, len(tokens), window_tokens - overlap_tokens):
            token_chunk = tokens[i:i + window_tokens]
            text_chunk = self.tokenizer.decode(token_chunk)
            
            included_block_ids = []
            included_headings = []
            included_types = set()
            included_pages = set()
            
            cum_tokens = 0
            for j, block_text in enumerate(all_text):
                block_tokens = self.tokenizer.encode(block_text)
                if cum_tokens <= i + window_tokens and cum_tokens + len(block_tokens) > i:
                    if all_block_ids[j]:
                        included_block_ids.append(all_block_ids[j])
                    if all_heading_contexts[j]:
                        included_headings = all_heading_contexts[j]
                    included_types.add(all_block_types[j])
                    included_pages.update(all_page_numbers[j])
                cum_tokens += len(block_tokens) + 2
            
            chunk = Chunk(
                schema_version="1.0",
                document_id=document_id,
                chunk_index=chunk_index,
                text=text_chunk,
                char_count=len(text_chunk),
                token_count=len(token_chunk),
                source_type=source_type,
                source_block_ids=included_block_ids,
                page_numbers=sorted(list(included_pages)) if included_pages else [],
                heading_context=included_headings,
                block_types=sorted(list(included_types)),
                chunker_strategy=ChunkerStrategy.FIXED,
                chunker_config=config
            )
            chunk.chunk_id = chunk.generate_chunk_id()
            
            bundle.add_chunk(chunk)
            chunk_index += 1
            
            if i + window_tokens >= len(tokens):
                break
        
        return bundle


class StructureAwareChunker(BaseChunker):
    """Structure-aware chunking - split by headings"""
    
    def chunk(self, blocks: List[dict], document_id: str, source_type: str, config: dict) -> ChunkBundle:
        max_tokens = config.get("max_tokens", 512)
        
        bundle = ChunkBundle(document_id, config.get("parse_job_id", ""))
        
        current_chunk_text = []
        current_block_ids = []
        current_heading_context = []
        current_types = set()
        current_pages = set()
        chunk_index = 1
        
        for block in blocks:
            text = block.get("text", "")
            block_id = block.get("block_id", "")
            block_type = block.get("block_type", "")
            heading_path = block.get("heading_path", [])
            
            if block_type == "heading" and current_chunk_text:
                chunk = self._create_chunk(
                    bundle, current_chunk_text, current_block_ids, 
                    current_heading_context, current_types, current_pages,
                    document_id, source_type, config, chunk_index
                )
                chunk_index += 1
                current_chunk_text = []
                current_block_ids = []
                current_types = set()
                current_pages = set()
            
            if heading_path:
                current_heading_context = [h.get("text", "") for h in heading_path]
            
            test_text = " ".join(current_chunk_text + [text])
            if self.tokenizer.encode(test_text) and len(self.tokenizer.encode(test_text)) > max_tokens and current_chunk_text:
                chunk = self._create_chunk(
                    bundle, current_chunk_text, current_block_ids,
                    current_heading_context, current_types, current_pages,
                    document_id, source_type, config, chunk_index
                )
                chunk_index += 1
                current_chunk_text = []
                current_block_ids = []
                current_types = set()
                current_pages = []
            
            current_chunk_text.append(text)
            if block_id:
                current_block_ids.append(block_id)
            current_types.add(block_type)
            
            locator = block.get("locator", {})
            if locator.get("type") == "pdf":
                for loc in locator.get("locations", []):
                    if loc.get("pdf_page"):
                        current_pages.add(loc["pdf_page"])
        
        if current_chunk_text:
            chunk = self._create_chunk(
                bundle, current_chunk_text, current_block_ids,
                current_heading_context, current_types, current_pages,
                document_id, source_type, config, chunk_index
            )
        
        return bundle
    
    def _create_chunk(self, bundle: ChunkBundle, texts: List[str], block_ids: List[str],
                      heading_context: List[str], block_types: set, page_numbers: set,
                      document_id: str, source_type: str, config: dict, chunk_index: int) -> Chunk:
        text = "\n\n".join(texts)
        chunk = Chunk(
            schema_version="1.0",
            document_id=document_id,
            chunk_index=chunk_index,
            text=text,
            char_count=len(text),
            token_count=len(self.tokenizer.encode(text)),
            source_type=source_type,
            source_block_ids=block_ids,
            page_numbers=sorted(list(page_numbers)) if page_numbers else [],
            heading_context=heading_context,
            block_types=sorted(list(block_types)),
            chunker_strategy=ChunkerStrategy.STRUCTURE_AWARE,
            chunker_config=config
        )
        chunk.chunk_id = chunk.generate_chunk_id()
        bundle.add_chunk(chunk)
        return chunk


def get_chunker(strategy: str, tokenizer: Optional[Callable] = None) -> BaseChunker:
    """Factory function to get chunker by strategy"""
    chunkers = {
        ChunkerStrategy.FIXED: FixedSizeChunker,
        ChunkerStrategy.STRUCTURE_AWARE: StructureAwareChunker,
    }
    
    chunker_class = chunkers.get(strategy, FixedSizeChunker)
    return chunker_class(tokenizer=tokenizer)
