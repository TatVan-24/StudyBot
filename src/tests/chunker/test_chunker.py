<<<<<<< HEAD
import pytest
from src.chunker import get_chunker, ChunkerStrategy, ChunkValidator, Chunk


@pytest.fixture
def blocks():
    return [
        {"block_id": "pdf_001_b0001", "block_type": "heading",
         "text": "Data Engineering Fundamentals",
         "heading_path": [{"level": 1, "role": "chapter", "text": "Data Engineering Fundamentals"}],
         "locator": {"type": "pdf", "locations": [{"pdf_page": 1}]}},
        {"block_id": "pdf_001_b0002", "block_type": "paragraph",
         "text": "Data sources include databases, APIs, and streaming systems.",
         "heading_path": [{"level": 1, "role": "chapter", "text": "Data Engineering Fundamentals"}],
         "locator": {"type": "pdf", "locations": [{"pdf_page": 1}]}},
        {"block_id": "pdf_001_b0003", "block_type": "heading",
         "text": "Data Sources",
         "heading_path": [{"level": 1, "role": "chapter", "text": "Data Engineering Fundamentals"},
                          {"level": 2, "role": "section", "text": "Data Sources"}],
         "locator": {"type": "pdf", "locations": [{"pdf_page": 2}]}},
        {"block_id": "pdf_001_b0004", "block_type": "paragraph",
         "text": "There are two main types of data: batch and streaming.",
         "heading_path": [{"level": 1, "role": "chapter", "text": "Data Engineering Fundamentals"},
                          {"level": 2, "role": "section", "text": "Data Sources"}],
         "locator": {"type": "pdf", "locations": [{"pdf_page": 2}]}},
        {"block_id": "pdf_001_b0005", "block_type": "paragraph",
         "text": "Streaming data requires real-time processing frameworks.",
         "heading_path": [{"level": 1, "role": "chapter", "text": "Data Engineering Fundamentals"},
                          {"level": 2, "role": "section", "text": "Data Sources"}],
         "locator": {"type": "pdf", "locations": [{"pdf_page": 2}]}},
    ]


@pytest.fixture
def valid_block_ids(blocks):
    return {b["block_id"] for b in blocks}


@pytest.mark.parametrize("strategy,config", [
    (ChunkerStrategy.FIXED, {"window_size": 50, "overlap_ratio": 0.1}),
    (ChunkerStrategy.STRUCTURE_AWARE, {"max_tokens": 50}),
])
def test_invariants_hold(strategy, config, blocks, valid_block_ids):
    config = {**config, "parse_job_id": "test_job_001"}
    bundle = get_chunker(strategy).chunk(blocks, "pdf_001", "pdf", config)
    assert bundle.chunks
    for chunk in bundle.chunks:
        assert ChunkValidator.validate_invariants(chunk, valid_block_ids) == []


@pytest.mark.parametrize("strategy,config", [
    (ChunkerStrategy.FIXED, {"window_size": 50, "overlap_ratio": 0.1}),
    (ChunkerStrategy.STRUCTURE_AWARE, {"max_tokens": 50}),
])
def test_chunk_index_contiguous_1_based(strategy, config, blocks):
    bundle = get_chunker(strategy).chunk(blocks, "pdf_001", "pdf", config)
    assert [c.chunk_index for c in bundle.chunks] == list(range(1, len(bundle.chunks) + 1))


def test_chunk_id_deterministic_across_reruns(blocks):
    cfg = {"window_size": 50, "overlap_ratio": 0.1}
    b1 = get_chunker(ChunkerStrategy.FIXED).chunk(blocks, "pdf_001", "pdf", cfg)
    b2 = get_chunker(ChunkerStrategy.FIXED).chunk(blocks, "pdf_001", "pdf", cfg)
    assert [c.chunk_id for c in b1.chunks] == [c.chunk_id for c in b2.chunks]


def test_lineage_is_subset_of_input(blocks, valid_block_ids):
    bundle = get_chunker(ChunkerStrategy.STRUCTURE_AWARE).chunk(blocks, "pdf_001", "pdf", {"max_tokens": 50})
    for c in bundle.chunks:
        assert set(c.source_block_ids) <= valid_block_ids


def test_strategies_do_not_collide(blocks):
    a = get_chunker(ChunkerStrategy.FIXED).chunk(blocks, "pdf_001", "pdf", {"window_size": 50})
    b = get_chunker(ChunkerStrategy.STRUCTURE_AWARE).chunk(blocks, "pdf_001", "pdf", {"max_tokens": 50})
    assert {c.chunk_id for c in a.chunks}.isdisjoint({c.chunk_id for c in b.chunks})


def test_chunk_id_includes_strategy():
    base = dict(schema_version="1.0", document_id="d", chunk_index=1, text="hello world", token_count=2)
    fa = Chunk(**base, chunker_strategy=ChunkerStrategy.FIXED)
    fb = Chunk(**base, chunker_strategy=ChunkerStrategy.STRUCTURE_AWARE)
    assert fa.generate_chunk_id() != fb.generate_chunk_id()   # resolve collision GPT nêu


def test_validator_rejects_empty_lineage(valid_block_ids):
    c = Chunk(document_id="d", chunk_index=1, text="x", token_count=1,
              source_block_ids=[], chunker_strategy=ChunkerStrategy.FIXED)
    assert any("I2" in e for e in ChunkValidator.validate_invariants(c, valid_block_ids))


def test_validator_rejects_unknown_block(valid_block_ids):
    c = Chunk(document_id="d", chunk_index=1, text="x", token_count=1,
              source_block_ids=["ghost_id"], chunker_strategy=ChunkerStrategy.FIXED)
    assert any("I2" in e for e in ChunkValidator.validate_invariants(c, valid_block_ids))
