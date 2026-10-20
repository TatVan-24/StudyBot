"""Structured Logger for Local Worker.

Outputs human-readable text to stdout in real-time.
Appends machine-parseable JSONL records to _data/logs/worker-YYYY-MM-DD.jsonl.
"""
import json
from datetime import datetime, timezone
from pathlib import Path
from src.worker.config import LOG_DIR


def _log_file_path() -> Path:
    """Tạo đường dẫn file log theo ngày hiện tại dạng UTC (worker-YYYY-MM-DD.jsonl)."""
    today = datetime.now(timezone.utc).strftime("%Y-%m-%d")
    return Path(LOG_DIR) / f"worker-{today}.jsonl"


def log_event(level: str, event: str, **fields):
    """Ghi log đồng thời ra cả terminal (human-readable) và file JSONL (structured)."""
    ts = datetime.now(timezone.utc).isoformat()
    
    # 1. Tạo dict bản ghi hoàn chỉnh
    record = {
        "ts": ts,
        "level": level,
        "event": event,
        **fields,
    }

    # 2. In ra màn hình console (căn lề dễ đọc)
    fields_str = " ".join(f"{k}={v}" for k, v in fields.items())
    print(f"[{ts}] {level:<8} {event:<20} {fields_str}".rstrip())

    # 3. Ghi nối tiếp vào file JSONL theo ngày (mỗi log 1 dòng)
    file_path = _log_file_path()
    with open(file_path, "a", encoding="utf-8") as f:
        f.write(json.dumps(record, ensure_ascii=False) + "\n")


# ── Các hàm tiện lợi gọi nhanh ──────────────────────────────────────────────
def log_info(event: str, **fields):
    log_event("INFO", event, **fields)


def log_warn(event: str, **fields):
    log_event("WARNING", event, **fields)


def log_error(event: str, **fields):
    log_event("ERROR", event, **fields)