import json
import argparse
import itertools

def classify_claim(p_e, p_c, high_e, high_c, has_rule_violation):
    if has_rule_violation:
        return "CONTRADICTION"
    if p_c >= high_c:
        return "CONTRADICTION"
    if p_e >= high_e:
        return "GROUNDED"
    return "AMBIGUOUS"

def evaluate_sweep(results, high_e, high_c):
    tp_grounded = 0
    fp_grounded = 0
    fn_grounded = 0
    
    tp_contradiction = 0
    fn_contradiction = 0
    
    for res in results:
        gt = res["ground_truth_label"]
        p_e = res["nli_probs"]["P_E"]
        p_c = res["nli_probs"]["P_C"]
        has_rule = res.get("has_rule_violation", False)
        
        pred = classify_claim(p_e, p_c, high_e, high_c, has_rule)
        
        # Grounded Metrics
        if gt == "GROUNDED":
            if pred == "GROUNDED":
                tp_grounded += 1
            else:
                fn_grounded += 1
                
        elif gt == "CONTRADICTION" or gt == "AMBIGUOUS":
            if pred == "GROUNDED":
                fp_grounded += 1
                
        # Contradiction Metrics
        if gt == "CONTRADICTION":
            if pred == "CONTRADICTION":
                tp_contradiction += 1
            else:
                fn_contradiction += 1
                
    return {
        "tp_grounded": tp_grounded,
        "fp_grounded": fp_grounded,
        "fn_grounded": fn_grounded,
        "tp_contradiction": tp_contradiction,
        "fn_contradiction": fn_contradiction
    }

def print_matrix(sweep_results, metric_name):
    print(f"\n--- Matrix for: {metric_name} ---")
    
    # Get unique thresholds and sort them
    high_e_vals = sorted(list(set(k[0] for k in sweep_results.keys())))
    high_c_vals = sorted(list(set(k[1] for k in sweep_results.keys())))
    
    # Header
    header = "E\\C\t" + "\t".join(f"{c:.2f}" for c in high_c_vals)
    print(header)
    print("-" * 50)
    
    for e in high_e_vals:
        row = f"{e:.2f}\t"
        for c in high_c_vals:
            val = sweep_results[(e, c)][metric_name]
            row += f"{val}\t"
        print(row)

def print_tradeoff_summary(sweep_results):
    print("\n================= THRESHOLD TRADE-OFFS =================")
    print("HIGH_E\tHIGH_C\t|\tGrounded (TP/FP/FN)\t|\tContradiction (TP/FN)")
    print("-" * 80)
    
    # Sort by HIGH_E, then HIGH_C
    keys = sorted(sweep_results.keys())
    for e, c in keys:
        m = sweep_results[(e, c)]
        grounded_str = f"{m['tp_grounded']:2d} / {m['fp_grounded']:2d} / {m['fn_grounded']:2d}"
        contra_str = f"{m['tp_contradiction']:2d} / {m['fn_contradiction']:2d}"
        
        # Highlight configurations with 0 FP grounded
        marker = "⭐" if m['fp_grounded'] == 0 else "  "
        print(f"{e:.2f}\t{c:.2f}\t|{marker}\t{grounded_str}\t\t|\t{contra_str}")

def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--input", type=str, default="evaluation/results/m6_check3_raw_nli_scores.jsonl")
    args = parser.parse_args()
    
    try:
        with open(args.input, 'r', encoding='utf-8') as f:
            results = [json.loads(line) for line in f]
    except FileNotFoundError:
        print(f"File {args.input} not found. Please run m6_step8_nli_inference.py first.")
        return

    # Define ranges for sweeping (0.5 to 0.9, step 0.1)
    thresholds = [0.5, 0.6, 0.7, 0.8, 0.9, 0.95]
    
    all_metrics = {}
    
    for high_e, high_c in itertools.product(thresholds, thresholds):
        metrics = evaluate_sweep(results, high_e, high_c)
        all_metrics[(high_e, high_c)] = metrics

    print(f"Total Cases: {len(results)}")
    print("NOTE: FP Grounded (Ảo giác) là chỉ số quan trọng nhất cần tối thiểu (tiến về 0).")
    
    print_tradeoff_summary(all_metrics)

if __name__ == "__main__":
    main()
