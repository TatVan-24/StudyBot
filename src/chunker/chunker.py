"""Chunking algorithms. Data contract lives in schema.py (single source of truth)."""
from typing import List, Callable, Optional
from .schema import Chunk, ChunkBundle, ChunkerStrategy


_tiktoken_available = False
try:
    import tiktoken
    _tiktoken_available = True
except ImportError:
    pass


class _FallbackTokenizer:
    """Character-based tokenizer: encode/decode round-trip.
    Critical fix: old code's `lambda t: t.split()` crashed because the
    algorithms call `.encode()`/`.decode()` on it. This keeps the chunker
    runnable even when tiktoken is absent (dev env has no tiktoken)."""
    def encode(self, text: str) -> List[int]:
        return [ord(c) for c in text]
    def decode(self, tokens: List[int]) -> str:
        return "".join(chr(t) for t in tokens)


class BaseChunker:
    strategy: ChunkerStrategy = ChunkerStrategy.FIXED

    def __init__(self, tokenizer: Optional[object] = None):
        self.tokenizer = tokenizer or self._default_tokenizer()

    def _default_tokenizer(self):
        if _tiktoken_available:
            return tiktoken.get_encoding("cl100k_base")
        return _FallbackTokenizer()

    def chunk(self, blocks: List[dict], document_id: str,
              source_type: str, config: dict) -> ChunkBundle:
        raise NotImplementedError

    def _build_chunk(self, document_id, source_type, chunk_index, text,
                     token_count, block_ids, pages, headings, types, config) -> Chunk:
        chunk = Chunk(
            schema_version="1.0", document_id=document_id, chunk_index=chunk_index,
            text=text, char_count=len(text), token_count=token_count,
            source_type=source_type, source_block_ids=block_ids,
            page_numbers=sorted(pages), heading_context=headings,
            block_types=sorted(types), chunker_strategy=self.strategy,
            chunker_config={k: v for k, v in config.items() if k != "parse_job_id"},
        )
        chunk.chunk_id = chunk.generate_chunk_id()
        return chunk


class FixedSizeChunker(BaseChunker):
    strategy = ChunkerStrategy.FIXED

    def chunk(self, blocks, document_id, source_type, config) -> ChunkBundle:
        window = config.get("window_size", 512)
        overlap = config.get("overlap_ratio", 0.1)
        bundle = ChunkBundle(document_id, config.get("parse_job_id", ""))

        texts, ids, heads, types, pages = [], [], [], [], []
        for b in blocks:
            texts.append(b.get("text", ""))
            ids.append(b.get("block_id", ""))
            heads.append([h.get("text", "") for h in b.get("heading_path", [])])
            types.append(b.get("block_type", ""))
            loc = b.get("locator", {})
            if loc.get("type") == "pdf":
                pages.append([l["pdf_page"] for l in loc.get("locations", []) if l.get("pdf_page")])
            else:
                pages.append([])

        full = "\n\n".join(texts)
        tokens = self.tokenizer.encode(full)
        step = max(1, window - int(window * overlap))

        idx = 1
        i = 0
        while i < len(tokens):
            window_tokens = tokens[i:i + window]
            text_chunk = self.tokenizer.decode(window_tokens)

            inc_ids, inc_heads, inc_types, inc_pages = [], [], set(), set()
            cum = 0
            for j, bt in enumerate(texts):
                btok = len(self.tokenizer.encode(bt))
                if cum <= i + window and (cum + btok) > i and ids[j]:
                    inc_ids.append(ids[j])
                    if heads[j]:
                        inc_heads = heads[j]
                    inc_types.add(types[j])
                    inc_pages.update(pages[j])
                cum += btok + 2

            bundle.add_chunk(self._build_chunk(
                document_id, source_type, idx, text_chunk, len(window_tokens),
                inc_ids, inc_pages, inc_heads, inc_types, config))
            idx += 1
            if i + window >= len(tokens):
                break
            i += step
        return bundle


class StructureAwareChunker(BaseChunker):
    strategy = ChunkerStrategy.STRUCTURE_AWARE

    def chunk(self, blocks, document_id, source_type, config) -> ChunkBundle:
        max_tokens = config.get("max_tokens", 512)
        bundle = ChunkBundle(document_id, config.get("parse_job_id", ""))

        cur_text, cur_ids, cur_heads = [], [], []
        cur_types, cur_pages = set(), set()   # FIX: set() nhất quán
        idx = 1

        for b in blocks:
            text = b.get("text", "")
            bid = b.get("block_id", "")
            btype = b.get("block_type", "")
            hp = b.get("heading_path", [])

            # Ranh giới heading: flush chunk đang gom
            if btype == "heading" and cur_text:
                joined = "\n\n".join(cur_text)
                bundle.add_chunk(self._build_chunk(
                    document_id, source_type, idx, joined,
                    len(self.tokenizer.encode(joined)), cur_ids,
                    cur_pages, cur_heads, cur_types, config))
                idx += 1
                cur_text, cur_ids, cur_types, cur_pages = [], [], set(), set()

            if hp:
                cur_heads = [h.get("text", "") for h in hp]

            # Vượt max_tokens: flush
            if cur_text and len(self.tokenizer.encode(" ".join(cur_text + [text]))) > max_tokens:
                joined = "\n\n".join(cur_text)
                bundle.add_chunk(self._build_chunk(
                    document_id, source_type, idx, joined,
                    len(self.tokenizer.encode(joined)), cur_ids,
                    cur_pages, cur_heads, cur_types, config))
                idx += 1
                cur_text, cur_ids, cur_types, cur_pages = [], [], set(), set()  # FIX

            cur_text.append(text)
            if bid:
                cur_ids.append(bid)
            cur_types.add(btype)
            loc = b.get("locator", {})
            if loc.get("type") == "pdf":
                for l in loc.get("locations", []):
                    if l.get("pdf_page"):
                        cur_pages.add(l["pdf_page"])

        if cur_text:
            joined = "\n\n".join(cur_text)
            bundle.add_chunk(self._build_chunk(
                document_id, source_type, idx, joined,
                len(self.tokenizer.encode(joined)), cur_ids,
                cur_pages, cur_heads, cur_types, config))
        return bundle


def get_chunker(strategy: str, tokenizer: Optional[object] = None) -> BaseChunker:
    chunkers = {
        ChunkerStrategy.FIXED.value: FixedSizeChunker,
        ChunkerStrategy.STRUCTURE_AWARE.value: StructureAwareChunker,
    }
    cls = chunkers.get(strategy.value if isinstance(strategy, ChunkerStrategy) else strategy,
                       FixedSizeChunker)
    return cls(tokenizer=tokenizer)