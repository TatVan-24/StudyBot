# M4 - Retrieval Validation Contracts

## 1. Object

**M4 Holdout Validation validates the generalization of the retrieval strategy selected from M4 Development.**

Specicific:
```
M4 Development
      ↓
Min-Max Score Fusion
      ↓
candidate α ∈ {0.2, 0.3, 0.4}
      ↓
M4 Holdout Validation
      ↓
Fresh unseen test-v1
```
**In scope**
- Min-Max Score Fusion
- α ∈ {0.2, 0.3, 0.4}
- Dense baseline
- BM25 baseline
- RRF baseline
- Retrieval quality on unseen evaluation cases

**Out of scope**
- Answer generation
- Citation generation
- LLM evaluation
= Dynamic gating implementation
- Cross-encoder implementation
- Parser/chunker changes

**Core question:**

```Does the candidate fixed-weight fusion region generalize to unseen data?```

## 2. Purpose

**Primary**
```Validate whether the candidate Min-Max α region generalizes beyond the development dataset.```

**Secondary**
- Regession Test BM25/Dense/RRF
- Test trade-off between 
    - First hit retrieval
    - Full evidence retrieval
- Recognize failure pattern on unseen cases
- Base for architecture decision
```
Holdout
   ↓
Generalization evidence
   ↓
Architecture Decision
   ↓
M5
```
## 3. Current State

**3.1 Data Ingestion Pipeline (Frozen)**
- Parsers (TXT, MD, PDF) and `StructureAwareChunker` have been frozen.
- `m3_index.db`: Vector Store (SQLite) using `mpnet-base-v2` for Dense embeddings and `rank_bm25` for Lexical. The lineage structure via `source_block_ids` works perfectly.

**3.2 Retrieval Evaluation (M4 Development)**
- **Baseline Metrics:** Affirms the necessity of Dual MRR (`MRR First` and `MRR Full`) and Cumulative Coverage@K for handling fragmented information.
- **RRF (Reciprocal Rank Fusion):** Found to have severe limitations. RRF only rewards Rank Agreement and ignores Score Magnitude, leading to the penalization of the Specialist in Rank Disagreement scenarios.
- **Score Fusion:** Min-Max normalization preserves Score Magnitude. Discovered a Regime Transition at $\alpha \approx 0.5$.
- **Candidate Region:** On the development-v2 dataset, the Min-Max region $\alpha \in \{0.2, 0.3, 0.4\}$ achieves an optimal balance: maintaining a higher MRR First than the Dense baseline while maximizing MRR Full.

**3.3 Current Evidence**
```text
              CURRENT EVIDENCE (from M4-E)

Min-Max
α .2 ─────────────── .4
    ← promising region →

Saturation
    ← no comparable region →

Next:
FRESH HOLDOUT
      ↓
Does .2–.4 survive?
      ↓
 YES → Fixed α
 NO  → investigate Dynamic Gating
```
- Min-Max score fusion shows a promising robust region around $\alpha=0.2-0.4$ on the current frozen 9-case development set (`development-v2`).
- $\alpha=0.4$ achieves the highest MRR Full (0.2242) while maintaining MRR First at 0.7066.
- Higher $\alpha$ values increasingly favor first-hit retrieval at the expense of full-evidence retrieval (Regime Transition at $\alpha \approx 0.5$).
- Saturation does not show a comparable robust Full-Coverage region.
## 4. Technique

### 4.1. Test Dataset Strategy
**Decision: Strategy A — Extend Current Corpus**
Create `test-v1` by extending the existing M4 corpus
with new evaluation cases while preserving the current
domain/corpus distribution.

The new cases must not be copied from or tuned against
`development-v2`.

### 4.2. Failure-Mode Coverage

`test-v1` will use a failure-mode matrix to ensure that
important retrieval behaviors observed during M4 Development
are represented in the holdout set.

Candidate failure modes include:

- Dense specialist
- BM25 specialist
- Strong rank disagreement
- Weak semantic anchor / context dependency
- Multi-block evidence
- Cross-document distractors
- Zero-hit / low-recall cases

A case may belong to multiple failure-mode categories.

The matrix is used to ensure coverage, not to tune alpha
or define the final result after evaluation.

### 4.3. Case Count

No fixed case count is locked yet.
The final size of `test-v1` is determined by:
- failure-mode coverage
- query diversity
- evidence diversity
- ability to detect meaningful regression

`30–50` cases may be used as an initial planning target,
but is not yet a contractual requirement.

## 5. Workflow

