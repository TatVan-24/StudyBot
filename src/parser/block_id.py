"""Shared block_id canonicalization per contract §6.2.

block_id = sha256(canonical_json({
    document_id, source_type, block_type,
    canonical_locator, canonical_native_content
}))[:32]

Excludes from hash (§6.2 dòng 431-442):
  block_index, source_order, list_id, item_index, table_id,
  heading_path ancestors, related_asset_ids, parse_job_id, created_at
"""

import hashlib
import json
import unicodedata


# ── Text normalization ──────────────────────────────────────────────

def normalize_text(text):
    """Canonical text: LF line endings, Unicode NFC, outer whitespace stripped."""
    text = text.replace("\r\n", "\n").replace("\r", "\n")
    text = unicodedata.normalize("NFC", text)
    return text.strip()


def normalize_code(code):
    """Canonical code: LF line endings, Unicode NFC; preserves indentation."""
    code = code.replace("\r\n", "\n").replace("\r", "\n")
    code = unicodedata.normalize("NFC", code)
    return code


def canonical_json(obj):
    """Deterministic JSON: sorted keys, compact separators."""
    return json.dumps(obj, sort_keys=True, ensure_ascii=False, separators=(",", ":"))


# ── block_id computation ────────────────────────────────────────────

def compute_block_id(document_id, source_type, block_type,
                     canonical_locator, canonical_native_content):
    payload = {
        "document_id": document_id,
        "source_type": source_type,
        "block_type": block_type,
        "canonical_locator": canonical_locator,
        "canonical_native_content": canonical_native_content,
    }
    digest = hashlib.sha256(
        canonical_json(payload).encode("utf-8")
    ).hexdigest()[:32]
    return f"{document_id}_b_{digest}"


# ── Canonical native content per block_type (§6.2 dòng 384-392) ────

def build_canonical_native_content(block_type, text_content, metadata, heading_path):
    """Block-type-aware canonical native content.

    heading_path[−1] is the block's own heading (for block_type=heading)
    or the nearest containing heading (for other types).
    """
    if block_type in ("title", "paragraph"):
        return normalize_text(text_content)

    if block_type == "heading":
        final = heading_path[-1]
        return {
            "text": normalize_text(text_content),
            "level": final["level"],
            "role": final["role"],
        }

    if block_type == "list_item":
        canonical = {
            "text": normalize_text(text_content),
            "list_type": metadata["list_type"],
            "list_level": metadata["list_level"],
        }
        if "marker" in metadata:
            canonical["marker"] = metadata["marker"]
        return canonical

    if block_type == "table_row":
        cells = []
        for cell in metadata["cells"]:
            cells.append({
                "column_start": cell["column_start"],
                "column_span": cell["column_span"],
                "row_span": cell["row_span"],
                "text": normalize_text(cell["text"]),
            })
        return {"cells": cells}

    if block_type == "caption":
        return {
            "text": normalize_text(text_content),
            "caption_kind": metadata["caption_kind"],
        }

    if block_type == "code_block":
        canonical = {"code": normalize_code(text_content)}
        if "language" in metadata:
            canonical["language"] = metadata["language"].strip().lower()
        return canonical

    if block_type == "quote":
        return {
            "text": normalize_text(text_content),
            "quote_level": metadata["quote_level"],
        }

    return normalize_text(text_content)
