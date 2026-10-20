"""Worker Configuration & Environment Loader.

Loads settings from .env file automatically using python-dotenv.
Fail-fast on missing mandatory AWS settings.
"""
import os
from pathlib import Path
from dotenv import load_dotenv

# Tự động nạp các biến từ file .env ở thư mục gốc
load_dotenv()

# ── 1. Env vars bắt buộc (Fail-fast nếu thiếu) ──────────────────────────────
AWS_REGION = os.environ["AWS_REGION"]
QUEUE_DOCUMENT_URL = os.environ["QUEUE_DOCUMENT_URL"]
QUEUE_INTERACTIVE_URL = os.environ["QUEUE_INTERACTIVE_URL"]
TABLE_JOBS = os.environ["TABLE_JOBS"]
TABLE_DOCUMENTS = os.environ["TABLE_DOCUMENTS"]
TABLE_WORKERS = os.environ["TABLE_WORKERS"]
BUCKET_DOCUMENT = os.environ["BUCKET_DOCUMENT"]

TABLE_MESSAGES = os.environ["TABLE_MESSAGES"]
TABLE_SESSIONS = os.environ["TABLE_SESSIONS"]
TABLE_SESSION_DOCUMENTS = os.environ["TABLE_SESSION_DOCUMENTS"]

# ── 2. Env vars có default ──────────────────────────────────────────────────
WORKER_ID = os.environ.get("WORKER_ID", "worker-local-1")
SQLITE_PATH = os.environ.get("SQLITE_PATH", "_data/studybot_index.db")
TEMP_DIR = os.environ.get("TEMP_DIR", "_data/tmp")
LOG_DIR = os.environ.get("LOG_DIR", "_data/logs")
EMBEDDING_MODEL = os.environ.get(
    "EMBEDDING_MODEL",
    "sentence-transformers/paraphrase-multilingual-mpnet-base-v2"
)
CHUNKER_STRATEGY = os.environ.get("CHUNKER_STRATEGY", "structure")
CHUNKER_MAX_TOKENS = int(os.environ.get("CHUNKER_MAX_TOKENS", 384))

# ── 3. Tự động tạo thư mục nếu chưa tồn tại ─────────────────────────────────
Path(TEMP_DIR).mkdir(parents=True, exist_ok=True)
Path(LOG_DIR).mkdir(parents=True, exist_ok=True)
Path(SQLITE_PATH).parent.mkdir(parents=True, exist_ok=True)

# ── 4. Config cho chunker (dict) ────────────────────────────────────────────
CHUNKER_CONFIG = {
    "max_tokens": CHUNKER_MAX_TOKENS,
}