import hashlib
import json
from pathlib import Path
from src.parser.pdf.opendataloader_reader import load_opendataloader_json
from src.parser.block_id import (
    compute_block_id,
    build_canonical_native_content,
)


def _map_semantic_type(type_str):
    t = str(type_str).lower().strip()
    if t in ("heading", "header", "title"):
        return "heading"
    if t in ("code", "code_block", "program"):
        return "code_block"
    if t in ("list", "list_item"):
        return "list_item"
    if t in ("table", "table_row"):
        return "table_row"
    if t in ("quote", "blockquote"):
        return "quote"
    return "paragraph"


def adapt_opendataloader_json_to_parsed_blocks(json_source, document_id):
    elements = load_opendataloader_json(json_source)
    parsed_blocks = []
    heading_stack = []
    list_counter = 0
    table_counter = 0
    list_state = None
    table_state = None

    for idx, elem in enumerate(elements, start=1):
        raw_text = str(elem.get("text", "")).strip()
        if not raw_text:
            continue

        raw_type = elem.get("type", "paragraph")
        btype = _map_semantic_type(raw_type)

        # Logical grouping boundary
        if btype != "list_item":
            list_state = None
        if btype != "table_row":
            table_state = None

        if btype == "heading":
            clean_text = raw_text.lstrip("#").strip()
            level = max(2, elem.get("level", 2))
            while heading_stack and heading_stack[-1]["level"] >= level:
                heading_stack.pop()
            heading_stack.append({
                "level": level,
                "role": "generic",
                "text": clean_text if clean_text else raw_text,
            })
            block_heading_path = [dict(h) for h in heading_stack]

        else:
            block_heading_path = [dict(h) for h in heading_stack]

        if btype in ("heading", "paragraph", "title"):
            metadata = {}
        elif btype == "code_block":
            metadata = {"language": elem.get("language", "text")}
        elif btype == "list_item":
            if list_state is None:
                list_counter += 1
                list_state = {
                    "list_id": f"list_{list_counter}",
                    "list_type": "unordered",
                    "list_level": 0,
                    "next_item_index": 1,
                }
            item_index = list_state["next_item_index"]
            list_state["next_item_index"] += 1
            metadata = {
                "list_id": list_state["list_id"],
                "item_index": item_index,
                "list_type": list_state["list_type"],
                "list_level": list_state["list_level"],
            }
        elif btype == "table_row":
            if table_state is None:
                table_counter += 1
                table_state = {
                    "table_id": f"table_{table_counter}",
                    "next_row_index": 1,
                }
            row_index = table_state["next_row_index"]
            table_state["next_row_index"] += 1
            cells_raw = elem.get("cells", [])
            cells = []
            for col_idx, cell in enumerate(cells_raw, start=1):
                cells.append({
                    "column_start": col_idx,
                    "column_span": 1,
                    "row_span": 1,
                    "text": str(cell).strip(),
                })
            metadata = {
                "table_id": table_state["table_id"],
                "row_index": row_index,
                "cells": cells if cells else [
                    {"column_start": 1, "column_span": 1, "row_span": 1, "text": raw_text}
                ],
            }
        elif btype == "quote":
            metadata = {"quote_level": 1}
        else:
            metadata = {}

        bbox = elem.get("bounding_box", [])
        bounding_boxes = []
        if isinstance(bbox, (list, tuple)) and len(bbox) == 4:
            bounding_boxes.append({
                "x_min": float(bbox[0]),
                "y_min": float(bbox[1]),
                "x_max": float(bbox[2]),
                "y_max": float(bbox[3]),
            })

        pdf_page = int(elem.get("page_number", 1))

        # canonical_locator per §6.2: type, pdf_pages, occurrence_index
        canonical_locator = {
            "type": "pdf",
            "pdf_pages": [pdf_page],
            "occurrence_index": 1,
        }
        canonical_native_content = build_canonical_native_content(
            btype, raw_text, metadata, block_heading_path
        )
        block_id = compute_block_id(
            document_id, "pdf", btype, canonical_locator, canonical_native_content
        )

        parsed_blocks.append({
            "schema_version": "1.0",
            "document_id": document_id,
            "block_id": block_id,
            "source_type": "pdf",
            "block_index": idx,
            "source_order": idx,
            "block_type": btype,
            "text": raw_text,
            "heading_path": block_heading_path,
            "related_asset_ids": [],
            "locator": {
                "type": "pdf",
                "occurrence_index": 1,
                "locations": [{
                    "pdf_page": pdf_page,
                    "printed_page": None,
                    "bounding_boxes": bounding_boxes,
                }],
            },
            "metadata": metadata,
        })

    for i, pb in enumerate(parsed_blocks, start=1):
        pb["block_index"] = i
        pb["source_order"] = i

    return parsed_blocks



def parse_pdf_bundle(json_source, document_id, output_dir):
    blocks = adapt_opendataloader_json_to_parsed_blocks(json_source, document_id)

    out_path = Path(output_dir)
    out_path.mkdir(parents=True, exist_ok=True)

    manifest = {"document_id": document_id}
    with (out_path / "manifest.json").open("w", encoding="utf-8") as f:
        json.dump(manifest, f, indent=2)

    with (out_path / "blocks.jsonl").open("w", encoding="utf-8") as f:
        for block in blocks:
            f.write(json.dumps(block, ensure_ascii=False) + "\n")

    for filename in ("assets.jsonl", "links.jsonl", "issues.jsonl"):
        (out_path / filename).touch(exist_ok=True)

    return blocks
