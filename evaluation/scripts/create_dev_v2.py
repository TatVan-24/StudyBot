import json
import os

input_file = "d:/Personal Project/AWS StudyBot/evaluation/datasets/development-v1.jsonl"
output_file = "d:/Personal Project/AWS StudyBot/evaluation/datasets/development-v2.jsonl"
allowed_docs = {"pdf_aws_001", "txt_aiops_001"}

cases = []
with open(input_file, 'r', encoding='utf-8') as f:
    for line in f:
        case = json.loads(line)
        doc_ids = set(case.get("scope", {}).get("document_ids", []))
        if doc_ids.issubset(allowed_docs) and len(doc_ids) > 0:
            cases.append(case)

# Create 2 semantic cases for wiki_06_markdown_sample
wiki_case_1 = {
    "schema_version": "1.0",
    "case_id": "eval_wiki_s3_pricing_001",
    "split": "development",
    "category": "direct_factual",
    "query": {
        "text": "What is the price per GB for the Glacier storage class?",
        "language": "en"
    },
    "scope": {
        "document_ids": ["wiki_06_markdown_sample"]
    },
    "expected": {
        "answerability": "ANSWERABLE",
        "reference_answer": "The price for the Glacier storage class is $0.004 per GB.",
        "required_facts": ["Glacier price is $0.004."],
        "forbidden_claims": []
    },
    "evidence": [
        {
            "document_id": "wiki_06_markdown_sample",
            "locator": {
                "type": "markdown",
                "start_line": 17,
                "end_line": 17
            },
            "evidence_note": "The pricing table states Glacier is $0.004."
        }
    ],
    "tags": ["markdown", "pricing", "factual"],
    "review": {
        "status": "PENDING_REVIEW",
        "reviewer": "system",
        "reviewed_at": "2026-09-08"
    }
}

wiki_case_2 = {
    "schema_version": "1.0",
    "case_id": "eval_wiki_s3_features_001",
    "split": "development",
    "category": "direct_factual",
    "query": {
        "text": "Những tính năng cốt lõi (core features) của Amazon S3 là gì?",
        "language": "vi"
    },
    "scope": {
        "document_ids": ["wiki_06_markdown_sample"]
    },
    "expected": {
        "answerability": "ANSWERABLE",
        "reference_answer": "Các tính năng cốt lõi của Amazon S3 bao gồm độ bền cao (High durability), độ sẵn sàng cao (High availability) và khả năng mở rộng vô hạn (Infinite scaling).",
        "required_facts": ["High durability", "High availability", "Infinite scaling"],
        "forbidden_claims": []
    },
    "evidence": [
        {
            "document_id": "wiki_06_markdown_sample",
            "locator": {
                "type": "markdown",
                "start_line": 8,
                "end_line": 10
            },
            "evidence_note": "The Core Features section lists these three traits."
        }
    ],
    "tags": ["markdown", "features", "cross_lingual"],
    "review": {
        "status": "PENDING_REVIEW",
        "reviewer": "system",
        "reviewed_at": "2026-09-08"
    }
}

cases.append(wiki_case_1)
cases.append(wiki_case_2)

with open(output_file, 'w', encoding='utf-8') as f:
    for case in cases:
        f.write(json.dumps(case, ensure_ascii=False) + "\n")

print(f"Created {output_file} with {len(cases)} cases.")
