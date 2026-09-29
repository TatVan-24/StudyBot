"""
m6_step4_threshold_sweep.py
===========================
Exploratory 2D Sweep for Evidence Sufficiency thresholds.
Sweeps bge_top1_score and bge_score_gap to find candidate operating points
on the 35-case annotated dev set.

Outputs are grouped by operational regions (e.g. FP=0, High F1).
"""

import json
import os
import numpy as np

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
GROUND_TRUTH_PATH = os.path.join(ROOT, "datasets", "m6_dev_sufficiency_ground_truth.jsonl")


def evaluate(predictions, labels):
    tp = sum(1 for p, l in zip(predictions, labels) if p == 1 and l == 1)
    fp = sum(1 for p, l in zip(predictions, labels) if p == 1 and l == 0)
    tn = sum(1 for p, l in zip(predictions, labels) if p == 0 and l == 0)
    fn = sum(1 for p, l in zip(predictions, labels) if p == 0 and l == 1)

    precision = tp / (tp + fp) if (tp + fp) > 0 else 0.0
    recall = tp / (tp + fn) if (tp + fn) > 0 else 0.0
    f1 = 2 * precision * recall / (precision + recall) if (precision + recall) > 0 else 0.0
    refusal_rate = (tn + fn) / len(labels) if len(labels) > 0 else 0.0

    return tp, fp, tn, fn, precision, recall, f1, refusal_rate


def main():
    records = []
    with open(GROUND_TRUTH_PATH, encoding="utf-8") as f:
        for line in f:
            if line.strip():
                records.append(json.loads(line))

    # Validate annotations
    labels = [r.get("ground_truth_label") for r in records]
    if any(l is None for l in labels):
        print("[ERROR] Found records with ground_truth_label = null. Please complete annotation first.")
        return

    bge_scores = [r["signals"].get("bge_top1_score", 0.0) for r in records]
    gap_scores = [r["signals"].get("bge_score_gap", 0.0) for r in records]

    # Sweep settings
    bge_range = np.arange(0.15, 0.41, 0.01)
    gap_range = np.arange(0.00, 0.16, 0.01)

    results = []

    for bth in bge_range:
        for gth in gap_range:
            predictions = []
            for bge, gap in zip(bge_scores, gap_scores):
                # SUFFICIENT if bge >= bge_threshold AND gap >= gap_threshold
                is_suff = 1 if (bge >= bth and gap >= gth) else 0
                predictions.append(is_suff)
            
            tp, fp, tn, fn, precision, recall, f1, refusal_rate = evaluate(predictions, labels)
            
            results.append({
                "bge_th": round(bth, 2),
                "gap_th": round(gth, 2),
                "tp": tp, "fp": fp, "tn": tn, "fn": fn,
                "precision": round(precision * 100, 1),
                "recall": round(recall * 100, 1),
                "f1": round(f1 * 100, 1),
                "refusal_rate": round(refusal_rate * 100, 1)
            })

    # Sort results to help with grouping
    # For FP=0, sort by recall descending
    fp_0 = sorted([r for r in results if r["fp"] == 0], key=lambda x: x["recall"], reverse=True)
    
    # For FP<=1, sort by F1 descending
    fp_1 = sorted([r for r in results if r["fp"] <= 1], key=lambda x: x["f1"], reverse=True)
    
    # Best F1 overall
    best_f1 = sorted(results, key=lambda x: x["f1"], reverse=True)
    
    # High Recall (>= 90%)
    high_recall = sorted([r for r in results if r["recall"] >= 90.0], key=lambda x: x["f1"], reverse=True)

    def print_table(title, data, limit=5):
        print(f"\n--- {title} ---")
        print(f"{'BGE_Th':<8} | {'Gap_Th':<8} | {'TP':<3} {'FP':<3} {'TN':<3} {'FN':<3} | {'Prec%':<6} {'Rec%':<6} {'F1%':<6} | {'Refusal%':<8}")
        print("-" * 75)
        
        seen = set()
        count = 0
        for r in data:
            if count >= limit: break
            # Deduplicate similar operational outcomes to show diverse points
            outcome = (r["tp"], r["fp"], r["tn"], r["fn"])
            if outcome in seen:
                continue
            seen.add(outcome)
            count += 1
            
            print(f"{r['bge_th']:<8.2f} | {r['gap_th']:<8.2f} | {r['tp']:<3} {r['fp']:<3} {r['tn']:<3} {r['fn']:<3} | {r['precision']:<6.1f} {r['recall']:<6.1f} {r['f1']:<6.1f} | {r['refusal_rate']:<8.1f}")

    print("=" * 75)
    print("M6 Check 1: 2D Threshold Sweep Exploratory Analysis")
    print("=" * 75)
    print("Total Cases: 35 (17 SUFFICIENT, 18 INSUFFICIENT)")

    print_table("REGION A: FP = 0 (Highest strictness against Hallucination)", fp_0, limit=3)
    print_table("REGION B: FP <= 1 (Balanced strictness)", fp_1, limit=3)
    print_table("REGION C: Top F1 (Statistical balance)", best_f1, limit=3)
    print_table("REGION D: High Recall >= 90% (Minimize Refusal)", high_recall, limit=3)
    
    print("\n[NOTE] This is an exploratory report. Do NOT auto-pick a production threshold.")
    print("Evaluate the cost of False Positives vs False Negatives carefully.")


if __name__ == "__main__":
    main()
