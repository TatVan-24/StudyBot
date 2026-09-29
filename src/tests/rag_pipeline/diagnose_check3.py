"""Check 3 isolated diagnostic. Per-claim evidence, no LLM call."""
import json
import re
from dataclasses import dataclass, field, asdict
from typing import Optional

# ── Frozen config — KHÔNG import từ validators.py ──────────────
HIGH_E = 0.50
HIGH_C = 0.70
NLI_MODEL_NAME = "MoritzLaurer/mDeBERTa-v3-base-mnli-xnli"
NLI_MAX_TOKENS = 512


# ── Data model ─────────────────────────────────────────────────
@dataclass
class ClaimRecord:
    case_id: str
    claim_index: int
    claim_text: str

    cited_ids: list
    evidence_chunk_ids: list
    evidence_text: str

    skipped: bool
    skip_reason: Optional[str]

    p_e: Optional[float] = None
    p_n: Optional[float] = None
    p_c: Optional[float] = None

    evidence_tokens: Optional[int] = None
    claim_tokens: Optional[int] = None
    total_tokens: Optional[int] = None
    truncated: Optional[bool] = None

    check3_status: Optional[str] = None

    expected_check3: Optional[str] = None
    pass_: Optional[bool] = None

    nli_raw: list = field(default_factory=list)


# ── NLI singleton ──────────────────────────────────────────────
_nli = None

def load_nli():
    global _nli
    if _nli is None:
        from transformers import pipeline, AutoTokenizer
        _nli = {
            "pipe": pipeline("text-classification",
                             model=NLI_MODEL_NAME, top_k=None),
            "tok":  AutoTokenizer.from_pretrained(NLI_MODEL_NAME),
        }
    return _nli


def run_nli(evidence: str, claim: str) -> dict:
    nli = load_nli()
    pipe, tok = nli["pipe"], nli["tok"]

    ev_tok = len(tok.encode(evidence, add_special_tokens=False))
    cl_tok = len(tok.encode(claim, add_special_tokens=False))
    truncated = (ev_tok + cl_tok) > NLI_MAX_TOKENS

    outputs = pipe({"text": evidence, "text_pair": claim})
    scores_list = outputs[0] if isinstance(outputs[0], list) else outputs

    p_e = p_n = p_c = 0.0
    for item in scores_list:
        lbl = item["label"].lower()
        if "entail" in lbl:        p_e = item["score"]
        elif "neutral" in lbl:     p_n = item["score"]
        elif "contradict" in lbl:  p_c = item["score"]

    return {
        "p_e": round(p_e, 4), "p_n": round(p_n, 4), "p_c": round(p_c, 4),
        "raw": scores_list,
        "evidence_tokens": ev_tok, "claim_tokens": cl_tok,
        "truncated": truncated,
    }


# ── Rule (frozen contract) ─────────────────────────────────────
def apply_check3_rule(p_e: float, p_c: float) -> str:
    if p_c >= HIGH_C:  return "CONTRADICTION"
    if p_e >= HIGH_E:  return "GROUNDED"
    return "AMBIGUOUS"

def _extract_relevant_evidence(claim: str, evidence: str, max_tokens: int = 200) -> str:
    if not evidence:
        return evidence

    sentences = re.split(r'(?<=[.!?])\s+(?=[A-ZÀ-Ỹ0-9])', evidence)
    if len(sentences) <= 1:
        return evidence

    claim_words = set(re.findall(r'\w+', claim.lower()))
    if not claim_words:
        return evidence[:max_tokens * 4]

    scored = []
    for i, sent in enumerate(sentences):
        sent_words = set(re.findall(r'\w+', sent.lower()))
        if not sent_words:
            continue
        overlap = len(claim_words & sent_words) / len(claim_words)
        scored.append((overlap, i, sent))

    if not scored:
        return evidence[:max_tokens * 4]

    scored.sort(reverse=True)
    top_indices = sorted([i for _, i, _ in scored[:3]])
    selected = " ".join(sentences[i] for i in top_indices)

    if len(selected) > max_tokens * 4:
        selected = selected[:max_tokens * 4]

    return selected


# ── Evaluate 1 claim ───────────────────────────────────────────
def evaluate_claim(case: dict, claim: dict) -> ClaimRecord:
    expected = case.get("expected_check3")

    # Claim bị skip — không tính vào accuracy
    if claim["skipped"]:
        return ClaimRecord(
            case_id=case["case_id"], claim_index=claim["index"],
            claim_text=claim["text"],
            cited_ids=claim["cited_ids"], evidence_chunk_ids=[],
            evidence_text="",
            skipped=True, skip_reason=claim["skip_reason"],
            expected_check3=expected, pass_=None,
        )

    # NLI trên PER-CLAIM evidence (chỉ chunk claim này cite)
    evidence_extracted = _extract_relevant_evidence(claim["text"], claim["evidence_text"], max_tokens=200)
    nli = run_nli(evidence_extracted, claim["text"])
    check3 = apply_check3_rule(nli["p_e"], nli["p_c"])

    pass_ = (check3 == expected) if expected is not None else None

    return ClaimRecord(
        case_id=case["case_id"], claim_index=claim["index"],
        claim_text=claim["text"],
        cited_ids=claim["cited_ids"],
        evidence_chunk_ids=claim["evidence_chunk_ids"],
        evidence_text=claim["evidence_text"],
        skipped=False, skip_reason=None,
        p_e=nli["p_e"], p_n=nli["p_n"], p_c=nli["p_c"],
        evidence_tokens=nli["evidence_tokens"],
        claim_tokens=nli["claim_tokens"],
        total_tokens=nli["evidence_tokens"] + nli["claim_tokens"],
        truncated=nli["truncated"],
        check3_status=check3,
        expected_check3=expected, pass_=pass_,
        nli_raw=nli["raw"],
    )


