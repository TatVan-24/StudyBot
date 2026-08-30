# Parser Contract v1 — Conformance Cases

## 1. Purpose

These ten cases test the frozen Parser Contract, not parser extraction accuracy against real source files.

```mermaid
flowchart LR
    C[Contract case] --> F[Field rules]
    F --> X[Cross-field rules]
    X --> R[Cross-record rules]
    R --> E[Expected VALID or INVALID]
```

The hexadecimal `block_id` and `asset_id` values are stable fixture identifiers for design-level conformance examples. Executable fixtures will recompute deterministic IDs after the JSON canonical serializer is implemented.

## 2. Valid cases

### VALID-01 — PDF paragraph

Expected: `VALID`.

```json
{
  "schema_version": "1.0",
  "document_id": "pdf_case_001",
  "block_id": "pdf_case_001_b_11111111111111111111111111111111",
  "source_type": "pdf",
  "block_index": 1,
  "source_order": 1,
  "block_type": "paragraph",
  "text": "Amazon S3 is object storage.",
  "heading_path": [],
  "related_asset_ids": [],
  "locator": {
    "type": "pdf",
    "occurrence_index": 1,
    "locations": [
      {
        "pdf_page": 10,
        "printed_page": "8",
        "bounding_boxes": []
      }
    ]
  },
  "metadata": {}
}
```

Proves PDF page provenance, occurrence identity, empty relationships, and paragraph metadata.

### VALID-02 — PPTX list item

Expected: `VALID`.

```json
{
  "schema_version": "1.0",
  "document_id": "pptx_case_001",
  "block_id": "pptx_case_001_b_22222222222222222222222222222222",
  "source_type": "pptx",
  "block_index": 1,
  "source_order": 1,
  "block_type": "list_item",
  "text": "Amazon S3",
  "heading_path": [
    {"level": 2, "role": "slide", "text": "AWS Storage"}
  ],
  "related_asset_ids": [],
  "locator": {
    "type": "pptx",
    "element_type": "text_paragraph",
    "slide": 4,
    "shape_path": [2],
    "shape_id": 102,
    "physical_paragraph_index": 1,
    "shape_bounding_box": null
  },
  "metadata": {
    "list_id": "pptx_case_001_list_001",
    "item_index": 1,
    "list_type": "unordered",
    "list_level": 0,
    "marker": "•"
  }
}
```

Proves logical list metadata can use a physical PPTX text-paragraph locator.

### VALID-03 — DOCX table row

Expected: `VALID`.

```json
{
  "schema_version": "1.0",
  "document_id": "docx_case_001",
  "block_id": "docx_case_001_b_33333333333333333333333333333333",
  "source_type": "docx",
  "block_index": 1,
  "source_order": 1,
  "block_type": "table_row",
  "text": "Service\tPurpose",
  "heading_path": [],
  "related_asset_ids": [],
  "locator": {
    "type": "docx",
    "element_type": "table_row",
    "body_child_index": 5,
    "physical_row_index": 1
  },
  "metadata": {
    "table_id": "docx_case_001_table_001",
    "row_index": 1,
    "cells": [
      {"column_start": 1, "column_span": 1, "row_span": 1, "text": "Service"},
      {"column_start": 2, "column_span": 1, "row_span": 1, "text": "Purpose"}
    ]
  }
}
```

Proves physical/logical row separation and deterministic tab-separated table text.

### VALID-04 — Markdown code block

Expected: `VALID`.

```json
{
  "schema_version": "1.0",
  "document_id": "md_case_001",
  "block_id": "md_case_001_b_44444444444444444444444444444444",
  "source_type": "markdown",
  "block_index": 1,
  "source_order": 1,
  "block_type": "code_block",
  "text": "print(\"hello\")",
  "heading_path": [],
  "related_asset_ids": [],
  "locator": {
    "type": "markdown",
    "start_line": 10,
    "end_line": 12
  },
  "metadata": {
    "language": "python"
  }
}
```

Proves a fenced construct span and canonical explicit language declaration.

### VALID-05 — TXT paragraph

Expected: `VALID`.

```json
{
  "schema_version": "1.0",
  "document_id": "txt_case_001",
  "block_id": "txt_case_001_b_55555555555555555555555555555555",
  "source_type": "txt",
  "block_index": 1,
  "source_order": 1,
  "block_type": "paragraph",
  "text": "Kafka buffers telemetry for downstream consumers.",
  "heading_path": [],
  "related_asset_ids": [],
  "locator": {
    "type": "txt",
    "start_line": 7,
    "end_line": 7
  },
  "metadata": {}
}
```

Proves conservative one-line TXT provenance and empty paragraph metadata.

## 3. Invalid cases

Each invalid case is derived from a valid baseline and changes only the data needed to violate the named invariant.

### INVALID-01 — Metadata variant mismatch

Derived from `VALID-05`. Expected: `INVALID_METADATA_VARIANT`.

```json
{
  "block_type": "paragraph",
  "metadata": {
    "list_level": 0
  }
}
```

