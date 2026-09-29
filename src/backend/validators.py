"""Validators for the RAG Generation pipeline. Implements Checks 1, 2, and 3."""

import re

# ═══════════════════════════════════════════════════════════
# [T1 Input Guardrail] Injection Detection
# ═══════════════════════════════════════════════════════════

# Known injection patterns (case-insensitive)
INJECTION_PATTERNS = [
    # English — ignore instructions
    r"ignore\s+(all\s+)?(previous|above|prior|earlier)\s+instructions?",
    r"disregard\s+(all\s+)?(previous|above|prior)\s+",
    r"forget\s+(all\s+)?(previous|above)",

    # English — reveal prompt
    r"reveal\s+(your|the|all)\s+(system|developer|hidden|secret)",
    r"(print|show|tell)\s+(me\s+)?(your|the)\s+(system\s+)?prompt",
    r"(print|show)\s+(your|the)\s+(developer|hidden)\s+",
    r"what\s+(is|are)\s+your\s+(system|initial)\s+(prompt|instruction)",

    # English — override
    r"you\s+are\s+no\s+longer\s+",
    r"from\s+now\s+on\s+(you|treat|ignore)",
    r"treat\s+this\s+(message|as)\s+",
    r"override\s+(your|all|previous)",
    r"new\s+instructions?:",
    r"system\s*:\s*you\s+are",

    # English — exfil
    r"(dump|give\s+me|show\s+me|list)\s+(all|every|the\s+entire)\s+(documents?|database|knowledge|corpus)",
    r"(dump|export)\s+(the\s+)?(vector|entire)\s+(database|index)",
    r"reveal\s+the\s+(hidden|private|internal)\s+",
    r"(api\s+key|secret|credential|password)",

    # English — jailbreak
    r"DAN\s+mode",
    r"(pretend|act|roleplay)\s+(you\s+are|as)\s+",
    r"hypothetically\s+speaking",

    # Vietnamese
    r"bỏ\s+qua\s+(mọi|tất\s+cả|các)\s+(hướng\s+dẫn|instruction)",
    r"tiết\s+lộ\s+(system|prompt|hướng\s+dẫn)",
    r"cho\s+(tôi|mình)\s+(toàn\s+bộ|xem)\s+(tài\s+liệu|database|corpus)",
    r"(in|hiển\s+thị)\s+(system\s+prompt|hướng\s+dẫn\s+hệ\s+thống)",
    r"từ\s+giờ\s+(trở\s+đi|hãy)",
]

COMPILED_PATTERNS = [re.compile(p, re.IGNORECASE) for p in INJECTION_PATTERNS]

def detect_injection(query: str) -> bool:
    """
    T1: Detect known injection patterns.
    Return True nếu phát hiện injection.
    """
    if not query:
        return False

    for pattern in COMPILED_PATTERNS:
        if pattern.search(query):
            return True
    return False

def input_guardrail(query: str) -> tuple[bool, str]:
    """
    Input Guardrail tổng hợp.

    Returns:
        (passed: bool, reason: str)
        - (True, "") nếu pass
        - (False, "reason") nếu fail
    """
    query_clean = query.strip()

    # T2: Query validation
    if not query_clean:
        return False, "Empty query"
    if len(query_clean) < 2:
        return False, "Query too short"

    # T1: Injection detection
    if detect_injection(query_clean):
        return False, "Injection pattern detected"

    # Legacy: greeting detection (giữ để backward compat)
    if query_clean.lower() in ["hi", "hello", "xin chao", "chào", "chào bạn"]:
        return False, "Greeting not supported"

    return True, ""

def check_1_sufficiency(chunks: list) -> bool:
    """
    Check 1: Evidence Sufficiency
    Currently using Dense thresholds since vector_store doesn't have BGE yet.
    is_sufficient = (dense_top1 >= 0.55) AND (dense_gap >= 0.005)
    """
    if not chunks:
        return False

    scores = [c.get("score", 0.0) for c in chunks]

    if len(scores) == 0:
        return False

    dense_top1 = scores[0]
    dense_gap = 0.0

    if len(scores) >= 2:
        dense_gap = scores[0] - scores[1]

    return (dense_top1 >= 0.55) and (dense_gap >= 0.005)