```mermaid
flowchart TD
    subgraph Phase 1: Preparation
        A[Curate test-v2.jsonl]
        B[blocks.jsonl & m3_index.db]
        A -->|Lock Dataset| C(FREEZE DATASET)
    end

    subgraph Phase 2: Execution
        C --> D(poc_holdout_validation.py)
        B --> D
        D --> E[Evaluate Baselines: Dense, BM25, RRF]
        D --> F[Evaluate Candidates: Min-Max α ∈ {0.2, 0.3, 0.4}]
    end

    subgraph Phase 3: Metrics Extraction
        E & F --> G(Dual MRR Extractor)
        G --> H[MRR Full]
        G --> I[MRR First]
        E & F --> J(Coverage Extractor)
        J --> K[Coverage@K]
        E & F --> L(Critical Failure Tracker)
        L --> M[Regression vs Baselines]
    end

    subgraph Phase 4: Decision Gate
        H & I & K & M --> N{Guardrail Check}
        N -->|Pass Thresholds & Robust| O[Production: Fixed α Candidate]
        N -->|Query-Dependent or Fail| P[Research: Dynamic Gating / Reranker]
    end
```
## 6. Input

### 6.1. Dataset: `test-v2.jsonl`

```json
{
  "case_id": "holdout_001",
  "category": "dense_specialist",
  "query": "Giải thích cơ chế attention trong transformer",
  "target_locators": [
    {"doc_id": "doc_transformer_001", "block_range": [24, 25]},
    {"doc_id": "doc_attention_002", "block_range": [10, 11]}
  ],
  "difficulty": "medium",
  "stratum": "semantic_heavy"
}
```
> **Note:** `ground_truth_answer` is explicitly excluded from this JSON schema, strictly honoring the principle that M4 only evaluates retrieval completeness and rank quality, not answer generation (which belongs to M5).

### 6.2. Retrieval Index
- `evaluation/index/m3_index.db`: The frozen SQLite Vector Store.
- `evaluation/bundle_all/blocks.jsonl`: Required metadata and index artifacts for block lineage resolution.

### 6.3. Evaluation Configuration

| Parameter | Value |
|---|---|
| **Alpha Candidates** | `[0.2, 0.3, 0.4]` |
| **Baselines** | Dense ($\alpha=1.0$), BM25 ($\alpha=0.0$), RRF (k=60) |
| **Normalization** | Min-Max |
| **K Values** | `[1, 3, 5, 10]` |
| **Top-K Retrieval** | `10` |
| **Metrics** | MRR First, MRR Full, Cov@1, Cov@3, Cov@5, Cov@10 |

### 6.4. Predefined Success Criteria

| Metric | Threshold | Role |
|---|---|---|
| **MRR Full** | $\ge 0.20$ | Primary Objective |
| **MRR First** | $\ge 0.65$ | Mandatory Guardrail |
| **Coverage@10** | $\ge 40\%$ | Supporting Evidence |
| **Critical Failure** | `MRR First < 0.50` OR `Zero-hit rate > X%` | Hard Constraint |

## 7. Expected Output

The output must definitively answer four core questions:
1. Did the case retrieve the evidence?
2. Which alpha achieved the quality target?
3. Does a stable robust region exist?
4. What is the next architecture decision?

The evaluation results flow through a strict 4-level hierarchy: `Metrics` $\rightarrow$ `PASS/FAIL` $\rightarrow$ `Robust/Sensitive` $\rightarrow$ `Architecture Decision`.

### 7.1. Case-Level Success / Failure

**Success**
A case is considered successful if:
- At least one target block is retrieved.
- `MRR First` does not violate the critical-failure threshold.

**Failure**
A case is flagged with `critical_failure` if:
- Zero-hit: fails to retrieve any target block.
- OR `MRR First` < critical threshold.

*(Note: Case-level failures must be preserved in the raw trace to investigate root causes).*

### 7.2. Alpha-Level Success

An alpha configuration is considered a `PASS` if it simultaneously satisfies:

| Condition | Requirement |
|---|---|
| Aggregate | `MRR Full` $\ge$ threshold AND `MRR First` $\ge$ threshold |
| Critical Failure | The rate of `critical_failure` across cases does not exceed the predefined aggregate threshold (e.g., `Zero-hit rate` $\le$ X% AND `MRR First < Y` rate $\le$ Z%). Thresholds must be frozen before holdout execution. |
| Coverage | Does not violate `Coverage@K` guardrails |
| Baseline | Achieves a minimum required improvement over Dense/BM25 |

### 7.3. Robust Region

Fixed Alpha is considered **robust** if:
- $\alpha = 0.2$ `PASS`
- $\alpha = 0.3$ `PASS`
- $\alpha = 0.4$ `PASS`
AND no alpha causes critical regression.

If only one alpha passes, the result is deemed **alpha-sensitive**. This provides insufficient evidence to conclude that Fixed Alpha is robust.

### 7.4. Architecture Decision

**PASS — Fixed Alpha**
If a robust region exists, aggregate metrics hit thresholds, there are no critical failures beyond allowed limits, and no unacceptable regressions:
$\rightarrow$ Fixed Alpha Score Fusion is selected as the retrieval baseline.

**CONDITIONAL — Alpha Sensitive**
If some alphas perform well but performance varies significantly according to failure-mode or design stratum:
$\rightarrow$ Do not conclude Fixed Alpha is robust.
$\rightarrow$ Retain Dynamic Weighting / Query Gating as a **research direction**.

