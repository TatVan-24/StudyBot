"""Document Ingestion Handler.

Orchestrates the complete pipeline:
S3 Download -> OpenDataLoader PDF Convert (with pypdf fallback) -> Structure-Aware Chunker -> MPNet Embedder -> SQLite Vector Store.
"""
import json
import tempfile
import shutil
from dataclasses import asdict
from datetime import datetime, timezone
from pathlib import Path
from typing import Optional

import boto3
# pyrefly: ignore [missing-import]
import opendataloader_pdf
from pypdf import PdfReader

from src.worker.config import (
    BUCKET_DOCUMENT,
    TEMP_DIR,
    CHUNKER_STRATEGY,
    CHUNKER_CONFIG,
)
from src.worker.logger import log_info, log_warn, log_error
from src.rag_pipeline.parser.pdf.pdf_adapter import (
    adapt_opendataloader_json_to_parsed_blocks,
)
from src.rag_pipeline.parser.text.txt_parser import build_blocks, to_parsed_blocks
from src.rag_pipeline.chunker.chunker import get_chunker
from src.rag_pipeline.indexer.schema import IndexMeta


def _download_pdf(s3_client, s3_key: str) -> Path:
    """Tải file PDF từ S3 về file tạm cục bộ với tên ngẫu nhiên."""
    temp_dir_path = Path(TEMP_DIR)
    temp_dir_path.mkdir(parents=True, exist_ok=True)

    tmp_file = tempfile.NamedTemporaryFile(
        dir=temp_dir_path,
        suffix=".pdf",
        delete=False,
    )
    tmp_path = Path(tmp_file.name)
    tmp_file.close()

    s3_client.download_file(
        Bucket=BUCKET_DOCUMENT,
        Key=s3_key,
        Filename=str(tmp_path),
    )
    return tmp_path


def _parse_pdf_to_blocks(pdf_path: Path, document_id: str) -> list:
    """Phân tích PDF: dùng OpenDataLoader convert sang JSON, tự động dọn dẹp và fallback về pypdf nếu cần."""
    output_dir = pdf_path.parent
    expected_json_file = output_dir / f"{pdf_path.stem}.json"

    # 1. Chạy OpenDataLoader convert sang file JSON
    try:
        opendataloader_pdf.convert(
            input_path=str(pdf_path),
            output_dir=str(output_dir),
            format=["json"],
            keep_line_breaks=True,
            quiet=True,
        )

        if expected_json_file.exists():
            with open(expected_json_file, "r", encoding="utf-8") as f:
                json_data = json.load(f)
            expected_json_file.unlink(missing_ok=True)  # Xóa file JSON tạm ngay sau khi nạp

            blocks = adapt_opendataloader_json_to_parsed_blocks(json_data, document_id)
            if blocks:
                log_info("parsed_with_opendataloader", document_id=document_id, block_count=len(blocks))
                return blocks
    except Exception as ex:
        log_warn("opendataloader_error", document_id=document_id, reason=str(ex))
        if expected_json_file.exists():
            expected_json_file.unlink(missing_ok=True)

    # 2. Fallback sang pypdf + txt_parser nếu OpenDataLoader không sinh được block nào
    log_info("fallback_to_pypdf", document_id=document_id)
    reader = PdfReader(str(pdf_path))
    extracted_text = "\n\n".join(page.extract_text() or "" for page in reader.pages)

    if not extracted_text.strip():
        return []

    lines = [
        {"line_number": i, "text": line}
        for i, line in enumerate(extracted_text.splitlines(), start=1)
    ]
    raw_blocks = build_blocks(lines)
    blocks = to_parsed_blocks(raw_blocks, document_id)
    log_info("parsed_with_pypdf", document_id=document_id, block_count=len(blocks))
    return blocks


def ingest_document(
    document_id: str,
    s3_key: str,
    s3_client,
    embedder,
    store,
    user_id: Optional[str] = None,
) -> dict:
    """Xử lý trọn gói 1 tài liệu: tải S3 -> parse PDF -> chunk -> embed -> lưu SQLite."""
    pdf_path: Optional[Path] = None
    try:
        if not user_id:
            parts = s3_key.split("/")
            if len(parts) >= 3 and parts[0] == "uploads":
                user_id = parts[1]

        log_info("ingest_started", document_id=document_id, s3_key=s3_key)

        # 1. Tải PDF từ S3
        pdf_path = _download_pdf(s3_client, s3_key)

        # 2. Parse PDF thành danh sách Blocks
        blocks = _parse_pdf_to_blocks(pdf_path, document_id)
        if not blocks:
            log_error("no_blocks_produced", document_id=document_id)
            return {"chunk_count": 0}

        # 3. Chunk blocks với StructureAwareChunker
        chunker = get_chunker(CHUNKER_STRATEGY, tokenizer=embedder.model.tokenizer)
        bundle = chunker.chunk(
            blocks=blocks,
            document_id=document_id,
            source_type="pdf",
            config=CHUNKER_CONFIG,
        )
        log_info("chunked", document_id=document_id, chunk_count=len(bundle.chunks))

        if not bundle.chunks:
            return {"chunk_count": 0}

        # 4. Embed chunks bằng MPNet
        texts = [c.text for c in bundle.chunks]
        vectors = embedder.encode(texts)
        log_info("embedded", document_id=document_id, vector_count=len(vectors))

        # 5. Tạo IndexMeta và chuẩn bị dữ liệu chunks
        meta = IndexMeta(
            model_name=embedder.model_name,
            revision=embedder.revision,
            dimension=embedder.dimension,
            max_seq_length=embedder.max_seq_length,
            normalization=embedder.normalization,
            index_version="1.0",
            created_at=datetime.now(timezone.utc).isoformat(),
        )

        chunks_as_dicts = []
        for c in bundle.chunks:
            c_dict = asdict(c)
            c_dict["user_id"] = user_id
            if "chunker_strategy" in c_dict and hasattr(c_dict["chunker_strategy"], "value"):
                c_dict["chunker_strategy"] = c_dict["chunker_strategy"].value
            chunks_as_dicts.append(c_dict)

        # 6. Lưu vào SQLiteVectorStore
        store.upsert_index(meta, chunks_as_dicts, vectors)
        log_info("stored", document_id=document_id, chunk_count=len(bundle.chunks))

        return {"chunk_count": len(bundle.chunks)}

    finally:
        # Luôn dọn dẹp file PDF tạm
        if pdf_path:
            try:
                if pdf_path.exists():
                    pdf_path.unlink()

                json_path = pdf_path.with_suffix(".json")
                if json_path.exists():
                    json_path.unlink()

                images_dir = pdf_path.parent / f"{pdf_path.stem}_images"
                if images_dir.exists() and images_dir.is_dir():
                    shutil.rmtree(images_dir)
            except Exception as ex:
                log_error("temp_cleanup_failed", file=str(pdf_path), error=str(ex))