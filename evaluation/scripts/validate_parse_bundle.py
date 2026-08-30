import argparse
import sys
import json
from pathlib import Path
from jsonschema import Draft202012Validator


REQUIRED_FILES = [
    "manifest.json",
    "blocks.jsonl",
    "assets.jsonl",
    "links.jsonl",
    "issues.jsonl",
]

PROJECT_ROOT = Path(__file__).resolve().parents[2]

PARSED_BLOCK_SCHEMA_PATH = (
    PROJECT_ROOT
    / "evaluation"
    / "schemas"
    / "parsed-block.schema.json"
)


def load_json(path):
    """Đọc một file JSON, dùng cho manifest.json."""
    with open(path, "r", encoding="utf-8") as f:
        return json.load(f)


def load_jsonl(path):
    """Đọc JSONL và giữ line number để báo lỗi."""
    records = []

    with open(path, "r", encoding="utf-8") as f:
        for line_number, line in enumerate(f, start=1):
            line = line.strip()

            if not line:
                continue

            record = json.loads(line)

            records.append({
                "line": line_number,
                "data": record,
            })

    return records


def validate_artifacts(bundle_dir):
    """Kiểm tra bundle có đủ manifest + 4 JSONL."""
    bundle_dir = Path(bundle_dir)

    errors = []

    for filename in REQUIRED_FILES:
        path = bundle_dir / filename

        if not path.is_file():
            errors.append({
                "file": filename,
                "code": "MISSING_ARTIFACT",
                "message": f"Missing required artifact: {filename}",
            })

    return errors


def validate_records(records, schema, artifact_name):
    """Validate từng JSONL record bằng JSON Schema."""
    validator = Draft202012Validator(schema)
    errors = []

    for item in records:
        line_number = item["line"]
        record = item["data"]

        for error in validator.iter_errors(record):
            field_path = ".".join(str(part) for part in error.path)

            errors.append({
                "file": artifact_name,
                "line": line_number,
                "record_id": record.get("block_id"),
                "field": field_path or None,
                "code": "SCHEMA_VIOLATION",
                "message": error.message,
            })

    return errors


def validate_bundle_rules(manifest, records):
    """Kiểm tra document identity và block indices."""
    errors = []

    manifest_document_id = manifest.get("document_id")

    if not manifest_document_id:
        errors.append({
            "file": "manifest.json",
            "line": None,
            "record_id": None,
            "field": "document_id",
            "code": "MISSING_DOCUMENT_ID",
            "message": "Manifest must contain document_id.",
        })
        return errors

    seen_block_ids = set()

    for item in records:
        line_number = item["line"]
        block = item["data"]
        block_id = block.get("block_id")

        if block.get("document_id") != manifest_document_id:
            errors.append({
                "file": "blocks.jsonl",
                "line": line_number,
                "record_id": block_id,
                "field": "document_id",
                "code": "DOCUMENT_ID_MISMATCH",
                "message": (
                    f"Expected {manifest_document_id!r}, "
                    f"got {block.get('document_id')!r}."
                ),
            })

        if block_id in seen_block_ids:
            errors.append({
                "file": "blocks.jsonl",
                "line": line_number,
                "record_id": block_id,
                "field": "block_id",
                "code": "DUPLICATE_BLOCK_ID",
                "message": f"Duplicate block_id: {block_id}",
            })

        seen_block_ids.add(block_id)

    actual_indices = [
        item["data"].get("block_index")
        for item in records
    ]
    expected_indices = list(range(1, len(records) + 1))

    if actual_indices != expected_indices:
        errors.append({
            "file": "blocks.jsonl",
            "line": None,
            "record_id": None,
            "field": "block_index",
            "code": "INVALID_BLOCK_INDEX_SEQUENCE",
            "message": (
                f"Expected {expected_indices}, "
                f"got {actual_indices}."
            ),
        })

    return errors


def main():
    parser = argparse.ArgumentParser(
        description="Validate a StudyBot ParseBundle."
    )
    parser.add_argument(
        "bundle_dir",
        help="Path to the ParseBundle directory.",
    )
    args = parser.parse_args()

    bundle_dir = Path(args.bundle_dir)

    artifact_errors = validate_artifacts(bundle_dir)

    if artifact_errors:
        for error in artifact_errors:
            print(
                f"{error['file']} "
                f"[{error['code']}] "
                f"{error['message']}"
            )
        return 1

    try:
        schema = load_json(PARSED_BLOCK_SCHEMA_PATH)
        blocks = load_jsonl(bundle_dir / "blocks.jsonl")
        manifest = load_json(bundle_dir / "manifest.json")
    except (OSError, json.JSONDecodeError) as error:
        print(f"VALIDATOR_ERROR: {error}")
        return 2

    errors = validate_records(
        blocks,
        schema,
        "blocks.jsonl",
    )

    errors.extend(
    validate_bundle_rules(manifest, blocks)
    )

    if errors:
        print(f"INVALID: {len(errors)} error(s)")

        for error in errors:
            location = error["file"]

            if error.get("line") is not None:
                location += f":{error['line']}"

            field = error["field"] or "<record>"

            print(
                f"{location} "
                f"[{error['code']}] "
                f"field={field} "
                f"{error['message']}"
            )

        return 1

    print(f"VALID: {bundle_dir}")
    return 0


if __name__ == "__main__":
    sys.exit(main())