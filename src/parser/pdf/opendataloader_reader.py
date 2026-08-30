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

    elements = data.get("elements", [])
    sorted_elements = sorted(
        elements,
        key=lambda x: x.get("reading_order", 0)
    )
    return sorted_elements
