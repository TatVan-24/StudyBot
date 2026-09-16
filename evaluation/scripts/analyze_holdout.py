import json
from collections import defaultdict
import os

results_path = "d:/Personal Project/AWS StudyBot/evaluation/results/m4_holdout_results.jsonl"

data = []
with open(results_path, 'r', encoding='utf-8') as f:
    for line in f:
        data.append(json.loads(line))

# 1. 24/24 case có target block tồn tại thật trong index không?
unique_cases = set(d['case_id'] for d in data)
cases_exist = {}
for d in data:
    case_id = d['case_id']
    if case_id not in cases_exist:
        cases_exist[case_id] = d['diagnostic_evidence']['target_blocks_exist_in_index']
    else:
        assert cases_exist[case_id] == d['diagnostic_evidence']['target_blocks_exist_in_index']

print("1. All 24 target blocks exist?", all(cases_exist.values()), "- Count True:", sum(cases_exist.values()))

# Group by config
by_config = defaultdict(list)
for d in data:
    cfg = d['retrieval_config']['fusion_method']
    if cfg == 'min_max':
        cfg = f"minmax_{d['retrieval_config']['alpha']}"
    by_config[cfg].append(d)

# 2. Dense critical failures breakdown
dense_fails = [d for d in by_config['dense'] if d['metrics']['coverage_at_10'] == 0.0 or d['metrics']['mrr_first_hit'] < 0.5]
zero_hits = [d for d in dense_fails if d['metrics']['coverage_at_10'] == 0.0]
low_mrr = [d for d in dense_fails if d['metrics']['coverage_at_10'] > 0.0 and d['metrics']['mrr_first_hit'] < 0.5]

print("\n2. Dense Critical Failures:", len(dense_fails))
print(f"   - Zero-hits: {len(zero_hits)}")
print(f"   - Low MRR First (Rank > 2 but found in top 10): {len(low_mrr)}")

# 3. Critical failures overlap
def get_critical_fail_cases(cfg):
    fails = set()
    for d in by_config[cfg]:
        if d['metrics']['coverage_at_10'] == 0.0 or d['metrics']['mrr_first_hit'] < 0.5:
            fails.add(d['case_id'])
    return fails

dense_cf = get_critical_fail_cases('dense')
bm25_cf = get_critical_fail_cases('bm25')
mm4_cf = get_critical_fail_cases('minmax_0.4')

common_all = dense_cf.intersection(bm25_cf).intersection(mm4_cf)
dense_only = dense_cf - bm25_cf - mm4_cf
bm25_only = bm25_cf - dense_cf - mm4_cf
mm4_only = mm4_cf - dense_cf - bm25_cf

print("\n3. Critical Failure Overlap:")
print(f"   - Common to Dense, BM25, MinMax .4: {len(common_all)} cases: {common_all}")
print(f"   - Fails only in Dense: {len(dense_only)} cases")
print(f"   - Fails only in BM25: {len(bm25_only)} cases")
print(f"   - Fails only in MinMax .4: {len(mm4_only)} cases")

# What cases fail in Dense and BM25 but pass in MinMax?
dense_bm25_fail = dense_cf.intersection(bm25_cf)
saved_by_mm4 = dense_bm25_fail - mm4_cf
print(f"   - Failed in Dense & BM25, but PASSED in MinMax .4: {len(saved_by_mm4)} cases: {saved_by_mm4}")

# 4. Did MinMax .4 improve hard cases or just boost aggregate?
print("\n4. MinMax .4 improvements over baselines:")
for d in by_config['minmax_0.4']:
    case_id = d['case_id']
    d_dense = next(item for item in by_config['dense'] if item['case_id'] == case_id)
    d_bm25 = next(item for item in by_config['bm25'] if item['case_id'] == case_id)
    
    mrr_dense = d_dense['metrics']['mrr_full_coverage']
    mrr_bm25 = d_bm25['metrics']['mrr_full_coverage']
    mrr_mm4 = d['metrics']['mrr_full_coverage']
    
    if mrr_mm4 > max(mrr_dense, mrr_bm25):
        print(f"   [Synergy] {case_id}: Dense({mrr_dense:.2f}), BM25({mrr_bm25:.2f}) -> MinMax.4({mrr_mm4:.2f})")
    elif mrr_mm4 < min(mrr_dense, mrr_bm25):
        print(f"   [Degradation] {case_id}: Dense({mrr_dense:.2f}), BM25({mrr_bm25:.2f}) -> MinMax.4({mrr_mm4:.2f})")
