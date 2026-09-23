"""Validators for the RAG Generation pipeline. Implements Checks 1, 2, and 3."""

def input_guardrail(query: str) -> bool:
    """
    Check 0: Input Guardrail
    Rejects greetings or extremely short queries.
    """
    query_clean = query.strip().lower()
    if len(query_clean) < 5 or query_clean in ["hi", "hello", "xin chao", "chào", "chào bạn"]:
        return False
    return True

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
        
    inputs = {"text": evidence_text, "text_pair": answer}
    outputs = classifier(inputs)
    
    scores_list = outputs[0] if isinstance(outputs[0], list) else outputs
    
    p_entailment = 0.0
    p_contradiction = 0.0
    
    for item in scores_list:
        label = item['label'].lower()
        score = item['score']
        if 'entailment' in label or label == 'label_1':
            p_entailment = score
        elif 'contradiction' in label or label == 'label_0':
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