# ── Eligibility (case-level) ───────────────────────────────────
def is_eligible(case: dict) -> tuple[bool, str]:
    if case.get("check2_status") != "VALID":
        return False, f"check2_{case.get('check2_status','?').lower()}"
    return True, "eligible"


# ── Logging ────────────────────────────────────────────────────
def log_claim(rec: ClaimRecord):
    exp = rec.expected_check3 or "(none)"
    passed = "-" if rec.pass_ is None else str(rec.pass_)

    if rec.skipped:
        print(f"[CASE]  {rec.case_id}#{rec.claim_index}  SKIPPED ({rec.skip_reason})")
        print(f"[CLAIM] {rec.claim_text[:100]}")
        print(f"[CITED] {rec.cited_ids}")
        print("-" * 70)
        return

    print(f"[CASE]  {rec.case_id}#{rec.claim_index}")
    print(f"[CLAIM] {rec.claim_text[:100]}")
    print(f"[EVID]  chunks={rec.evidence_chunk_ids}  tokens={rec.evidence_tokens}")
    print(f"[NLI]   E={rec.p_e:.4f}  N={rec.p_n:.4f}  C={rec.p_c:.4f}")
    print(f"[TOK]   total={rec.total_tokens}  truncated={rec.truncated}")
    print(f"[RULE]  E>={HIGH_E}? {rec.p_e >= HIGH_E}  C>={HIGH_C}? {rec.p_c >= HIGH_C}")
    print(f"[OUT]   {rec.check3_status}  expected={exp}  pass={passed}")
    print("-" * 70)


# ── Summary ────────────────────────────────────────────────────
def build_summary(records: list[ClaimRecord], skipped_cases: list) -> dict:
    evaluated = [r for r in records if not r.skipped]
    skipped   = [r for r in records if r.skipped]

    by_status = {"GROUNDED": 0, "AMBIGUOUS": 0, "CONTRADICTION": 0}
    for r in evaluated:
        by_status[r.check3_status] += 1

    skip_reasons = {}
    for r in skipped:
        skip_reasons[r.skip_reason] = skip_reasons.get(r.skip_reason, 0) + 1

    labelled = [r for r in evaluated if r.expected_check3 is not None]

    cross = {}
    for r in labelled:
        k = f"{r.expected_check3}->{r.check3_status}"
        cross[k] = cross.get(k, 0) + 1

    failures = [
        {"case_id": r.case_id, "claim_index": r.claim_index,
         "claim": r.claim_text[:80],
         "expected": r.expected_check3, "actual": r.check3_status,
         "p_e": r.p_e, "p_n": r.p_n, "p_c": r.p_c,
         "truncated": r.truncated}
        for r in labelled if not r.pass_
    ]

    return {
        "total_claims": len(records),
        "evaluated_claims": len(evaluated),
        "skipped_claims": len(skipped),
        "skipped_by_reason": skip_reasons,
        "status_distribution": by_status,
        "expected_vs_actual_on_labelled": cross,
        "claim_accuracy_on_labelled": (
            round(sum(1 for r in labelled if r.pass_) / len(labelled), 4)
            if labelled else None
        ),
        "failures": failures,
        "skipped_cases": skipped_cases,
    }


# ── Main ───────────────────────────────────────────────────────
def main():
    import os
    INPUT   = "outputs/e2e_dump.jsonl"
    OUT     = "outputs/check3_claims.jsonl"
    SUMMARY = "outputs/check3_summary.json"

    os.makedirs("outputs", exist_ok=True)

    cases = []
    with open(INPUT, "r", encoding="utf-8") as f:
        for line in f:
            cases.append(json.loads(line))

    print(f"[*] Loaded {len(cases)} cases")

    all_records = []
    skipped_cases = []

    for case in cases:
        ok, reason = is_eligible(case)
        if not ok:
            skipped_cases.append({"case_id": case["case_id"], "reason": reason})
            continue

        for claim in case["claims"]:
            rec = evaluate_claim(case, claim)
            log_claim(rec)
            all_records.append(rec)

    summary = build_summary(all_records, skipped_cases)

    with open(OUT, "w", encoding="utf-8") as f:
        for r in all_records:
            f.write(json.dumps(asdict(r), ensure_ascii=False) + "\n")

    with open(SUMMARY, "w", encoding="utf-8") as f:
        json.dump(summary, f, indent=2, ensure_ascii=False)

    print("\n" + "=" * 70)
    print(f"Total claims:      {summary['total_claims']}")
    print(f"Evaluated:         {summary['evaluated_claims']}")
    print(f"Skipped:           {summary['skipped_claims']}  {summary['skipped_by_reason']}")
    print()
    print("Check 3 distribution:")
    for k, v in summary["status_distribution"].items():
        print(f"  {k:14s}: {v}")
    print()
    print("Expected → Actual (labelled):")
    for k, v in summary["expected_vs_actual_on_labelled"].items():
        print(f"  {k}: {v}")
    print()
    print(f"Claim accuracy: {summary['claim_accuracy_on_labelled']}")
    print(f"\nFailures ({len(summary['failures'])}):")
    for f in summary["failures"][:20]:
        print(f"  {f['case_id']}#{f['claim_index']}: "
              f"{f['expected']}->{f['actual']}  "
              f"(E={f['p_e']} N={f['p_n']} C={f['p_c']}, trunc={f['truncated']})")


if __name__ == "__main__":
    main()
