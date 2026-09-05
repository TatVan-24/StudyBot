# M2 — Chunker Evaluation Summary Report

**Run ID:** `m2-20260902-085738`  
**Date:** `2026-09-02T08:57:38.855634+00:00`  
**Input File:** `evaluation\bundle\blocks.jsonl` (SHA256: `a8ea97b93817d06d...`)  
**Tokenizer:** `Encoding` (`tiktoken_available`: `True`)

---

## 1. Executive Summary & Strategy Comparison

Evaluation of **FixedSizeChunker** (`fixed`) vs **StructureAwareChunker** (`structure`) on **242 real ParsedBlocks** from `evaluation\bundle\blocks.jsonl`.

| Metric | Fixed Strategy | Structure-Aware Strategy |
|---|---|---|
| **Config Budget** | `window_size: 256, overlap: 0.1` | `max_tokens: 256` |
| **Total Chunks Produced** | `28` | `39` |
| **Deterministic (`sha256`)** | `True` | `True` |
| **Token Min / Max / Mean** | `173 / 256 / 253.04` | `8 / 264 / 164.1` |
| **Token Median / P95** | `256.0 / 256.0` | `200.0 / 255.0` |
| **Chunks Over Budget (> 256)** | `0` | `1` |
| **Block Coverage** | `232/242` (95.87%) | `242/242` (100.00%) |
| **Duplicate Block Appearances** | `46` | `0` |
| **Heading Context Coverage** | `100.0%` (28/28) | `100.0%` (39/39) |
| **Empty Page Numbers (TXT)** | `28` | `39` |
| **Invariant Errors** | `PASS (0 errors)` | `PASS (0 errors)` |
| **Schema Violations** | `PASS (0 errors)` | `PASS (0 errors)` |

---

## 2. Token Length Distributions

### Token Bins Histogram
| Range | Fixed Count | Structure Count | Note |
|---|---|---|---|
| `0 - 64` | `0` | `8` | Short heading or list items |
| `65 - 128` | `0` | `5` | Standard paragraphs |
| `129 - 256` | `28` | `25` | Target window budget |
| `257 - 512` | `0` | `1` | Outliers exceeding budget |
| `> 512` | `0` | `0` | Large atomic blocks |

---

## 3. Data-Driven Findings

1. **Validation & Determinism:** Fixed strategy invariant errors: `0`; Structure strategy invariant errors: `0`. Re-run determinism test: `True`.
2. **Block Coverage:** Fixed strategy covers `232` unique blocks; Structure strategy covers `242` unique blocks out of `242` total blocks.
3. **Outlier Analysis (Over-Budget Chunks):** `StructureAwareChunker` produced `1` chunk(s) exceeding `256` tokens (max token length: `264`). This occurs because `StructureAwareChunker` treats individual `ParsedBlock` records atomically; if an atomic `ParsedBlock` length exceeds `max_tokens`, it is emitted without intra-block splitting.
4. **Heading Context & Page Numbers:** `100.0%` of structure chunks contain heading context trails. All `39` structure chunks have empty `page_numbers` because the source document is a plain text file (`source_type = "txt"`).

---

## 4. Verdict & Recommendation

**Verdict:** `EVIDENCE EVALUATED (M3 Baseline Selection)`


**FIXED:**      **REJECT** (10 blocks uncovered, coverage 95.87%)
**STRUCTURE:**  **CANDIDATE** (100% coverage; awaiting M4 retrieval metrics)
**BASELINE:**   **INSUFFICIENT EVIDENCE** for final M3 pick, pending M4
