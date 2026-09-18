import json
import sys

ROOT = "d:/Personal Project/AWS StudyBot/evaluation"
RESULTS_PATH = f"{ROOT}/results/m5_step3_per_case.json"

def safe_mrr(rank):
    return 1.0 / rank if rank > 0 else 0.0

def main():
    try:
        with open(RESULTS_PATH, 'r', encoding='utf-8') as f:
            data = json.load(f)
    except FileNotFoundError:
        print(f"Error: {RESULTS_PATH} not found.")
        print("Please run m5_step3_micro_experiment.py first to generate the results.")
        sys.exit(1)
        
    baseline_results = {r['case_id']: r for r in data.get('baseline', [])}
    ce_results = {r['case_id']: r for r in data.get('cross_encoder', [])}
    
    if not baseline_results or not ce_results:
        print("Error: Empty results found in JSON file.")
        sys.exit(1)
        
    analysis_results = []
    
    for case_id, mb in baseline_results.items():
        if case_id not in ce_results:
            continue
            
        mce = ce_results[case_id]
        group = mb.get('group', 'Unknown')
        
        b_first = safe_mrr(mb['first_rank'])
        ce_first = safe_mrr(mce['first_rank'])
        b_full = safe_mrr(mb['full_rank'])
        ce_full = safe_mrr(mce['full_rank'])
        
        # Classification Logic
        if group == "Strong Anchors":
            # Baseline was perfect here
            if ce_first < b_first or ce_full < b_full or mce['cov_10'] < mb['cov_10']:
                category = "BGE gây collateral damage"
            else:
                category = "Giữ vững phong độ"
        else:
            if ce_first > b_first and ce_full > b_full:
                category = "BGE cải thiện cả First + Full"
            elif ce_first > b_first and ce_full <= b_full:
                category = "BGE cải thiện First nhưng giảm/không đổi Full"
            elif ce_first < b_first and ce_full < b_full:
                category = "BGE giảm cả First + Full"
            elif ce_first < b_first:
                category = "BGE giảm First"
            elif ce_first == b_first and ce_full == b_full:
                category = "BGE không đổi"
            else:
                category = "Khác"

        analysis_results.append({
            "case_id": case_id,
            "group": group,
            "b_first_rank": mb['first_rank'],
            "ce_first_rank": mce['first_rank'],
            "b_full_rank": mb['full_rank'],
            "ce_full_rank": mce['full_rank'],
            "b_cov_10": f"{mb['cov_10']:.2f}",
            "ce_cov_10": f"{mce['cov_10']:.2f}",
            "category": category
        })
        
    print("\n=== M5 Step 3 BGE Case-level Analysis (Offline) ===\n")
    print(f"{'Case ID':<20} | {'Group':<15} | {'B First':<7} | {'CE First':<8} | {'B Full':<6} | {'CE Full':<7} | {'B Cov10':<7} | {'CE Cov10':<8} | {'Category'}")
    print("-" * 135)
    for res in analysis_results:
        print(f"{res['case_id']:<20} | {res['group']:<15} | {res['b_first_rank']:<7} | {res['ce_first_rank']:<8} | {res['b_full_rank']:<6} | {res['ce_full_rank']:<7} | {res['b_cov_10']:<7} | {res['ce_cov_10']:<8} | {res['category']}")
        
    print("\n--- Summary Distribution ---")
    cat_counts = {}
    for r in analysis_results:
        cat_counts[r['category']] = cat_counts.get(r['category'], 0) + 1
    for cat, count in sorted(cat_counts.items(), key=lambda x: -x[1]):
        print(f"{count:2d} cases : {cat}")

if __name__ == "__main__":
    main()
