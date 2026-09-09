import json
from pathlib import Path


def load_opendataloader_json(json_source):
    """
    Nạp dữ liệu Structured JSON từ OpenDataLoader PDF (dạng dict hoặc đường dẫn file .json).
    Sắp xếp các element theo thứ tự đọc (reading_order).
    """
    if isinstance(json_source, (str, Path)):
        path = Path(json_source)
        with path.open("r", encoding="utf-8") as f:
            data = json.load(f)
    elif isinstance(json_source, dict):
        data = json_source
    else:
        raise ValueError("json_source phải là dict hoặc đường dẫn file JSON hợp lệ")

    kids = data.get("kids", [])
    elements = []
    
    def process_kid(kid):
        ktype = kid.get("type", "").lower()
        page = kid.get("page number", 1)
        bbox = kid.get("bounding_box", [])
        order = kid.get("reading_order", 0)
        
        if ktype == "list":
            for li in kid.get("list items", []):
                elements.append({
                    "type": "list_item",
                    "text": li.get("content", ""),
                    "page_number": li.get("page number", page),
                    "bounding_box": li.get("bounding_box", bbox),
                    "reading_order": li.get("reading_order", order)
                })
            return
            
        if ktype == "table":
            for row in kid.get("rows", []):
                cells = row.get("cells", [])
                cells_content = [c.get("content", "") if isinstance(c, dict) else str(c) for c in cells]
                elements.append({
                    "type": "table_row",
                    "text": " | ".join(cells_content),
                    "cells": cells_content,
                    "page_number": page,
                    "bounding_box": bbox,
                    "reading_order": order
                })
            return

        elements.append({
            "type": ktype,
            "text": kid.get("content", ""),
            "level": kid.get("heading level", 2),
            "page_number": page,
            "bounding_box": bbox,
            "reading_order": order
        })

    for kid in kids:
        process_kid(kid)

    sorted_elements = sorted(
        elements,
        key=lambda x: x.get("reading_order", 0)
    )
    return sorted_elements
