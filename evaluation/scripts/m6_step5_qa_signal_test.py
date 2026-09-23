"""
m6_step5_qa_signal_test.py
==========================
Tests the 'cross-encoder/ms-marco-MiniLM-L-6-v2' model as a candidate 
Signal #3 for the M6 Evidence Sufficiency gate.

Outputs a diagnostic report comparing QA scores across SUFFICIENT and INSUFFICIENT cases,
with special focus on Hard FPs (015, 033) and the FN (001).
"""

import json
import os
import numpy as np

try:
    from sentence_transformers import CrossEncoder
except ImportError:
    print("[ERROR] Please install sentence-transformers: pip install sentence-transformers")
    exit(1)

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
GROUND_TRUTH_PATH = os.path.join(ROOT, "datasets", "m6_dev_sufficiency_ground_truth.jsonl")

def main():
    print("[INFO] Loading dataset...")
    records = []
    with open(GROUND_TRUTH_PATH, encoding="utf-8") as f:
        for line in f:
            if line.strip():
                records.append(json.loads(line))

    print("[INFO] Loading QA Cross-Encoder (ms-marco-MiniLM-L-6-v2)...")
    model = CrossEncoder("cross-encoder/ms-marco-MiniLM-L-6-v2", max_length=512)

    sufficient_scores = []
    insufficient_scores = []
    hard_cases = {}

    print("[INFO] Scoring 35 cases...")
    for r in records:
        qid = r["query_id"]
        q = r["query"]
        chunk = r["retrieved_context"][0]["text"]
        gt = r.get("ground_truth_label")

        if gt is None:
            continue

        # Score with QA Cross-Encoder
        # The model expects a list of pairs: [[query, passage]]
        score = float(model.predict([[q, chunk]])[0])
        
        if gt == 1:
            sufficient_scores.append(score)
        else:
            insufficient_scores.append(score)

        # Track specific cases
        if "015" in qid or "033" in qid or "001" in qid:
            hard_cases[qid] = {
                "bge_score": r["signals"].get("bge_top1_score"),
                "qa_score": score,
                "gt": gt
            }

    if not sufficient_scores or not insufficient_scores:
        print("[ERROR] Missing ground truth labels.")
        return

    # Print Report
    print("=" * 60)
    print("M6 Step 5: QA Cross-Encoder Signal Test Report")
    print("=" * 60)
    
    print("\n[ AGGREGATE STATISTICS ]")
    print(f"SUFFICIENT ({len(sufficient_scores)} cases):")
    print(f"  Mean   QA Score: {np.mean(sufficient_scores):>8.4f}")
    print(f"  Median QA Score: {np.median(sufficient_scores):>8.4f}")
    print(f"  Min QA Score   : {np.min(sufficient_scores):>8.4f}")
    
    print(f"\nINSUFFICIENT ({len(insufficient_scores)} cases):")
    print(f"  Mean   QA Score: {np.mean(insufficient_scores):>8.4f}")
    print(f"  Median QA Score: {np.median(insufficient_scores):>8.4f}")
    print(f"  Max QA Score   : {np.max(insufficient_scores):>8.4f}")

    print("\n[ HARD CASES SPOTLIGHT ]")
    
    print("\n--- Hard FPs (BGE is confident but evidence is INSUFFICIENT) ---")
    case_015 = next((v for k, v in hard_cases.items() if "015" in k), None)
    case_033 = next((v for k, v in hard_cases.items() if "033" in k), None)
    
    if case_015:
        print(f"Case 015 (Missing Entity Slot):")
        print(f"  BGE Top-1 : {case_015['bge_score']:.4f}")
        print(f"  QA Score  : {case_015['qa_score']:.4f}")
        
    if case_033:
        print(f"\nCase 033 (Entity Mismatch / Collector vs Tool):")
        print(f"  BGE Top-1 : {case_033['bge_score']:.4f}")
        print(f"  QA Score  : {case_033['qa_score']:.4f}")

    print("\n--- Hard FN (BGE is doubtful but evidence is SUFFICIENT) ---")
    case_001 = next((v for k, v in hard_cases.items() if "001" in k), None)
    if case_001:
        print(f"Case 001 (Semantic Negation Trap):")
        print(f"  BGE Top-1 : {case_001['bge_score']:.4f}")
        print(f"  QA Score  : {case_001['qa_score']:.4f}")

    print("\n" + "=" * 60)
    print("Decision Criteria:")
    print("If QA Score of 015/033 is significantly lower than SUFFICIENT median,")
    print("then QA Score has strong incremental value as Signal #3.")
    print("=" * 60)

if __name__ == "__main__":
    main()
