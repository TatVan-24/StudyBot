# M3 — Embedding and Local Vector Index Summary Report

**Status:** `COMPLETED`  
**Date:** `2026-09-02T08:57:38Z` (Frozen Execution Time for Determinism)

## 1. Locked Architecture (ADR-003)

- **Model:** `sentence-transformers/paraphrase-multilingual-mpnet-base-v2`
- **Revision (Hash):** `4328cf26390c98c5e3c738b4460a05b95f4911f5`
- **Dimension:** 768
- **Max Sequence Length:** 512 (Overridden to avoid silent truncation of 264-token chunks)
- **Engine:** SQLite + NumPy (Exact KNN via dot product)
- **Normalization:** L2-normalized vectors

## 2. Verification Invariants (100% Passed)

- ✅ **Count Invariant:** Index count == Chunk count == 39. `chunk_ids` match exactly between JSONL and DB.
- ✅ **Dimension Check:** Validated vector shape matches model dimension (768).
- ✅ **Traceability:** 100% of `source_block_ids` in all chunks successfully traced back to `blocks.jsonl`.
- ✅ **Fail-Fast Gateway:** Verified that texts exceeding 512 tokens immediately raise `ValueError` rather than silently truncating.
- ✅ **Determinism:** Rebuilding the index from the same chunks yielded identical vectors (max diff `0.00000000e+00`).
- ✅ **L2 Normalization:** Dot product is mathematically equivalent to Cosine Similarity.

## 3. Smoke Retrieval Test (Passed)

**Query 1:** *"Data Observability Pipeline có những thành phần nào?"*
- [1] Score: 0.7792 | Chunk: `sha256:2d5fe21ad728a412` (W1-D3: Data Layer Architecture...)
- [2] Score: 0.7186 | Chunk: `sha256:2651f7323c0770bb`
- [3] Score: 0.6737 | Chunk: `sha256:d5081477acf126a4`

**Query 2:** *"Feature Store dùng để làm gì trong ML?"*
- [1] Score: 0.4469 | Chunk: `sha256:a932be644d151e6e` (Feature Store — Khi Cần ML)
- [2] Score: 0.3669 | Chunk: `sha256:2651f7323c0770bb`
- [3] Score: 0.3520 | Chunk: `sha256:ce6002e1ea9327a7`

## 4. Artifacts Generated
- **Index Database:** `evaluation/index/m3_index.db` (Contains metadata and BLOB vectors)
- **Manifest:** `evaluation/index/m3_manifest.json` (Captures dimension, exact model, sequence length, and execution timestamp).
