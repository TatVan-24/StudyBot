# M5 — Decision Gate Holdout Report

## 10.1 Experiment Identity
| Field | Value |
|---|---|
| run_id | `m5-holdout-v1` |
| dataset | `test-v2.jsonl` |
| candidate_pool | Dense Top-20 ∪ BM25 Top-20 |
| reranker | `BAAI/bge-reranker-v2-m3` |
| gate_version | `score>=0.2 OR rank<=1` |
| timestamp | `2026-09-18T02:54:27.016494+00:00` |

## 10.2 Frozen Configuration
```text
score_threshold        = 0.2
baseline_rank_threshold = 1
candidate_dense_top_k  = 20
candidate_bm25_top_k   = 20
dense_alpha            = 0.4
bm25_alpha             = 0.6
```

## 10.3 Preconditions
- dataset valid ✓
- candidate pool valid ✓ (Dense Top-20 ∪ BM25 Top-20)
- baseline valid ✓ (Min-Max fusion α=0.4)
- reranker valid ✓ (`BAAI/bge-reranker-v2-m3`)
- ground truth valid ✓
- testability: BGE Rescue=4 ≥ 1 ✓, BGE Regression=1 ≥ 1 ✓

## 10.4 Aggregate Result

| System   | Rescue | Regression | MRR First | Cov@10 |
| -------- | -----: | ---------: | --------: | -----: |
| Baseline |      — |          0 | 88.5833 | 0.6256 |
| BGE-only |      4 |          1 | 86.5417 | 0.6673 |
| Gated    |      4 |          1 | 87.8750 | 0.6673 |

Cases evaluated: 24

## 10.5 Rescue Analysis
- Cases rescued by Gate         : 4
- Cases rescued by BGE-only     : 4
- Rescue retention              : 100.0%
- Gate rescue cases             : ['holdout_011', 'holdout_012', 'holdout_019', 'holdout_022']

## 10.6 Regression Analysis
- Strong Anchor regressions (BGE-only)  : 1
- Strong Anchor regressions (Gated)     : 1
- Regression reduction                  : 0.0%
- Cases protected by Gate               : 0  []
- General rank degradations (non-SA)    : 1  ['holdout_001']
- Gate regression cases                 : ['holdout_008']

## 10.7 Decision Trace (top 10 most impactful cases)

| Case ID | Baseline rank | BGE rank | BGE score | Baseline rank of BGE Top-1 | Gate decision | Final rank | Rescue | Regression |
|---------|----------:|--------:|--------:|--------:|-----------|-------:|:------:|:-------:|
| holdout_011 | 15 | 1 | 0.8904 | 15 | BGE | 1 | ✓ | — |
| holdout_012 | 6 | 3 | 0.1112 | 1 | BGE | 3 | ✓ | — |
| holdout_001 | 2 | 3 | 0.8145 | 1 | BGE | 3 | — | — |
| holdout_008 | 1 | 2 | 0.9960 | 2 | BGE | 2 | — | ✓ |
| holdout_019 | 3 | 2 | 0.9648 | 1 | BGE | 2 | ✓ | — |
| holdout_022 | 2 | 1 | 0.9860 | 2 | BGE | 1 | ✓ | — |
| holdout_002 | 37 | 35 | 0.0042 | 20 | BASELINE | 37 | — | — |
| holdout_003 | 39 | 18 | 0.0024 | 12 | BASELINE | 39 | — | — |
| holdout_004 | 1 | 1 | 0.7506 | 1 | BGE | 1 | — | — |
| holdout_005 | 1 | 1 | 0.4140 | 1 | BGE | 1 | — | — |

## 10.7b Slice Analysis (diagnostic only — does not modify decision)

| Tag | Total | Rescue | Regression |
|-----|------:|-------:|-----------:|
| ambiguous | 2 | 0 | 0 |
| context-dependent | 4 | 2 | 0 |
| distractor-heavy | 1 | 0 | 0 |
| easy | 9 | 1 | 1 |
| hard | 6 | 1 | 0 |
| lexical-anchor-heavy | 10 | 1 | 1 |
| markdown | 4 | 1 | 0 |
| medium | 9 | 2 | 0 |
| multi-block | 1 | 0 | 0 |
| pdf | 8 | 2 | 0 |
| semantic-heavy | 6 | 1 | 0 |
| txt | 12 | 1 | 1 |

## 10.8 H6 Conclusion

```
H6 = SUPPORTED ON HOLDOUT
```

## 10.9 Interpretation

**Observed facts:**
- Evaluated 24 answerable cases from `test-v2.jsonl`.
- BGE-only produced 4 Rescue and 1 Regression on Holdout.
- Gate produced 4 Rescue and 1 Regression.
- Rescue retention: 100.0% (threshold: 90%).
- Regression change: 1 → 1.

**Hypothesis conclusion:**
H6 = SUPPORTED ON HOLDOUT

**Unresolved issues (not answered by this experiment):**
- Whether this Gate rule is optimal for production.
- Whether the CE should run for every query at inference time.
- Whether a single routing policy is universally optimal.

> `H6 SUPPORTED` does not imply `Gate approved for production`.
> These two conclusions are not equivalent. (ADR-006 §9.4)