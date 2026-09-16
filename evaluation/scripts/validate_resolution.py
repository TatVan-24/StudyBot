import json
import os
import sys

import argparse

dataset_paths = [
    "d:/Personal Project/AWS StudyBot/evaluation/datasets/development-v2.jsonl",
    "d:/Personal Project/AWS StudyBot/evaluation/datasets/test-v1.jsonl",
    "d:/Personal Project/AWS StudyBot/evaluation/datasets/test-v2.jsonl"
]
blocks_path = "d:/Personal Project/AWS StudyBot/evaluation/bundle_all/blocks.jsonl"

def load_blocks():
    blocks_by_doc = {}
    with open(blocks_path, 'r', encoding='utf-8') as f:
        for line in f:
            block = json.loads(line)
            doc_id = block.get('document_id')
            if doc_id not in blocks_by_doc:
                blocks_by_doc[doc_id] = []
            blocks_by_doc[doc_id].append(block)
    return blocks_by_doc

def match_locator(gt_locator, block):
    block_locator = block.get('locator', {})
    
    # 1. Match Markdown and Text (start_line, end_line)
    if gt_locator.get('type') in ['markdown', 'text_span', 'txt'] and block_locator.get('type') in ['markdown', 'text_span', 'text', 'txt']:
        gt_start = gt_locator.get('start_line')
        gt_end = gt_locator.get('end_line')
        bl_start = block_locator.get('start_line')
        bl_end = block_locator.get('end_line')
        
        if gt_start is not None and gt_end is not None and bl_start is not None and bl_end is not None:
            # Overlap check
            if max(gt_start, bl_start) <= min(gt_end, bl_end):
                return True
                
    # 2. Match PDF (pdf_page)
    if gt_locator.get('type') in ['page', 'pdf'] and block_locator.get('type') == 'pdf':
        gt_page = gt_locator.get('pdf_page')
        if gt_page is None:
            locations = gt_locator.get('locations', [])
            if locations:
                gt_page = locations[0].get('pdf_page')
                
        locations = block_locator.get('locations', [])
        for loc in locations:
            if loc.get('pdf_page') == gt_page:
                return True

    return False

def main():
    blocks_by_doc = load_blocks()
    
    all_valid = True
    for p in dataset_paths:
        if not os.path.exists(p):
            print(f"Skipping {p} (does not exist).")
            continue
            
        cases = []
        with open(p, 'r', encoding='utf-8') as f:
            for line in f:
                if line.strip():
                    cases.append(json.loads(line))
                
        print(f"\n--- Validating {os.path.basename(p)} ---")
            
        for case in cases:
            case_id = case.get('case_id')
            evidences = case.get('evidence', [])
            scope_docs = set(case.get("scope", {}).get("document_ids", []))
            
            for ev in evidences:
                doc_id = ev.get('document_id')
                gt_locator = ev.get('locator')
                
                # Check evidence document is in scope
                if doc_id not in scope_docs:
                    print(f"[FAIL] Case {case_id}: Evidence document {doc_id} is not in scope {scope_docs}.")
                    all_valid = False
                
                # Check document exists
                if doc_id not in blocks_by_doc:
                    print(f"[FAIL] Case {case_id}: Document {doc_id} not found in blocks.")
                    all_valid = False
                    continue
                    
                # Check locator resolution
                doc_blocks = blocks_by_doc[doc_id]
                matched_blocks = []
                for b in doc_blocks:
                    if match_locator(gt_locator, b):
                        matched_blocks.append(b)
                        
                if len(matched_blocks) == 0:
                    print(f"[FAIL] Case {case_id}: Locator {gt_locator} resolved to 0 blocks for doc {doc_id}.")
                    all_valid = False
                else:
                    pass # print(f"[OK] Case {case_id}: Locator resolved to {len(matched_blocks)} blocks.")
                
    if all_valid:
        print("\nSUCCESS: All cases target indexed docs and resolve to >= 1 ParsedBlock.")
    else:
        print("\nFAILURE: Some cases failed validation.")
        sys.exit(1)

if __name__ == "__main__":
    main()
