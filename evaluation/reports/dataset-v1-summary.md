# StudyBot Evaluation Dataset v1 Summary

**Closure status:** `READY`

## Overview

| Metric | Value |
| --- | --- |
| Corpus entries | 7 |
| Ground-truth documents | 6 |
| Evaluation cases | 40 |
| Human-reviewed cases | 40 |
| Development cases | 30 |
| Test cases | 10 |
| Answerable cases | 32 |
| Unanswerable cases | 8 |
| Unanswerable ratio | 20.0% |

## Cases by document

| Document ID | Cases |
| --- | --- |
| docx_review_001 | 7 |
| md_interview_001 | 9 |
| pdf_aws_001 | 5 |
| pdf_dmls_001 | 10 |
| pptx_nlp_001 | 3 |
| txt_aiops_001 | 8 |

## Cases by category

| Category | Cases |
| --- | --- |
| cross_document_confusion | 1 |
| cross_lingual | 3 |
| direct_factual | 18 |
| lexical_mismatch | 2 |
| multi_document_synthesis | 1 |
| multi_section_synthesis | 6 |
| table_or_visual_limitation | 1 |
| unanswerable | 8 |

## Cases by query language

| Language | Cases |
| --- | --- |
| en | 35 |
| vi | 5 |

## Cases by answerability

| Answerability | Cases |
| --- | --- |
| ANSWERABLE | 32 |
| UNANSWERABLE | 8 |

## Closure blockers

- None.

## Warnings

- None.

## Development/test evidence overlap

No evidence overlap detected.

## Cross-split fact-similarity candidates

No high-similarity fact pairs detected.

## Duplicate queries

No duplicate normalized queries detected.

## Closure rule

Dataset v1 can be marked complete only when:

- All 40 cases are human-reviewed.
- Split contains 30 development and 10 test cases.
- All planned categories are represented.
- Every ground-truth document has evaluation coverage.
- No development/test evidence overlap remains.
- No duplicate query remains.
- Fact-similarity warnings have been manually reviewed.
