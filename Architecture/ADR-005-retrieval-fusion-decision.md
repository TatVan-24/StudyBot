# ADR 005: Retrieval Fusion Decision and M5 Transition

## 1. Context
During the M4 phase, we investigated whether a Fixed Min-Max Fusion strategy (combining MPNet Dense embeddings and BM25 Sparse retrieval with a fixed alpha parameter) could successfully pass our predefined holdout quality gates on an unseen evaluation dataset (`test-v2.jsonl`). The primary goal was to establish a robust baseline retrieval architecture.

## 2. Evidence and Findings
Based on the execution of the official M4 Holdout evaluation and subsequent Root Cause Analysis (RCA) on all 24 cases:
1. **Dataset Integrity**: The holdout dataset (`test-v2.jsonl`) is structurally valid and frozen after repairing Case 016. All targets exist in the index.
2. **Quality Gates Failed**: Dense, BM25, and all Fixed Min-Max Fusion alpha variants failed to meet the required quality gates (e.g., MRR First >= 0.65, Critical rate <= 5%).
3. **Positive Controls Validated**: Several test cases (e.g., 015, 016, 019) achieved near-perfect retrieval (Rank 1 or 2). This demonstrates that the retrieval and indexing pipeline works effectively when there is strong lexical or semantic alignment between the query and the evidence. The index itself is not broken.
4. **Failure Mechanisms Classified**:
    - **Insufficient Query-Evidence Alignment**: In multiple cases (e.g., 002, 003, 012), there is a significant vocabulary mismatch between the natural-language query and the technical terminology in the evidence. Both Dense and BM25 fail to retrieve the target within the Top-N, rendering any downstream fusion or reranking ineffective.
    - **Ranking Weakness**: In other cases (e.g., 010, 018), relevant evidence is successfully retrieved into the candidate pool but fails to rank high enough (Top-2) to satisfy the guardrails.
5. **No Fusion "Magic"**: Fixed Min-Max fusion cannot synthesize a retrieval signal when both underlying channels fail. It is fundamentally a scoring technique, not a signal generator.

## 3. Decision
1. **Reject Fixed Min-Max Fusion**: It will not be adopted as the primary architectural improvement for M4, as it does not address the root causes of our retrieval failures.
2. **Defer BGE-M3 Substitution**: Changing the embedding model is deferred. Current evidence isolates the failure to query-evidence alignment gaps and ranking thresholds, rather than strictly the representation quality of MPNet.
3. **Transition to M5**: We officially close M4 and transition to M5. M5 will investigate **ONE** targeted retrieval improvement based on a controlled experiment (Proof of Concept).

## 4. Next Steps (M5 Framework)
The M5 phase will strictly follow a hypothesis-driven controlled experiment model:
*   Identify the targeted failure mechanism (e.g., Query-Evidence alignment gap).
*   Formulate a hypothesis (e.g., LLM Query Rewriting will bridge the vocabulary gap).
*   Conduct a Proof of Concept (POC) keeping all other variables constant.
*   Decision Gate: Does it improve the targeted failure? If YES, keep it. If NO, revert.

*Note: Any intervention involving a Cross-Encoder must recognize that reranking can only re-order candidates that have already been retrieved into the Top-N pool by the candidate generation layer.*
