"""Validate StudyBot's chunk-independent evaluation dataset with stdlib only."""

from __future__ import annotations

import argparse
import json
import os
import re
import sys
from pathlib import Path
from typing import Any


ROOT = Path(__file__).resolve().parents[1]
SCHEMAS = ROOT / "schemas"
PUBLIC_MANIFEST = ROOT / "corpus" / "manifest.public.jsonl"
LOCAL_MANIFEST = ROOT / "corpus" / "manifest.local.jsonl"
DATASETS = (ROOT / "datasets" / "development-v1.jsonl", ROOT / "datasets" / "test-v1.jsonl")

FORBIDDEN_CHUNK_KEYS = {"chunk_id", "chunk_ids", "relevant_chunk_ids", "retrieved_chunks"}
LOCATOR_REQUIRED = {
    "page": {"pdf_page"},
    "slide": {"slide"},
    "section": {"heading_path"},
    "paragraph": {"paragraph_index"},
    "text_span": {"start_line", "end_line"},
}


class ValidationErrors:
    def __init__(self) -> None:
        self.items: list[str] = []

    def add(self, location: str, message: str) -> None:
        self.items.append(f"{location}: {message}")

    def require(self, condition: bool, location: str, message: str) -> None:
        if not condition:
            self.add(location, message)


def read_json(path: Path, errors: ValidationErrors) -> dict[str, Any]:
    try:
        with path.open("r", encoding="utf-8") as handle:
            value = json.load(handle)
    except (OSError, json.JSONDecodeError) as exc:
        errors.add(str(path), str(exc))
        return {}
    if not isinstance(value, dict):
        errors.add(str(path), "root must be a JSON object")
        return {}
    return value


def read_jsonl(path: Path, errors: ValidationErrors) -> list[dict[str, Any]]:
    rows: list[dict[str, Any]] = []
    try:
        with path.open("r", encoding="utf-8") as handle:
            for line_number, raw in enumerate(handle, start=1):
                if not raw.strip():
                    continue
                try:
                    value = json.loads(raw)
                except json.JSONDecodeError as exc:
                    errors.add(f"{path}:{line_number}", f"invalid JSON: {exc.msg}")
                    continue
                if not isinstance(value, dict):
                    errors.add(f"{path}:{line_number}", "entry must be a JSON object")
                    continue
                value["__location__"] = f"{path}:{line_number}"
                rows.append(value)
    except OSError as exc:
        errors.add(str(path), str(exc))
    return rows


def find_forbidden_keys(value: Any, path: str = "$") -> list[str]:
    found: list[str] = []
    if isinstance(value, dict):
        for key, child in value.items():
            if key in FORBIDDEN_CHUNK_KEYS:
                found.append(f"{path}.{key}")
            found.extend(find_forbidden_keys(child, f"{path}.{key}"))
    elif isinstance(value, list):
        for index, child in enumerate(value):
            found.extend(find_forbidden_keys(child, f"{path}[{index}]"))
    return found


def validate_manifest(rows: list[dict[str, Any]], errors: ValidationErrors) -> dict[str, dict[str, Any]]:
    documents: dict[str, dict[str, Any]] = {}
    required = {
        "schema_version", "document_id", "title", "file_type", "languages",
        "corpus_role", "expected_ingestion", "locator_types",
    }
    valid_types = {"pdf", "pptx", "ppt", "docx", "md", "txt"}
    for row in rows:
        location = row.pop("__location__")
        missing = required - row.keys()
        errors.require(not missing, location, f"missing fields: {sorted(missing)}")
        document_id = row.get("document_id")
        errors.require(isinstance(document_id, str) and bool(re.fullmatch(r"[a-z0-9]+(?:_[a-z0-9]+)*", document_id)), location, "invalid document_id")
        if isinstance(document_id, str):
            errors.require(document_id not in documents, location, f"duplicate document_id {document_id}")
            documents[document_id] = row
        errors.require(row.get("schema_version") == "1.0", location, "schema_version must be 1.0")
        errors.require(row.get("file_type") in valid_types, location, "unsupported file_type")
        errors.require(row.get("corpus_role") in {"GROUND_TRUTH", "COMPATIBILITY_ONLY"}, location, "invalid corpus_role")
        errors.require(isinstance(row.get("languages"), list) and bool(row.get("languages")), location, "languages must be non-empty")
        errors.require(isinstance(row.get("locator_types"), list) and bool(row.get("locator_types")), location, "locator_types must be non-empty")
        errors.require(not find_forbidden_keys(row), location, "chunk-derived fields are forbidden")
        serialized = json.dumps(row, ensure_ascii=False)
        errors.require("source_path" not in row and not re.search(r"[A-Za-z]:\\\\", serialized), location, "public manifest must not contain an absolute Windows path")
    return documents


def validate_locator(locator: Any, location: str, errors: ValidationErrors) -> None:
    if not isinstance(locator, dict):
        errors.add(location, "locator must be an object")
        return
    locator_type = locator.get("type")
    errors.require(locator_type in LOCATOR_REQUIRED, location, f"unsupported locator type {locator_type!r}")
    if locator_type not in LOCATOR_REQUIRED:
        return
    missing = LOCATOR_REQUIRED[locator_type] - locator.keys()
    errors.require(not missing, location, f"missing locator fields: {sorted(missing)}")
    if locator_type == "section":
        errors.require(isinstance(locator.get("heading_path"), list) and bool(locator.get("heading_path")), location, "heading_path must be non-empty")
    elif locator_type == "text_span":
        start, end = locator.get("start_line"), locator.get("end_line")
        errors.require(isinstance(start, int) and isinstance(end, int) and 1 <= start <= end, location, "line span must satisfy 1 <= start_line <= end_line")
    else:
        numeric_key = next(iter(LOCATOR_REQUIRED[locator_type]))
        errors.require(isinstance(locator.get(numeric_key), int) and locator[numeric_key] >= 1, location, f"{numeric_key} must be a positive integer")