def check_2_citations(citations: list, chunks: list) -> str:
    """
    Check 2: Citation Validity
    Ensures that every citation cited by the LLM actually exists in the retrieved chunks.
    Returns:
    - 'VALID' if all citations exist in retrieved chunks.
    - 'INVALID' if it hallucinated a citation.
    - 'MISSING' if no citations were provided.
    """
    if not citations:
        return "MISSING"

    retrieved_ids = {c.get("doc_id", "") for c in chunks}
    if not retrieved_ids:
        # If there are no retrieved docs, but LLM made citations
        return "INVALID"

    for citation in citations:
        chunk_id = citation.get("chunk_id", "")
        if chunk_id not in retrieved_ids:
            return "INVALID"

    return "VALID"

# Global singleton for NLI model to avoid reloading
_nli_classifier = None

def get_nli_classifier():
    global _nli_classifier
    if _nli_classifier is None:
        try:
            from transformers import pipeline
            _nli_classifier = pipeline("text-classification", model="MoritzLaurer/mDeBERTa-v3-base-mnli-xnli", top_k=None)
        except Exception as e:
            print(f"Failed to load NLI model: {e}")
            return None
    return _nli_classifier

def _extract_relevant_evidence(claim: str, evidence: str, max_tokens: int = 200) -> str:
    """
    Chỉ giữ 2-3 câu trong evidence có lexical overlap cao nhất với claim.
    Tránh NLI bị truncate hoặc loãng bởi nội dung lạc đề.
    """
    if not evidence:
        return evidence

    # Split evidence thành câu (đơn giản, an toàn với số thập phân)
    sentences = re.split(r'(?<=[.!?])\s+(?=[A-ZÀ-Ỹ0-9])', evidence)
    if len(sentences) <= 1:
        return evidence

    # Lexical overlap với claim
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

    # Top-3 sentences theo overlap, restore order gốc
    scored.sort(reverse=True)
    top_indices = sorted([i for _, i, _ in scored[:3]])
    selected = " ".join(sentences[i] for i in top_indices)

    # Enforce token budget (rough estimate ~4 chars/token)
    if len(selected) > max_tokens * 4:
        selected = selected[:max_tokens * 4]

    return selected

def check_3_grounding(answer: str, chunks: list) -> str:
    """
    Check 3: Claim Grounding
    Runs mDeBERTa NLI to classify the relationship between the retrieved evidence and the generated answer.
    Returns: "GROUNDED", "CONTRADICTION", or "AMBIGUOUS"
    """
    classifier = get_nli_classifier()
    if not classifier:
        # If model can't be loaded, fallback to AMBIGUOUS or GROUNDED depending on strictness
        return "AMBIGUOUS"

    evidence_text = " ".join([c.get("text", "") for c in chunks])
    if not evidence_text.strip():
        return "AMBIGUOUS"

    # NEW: filter evidence trước khi NLI
    evidence_text = _extract_relevant_evidence(answer, evidence_text, max_tokens=200)

    inputs = {"text": evidence_text, "text_pair": answer}
    outputs = classifier(inputs)

    scores_list = outputs[0] if isinstance(outputs[0], list) else outputs

    p_entailment = 0.0
    p_contradiction = 0.0

    for item in scores_list:
        label = item['label'].lower()
        score = item['score']
        if 'entail' in label:
            p_entailment = score
        elif 'contradict' in label:
            p_contradiction = score

    HIGH_E = 0.50
    HIGH_C = 0.70

    if p_contradiction >= HIGH_C:
        return "CONTRADICTION"
    if p_entailment >= HIGH_E:
        return "GROUNDED"

    return "AMBIGUOUS"

def output_guardrail(res: dict) -> bool:
    """
    Ensures the output doesn't contain forbidden patterns or completely failed generation.
    Returns True if safe, False if it violates guardrails.
    """
    answer = res.get("answer", "")
    # Add any specific block words or basic guardrails here
    if "Lỗi khi gọi mô hình" in answer:
        return False
    return True
