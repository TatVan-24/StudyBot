# test_chunker.py
import json
from src.chunker.chunker import get_chunker, ChunkerStrategy, ChunkValidator

blocks = [
    {
        "block_id": "pdf_001_b0001",
        "block_type": "heading",
        "text": "Data Engineering Fundamentals",
        "heading_path": [{"level": 1, "role": "chapter", "text": "Data Engineering Fundamentals"}],
        "locator": {"type": "pdf", "locations": [{"pdf_page": 1}]}
    },
    {
        "block_id": "pdf_001_b0002", 
        "block_type": "paragraph",
        "text": "Data sources include databases, APIs, and streaming systems. Ingesting data requires careful planning.",
        "heading_path": [{"level": 1, "role": "chapter", "text": "Data Engineering Fundamentals"}],
        "locator": {"type": "pdf", "locations": [{"pdf_page": 1}]}
    },
    {
        "block_id": "pdf_001_b0003",
        "block_type": "heading", 
        "text": "Data Sources",
        "heading_path": [{"level": 1, "role": "chapter", "text": "Data Engineering Fundamentals"}, {"level": 2, "role": "section", "text": "Data Sources"}],
        "locator": {"type": "pdf", "locations": [{"pdf_page": 2}]}
    },
    {
        "block_id": "pdf_001_b0004",
        "block_type": "paragraph",
        "text": "There are two main types of data: batch and streaming. Batch processing handles large volumes at once.",
        "heading_path": [{"level": 1, "role": "chapter", "text": "Data Engineering Fundamentals"}, {"level": 2, "role": "section", "text": "Data Sources"}],
        "locator": {"type": "pdf", "locations": [{"pdf_page": 2}]}
    },
    {
        "block_id": "pdf_001_b0005",
        "block_type": "paragraph",
        "text": "Streaming data requires real-time processing frameworks like Kafka or Apache Flink.",
        "heading_path": [{"level": 1, "role": "chapter", "text": "Data Engineering Fundamentals"}, {"level": 2, "role": "section", "text": "Data Sources"}],
        "locator": {"type": "pdf", "locations": [{"pdf_page": 2}]}
    }
]

config = {
    "window_size": 50,  
    "overlap_ratio": 0.1,
    "parse_job_id": "test_job_001"
}

document_id = "pdf_001"
source_type = "pdf"


print("Test Fixed Strategy")
chunker = get_chunker(ChunkerStrategy.FIXED)
bundle = chunker.chunk(blocks, document_id, source_type, config)
print(f"Total chunks: {len(bundle.chunks)}\n")

for i, chunk in enumerate(bundle.chunks):
    print(f"--- Chunk {chunk.chunk_index} ---")
    print(f"chunk_id: {chunk.chunk_id}")
    print(f"token_count: {chunk.token_count}")
    print(f"source_block_ids: {chunk.source_block_ids}")
    print(f"heading_context: {chunk.heading_context}")
    print(f"page_numbers: {chunk.page_numbers}")
    print(f"text: {chunk.text[:100]}...")
    print()
print()
print("Test STRUCTURE_AWARE strategy")
chunker = get_chunker(ChunkerStrategy.STRUCTURE_AWARE)
bundle = chunker.chunk(blocks, document_id, source_type, {"max_tokens": 50, "parse_job_id": "test_job_001"})

print(f"Total chunks: {len(bundle.chunks)}\n")

for chunk in bundle.chunks:
    print(f"Chunk {chunk.chunk_index}: {chunk.text[:80]}...")
    print(f"  source_block_ids: {chunk.source_block_ids}")
    print(f"  heading_context: {chunk.heading_context}")
    print()