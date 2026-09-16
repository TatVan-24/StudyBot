# M4 — Retrieval Depth Sweep

> **Diagnostic experiment** — NOT a modification to the M4 baseline contract.
> Baseline: K = [1, 3, 5, 10] | Sweep: K = [1, 3, 5, 10, 20, 50, 100]

## 1. Configuration

| Item | Value |
|---|---|
| Embedding model | sentence-transformers/paraphrase-multilingual-mpnet-base-v2 |
| Retrieval scope | Global Search (D5) |
| Sweep K values | [1, 3, 5, 10, 20, 50, 100] |
| Run timestamp | 2026-09-09T08:19:58.247156Z |
| Cases evaluated | 9 |

## 2. Pattern Summary

| Case | Target Blocks | Pattern | First Hit | Full Cov Rank |
|---|---:|---|---:|---:|
| eval_pdf_aws_s3_001 | 8 | PARTIAL     — partial retrieval, evidence missing even at Top-100 | #1 | — |
| eval_txt_observability_pillars_001 | 15 | PARTIAL     — partial retrieval, evidence missing even at Top-100 | #1 | — |
| eval_aws_security_levels_001 | 5 | PARTIAL     — partial retrieval, evidence missing even at Top-100 | #5 | — |
| eval_aws_regions_az_001 | 8 | DEEP_HIT    — evidence only appears past Rank-10 (ranking/alignment issue) | #33 | — |
| eval_txt_pipeline_stages_001 | 16 | PARTIAL     — partial retrieval, evidence missing even at Top-100 | #1 | — |
| eval_txt_kafka_recovery_001 | 26 | PARTIAL     — partial retrieval, evidence missing even at Top-100 | #1 | — |
| eval_aws_tenant_access_001 | 5 | PARTIAL     — partial retrieval, evidence missing even at Top-100 | #1 | — |
| eval_wiki_s3_pricing_001 | 1 | EARLY_FULL  — full coverage within Top-10 (strong retrieval) | #1 | #1 |
| eval_wiki_s3_features_001 | 3 | TOTAL_MISS  — no relevant evidence in Top-100 (embedding/representation issue) | — | — |

## 3. Per-Case Coverage Curves

### `eval_pdf_aws_s3_001`

- Query: *Amazon S3 lưu dữ liệu theo mô hình nào?*
- Target blocks: 8
- Pattern: **PARTIAL     — partial retrieval, evidence missing even at Top-100**
- First relevant chunk: Rank #1
- Full coverage: **Not achieved in Top-100**
- Uncovered blocks: `['pdf_aws_001_b_161272b777ad7cd0582ff340a3df4a9b']`

```
     K  Coverage  Bar
--------------------------------------------------
     1     25.0%  ███████
     3     25.0%  ███████
     5     25.0%  ███████
    10     25.0%  ███████
    20     25.0%  ███████
    50     50.0%  ███████████████
   100     87.5%  ██████████████████████████
```

### `eval_txt_observability_pillars_001`

- Query: *Which observability signal answers where a request became slow, and what trade-off does it have?*
- Target blocks: 15
- Pattern: **PARTIAL     — partial retrieval, evidence missing even at Top-100**
- First relevant chunk: Rank #1
- Full coverage: **Not achieved in Top-100**
- Uncovered blocks: `['txt_aiops_001_b_64db1d3c1afa8069361134dc45f75763', 'txt_aiops_001_b_a4dd43ed3df50e480deb141bcfd1f8b2']`

```
     K  Coverage  Bar
--------------------------------------------------
     1     26.7%  ████████
     3     33.3%  █████████
     5     53.3%  ███████████████
    10     53.3%  ███████████████
    20     53.3%  ███████████████
    50     53.3%  ███████████████
   100     86.7%  ██████████████████████████
```

### `eval_aws_security_levels_001`

- Query: *What are the two levels of data security described in Learning AWS?*
- Target blocks: 5
- Pattern: **PARTIAL     — partial retrieval, evidence missing even at Top-100**
- First relevant chunk: Rank #5
- Full coverage: **Not achieved in Top-100**
- Uncovered blocks: `['pdf_aws_001_b_5b2edf7db33d318502cb9e84be12f057', 'pdf_aws_001_b_37785785343b8fa73619670eb322c634', 'pdf_aws_001_b_64309e6ab78c99f193ef224ba270d7fc']`

```
     K  Coverage  Bar
--------------------------------------------------
     1      0.0%  
     3      0.0%  
     5     20.0%  ██████
    10     40.0%  ████████████
    20     40.0%  ████████████
    50     40.0%  ████████████
   100     40.0%  ████████████
```

### `eval_aws_regions_az_001`

- Query: *How does the passage relate AWS Regions and Availability Zones for EC2 deployment?*
- Target blocks: 8
- Pattern: **DEEP_HIT    — evidence only appears past Rank-10 (ranking/alignment issue)**
- First relevant chunk: Rank #33
- Full coverage: **Not achieved in Top-100**
- Uncovered blocks: `['pdf_aws_001_b_ecc3bb87babc5d271682eabae943b9f2', 'pdf_aws_001_b_0edece00ab3e14367e28484abd6deff9', 'pdf_aws_001_b_161272b777ad7cd0582ff340a3df4a9b', 'pdf_aws_001_b_c6e51c170ab28733006ffe25d57188ca', 'pdf_aws_001_b_469765fec4d08e465a17fffaaff9c686']`

