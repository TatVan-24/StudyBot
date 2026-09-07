import pytest
from src.parser.markdown.md_parser import parse_md

def test_md_parser_wiki_06(tmp_path):
    output_dir = tmp_path / "bundle_md"
    blocks = parse_md("src/sample_data/wiki_06_markdown_sample.md", "wiki_06_markdown_sample", str(output_dir))
    
    assert len(blocks) > 0
    
    # Verify we get the expected block types
    block_types = [b["block_type"] for b in blocks]
    
    # Expecting: 
    # H1: AWS Storage Overview -> heading
    # Amazon S3... -> paragraph
    # H2: Core Features -> heading
    # - High durability -> list_item
    # - High availability -> list_item
    # - Infinite scaling -> list_item
    # H3: Pricing Model -> heading
    # Table headers -> table_row
    # Table row 1 -> table_row
    # Table row 2 -> table_row
    # H2: Usage Example -> heading
    # Below is... -> paragraph
    # Code snippet -> code_block
    # > Note: ... -> quote
    
    assert "heading" in block_types
    assert "paragraph" in block_types
    assert "list_item" in block_types
    assert "table_row" in block_types
    assert "code_block" in block_types
    assert "quote" in block_types
    
    # Check heading levels
    headings = [b for b in blocks if b["block_type"] == "heading"]
    assert len(headings) >= 4
    assert headings[0]["metadata"] == {}
    assert headings[0]["heading_path"][-1]["level"] == 2
    assert headings[0]["heading_path"][-1]["text"] == "AWS Storage Overview"
    
    # Check code block language
    code_blocks = [b for b in blocks if b["block_type"] == "code_block"]
    assert len(code_blocks) == 1
    assert code_blocks[0]["metadata"]["language"] == "python"
    assert "import boto3" in code_blocks[0]["text"]
    
    # Check list items
    list_items = [b for b in blocks if b["block_type"] == "list_item"]
    assert len(list_items) == 3
    assert list_items[0]["metadata"]["marker"] == "-"
    
    # Check table rows
    table_rows = [b for b in blocks if b["block_type"] == "table_row"]
    assert len(table_rows) == 3
    # The first row is headers
    assert len(table_rows[0]["metadata"]["cells"]) == 2
    
    # Check quote
    quotes = [b for b in blocks if b["block_type"] == "quote"]
    assert len(quotes) == 1
    assert quotes[0]["text"].startswith("> Note:")