Reason: paragraph metadata must be exactly `{}`.

### INVALID-02 — PPTX locator variant mismatch

Derived from `VALID-02`. All omitted fields remain unchanged. Expected: `INVALID_LOCATOR_VARIANT`.

```json
{
  "block_type": "list_item",
  "locator": {
    "type": "pptx",
    "element_type": "table_row",
    "slide": 4,
    "shape_path": [2],
    "shape_id": 102,
    "physical_row_index": 1,
    "shape_bounding_box": null
  }
}
```

Reason: a PPTX non-table block must use `element_type = text_paragraph`.

### INVALID-03 — Heading self-structure mismatch

Expected: `INVALID_HEADING_SELF_STRUCTURE`.

```json
{
  "schema_version": "1.0",
  "document_id": "md_case_heading_001",
  "block_id": "md_case_heading_001_b_66666666666666666666666666666666",
  "source_type": "markdown",
  "block_index": 1,
  "source_order": 1,
  "block_type": "heading",
  "text": "AWS Storage",
  "heading_path": [
    {"level": 2, "role": "generic", "text": "AWS Compute"}
  ],
  "related_asset_ids": [],
  "locator": {
    "type": "markdown",
    "start_line": 1,
    "end_line": 1
  },
  "metadata": {}
}
```

Reason: the final heading-path item does not describe the heading block's own text.

### INVALID-04 — Asymmetric block–asset relationship

Expected: `ASYMMETRIC_BLOCK_ASSET_RELATIONSHIP`.

```json
{
  "document_id": "pdf_case_relation_001",
  "blocks": [
    {
      "schema_version": "1.0",
      "document_id": "pdf_case_relation_001",
      "block_id": "pdf_case_relation_001_b_77777777777777777777777777777777",
      "source_type": "pdf",
      "block_index": 1,
      "source_order": 1,
      "block_type": "paragraph",
      "text": "The architecture is shown below.",
      "heading_path": [],
      "related_asset_ids": ["pdf_case_relation_001_a_001"],
      "locator": {
        "type": "pdf",
        "occurrence_index": 1,
        "locations": [
          {"pdf_page": 2, "printed_page": "1", "bounding_boxes": []}
        ]
      },
      "metadata": {}
    }
  ],
  "assets": [
    {
      "schema_version": "1.0",
      "document_id": "pdf_case_relation_001",
      "asset_id": "pdf_case_relation_001_a_001",
      "source_order": 2,
      "asset_type": "image",
      "media_type": "image/png",
      "locator": {
        "type": "pdf",
        "locations": [
          {"pdf_page": 2, "printed_page": "1", "bounding_boxes": []}
        ]
      },
      "native_context": {
        "alt_text": null,
        "caption": null,
        "related_block_ids": []
      },
      "extraction": {
        "status": "DETECTED_ONLY"
      }
    }
  ]
}
```

Reason: the block references the asset, but the asset does not reverse-reference the block.

### INVALID-05 — Logical block-index gap

Expected: `INVALID_BLOCK_INDEX_SEQUENCE`.

```json
{
  "document_id": "txt_case_index_001",
  "blocks": [
    {
      "schema_version": "1.0",
      "document_id": "txt_case_index_001",
      "block_id": "txt_case_index_001_b_88888888888888888888888888888888",
      "source_type": "txt",
      "block_index": 1,
      "source_order": 1,
      "block_type": "paragraph",
      "text": "First paragraph.",
      "heading_path": [],
      "related_asset_ids": [],
      "locator": {"type": "txt", "start_line": 1, "end_line": 1},
      "metadata": {}
    },
    {
      "schema_version": "1.0",
      "document_id": "txt_case_index_001",
      "block_id": "txt_case_index_001_b_99999999999999999999999999999999",
      "source_type": "txt",
      "block_index": 3,
      "source_order": 2,
      "block_type": "paragraph",
      "text": "Second paragraph.",
      "heading_path": [],
      "related_asset_ids": [],
      "locator": {"type": "txt", "start_line": 3, "end_line": 3},
      "metadata": {}
    }
  ]
}
```

Reason: `block_index` must be the contiguous sequence `1..N`; physical source lines may still contain gaps.

## 4. Closure result

Coverage:

| Case group | Contract surface |
| --- | --- |
| Five valid cases | PDF, PPTX, DOCX, Markdown, and TXT record compatibility |
| Invalid metadata | `block_type` to metadata discriminator |
| Invalid locator | `block_type` to physical locator variant |
| Invalid heading | Heading self-structure invariant |
| Invalid relation | Cross-record symmetry |
| Invalid index | Logical/output index contiguity |

Design-level expected result:

```text
5 VALID cases   → accepted
5 INVALID cases → rejected for their named reason
```

No case requires a new field, a reinterpretation of a frozen rule, or a new feature. Final Consistency Review passes at the design level, and ParsedBlock Contract v1 is frozen. Executable schema and bundle validation are the next implementation step.
