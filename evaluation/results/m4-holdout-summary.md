# M4-Holdout Summary Report

## 1. Aggregate Metrics

| Configuration | MRR First | MRR Full | Cov@10 | Critical Fails | Zero-Hits | Decision |
|---|---|---|---|---|---|---|
| **dense** | 0.5451 | 0.3472 | 53.60% | 9 (37.5%) | 7 (29.2%) | Baseline |
| **bm25** | 0.5702 | 0.3983 | 56.31% | 10 (41.7%) | 6 (25.0%) | Baseline |
| **rrf60** | 0.5181 | 0.3375 | 60.69% | 10 (41.7%) | 5 (20.8%) | Baseline |
| **minmax_0.2** | 0.5920 | 0.4062 | 56.31% | 11 (45.8%) | 6 (25.0%) | FAIL |
| **minmax_0.3** | 0.6066 | 0.4201 | 56.31% | 10 (41.7%) | 6 (25.0%) | FAIL |
| **minmax_0.4** | 0.6105 | 0.4248 | 60.48% | 10 (41.7%) | 5 (20.8%) | FAIL |

## 2. Robust Region Conclusion

**Conclusion:** Fusion Strategy FAIL. No alphas passed guardrails.


## 3. Strata Analysis

| Stratum | Best Alpha | MRR First | MRR Full |
|---|---|---|---|
| **direct_factual** | 0.4 | 0.6105 | 0.4248 |