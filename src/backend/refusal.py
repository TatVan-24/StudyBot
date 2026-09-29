"""Truthful Refusal detection + classification.

Phân biệt 4 trạng thái:
  - truthful_refusal    : LLM refuse + context không đủ  → status=refusal
  - false_refusal       : LLM refuse + context đủ        → status=rejection (bug)
  - hallucination_risk  : LLM trả lời + context không đủ → tiếp pipeline, Check 3 catch
  - truthful_answer     : LLM trả lời + context đủ       → tiếp pipeline

GIAI ĐOẠN HIỆN TẠI: log_only mode.
  - Chỉ zero_hit mới trigger insufficient.
  - Threshold (score_threshold, lexical_min_ratio) chỉ để LOG, chưa dùng để reject.
  - Sau khi có ≥ 50 case có ground truth → derive threshold từ ROC curve.
"""
import re


# ── CONFIG ──────────────────────────────────────────────────────────────────
CONFIG = {
    # ✅ STRICT MODE (Approach A) — tuned 2026-09-29
    # score_threshold derive từ test 13 case: OOD max=0.4833, IN min=0.5713
    # Verified trên 130-case benchmark: F1=1.0, FP=0, FN=0 tại 0.40–0.50
    # Chọn 0.40 (rìa dưới khoảng an toàn): ưu tiên tránh FP (reject oan IN)
    "score_threshold":   0.40,   # chốt 2026-09-29 từ 130-case sweep
    "lexical_min_ratio": 0.10,   # chỉ LOG, không dùng để reject (Approach A)
    "lexical_top_k":     3,
    "log_only":          False,  # strict mode
}


STOPWORDS = {
    # Vietnamese
    "là", "và", "của", "có", "cho", "với", "trong", "một", "các", "những",
    "này", "đó", "khi", "để", "được", "không", "thì", "về", "từ", "ra",
    "vào", "lên", "xuống", "ở", "tại", "do", "bởi", "nếu", "mà", "hay",
    # English
    "the", "a", "an", "is", "are", "was", "were", "of", "in", "on", "at",
    "to", "for", "with", "and", "or", "but", "by", "as", "that", "this",
    "it", "its", "be", "been", "being", "have", "has", "had", "do", "does",
    "did", "will", "would", "can", "could", "should", "may", "might",
    "how", "what", "when", "where", "which", "who", "why", "from", "into",
}

REFUSAL_PATTERNS = re.compile(
    r"("
    r"tôi không tìm thấy|không tìm thấy đủ thông tin|"
    r"không đủ thông tin|không có thông tin|"
    r"i couldn'?t find|not enough information|"
    r"i cannot answer|i can'?t answer|"
    r"insufficient information"
    r")",
    re.IGNORECASE,
)


# ── Rule 1: Zero-hit ────────────────────────────────────────────────────────
def _is_zero_hit(chunks: list) -> bool:
    """Không có chunk nào → không đủ."""
    return not chunks


# ── Rule 2: Low-score (log-only) ────────────────────────────────────────────
def _is_low_score(chunks: list, threshold: float = None) -> bool:
    """Top-1 score < ngưỡng → không đủ."""
    if not chunks:
        return True
    if threshold is None:
        threshold = CONFIG["score_threshold"]
    top1 = chunks[0].get("score", 0.0)
    return top1 < threshold


# ── Rule 3: Lexical overlap (log-only) ──────────────────────────────────────
def _compute_lexical_ratio(query: str, chunks: list, top_k: int = None) -> float:
    """Trả về lexical overlap ratio cao nhất giữa query và top-K chunks."""
    if not chunks or not query:
        return 0.0
    if top_k is None:
        top_k = CONFIG["lexical_top_k"]

    qwords = set(re.findall(r"\w+", query.lower())) - STOPWORDS
    if not qwords:
        return 1.0  # query quá ngắn, không đánh giá được → coi như overlap đủ

    max_ratio = 0.0
    for c in chunks[:top_k]:
        text = c.get("text", "")
        if not text:
            continue
        cwords = set(re.findall(r"\w+", text.lower())) - STOPWORDS
        if not cwords:
            continue
        ratio = len(qwords & cwords) / len(qwords)
        max_ratio = max(max_ratio, ratio)
    return max_ratio


def _has_lexical_overlap(query: str, chunks: list, min_ratio: float = None) -> bool:
    """Query và top-K chunks có ít nhất min_ratio từ chung không."""
    if min_ratio is None:
        min_ratio = CONFIG["lexical_min_ratio"]
    return _compute_lexical_ratio(query, chunks) >= min_ratio


# ── Combined answerability ──────────────────────────────────────────────────
def is_context_sufficient(query: str, chunks: list) -> dict:
    """
    Trả về dict để log được từng rule.

    Strict mode (Approach A):
      sufficient = (not zero_hit) AND (top1_score >= score_threshold)
      Lexical overlap chỉ dùng để LOG, không ảnh hưởng quyết định.

    Log-only mode:
      sufficient = not zero_hit   (để thu data)
    """
    zero_hit = _is_zero_hit(chunks)

    top1_score = chunks[0].get("score", 0.0) if chunks else 0.0
    lexical_ratio = _compute_lexical_ratio(query, chunks)

    low_score = top1_score < CONFIG["score_threshold"]
    low_lex   = lexical_ratio < CONFIG["lexical_min_ratio"]

    if CONFIG["log_only"]:
        # Chỉ zero_hit mới trigger. Các rule khác CHỈ LOG.
        sufficient = not zero_hit
    else:
        # Approach A: chỉ zero_hit + low_score quyết định
        sufficient = (not zero_hit) and (not low_score)

    return {
        "sufficient": sufficient,
        "zero_hit": zero_hit,
        "low_score_would_trigger": low_score,
        "no_overlap_would_trigger": low_lex,    # log only, không ảnh hưởng quyết định
        "top1_score": round(top1_score, 4),
        "lexical_ratio": round(lexical_ratio, 4),
        "mode": "log_only" if CONFIG["log_only"] else "strict_A",
    }


# ── Refusal detection ───────────────────────────────────────────────────────
def detect_refusal(answer: str) -> bool:
    """Regex detect LLM refuse hay không."""
    if not answer:
        return False
    return bool(REFUSAL_PATTERNS.search(answer))


# ── Cross-validator ─────────────────────────────────────────────────────────
def classify(answer: str, query: str, chunks: list) -> dict:
    """
    4-way classifier:
      truthful_refusal    → status=refusal
      false_refusal       → status=rejection (reason="False refusal")
      hallucination_risk  → tiếp pipeline, Check 3 catch
      truthful_answer     → tiếp pipeline
    """
    refused = detect_refusal(answer)
    diag = is_context_sufficient(query, chunks)
    sufficient = diag["sufficient"]

    if refused and not sufficient:
        label = "truthful_refusal"
    elif refused and sufficient:
        label = "false_refusal"
    elif not refused and not sufficient:
        label = "hallucination_risk"
    else:
        label = "truthful_answer"

    return {
        "label": label,
        "refused": refused,
        "context_sufficient": sufficient,
        "diagnostics": diag,
    }
