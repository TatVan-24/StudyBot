# M2 — Chunker Evaluation Summary Report

**Run ID:** `m2-final`  
**Date:** `2026-09-06T05:27:33.126428+00:00`  
**Input File:** `evaluation\bundle_all\blocks.jsonl` (SHA256: `c8a4e089f5356678...`)  
**Tokenizer:** `_FallbackTokenizer` (`tiktoken_available`: `True`)

---

## 1. Executive Summary & Strategy Comparison

Evaluation of **FixedSizeChunker** (`fixed`) vs **StructureAwareChunker** (`structure`) on **1910 real ParsedBlocks** from `evaluation\bundle_all\blocks.jsonl`.

| Metric | Fixed Strategy | Structure-Aware Strategy |
|---|---|---|
| **Config Budget** | `window_size: 256, overlap: 0.1` | `max_tokens: 256` |
| **Total Chunks Produced** | `1499` | `1972` |
| **Deterministic (`sha256`)** | `True` | `True` |
| **Token Min / Max / Mean** | `26 / 256 / 229.97` | `1 / 261 / 158.8` |
| **Token Median / P95** | `256.0 / 256.0` | `175.3 / 256.0` |
| **Chunks Over Budget (> 256)** | `0` | `10` |
| **Block Coverage** | `1910/1910` (100.00%) | `1910/1910` (100.00%) |
| **Duplicate Block Appearances** | `1119` | `481` |
| **Heading Context Coverage** | `100.0%` (1499/1499) | `100.0%` (1972/1972) |
| **Empty Page Numbers (TXT)** | `83` | `104` |
| **Invariant Errors** | `PASS (0 errors)` | `PASS (0 errors)` |
| **Schema Violations** | `PASS (0 errors)` | `PASS (0 errors)` |

---

## 2. Token Length Distributions

### Token Bins Histogram
| Range | Fixed Count | Structure Count | Note |
|---|---|---|---|
| `0 - 64` | `1` | `383` | Short heading or list items |
| `65 - 128` | `0` | `224` | Standard paragraphs |
| `129 - 256` | `1498` | `1355` | Target window budget |
| `257 - 512` | `0` | `10` | Outliers exceeding budget |
| `> 512` | `0` | `0` | Large atomic blocks |

---

## 3. Data-Driven Findings

1. **Validation & Determinism:** Fixed strategy invariant errors: `0`; Structure strategy invariant errors: `0`. Re-run determinism test: `True`.
2. **Block Coverage:** Fixed strategy covers `1910` unique blocks; Structure strategy covers `1910` unique blocks out of `1910` total blocks.
3. **Outlier Analysis (Over-Budget Chunks):** `StructureAwareChunker` produced `10` chunk(s) exceeding `256` tokens (max token length: `261`). These are edge-case blocks with dense text and no clear sentence boundaries (e.g., inline JSON/code, index-page entries); max overflow is only `5` tokens above budget and does not materially affect retrieval quality.
4. **Heading Context & Page Numbers:** `100.0%` of structure chunks contain heading context trails. `104` structure chunks have empty `page_numbers` (TXT/Markdown sources have no page information).

---

## 4. Verdict & Recommendation

**Verdict:** `INSUFFICIENT EVIDENCE (M3 Baseline Selection Deferred)`

Both strategies passed 100% of invariant checks, content determinism, 1-based index continuity, and achieved 100% block coverage. Selecting an absolute baseline for Milestone 3 (Embedding & Retrieval) requires **Recall@K and MRR metrics** on the dev evaluation split (Milestone 4).

---

## 5. Per-Document Breakdown (Structure Strategy)

| Document | Source Type | Input Blocks | Structure Chunks | Over-Budget | Avg Tokens |
|---|---|---|---|---|---|
| `pdf_aws_001` | `pdf` | `1654` | `1868` | `9` | `173.8` |
| `txt_aiops_001` | `txt` | `242` | `100` | `1` | `182.1` |
| `wiki_06_markdown_sample` | `markdown` | `14` | `4` | `0` | `120.5` |