**FAIL — Fusion Strategy Insufficient**
If no alpha meets aggregate criteria, or critical failures are not improved, or baseline improvement is not met:
$\rightarrow$ Fixed Score Fusion is rejected.
$\rightarrow$ Open research into Dynamic Gating or Cross-Encoder Reranking as the next strategy.

## 8. Relevant Files

To maintain strict traceability, the holdout validation process depends on and generates specific artifacts.

### 8.1. Existing / Source
- **Evaluation Environment:**
  - `evaluation/datasets/` (Contains the frozen `development-v2.jsonl` and others)
  - `evaluation/index/` (Contains `m3_index.db`)
  - `evaluation/scripts/`
  - `evaluation/results/`
- **Architecture & Evaluation Contracts:**
  - `Architecture/11-retrieval-contracts.md`
  - `Architecture/ADR-004 Retrieval Evaluation.md`

### 8.2. Required Artifacts (To be generated)
- **Test Dataset:**
  - `evaluation/datasets/test-v2.jsonl` (The unseen holdout set)
- **Output Results:**
  - `evaluation/results/m4_holdout_results.jsonl` (Raw Forensic Evidence)
  - `evaluation/results/m4-holdout-summary.md` (Aggregate Metrics & Case Matrix)

### 8.3. Decision Artifact
- **Target:** A formal ADR (Architecture Decision Record) or retrieval decision document. This will be published under `Architecture/` to officially lock the Hybrid Retrieval architecture (Fixed Weight vs Dynamic Gating) based on the outcome of `m4-holdout-summary.md`.

## 9. Report Format

### 9.1. Raw Trace Report: `m4_holdout_results.jsonl`
```json
{
  "run_metadata": {
    "run_id": "m4-holdout-v1",
    "dataset": "test-v1",
    "index": "m3_index.db",
    "timestamp": "2026-09-15T10:00:00Z"
  },
  "retrieval_config": {
    "fusion_method": "min_max",
    "alpha": 0.3,
    "embedding_model": "text-embedding-3-small",
    "top_k": 10
  },
  "case_id": "holdout_001",
  "stratum": "semantic_heavy",
  "query": "Giải thích cơ chế attention trong transformer",
  "target_block_ids": ["block_txt_24", "block_txt_25"],
  "metrics": {
    "coverage_at_1": 0.5,
    "coverage_at_3": 1.0,
    "coverage_at_5": 1.0,
    "coverage_at_10": 1.0,
    "mrr_first_hit": 1.0,
    "mrr_full_coverage": 0.3333
  },
  "diagnostic_evidence": {
    "target_blocks_exist_in_index": true,
    "target_blocks_retrieved": true,
    "first_hit_rank": 1,
    "full_coverage_rank": 3
  }
}
```

### 9.2. Aggregate Report: `m4-holdout-summary.md`
| Alpha | MRR First | MRR Full | Cov@10 | Critical Failures | Decision |
|---|---|---|---|---|---|
| **0.2** | 0.68 | 0.21 | 42% | 0 | PASS |
| **0.3** | 0.70 | 0.22 | 43% | 0 | PASS |
| **0.4** | 0.71 | 0.22 | 43% | 0 | PASS |
| **Dense** | 0.69 | 0.11 | 41% | 0 | Baseline |
| **BM25** | 0.64 | 0.22 | 38% | 0 | Baseline |
| **RRF** | 0.61 | 0.12 | 34% | 0 | Baseline |

### 9.3. Strata Analysis Report
| Stratum | Best Alpha | MRR First | MRR Full | Insight |
|---|---|---|---|---|
| **Semantic-heavy** | 0.4 | 0.75 | 0.18 | Dense dominates, requires high alpha |
| **Lexical-heavy** | 0.2 | 0.62 | 0.28 | BM25 dominates, requires low alpha |
| **Balanced** | 0.3 | 0.70 | 0.22 | Alpha 0.3 provides balance |
| **Multi-hop** | 0.3 | 0.68 | 0.20 | Requires signals from both sources |

**Conclusion Mechanism:**
- If the `Best Alpha` changes drastically according to the stratum $\rightarrow$ **Query-dependent** (Dynamic Gating).
- If the `Best Alpha` is stable and consistently passes guardrails across strata $\rightarrow$ **Fixed Alpha**.

### 9.4. Decision Report: `ADR-005`
*(To be created in `Architecture/ADR-005 Retrieval Fusion Strategy Decision.md`)*

```markdown
# ADR 005: Retrieval Fusion Strategy Decision

## Status
Proposed / Accepted / Rejected

## Context
Following the M4 Holdout Validation on the `test-v1` dataset, a final architectural decision must be made regarding the Retrieval Fusion strategy.

## Decision
[Specify the architectural choice: Fixed Alpha / Dynamic Gating / Cross-Encoder Reranker]

## Evidence
[Include aggregate metrics table, Pareto analysis, and strata breakdown]

## Consequences
[Detail the impact on M5, latency, token cost, and system complexity]
```