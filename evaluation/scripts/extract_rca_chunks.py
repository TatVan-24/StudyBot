import json
import sqlite3

dev_v2_path = "d:/Personal Project/AWS StudyBot/evaluation/datasets/development-v2.jsonl"
blocks_path = "d:/Personal Project/AWS StudyBot/evaluation/bundle_all/blocks.jsonl"
db_path = "d:/Personal Project/AWS StudyBot/evaluation/index/m3_index.db"
output_path = "d:/Personal Project/AWS StudyBot/idea/demo/rca_extracted_chunks.md"

DOC_TITLES = {
    "pdf_aws_001": "AWS Cloud Computing Whitepaper",
    "txt_aiops_001": "AIOps and Observability Guide",
    "wiki_06_markdown_sample": "AWS Storage Overview"
}

def match_locator(gt_locator, block):
    block_locator = block.get('locator', {})
    if gt_locator.get('type') in ['markdown', 'text_span'] and block_locator.get('type') in ['markdown', 'text_span', 'text', 'txt']:
        gt_start = gt_locator.get('start_line')
        gt_end = gt_locator.get('end_line')
        bl_start = block_locator.get('start_line')
        bl_end = block_locator.get('end_line')
        if gt_start is not None and gt_end is not None and bl_start is not None and bl_end is not None:
            if max(gt_start, bl_start) <= min(gt_end, bl_end): return True
    if gt_locator.get('type') == 'page' and block_locator.get('type') == 'pdf':
        gt_page = gt_locator.get('pdf_page')
        for loc in block_locator.get('locations', []):
            if loc.get('pdf_page') == gt_page: return True
    return False

def main():
    # Load blocks
    blocks_by_doc = {}
    with open(blocks_path, 'r', encoding='utf-8') as f:
        for line in f:
            block = json.loads(line)
            blocks_by_doc.setdefault(block.get('document_id'), []).append(block)

    # Load cases
    cases = {}
    with open(dev_v2_path, 'r', encoding='utf-8') as f:
        for line in f:
            c = json.loads(line)
            cases[c['case_id']] = c

    target_ids = [
        "eval_pdf_aws_s3_001",
        "eval_txt_observability_pillars_001",
        "eval_aws_security_levels_001",
        "eval_aws_regions_az_001",
        "eval_txt_pipeline_stages_001",
        "eval_txt_kafka_recovery_001",
        "eval_aws_tenant_access_001",
        "eval_wiki_s3_pricing_001",
        "eval_wiki_s3_features_001"
    ]
    
    conn = sqlite3.connect(db_path)
    cur = conn.cursor()
    cur.execute('SELECT chunk_id, document_id, text, heading_context, source_block_ids FROM embeddings')
    rows = cur.fetchall()
    
    with open(output_path, 'w', encoding='utf-8') as f:
        f.write("# RCA Chunk Extraction\n\n")
        
        for case_id in target_ids:
            case = cases[case_id]
            f.write(f"## {case_id}\n")
            f.write(f"**Query**: {case['query']['text']}\n\n")
            
            # Find target blocks
            target_blocks = set()
            for ev in case.get('evidence', []):
                doc_id = ev['document_id']
                gt_locator = ev['locator']
                for b in blocks_by_doc.get(doc_id, []):
                    if match_locator(gt_locator, b):
                        target_blocks.add(b['block_id'])
            
            # Find matching chunks
            f.write("### Target Chunks:\n")
            for r in rows:
                chunk_id, doc_id, text, hc_str, sbi_str = r
                sbi = set(json.loads(sbi_str) if sbi_str else [])
                if sbi.intersection(target_blocks):
                    hc = json.loads(hc_str) if hc_str else []
                    doc_title = DOC_TITLES.get(doc_id, "")
                    full_context = " > ".join(filter(None, [doc_title] + hc))
                    
                    f.write(f"**Chunk ID**: `{chunk_id}`\n")
                    f.write(f"**Baseline Text**:\n```text\n{text}\n```\n")
                    f.write(f"**Context Injection**:\n```text\n{full_context}\n```\n\n")
                    
if __name__ == '__main__':
    main()
