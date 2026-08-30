import subprocess
import sys
from pathlib import Path
from src.parser.pdf.pdf_adapter import adapt_opendataloader_json_to_parsed_blocks, parse_pdf_bundle


def test_adapt_opendataloader_json_maps_elements_correctly():
    fixture_json = {
        "document_id": "pdf_aws_001",
        "elements": [
            {
                "element_id": "elem_1",
                "type": "heading",
                "text": "AWS Overview",
                "page_number": 1,
                "bounding_box": [0.1, 0.1, 0.9, 0.15],
                "reading_order": 1,
                "level": 2,
            },
            {
                "element_id": "elem_2",
                "type": "paragraph",
                "text": "Amazon Web Services provides cloud infrastructure.",
                "page_number": 1,
                "bounding_box": [0.1, 0.16, 0.9, 0.35],
                "reading_order": 2,
            },
        ],
    }

    blocks = adapt_opendataloader_json_to_parsed_blocks(fixture_json, "pdf_aws_001")
    assert len(blocks) == 2
    assert blocks[0]["block_type"] == "heading"
    assert blocks[0]["source_type"] == "pdf"
    assert blocks[0]["locator"]["type"] == "pdf"
    assert blocks[0]["locator"]["locations"][0]["pdf_page"] == 1
    assert blocks[1]["block_type"] == "paragraph"
    assert blocks[1]["heading_path"] == [{"level": 2, "role": "generic", "text": "AWS Overview"}]


def test_parse_pdf_bundle_generates_valid_bundle(tmp_path):
    fixture_json = {
        "elements": [
            {
                "type": "heading",
                "text": "# Storage Architecture",
                "page_number": 1,
                "bounding_box": [0.05, 0.05, 0.95, 0.1],
                "reading_order": 1,
            },
            {
                "type": "paragraph",
                "text": "S3 stores data as objects within buckets.",
                "page_number": 1,
                "bounding_box": [0.05, 0.12, 0.95, 0.3],
                "reading_order": 2,
            },
        ],
    }

    output_dir = tmp_path / "bundle_pdf"
    blocks = parse_pdf_bundle(fixture_json, "pdf_aws_001", output_dir)
    assert len(blocks) == 2
    assert (output_dir / "manifest.json").exists()
    assert (output_dir / "blocks.jsonl").exists()

    validator_script = Path("evaluation/scripts/validate_parse_bundle.py")
    res = subprocess.run(
        [sys.executable, str(validator_script), str(output_dir)],
        capture_output=True,
        text=True,
    )
    assert res.returncode == 0
