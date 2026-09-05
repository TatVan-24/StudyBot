# ADR 003: Embedding Baseline Selection (Milestone 3)

## Status
Accepted

## Context
In Milestone 3, we need to convert textual chunks from our `StructureAwareChunker` (M2 output) into dense vector representations. These vectors will be indexed and stored locally alongside metadata for retrieval (KNN exact search via dot product).

Our original system mapping provisionally suggested `paraphrase-multilingual-MiniLM-L12-v2` (384 dimensions, `max_seq_length=128`). However, the `StructureAwareChunker` packs content logically based on heading contexts, resulting in some chunks being up to 264 tokens long (e.g., Chunk 2 in our dataset). 

If we use `MiniLM-L12-v2` with `max_seq_length=128`, it would lead to silent truncation. While we could truncate anyway or split the chunks, modifying the frozen chunking schema from M2 breaks the modular pipeline boundary. We strictly mandate a fail-fast mechanism to avoid truncation, as silent truncation corrupts downstream retrieval metrics (M4).

## Decision
We select `sentence-transformers/paraphrase-multilingual-mpnet-base-v2` as the baseline embedding model.
- **Dimension:** 768
- **Max Sequence Length:** 512
- **Pooling:** Mean pooling (default for model)
- **Normalization:** L2-normalized vectors
- **Similarity Metric:** Dot product (which equates to cosine similarity when vectors are L2-normalized).

We also mandate that the indexing mechanism fail-fast with a `ValueError` if any chunk exceeds the `max_seq_length` measured by the exact wordpieces of the model's tokenizer.

## Consequences
- **Positive:** We can embed all 39 M2 chunks completely without any truncation or chunk-splitting, maintaining 100% data integrity for M4 metrics calculation.
- **Positive:** `mpnet` has high capacity across multilingual texts, ensuring strong embedding quality for Vietnamese/English technical jargon.
- **Negative (Trade-off):** `mpnet` (768d) is a larger model than `MiniLM` (384d). It requires more disk space, memory, and slightly more computation during exact search (`N x 768` matrix multiplication). However, given our small initial scale (39 chunks), this performance hit is negligible, and accuracy/integrity takes precedence.
- **Negative (Trade-off):** Dependency size increases. We are pinning `sentence-transformers==2.7.0`, which brings in `torch` and `transformers`.

## Compliance
- This decision aligns with the "start-simple, evaluation-driven" AI Engineering principle. We measure retrieval using exact KNN, preserving all lineage (source block IDs), and only consider complex optimizations (ANN, Hybrid, Reranking) if failure is proven in M4.
