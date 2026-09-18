# M5 Hypothesis Conclusion

## Purpose
Freeze what M5 has actually established before finalizing the Decision Gate contract.
This document is a hypothesis conclusion, not an implementation specification.

---

## H1 — Query-Evidence Alignment Gap is the dominant failure mechanism
**Status: NOT SUPPORTED as the dominant mechanism.**

**Evidence from M5 Step 1 / Step 2:**
- 22 failure cases were analyzed.
- 18/22 (81.8%) already had the target inside the Top-20 candidate space.
- 14/22 (63.6%) had the target in Dense/BM25 Top-10.
- 4/22 (18.2%) were outside Top-20 / zero-hit.

**Interpretation:**
- Alignment / candidate availability is a real failure mechanism.
- However, it cannot explain the majority of observed failures.
- Ranking / fusion is the stronger explanation for the majority of cases where the target is already available.

**Conclusion:** H1 remains valid as a mechanism, but is not the dominant M5 failure mechanism.

---

## H2 — Ranking / reranking is a major bottleneck when the target is already available
**Status: SUPPORTED.**

**Evidence:**
- Most failed cases had the target inside the candidate pool.
- Cross-Encoder experiments showed substantial rank movement on those cases.
- With BGE, 12/18 Group A+B cases improved First-hit ranking.
- The same type of ranking sensitivity was also observed with the mMARCO Cross-Encoder.

**Interpretation:**
- The system can have the correct evidence available but rank it poorly.
- Reranking can materially change the ordering inside the candidate pool.

**Conclusion:** Ranking is a confirmed major bottleneck.

---

## H3 — Reranker/model choice materially changes system behavior
**Status: SUPPORTED.**

**Evidence:**
- Replacing the reranker changed case-level ranking substantially.
- BGE rescued previously weak A/B cases.
- BGE also changed rankings on Strong Anchor cases.

**Interpretation:**
- Retrieval behavior is model-sensitive.
- A model change is therefore a system-level change, not a drop-in implementation detail.

**Conclusion:** Model choice materially affects retrieval behavior. This does not establish that BGE is the production model.

---

## H4 — Cross-Encoder can improve hard cases without harming already-correct cases
**Status: NOT SUPPORTED.**

**Evidence from Strong Anchors:**
- Baseline target was already rank #1.
- BGE caused target displacement in 5/13 Strong Anchor cases.
- Examples include target movement from #1 to #2, #3, or #4.

**Interpretation:**
- Cross-Encoder has rescue capability.
- But applying it unconditionally introduces collateral regression.

**Conclusion:** CE is useful as an intervention, but is not proven safe as a universal replacement for the baseline ranking.

---

## H5 — Observable top-1/top-2 margin is a sufficient confidence signal
**Status: REJECTED.**

**Evidence:**
- Strong Anchor failures and successful cases had overlapping observable margins.
- BGE could produce a large top-1/top-2 margin while still selecting the wrong chunk.

**Interpretation:**
- A large margin means the model strongly prefers one candidate.
- It does not prove that the preferred candidate is correct.

**Conclusion:** Observable margin alone is insufficient for Gate C.

---

## H6 — A simple Gate can control the Rescue ↔ Regression trade-off
**Status: SUPPORTED on Development Set; NOT YET VALIDATED on Holdout.**

**Development sweep:**
- BGE-only: Rescue 10, Regression 5, MRR First 0.7173.
- Candidate rule: `Score >= 0.20 OR Baseline Rank <= 1`
- Result: Rescue 9, Regression 2, MRR First 0.7485.

**Interpretation:**
- A simple deterministic guard can reduce collateral regression while retaining most of the observed rescue capability.
- This is evidence that a gate is viable as a mechanism.
- The selected threshold/rule is still a development-set decision, not yet a production truth.

**Conclusion:** Gate C is promising and ready for holdout validation, but its generalization is still unproven.

---

## Overall M5 Conclusion

M5 has moved the problem definition from:
> "Which model should retrieve the correct chunk?"

to:
> "How should the system control ranking interventions when the correct evidence may already be available?"

The current evidence supports this system view:

```text
Recall / Candidate Availability
        ↓
  real but not dominant

Ranking / Reranking
        ↓
  major bottleneck

Cross-Encoder
        ↓
  can rescue ranking
  but can cause collateral regression

Decision Gate
        ↓
  promising control mechanism
  not yet holdout-validated
```

### What is now established
- Alignment failure exists, but is not the dominant M5 mechanism.
- Ranking is a major bottleneck once the target is available.
- Reranker/model choice materially changes system behavior.
- Unconditional Cross-Encoder reranking is not safe for all queries.
- Observable margin alone is not sufficient confidence.
- A simple deterministic gate shows promising development-set trade-offs.

### What is NOT yet established
- The production reranker model.
- The production threshold beyond the frozen validation protocol.
- That the selected Gate rule generalizes to holdout.
- That the final system should always route through CE.
- That a particular routing policy is universally optimal.

### Decision Before Contract Finalization
Only after this hypothesis conclusion is frozen should the Decision Gate contract define:
- the exact frozen rule,
- the fallback behavior,
- the holdout protocol,
- the acceptance criteria,
- and the conditions under which the rule may be merged.
