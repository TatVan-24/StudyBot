# M5 Step 1: Scale Validation Report

## 1. Aggregate Metrics

| Configuration | MRR First | MRR Full | Cov@10 | Critical Fails | Zero-Hits | Decision |
|---|---|---|---|---|---|---|
| **minmax_0.4** | 0.4761 | 0.1848 | 48.12% | 20 (57.1%) | 8 (22.9%) | FAIL |

## 2. Frozen Baseline Conclusion

**Conclusion: FAIL.**
The frozen M4 baseline (`minmax_0.4`) failed the predefined M5 quality gates on test-v3.


## 3. Tag-Level Analysis

| Tag | N | MRR First | MRR Full | Critical Fails | Zero-Hits |
|---|---|---|---|---|---|
| **pdf** | 20 | 0.5097 | 0.0000 | 11 | 5 |
| **semantic-heavy** | 21 | 0.3966 | 0.1683 | 13 | 7 |
| **ambiguous** | 2 | 0.5000 | 0.5000 | 1 | 1 |
| **lexical-anchor-heavy** | 12 | 0.5279 | 0.1612 | 7 | 1 |
| **context-dependent** | 2 | 1.0000 | 0.0000 | 0 | 0 |
| **txt** | 15 | 0.4312 | 0.4312 | 9 | 3 |
| **cross_lingual** | 1 | 0.2000 | 0.2000 | 1 | 0 |
| **multi-block** | 1 | 0.0000 | 0.0000 | 1 | 1 |