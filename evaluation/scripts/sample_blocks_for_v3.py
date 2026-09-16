import json
import random
from pathlib import Path
from collections import defaultdict

def sample_blocks():
    blocks_file = Path("evaluation/bundle_all/blocks.jsonl")
    output_file = Path("evaluation/results/sampled_blocks_v3.md")
    
    # Load all blocks
    blocks_by_doc = defaultdict(list)
    with open(blocks_file, "r", encoding="utf-8") as f:
        for line in f:
            if line.strip():
                block = json.loads(line)
                blocks_by_doc[block["document_id"]].append(block)
                
    # We want 50 blocks in total
    # Let's aim for:
    # 20 from pdf_aws_001
    # 15 from txt_aiops_001
    # 5 from wiki_06_markdown_sample
    # 5 from pdf_dmls_001
    # 5 from pptx_nlp_001 or docx_review_001
    
    targets = {
        "pdf_aws_001": 20,
        "txt_aiops_001": 15,
        "wiki_06_markdown_sample": 5,
        "pdf_dmls_001": 5,
        "docx_review_001": 5
    }
    
    sampled_blocks = []
    random.seed(42) # For reproducibility
    
    for doc_id, count in targets.items():
        doc_blocks = blocks_by_doc.get(doc_id, [])
        # Filter out very short blocks (likely noise)
        valid_blocks = [b for b in doc_blocks if len(b["text"].split()) > 10]
        
        if len(valid_blocks) >= count:
            sampled = random.sample(valid_blocks, count)
        else:
            sampled = valid_blocks
        sampled_blocks.extend(sampled)
        
    # Write to markdown for easy reading
    with open(output_file, "w", encoding="utf-8") as f:
        f.write("# Sampled Blocks for test-v3.jsonl\n\n")
        for i, b in enumerate(sampled_blocks):
            f.write(f"## Block {i+1} - {b['document_id']}\n")
            f.write(f"**Block ID**: `{b['block_id']}`\n")
            f.write(f"**Locator**: `{json.dumps(b.get('locator', {}))}`\n\n")
            f.write(f"```text\n{b['text']}\n```\n\n")
            f.write("---\n")
            
    print(f"Sampled {len(sampled_blocks)} blocks and saved to {output_file}")

if __name__ == "__main__":
    sample_blocks()
