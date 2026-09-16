# M4 — Retrieval Evaluation Summary

## 1. Evaluation Overview

| Item | Value |
|---|---|
| Dataset | development-v2 |
| Evaluation cases | 9 |
| Retrieval scope | Global Search |
| Embedding model | sentence-transformers/paraphrase-multilingual-mpnet-base-v2 |
| Embedding dimension | 768 |
| Normalization | L2 |
| Similarity metric | dot_product_on_L2_normalized (cosine equivalent) |
| Retrieval K | 1, 3, 5, 10 |
| Index version | 1.0 |
| Run timestamp | 2026-09-09T07:46:56.137749Z |
| Ground-truth unit | ParsedBlock |
| Relevance definition | chunk.source_block_ids ∩ target_block_ids |
| Evaluation status | COMPLETED |

---

## 2. Metric Results

| Metric | Mean |
|---|---:|
| Coverage@1 | 22.87% |
| Coverage@3 | 26.68% |
| Coverage@5 | 35.49% |
| Coverage@10 | 41.13% |
| MRR — First Hit | 0.6889 |
| MRR — Full Coverage | 0.1111 |

### Interpretation

The retriever finds at least one relevant block at a relatively high rank (MRR First Hit = **0.6889**).

However cumulative evidence coverage remains limited:

- At Top-1, mean coverage is **22.87%**.
- At Top-3, mean coverage is **26.68%**.
- At Top-5, mean coverage is **35.49%**.
- At Top-10, mean coverage is **41.13%**.

MRR Full Coverage = **0.1111** — full evidence retrieval is rarely achieved.

---

## 3. Per-Case Results

| Case | Target Blocks | Cov@1 | Cov@3 | Cov@5 | Cov@10 | First Hit | Full Cov |
|---|---:|---:|---:|---:|---:|---:|---:|
| eval_pdf_aws_s3_001 | 8 | 25.0% | 25.0% | 25.0% | 25.0% | #1 | No |
| eval_txt_observability_pillars_001 | 15 | 26.7% | 33.3% | 53.3% | 53.3% | #1 | No |
| eval_aws_security_levels_001 | 5 | 0.0% | 0.0% | 20.0% | 40.0% | #5 | No |
| eval_aws_regions_az_001 | 8 | 0.0% | 0.0% | 0.0% | 0.0% | — | No |
| eval_txt_pipeline_stages_001 | 16 | 18.8% | 18.8% | 18.8% | 18.8% | #1 | No |
| eval_txt_kafka_recovery_001 | 26 | 15.4% | 23.1% | 42.3% | 73.1% | #1 | No |
| eval_aws_tenant_access_001 | 5 | 20.0% | 40.0% | 60.0% | 60.0% | #1 | No |
| eval_wiki_s3_pricing_001 | 1 | 100.0% | 100.0% | 100.0% | 100.0% | #1 | Yes |
| eval_wiki_s3_features_001 | 3 | 0.0% | 0.0% | 0.0% | 0.0% | — | No |

---

## 4. Case-Level Observations

### 4.1 Full Coverage Cases

#### `eval_wiki_s3_pricing_001`

- Target blocks: 1
- Coverage@10: 100%
- First relevant result: Rank #1
- Full coverage achieved at Rank #1

### 4.2 Partial Retrieval Cases

#### `eval_pdf_aws_s3_001`

- Coverage@1: 25.0%
- Coverage@3: 25.0%
- Coverage@5: 25.0%
- Coverage@10: 25.0%
- Uncovered blocks: ['pdf_aws_001_b_469765fec4d08e465a17fffaaff9c686', 'pdf_aws_001_b_c6e51c170ab28733006ffe25d57188ca', 'pdf_aws_001_b_0edece00ab3e14367e28484abd6deff9', 'pdf_aws_001_b_a356bdde0b7d2be39cb000443b961fd7', 'pdf_aws_001_b_6c4fa02bc85f498492f93fad73195591']...

#### `eval_txt_observability_pillars_001`

- Coverage@1: 26.7%
- Coverage@3: 33.3%
- Coverage@5: 53.3%
- Coverage@10: 53.3%
- Uncovered blocks: ['txt_aiops_001_b_7d41ae2bf1b35f7b313ef5ede6f0cb82', 'txt_aiops_001_b_9af912babd0eaa9ed14ba7ff0982379a', 'txt_aiops_001_b_21b7f0bd7a3589bc761f20de3fa56f81', 'txt_aiops_001_b_a4dd43ed3df50e480deb141bcfd1f8b2', 'txt_aiops_001_b_5121c7711ef222284446141113bac1b5']...

#### `eval_aws_security_levels_001`

- Coverage@1: 0.0%
- Coverage@3: 0.0%
- Coverage@5: 20.0%
- Coverage@10: 40.0%
- Uncovered blocks: ['pdf_aws_001_b_64309e6ab78c99f193ef224ba270d7fc', 'pdf_aws_001_b_5b2edf7db33d318502cb9e84be12f057', 'pdf_aws_001_b_37785785343b8fa73619670eb322c634']