def validate_cases(rows: list[dict[str, Any]], expected_split: str, documents: dict[str, dict[str, Any]], errors: ValidationErrors, seen_case_ids: set[str]) -> None:
    required = {"schema_version", "case_id", "split", "category", "query", "scope", "expected", "evidence", "tags", "review"}
    for row in rows:
        location = row.pop("__location__")
        missing = required - row.keys()
        errors.require(not missing, location, f"missing fields: {sorted(missing)}")
        errors.require(row.get("schema_version") == "1.0", location, "schema_version must be 1.0")
        case_id = row.get("case_id")
        errors.require(isinstance(case_id, str) and case_id.startswith("eval_"), location, "invalid case_id")
        if isinstance(case_id, str):
            errors.require(case_id not in seen_case_ids, location, f"duplicate case_id {case_id}")
            seen_case_ids.add(case_id)
        errors.require(row.get("split") == expected_split, location, f"split must be {expected_split}")
        forbidden = find_forbidden_keys(row)
        errors.require(not forbidden, location, f"chunk-derived fields are forbidden: {forbidden}")

        scope = row.get("scope", {})
        document_ids = scope.get("document_ids", []) if isinstance(scope, dict) else []
        errors.require(isinstance(document_ids, list) and bool(document_ids), location, "scope.document_ids must be non-empty")
        for document_id in document_ids:
            errors.require(document_id in documents, location, f"unknown scoped document_id {document_id}")
            if document_id in documents:
                errors.require(documents[document_id].get("corpus_role") == "GROUND_TRUTH", location, f"{document_id} is not eligible for QA ground truth")

        expected = row.get("expected", {})
        evidence = row.get("evidence", [])
        answerability = expected.get("answerability") if isinstance(expected, dict) else None
        if answerability == "ANSWERABLE":
            errors.require(isinstance(expected.get("reference_answer"), str) and bool(expected.get("reference_answer", "").strip()), location, "answerable case requires reference_answer")
            errors.require(isinstance(evidence, list) and bool(evidence), location, "answerable case requires evidence")
        elif answerability == "UNANSWERABLE":
            errors.require(expected.get("reference_answer") is None, location, "unanswerable case requires null reference_answer")
            errors.require(evidence == [], location, "unanswerable case must have no evidence")
        else:
            errors.add(location, "answerability must be ANSWERABLE or UNANSWERABLE")

        if isinstance(evidence, list):
            for index, item in enumerate(evidence):
                evidence_location = f"{location} evidence[{index}]"
                if not isinstance(item, dict):
                    errors.add(evidence_location, "evidence must be an object")
                    continue
                document_id = item.get("document_id")
                errors.require(document_id in document_ids, evidence_location, "evidence document must be inside case scope")
                validate_locator(item.get("locator"), evidence_location, errors)
                if document_id in documents and isinstance(item.get("locator"), dict):
                    locator_type = item["locator"].get("type")
                    errors.require(locator_type in documents[document_id].get("locator_types", []), evidence_location, f"locator {locator_type} is not declared by {document_id}")


def validate_local_manifest(documents: dict[str, dict[str, Any]], errors: ValidationErrors) -> None:
    rows = read_jsonl(LOCAL_MANIFEST, errors)
    mappings: dict[str, str] = {}
    for row in rows:
        location = row.pop("__location__")
        errors.require(set(row) == {"document_id", "source_path"}, location, "local entry must contain only document_id and source_path")
        document_id, source_path = row.get("document_id"), row.get("source_path")
        errors.require(document_id in documents, location, f"unknown document_id {document_id}")
        errors.require(isinstance(source_path, str) and os.path.isabs(source_path), location, "source_path must be absolute")
        if isinstance(document_id, str) and isinstance(source_path, str):
            errors.require(document_id not in mappings, location, f"duplicate local mapping {document_id}")
            mappings[document_id] = source_path
            errors.require(Path(source_path).is_file(), location, f"source file does not exist: {source_path}")
    errors.require(set(mappings) == set(documents), str(LOCAL_MANIFEST), "local manifest must map every public document exactly once")


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--check-local", action="store_true", help="also validate private source paths")
    args = parser.parse_args()
    errors = ValidationErrors()

    for schema_name in ("corpus-manifest.schema.json", "evaluation-case.schema.json"):
        schema = read_json(SCHEMAS / schema_name, errors)
        errors.require(schema.get("$schema") == "https://json-schema.org/draft/2020-12/schema", str(SCHEMAS / schema_name), "must declare JSON Schema draft 2020-12")

    documents = validate_manifest(read_jsonl(PUBLIC_MANIFEST, errors), errors)
    seen_case_ids: set[str] = set()
    for dataset in DATASETS:
        expected_split = "development" if dataset.name.startswith("development") else "test"
        validate_cases(read_jsonl(dataset, errors), expected_split, documents, errors, seen_case_ids)

    if args.check_local:
        validate_local_manifest(documents, errors)

    if errors.items:
        print(f"FAILED: {len(errors.items)} validation error(s)")
        for item in errors.items:
            print(f"- {item}")
        return 1

    print(f"OK: {len(documents)} corpus entries, {len(seen_case_ids)} evaluation cases")
    if args.check_local:
        print("OK: local manifest maps all documents to existing source files")
    return 0


if __name__ == "__main__":
    sys.exit(main())