```
     K  Coverage  Bar
--------------------------------------------------
     1      0.0%  
     3      0.0%  
     5      0.0%  
    10      0.0%  
    20      0.0%  
    50     25.0%  ███████
   100     25.0%  ███████
```

### `eval_txt_pipeline_stages_001`

- Query: *What are the five main stages after Service in the observability data pipeline?*
- Target blocks: 16
- Pattern: **PARTIAL     — partial retrieval, evidence missing even at Top-100**
- First relevant chunk: Rank #1
- Full coverage: **Not achieved in Top-100**
- Uncovered blocks: `['txt_aiops_001_b_18d51034a9f4e2a8e44aac88af3e9a81', 'txt_aiops_001_b_c99861bc1c7e9195849363bfcb9e5072', 'txt_aiops_001_b_39caa2182cd53b94ca2220273c1781bc', 'txt_aiops_001_b_27c2cbe7a0aaadfa178b023fce27a848', 'txt_aiops_001_b_b3011b94af793565e3b7ee429b9324ef']`

```
     K  Coverage  Bar
--------------------------------------------------
     1     18.8%  █████
     3     18.8%  █████
     5     18.8%  █████
    10     18.8%  █████
    20     18.8%  █████
    50     37.5%  ███████████
   100     37.5%  ███████████
```

### `eval_txt_kafka_recovery_001`

- Query: *How does Kafka help when downstream observability storage fails?*
- Target blocks: 26
- Pattern: **PARTIAL     — partial retrieval, evidence missing even at Top-100**
- First relevant chunk: Rank #1
- Full coverage: **Not achieved in Top-100**
- Uncovered blocks: `['txt_aiops_001_b_60fb1de0c71d6c6164ee5c45a554311a', 'txt_aiops_001_b_267b8261b449841d4b5c14e6bef40495', 'txt_aiops_001_b_ce16052b9eab018ea853a42850bad92d', 'txt_aiops_001_b_d9bb763edaaa1337ca1ccb1945b0759e']`

```
     K  Coverage  Bar
--------------------------------------------------
     1     15.4%  ████
     3     23.1%  ██████
     5     42.3%  ████████████
    10     73.1%  █████████████████████
    20     73.1%  █████████████████████
    50     80.8%  ████████████████████████
   100     84.6%  █████████████████████████
```

### `eval_aws_tenant_access_001`

- Query: *How does the described design restrict tenant and end-user access to data?*
- Target blocks: 5
- Pattern: **PARTIAL     — partial retrieval, evidence missing even at Top-100**
- First relevant chunk: Rank #1
- Full coverage: **Not achieved in Top-100**
- Uncovered blocks: `['pdf_aws_001_b_5b2edf7db33d318502cb9e84be12f057']`

```
     K  Coverage  Bar
--------------------------------------------------
     1     20.0%  ██████
     3     40.0%  ████████████
     5     60.0%  ██████████████████
    10     60.0%  ██████████████████
    20     60.0%  ██████████████████
    50     60.0%  ██████████████████
   100     80.0%  ████████████████████████
```

### `eval_wiki_s3_pricing_001`

- Query: *What is the price per GB for the Glacier storage class?*
- Target blocks: 1
- Pattern: **EARLY_FULL  — full coverage within Top-10 (strong retrieval)**
- First relevant chunk: Rank #1
- Full coverage at: Rank #1

```
     K  Coverage  Bar
--------------------------------------------------
     1    100.0%  ██████████████████████████████
     3    100.0%  ██████████████████████████████
     5    100.0%  ██████████████████████████████
    10    100.0%  ██████████████████████████████
    20    100.0%  ██████████████████████████████
    50    100.0%  ██████████████████████████████
   100    100.0%  ██████████████████████████████
```

### `eval_wiki_s3_features_001`

- Query: *Những tính năng cốt lõi (core features) của Amazon S3 là gì?*
- Target blocks: 3
- Pattern: **TOTAL_MISS  — no relevant evidence in Top-100 (embedding/representation issue)**
- First relevant chunk: **None in Top-100**
- Full coverage: **Not achieved in Top-100**
- Uncovered blocks: `['wiki_06_markdown_sample_b_58d21ed73e8210ee76ad0b86600f151a', 'wiki_06_markdown_sample_b_75c4ea1fd6d2e216eb1f05b89ecdd55f', 'wiki_06_markdown_sample_b_c6672b8f15ea97c2ba1af94a4367b653']`

```
     K  Coverage  Bar
--------------------------------------------------
     1      0.0%  
     3      0.0%  
     5      0.0%  
    10      0.0%  
    20      0.0%  
    50      0.0%  
   100      0.0%  
```

## 4. Root-Cause Investigation Guide

Based on the pattern observed per case:

| Pattern | Investigation Priority |
|---|---|
| TOTAL_MISS | Query ↔ Target embedding similarity; chunk boundary; ingestion |
| DEEP_HIT | Ranking / semantic alignment / distractor competition |
| PARTIAL | Evidence granularity; multi-block span vs chunk size |
| PLATEAU_LOW | Redundancy in top results; evidence fragmented across corpus |
| EARLY_FULL | No issue — use as control case |

> **Next step**: Pick 1 TOTAL_MISS and 1 DEEP_HIT case.
> Read `query text`, `target block text`, and `top-3 retrieved chunk text` side-by-side.
> Only after text-level inspection should a root-cause hypothesis be formed.