#### `eval_txt_pipeline_stages_001`

- Coverage@1: 18.8%
- Coverage@3: 18.8%
- Coverage@5: 18.8%
- Coverage@10: 18.8%
- Uncovered blocks: ['txt_aiops_001_b_b3011b94af793565e3b7ee429b9324ef', 'txt_aiops_001_b_8f4a9d5f394ae52e3056690907c042ff', 'txt_aiops_001_b_c99861bc1c7e9195849363bfcb9e5072', 'txt_aiops_001_b_1d834d7ac145de8c6f5acf6c814abfd6', 'txt_aiops_001_b_2e7bc908281d0b1484e7adfa64a6e5f2']...

#### `eval_txt_kafka_recovery_001`

- Coverage@1: 15.4%
- Coverage@3: 23.1%
- Coverage@5: 42.3%
- Coverage@10: 73.1%
- Uncovered blocks: ['txt_aiops_001_b_267b8261b449841d4b5c14e6bef40495', 'txt_aiops_001_b_d9bb763edaaa1337ca1ccb1945b0759e', 'txt_aiops_001_b_22872495ef6516a742d53bffdcd15a83', 'txt_aiops_001_b_60fb1de0c71d6c6164ee5c45a554311a', 'txt_aiops_001_b_ce16052b9eab018ea853a42850bad92d']...

#### `eval_aws_tenant_access_001`

- Coverage@1: 20.0%
- Coverage@3: 40.0%
- Coverage@5: 60.0%
- Coverage@10: 60.0%
- Uncovered blocks: ['pdf_aws_001_b_6f94b25eb540fc6a0b6e4a805cd04b4a', 'pdf_aws_001_b_5b2edf7db33d318502cb9e84be12f057']

### 4.3 Late Retrieval Cases

#### `eval_aws_security_levels_001`

- First relevant chunk appears at Rank #5.
- Coverage@1 = 0.0%  →  Coverage@10 = 40.0%

### 4.4 Clean Misses (Coverage@K = 0)

#### `eval_aws_regions_az_001`

```
Target blocks exist in index : True
Retrieved in Top-10       : False
Coverage@10               : 0%
```
The target blocks exist in the index but were not retrieved. This is a retrieval failure, not a corpus-absence failure.

#### `eval_wiki_s3_features_001`

```
Target blocks exist in index : True
Retrieved in Top-10       : False
Coverage@10               : 0%
```
The target blocks exist in the index but were not retrieved. This is a retrieval failure, not a corpus-absence failure.

---

## 5. Important Findings

### Finding 1 — Retrieval pipeline is functional

All 9 evaluation cases were executed successfully. Embedding invariant verified. Target blocks resolved. Traces generated.

### Finding 2 — First-hit retrieval is substantially better than full coverage

```
MRR First Hit      = 0.6889
MRR Full Coverage  = 0.1111
Gap                = 0.5778
```
The retriever can often surface some relevant evidence, but retrieving the **complete evidence set** is much harder.

### Finding 3 — Target evidence exists for the failed cases

The following zero-hit cases have target blocks present in the index:

- `eval_aws_regions_az_001`
- `eval_wiki_s3_features_001`

Therefore these are **retrieval failures**, not corpus gaps.

### Finding 4 — Global Search causes cross-document competition

Non-target document chunks compete directly with relevant evidence. This is expected behavior under D5 (Global Search) and should be treated as evaluation evidence, not as an implementation bug.

---

## 6. Current Limitations

The current M4 results do **not** yet establish:

- that the embedding model is inadequate
- that the chunker is the root cause
- that the queries are poorly written
- that Global Search should be replaced by scoped search
- that a reranker is required

The current trace provides **failure evidence**, but not sufficient evidence to assign a definitive root cause.

---

## 7. M4 Baseline Verdict

### Pipeline Integrity

**PASS**

- 9/9 cases executed
- Embedding invariant verified
- Target blocks resolved
- Target blocks checked against index
- Retrieval traces generated

### Retrieval Quality

**BASELINE ESTABLISHED — QUALITY REQUIRES INVESTIGATION**

> The retriever can consistently find relevant evidence in some cases, but evidence coverage is incomplete and several queries produce substantial retrieval misses.

---

## 8. Next Investigation

Before changing the retriever, inspect the failure cases at the evidence level:

1. Ground-truth block text
- Retrieved chunk text
- Query text
- Chunk boundaries
- Target/non-target semantic similarity
- Ranking position
- Cross-document distractors

**Priority cases:**

```
P0  eval_aws_regions_az_001
P0  eval_wiki_s3_features_001
P1  eval_aws_security_levels_001
```

Only after this inspection should a root-cause category be assigned.
