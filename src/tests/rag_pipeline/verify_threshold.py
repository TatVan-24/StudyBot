"""Verify threshold trên ood_benchmark.jsonl.

Đọc file benchmark, áp rule answerability:
  sufficient = top1_score >= threshold

Tính confusion matrix:
  TP: OOD + insufficient (đúng: phát hiện OOD)
  FN: OOD + sufficient   (sai: miss OOD)
  TN: IN  + sufficient   (đúng: accept IN)
  FP: IN  + insufficient (sai: reject IN oan)

Usage:
  python src/tests/rag_pipeline/verify_threshold.py
  python src/tests/rag_pipeline/verify_threshold.py --threshold 0.55
"""
import argparse
import json
from pathlib import Path


BENCHMARK = Path("src/tests/rag_pipeline/ood_benchmark.jsonl")


def load_benchmark(path: Path) -> list:
    cases = []
    with open(path, "r", encoding="utf-8") as f:
        for line in f:
            line = line.strip()
            if line:
                cases.append(json.loads(line))
    return cases


def eval_threshold(cases: list, threshold: float) -> dict:
    TP = FP = TN = FN = 0
    in_rejected = []
    ood_accepted = []

    for case in cases:
        label = case.get("label", "")
        top1  = case.get("top1_score", 0.0)
        pred  = "sufficient" if top1 >= threshold else "insufficient"

        if label == "in_domain":
            if pred == "sufficient":
                TN += 1
            else:
                FP += 1
                in_rejected.append((case.get("query", ""), top1))
        elif label == "ood":
            if pred == "insufficient":
                TP += 1
            else:
                FN += 1
                ood_accepted.append((case.get("query", ""), top1))

    total     = TP + FP + TN + FN
    accuracy  = (TP + TN) / total if total else 0.0
    precision = TP / (TP + FP)    if (TP + FP) else 0.0
    recall    = TP / (TP + FN)    if (TP + FN) else 0.0
    f1        = (2 * precision * recall / (precision + recall)) if (precision + recall) else 0.0

    return {
        "threshold": threshold,
        "TP": TP, "FN": FN, "TN": TN, "FP": FP,
        "total": total,
        "accuracy":  accuracy,
        "precision": precision,
        "recall":    recall,
        "f1":        f1,
        "in_rejected":  sorted(in_rejected,  key=lambda x: -x[1]),
        "ood_accepted":  sorted(ood_accepted, key=lambda x: -x[1]),
    }


def main():
    parser = argparse.ArgumentParser(description="Verify answerability threshold")
    parser.add_argument("--threshold", type=float, default=0.50)
    parser.add_argument("--input", default=str(BENCHMARK))
    args = parser.parse_args()

    cases = load_benchmark(Path(args.input))
    n_in  = sum(1 for c in cases if c.get("label") == "in_domain")
    n_ood = sum(1 for c in cases if c.get("label") == "ood")
    print(f"[*] Benchmark: {len(cases)} cases  ({n_in} in_domain, {n_ood} ood)")
    print(f"[*] Default threshold = {args.threshold}")
    print("=" * 80)

    # ── Evaluate default threshold ──────────────────────────────────────────
    res = eval_threshold(cases, args.threshold)
    print(f"Confusion Matrix (threshold={args.threshold}):")
    print(f"  TP (OOD + insufficient): {res['TP']:4d}   <- correct refusal")
    print(f"  FN (OOD + sufficient)  : {res['FN']:4d}   <- missed OOD")
    print(f"  TN (IN  + sufficient)  : {res['TN']:4d}   <- correct accept")
    print(f"  FP (IN  + insufficient): {res['FP']:4d}   <- false reject")
    print()
    print(f"Accuracy : {res['accuracy']:.4f}  ({res['TP'] + res['TN']}/{res['total']})")
    print(f"Precision: {res['precision']:.4f}  (OOD detection)")
    print(f"Recall   : {res['recall']:.4f}  (OOD detection)")
    print(f"F1       : {res['f1']:.4f}")

    if res["in_rejected"]:
        print(f"\n--- IN bị reject oan ({len(res['in_rejected'])} cases) ---")
        for q, top1 in res["in_rejected"][:10]:
            print(f"  [{top1:.4f}] {q[:80]}")

    if res["ood_accepted"]:
        print(f"\n--- OOD bị miss ({len(res['ood_accepted'])} cases) ---")
        for q, top1 in res["ood_accepted"][:10]:
            print(f"  [{top1:.4f}] {q[:80]}")

    # ── Threshold sweep ─────────────────────────────────────────────────────
    print("\n" + "=" * 80)
    print("Threshold sweep (IN vs OOD trade-off):")
    print(f"  {'thr':>5}  {'TP':>4} {'FN':>4} {'TN':>4} {'FP':>4}  {'acc':>6}  {'prec':>6}  {'rec':>6}  {'F1':>6}")
    for thr in [0.40, 0.43, 0.46, 0.48, 0.50, 0.52, 0.55, 0.57, 0.60]:
        r = eval_threshold(cases, thr)
        marker = " <-- current" if thr == args.threshold else ""
        print(f"  {thr:>5.2f}  {r['TP']:>4} {r['FN']:>4} {r['TN']:>4} {r['FP']:>4}"
              f"  {r['accuracy']:>6.4f}  {r['precision']:>6.4f}  {r['recall']:>6.4f}"
              f"  {r['f1']:>6.4f}{marker}")

    # ── Recommendation ──────────────────────────────────────────────────────
    print("\n[RECOMMENDATION]")
    best = max(
        [eval_threshold(cases, t) for t in [0.40, 0.45, 0.48, 0.50, 0.52, 0.55, 0.57, 0.60]],
        key=lambda x: x["f1"]
    )
    print(f"  Best F1 threshold: {best['threshold']:.2f}  (F1={best['f1']:.4f})")
    print(f"  FP={best['FP']} (IN rejected oan)   FN={best['FN']} (OOD missed)")

    # Prioritize recall (avoid accepting OOD = hallucination risk)
    best_rec = max(
        [eval_threshold(cases, t) for t in [0.40, 0.45, 0.48, 0.50, 0.52, 0.55, 0.57, 0.60]],
        key=lambda x: (x["recall"], -x["FP"])
    )
    print(f"  Best Recall threshold: {best_rec['threshold']:.2f}"
          f"  (Recall={best_rec['recall']:.4f}, FP={best_rec['FP']})")

    print()


if __name__ == "__main__":
    main()
