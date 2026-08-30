import hashlib
import json
from pathlib import Path
import re


def read_lines(path):
    lines = []

    with Path(path).open("r", encoding="utf-8-sig") as file:
        for line_number, raw_line in enumerate(file, start=1):
            lines.append({
                "line_number": line_number,
                "text": raw_line.rstrip("\r\n"),
            })

    return lines


def detect_line(text):
    stripped = text.strip()

    if not stripped:
        return "BLANK"

    if stripped.startswith("```"):
        return "CODE_FENCE"

    if stripped.startswith("#"):
        return "HEADING"

    if stripped.startswith("|") and stripped.endswith("|"):
        return "TABLE_ROW"

    if stripped.startswith(">"):
        return "QUOTE"

    if re.match(r'^(\d+[\.\)] |- |\+ |\* )', stripped):
        return "LIST_ITEM"

    return "TEXT"


def build_blocks(lines):
    raw_blocks = []
    current_block = None
    in_code_fence = False

    def flush_block():
        nonlocal current_block
        if current_block and current_block["lines"]:
            raw_blocks.append(current_block)
            current_block = None

    for line in lines:
        text = line["text"]
        kind = detect_line(text)

        if in_code_fence:
            current_block["lines"].append(line)
            current_block["end_line"] = line["line_number"]
            if kind == "CODE_FENCE":
                in_code_fence = False
                flush_block()
            continue

        if kind == "CODE_FENCE":
            flush_block()
            in_code_fence = True
            fence_str = text.strip().lstrip("`").strip()
            current_block = {
                "block_type": "code_block",
                "lines": [line],
                "start_line": line["line_number"],
                "end_line": line["line_number"],
                "language": fence_str if fence_str else "text",
            }
            continue

        if kind == "BLANK":
            flush_block()
            continue

        if kind == "TEXT":
            if current_block and current_block["block_type"] == "paragraph":
                current_block["lines"].append(line)
                current_block["end_line"] = line["line_number"]
            else:
                flush_block()
                current_block = {
                    "block_type": "paragraph",
                    "lines": [line],
                    "start_line": line["line_number"],
                    "end_line": line["line_number"],
                }
            continue

        # For single-line structures (HEADING, LIST_ITEM, TABLE_ROW, QUOTE)
        flush_block()
        raw_blocks.append({
            "block_type": kind.lower(),
            "lines": [line],
            "start_line": line["line_number"],
            "end_line": line["line_number"],
        })

    if in_code_fence or current_block:
        flush_block()

    return raw_blocks


def _parse_heading_level_and_text(text):
    stripped = text.strip()
    hash_count = 0
    for ch in stripped:
        if ch == "#":
            hash_count += 1
        else:
            break
    clean_text = stripped[hash_count:].strip()
    if not clean_text:
        clean_text = stripped
    level = max(2, hash_count + 1)
    return level, clean_text


def _parse_table_cells(text):
    parts = text.strip().strip("|").split("|")
    cells = []
    for col_idx, part in enumerate(parts, start=1):
        cells.append({
            "column_start": col_idx,
            "column_span": 1,
            "row_span": 1,
            "text": part.strip(),
        })
    return cells


def to_parsed_blocks(raw_blocks, document_id):
    parsed_blocks = []
    heading_stack = []
    list_counter = 0
    table_counter = 0

    for idx, raw in enumerate(raw_blocks, start=1):
        btype = raw["block_type"]
        raw_text_lines = [l["text"] for l in raw["lines"]]
        text_content = "\n".join(raw_text_lines)

        if not text_content.strip():
            continue

        if btype == "heading":
            level, clean_text = _parse_heading_level_and_text(text_content)
            while heading_stack and heading_stack[-1]["level"] >= level:
                heading_stack.pop()

            block_heading_path = [dict(h) for h in heading_stack]

            heading_stack.append({
                "level": level,
                "role": "generic",
                "text": clean_text,
            })
        else:
            block_heading_path = [dict(h) for h in heading_stack]

        if btype in ("heading", "paragraph", "title"):
            metadata = {}
        elif btype == "code_block":
            lang = raw.get("language", "text")
            metadata = {"language": lang if lang else "text"}
        elif btype == "list_item":
            list_counter += 1
            metadata = {
                "list_id": f"list_{list_counter}",
                "item_index": 1,
                "list_type": "unordered",
                "list_level": 0,
            }
        elif btype == "table_row":
            table_counter += 1
            cells = _parse_table_cells(text_content)
            metadata = {
                "table_id": f"table_{table_counter}",
                "row_index": 1,
                "cells": cells if cells else [{"column_start": 1, "column_span": 1, "row_span": 1, "text": text_content}],
            }
        elif btype == "quote":
            metadata = {"quote_level": 1}
        else:
            metadata = {}

        block_id_hash = hashlib.sha256(f"{document_id}:{idx}:{text_content}".encode()).hexdigest()[:32]
        block_id = f"{document_id}_b_{block_id_hash}"

        parsed_blocks.append({
            "schema_version": "1.0",
            "document_id": document_id,
            "block_id": block_id,
            "source_type": "txt",
            "block_index": idx,
            "source_order": idx,
            "block_type": btype,
            "text": text_content,
            "heading_path": block_heading_path,
            "related_asset_ids": [],
            "locator": {
                "type": "txt",
                "start_line": raw["start_line"],
                "end_line": raw["end_line"],
            },
            "metadata": metadata,
        })

    for i, pb in enumerate(parsed_blocks, start=1):
        pb["block_index"] = i
        pb["source_order"] = i

    return parsed_blocks


def parse_txt(file_path, document_id, output_dir):
    lines = read_lines(file_path)
    raw_blocks = build_blocks(lines)
    blocks = to_parsed_blocks(raw_blocks, document_id)

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
