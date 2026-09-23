"""
m6_step6_qa_incremental_value.py
================================
1. Injects `qa_score` into the JSONL dataset if not already present.
2. Runs a 1D sweep on `qa_score` ON TOP OF the established BGE baseline
   (BGE >= 0.23 AND Gap >= 0.02) to evaluate incremental value.
"""

import json
import os
import numpy as np

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
GROUND_TRUTH_PATH = os.path.join(ROOT, "datasets", "m6_dev_sufficiency_ground_truth.jsonl")

def main():
    records = []
    with open(GROUND_TRUTH_PATH, encoding="utf-8") as f:
        for line in f:
            if line.strip():
                records.append(json.loads(line))

    # 1. Check if we need to compute qa_score
    needs_qa = any("qa_score" not in r["signals"] for r in records)
    if needs_qa:
        print("[INFO] Computing and injecting qa_score into dataset...")
        from sentence_transformers import CrossEncoder
        model = CrossEncoder("cross-encoder/ms-marco-MiniLM-L-6-v2", max_length=512)
        
        for r in records:
            if "qa_score" not in r["signals"]:
                q = r["query"]
                chunk = r["retrieved_context"][0]["text"]
                score = float(model.predict([[q, chunk]])[0])
                r["signals"]["qa_score"] = score
        
        # Save back
        with open(GROUND_TRUTH_PATH, "w", encoding="utf-8") as f:
            for r in records:
                f.write(json.dumps(r, ensure_ascii=False) + "\n")
        print("[INFO] Saved qa_score to dataset.")

    # 2. Extract Data
    y_true = []
    bge_scores = []
    gap_scores = []
    qa_scores = []
    
    for r in records:
        gt = r.get("ground_truth_label")
        if gt is None:
            continue
        y_true.append(gt)
        bge_scores.append(r["signals"].get("bge_top1_score", 0.0))
        gap_scores.append(r["signals"].get("bge_score_gap", 0.0))
        qa_scores.append(r["signals"].get("qa_score", 0.0))

    if not y_true:
        print("[ERROR] No ground truth labels found.")
        return

    # Baseline Rule
    baseline_bge = 0.23
    baseline_gap = 0.02

    def evaluate_rule(qa_th=None):
        tp = fp = tn = fn = 0
        for bge, gap, qa, gt in zip(bge_scores, gap_scores, qa_scores, y_true):
            # Baseline decision
            is_suff = (bge >= baseline_bge) and (gap >= baseline_gap)
            
            # QA conditional decision
            if qa_th is not None:
                is_suff = is_suff and (qa >= qa_th)
            
            if is_suff and gt == 1: tp += 1
            if is_suff and gt == 0: fp += 1
            if not is_suff and gt == 0: tn += 1
            if not is_suff and gt == 1: fn += 1
            
        return tp, fp, tn, fn

    # 3. Baseline Performance
    base_tp, base_fp, base_tn, base_fn = evaluate_rule(qa_th=None)
    print("=" * 60)
    print("BASELINE: BGE >= 0.23 AND Gap >= 0.02")
    print("=" * 60)
    print(f"TP: {base_tp} | FP: {base_fp} | TN: {base_tn} | FN: {base_fn}")
    print("Hard FPs remaining: 015, 033")
    
    # 4. Sweep QA Score on top of Baseline
    print("\n" + "=" * 60)
    print("INCREMENTAL VALUE SWEEP (Baseline AND QA >= qa_th)")
    print("=" * 60)
    print(f"{'QA_Th':<8} | {'TP':<3} {'FP':<3} {'TN':<3} {'FN':<3} | {'Delta FP':<10} {'Delta FN':<10}")
    print("-" * 60)
    
    qa_thresholds = np.arange(-5.0, 5.0, 0.5)
    best_configs = []
    
    for th in qa_thresholds:
        tp, fp, tn, fn = evaluate_rule(qa_th=th)
        delta_fp = fp - base_fp
        delta_fn = fn - base_fn
        
        row = f"{th:<8.1f} | {tp:<3} {fp:<3} {tn:<3} {fn:<3} | {delta_fp:<10} +{delta_fn:<9}"
        
        # Highlight if it drops FP without spiking FN by more than 1
        if delta_fp < 0:
            if delta_fn <= 1:
                row += " <-- CANDIDATE"
                best_configs.append((th, delta_fp, delta_fn))
        
        print(row)

    print("\n[CONCLUSION]")
    if best_configs:
        print("YES, QA Score provides incremental value!")
        print("It can reduce FP without catastrophic FN spikes.")
    else:
        print("NO, QA Score does NOT provide clean incremental value.")
        print("It either fails to reduce FP, or destroys FN in the process.")
        print("Action: Reject QA Score, stick to BGE + Gap.")

if __name__ == "__main__":
    main()
