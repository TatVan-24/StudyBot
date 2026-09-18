# M5 Step 5: Gate Sweep Analysis (Final - Raw Logits)

## 1. Overview
After fixing the PyTorch Segfault issue and removing the unintended `Softmax` conversion, we successfully evaluated the `Decision under Uncertainty` Gate using **Raw Logits** from the `BAAI/bge-reranker-v2-m3` Cross-Encoder.

The Gate determines whether to trust the BGE-Reranker's ranking or fallback to the Dense+BM25 Baseline:
```text
ALLOW_BGE = (BGE_Top1_Score >= T) OR (Baseline_Rank_of_BGE_Top1 <= R)
```

## 2. Key Findings

The results reveal a **massive breakthrough**: the Gate can actually *outperform* both the Baseline and the BGE-only setup by filtering out BGE's "Confident Regressions".

| Configuration | Rescue | Regression | MRR First |
|---|---:|---:|---:|
| Baseline | — | 0 | 0.5589 |
| BGE-only | 10 | 5 | 0.7173 |
| **Rule: T=0.20 OR R≤1** | **9** | **2** | **0.7485** |

### Why is MRR First higher than BGE-only?
Because the Gate correctly blocked 3 out of 5 regressions (Strong Anchors that BGE would have ruined). 
When a case falls back to Baseline, its MRR remains high (since Baseline ranked them correctly). By saving those 3 Strong Anchors, the overall MRR jumps to **0.7485**, easily beating the BGE-only MRR of 0.7173. We only sacrificed 1 rescue (from 10 down to 9) to achieve this!

## 3. The Trade-off Spectrum

Scanning the threshold `T` reveals a clear Pareto front:

| Rule | Rescue | Regression | MRR First | Note |
|---|---:|---:|---:|---|
| BGE-only | 10 | 5 | 0.7173 | Max Rescue, but high collateral |
| `T=0.10 OR R≤1` | 9 | 4 | 0.7109 | |
| `T=0.20 OR R≤1` | 9 | 2 | 0.7485 | **👑 Best Balance (Max MRR)** |
| `T=0.30 OR R≤1` | 6 | 1 | 0.6820 | Rescue drops significantly |
| `T=0.50 OR R≤1` | 6 | 1 | 0.6769 | |
| `T=0.80 OR R≤1` | 4 | 0 | 0.6458 | **🛡️ Ultra-Conservative** (0 regressions) |

## 4. Conclusion & Recommendation

We have successfully engineered a deterministic `Decision under Uncertainty` Gate that is simple, interpretable, and highly effective.

> **Recommendation:** We should select **`T = 0.20`** and **`R = 1`** as our hard-coded Gate rule.
>
> **Logic:** `(bge_top1_score >= 0.20) OR (baseline_rank_of_bge_top1 <= 1)`

This rule gives us the absolute best MRR (0.7485) on the dev set by rescuing almost all hard cases (9/10) while minimizing regressions (2/5). 

**Next Steps:**
1. Hard-code this logic into the retrieval pipeline.
2. Validate on the Holdout set to ensure `0.20` is not overfitted to this micro-batch.
