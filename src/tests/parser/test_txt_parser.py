import subprocess
import sys
from pathlib import Path
from src.parser.text.txt_parser import read_lines, detect_line, build_blocks, to_parsed_blocks, parse_txt


def test_read_lines_preserves_line_numbers_and_blank_lines(tmp_path):
    source = tmp_path / "sample.txt"
    source.write_text("# Heading\n\nFirst paragraph line\n  indented text", encoding="utf-8")
    result = read_lines(source)
    assert result == [
        {"line_number": 1, "text": "# Heading"},
        {"line_number": 2, "text": ""},
        {"line_number": 3, "text": "First paragraph line"},
        {"line_number": 4, "text": "  indented text"},
    ]


def test_detect_line_classifies_baseline_txt_structures():
    assert detect_line("") == "BLANK"
    assert detect_line("## Storage") == "HEADING"
    assert detect_line("  + Prometheus") == "LIST_ITEM"
    assert detect_line("| Tool | Cost |") == "TABLE_ROW"
    assert detect_line("```python") == "CODE_FENCE"
    assert detect_line("> Important") == "QUOTE"
    assert detect_line("Normal paragraph") == "TEXT"


def test_build_blocks_groups_paragraphs_and_code_fences():
    lines = [
        {"line_number": 1, "text": "# Header"},
        {"line_number": 2, "text": ""},
        {"line_number": 3, "text": "Para line 1"},
        {"line_number": 4, "text": "Para line 2"},
        {"line_number": 5, "text": ""},
        {"line_number": 6, "text": "```python"},
        {"line_number": 7, "text": "print('hello')"},
        {"line_number": 8, "text": "```"},
    ]
    raw_blocks = build_blocks(lines)
    assert len(raw_blocks) == 3
    assert raw_blocks[0]["block_type"] == "heading"
    assert raw_blocks[1]["block_type"] == "paragraph"
    assert raw_blocks[1]["start_line"] == 3
    assert raw_blocks[1]["end_line"] == 4
    assert raw_blocks[2]["block_type"] == "code_block"
    assert raw_blocks[2]["start_line"] == 6
    assert raw_blocks[2]["end_line"] == 8


def test_parse_txt_generates_valid_parse_bundle(tmp_path):
    source = tmp_path / "sample.txt"
    source.write_text("# Overview\n\nSample paragraph text.", encoding="utf-8")
    output_dir = tmp_path / "bundle"

    blocks = parse_txt(source, "doc_test_01", output_dir)
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
