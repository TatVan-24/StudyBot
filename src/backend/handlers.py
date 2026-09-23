"""Endpoint handlers. Pure business logic — knows nothing about FastAPI or AWS specifics."""
import io
import uuid
from typing import Optional


PROMPT_TEMPLATE = """You are a Study Assistant for AWS StudyBot.

TASK:
Help users study based on the provided documents. You can:
- Summarize content
- Create reports
- Generate study guides
- Create flashcards
- Generate practice exams

CONSTRAINTS:
- ONLY use the provided context.
- NEVER use outside knowledge.
- If context is insufficient, say so clearly.

CITATIONS:
- Cite sources using [chunk_id] format.
- Only cite chunks provided in the context.

OUTPUT:
- Return answer in plain text.
- Answer in the same language as the query.
- Be concise and factual.

REFUSAL:
- If context is insufficient, respond: "I couldn't find enough information in the provided documents to answer this question."

CONTEXT:
{context}

QUESTION: {question}

ANSWER:"""


def _extract_text(filename: str, data: bytes) -> str:
    """Extract plain text from PDF or .txt upload."""
    name = filename.lower()
    if name.endswith(".pdf"):
        try:
            from pypdf import PdfReader
        except ImportError:
            return "(pypdf not installed — install requirements.txt)"
        reader = PdfReader(io.BytesIO(data))
        return "\n\n".join(page.extract_text() or "" for page in reader.pages)
    # Default: assume UTF-8 text
    try:
        return data.decode("utf-8", errors="replace")
    except Exception:
        return ""


def handle_upload(
    user_id: str,
    filename: str,
    data: bytes,
    storage,
    userstore,
    vector_store,
) -> dict:
    """Store the file, extract text, ingest into vector store, record in userstore."""
    doc_id = str(uuid.uuid4())
    key = f"{user_id}/{doc_id}/{filename}"
    location = storage.put(key, data)
    text = _extract_text(filename, data)
    if text.strip():
        vector_store.ingest(doc_id=doc_id, text=text, metadata={"user_id": user_id, "filename": filename})
    userstore.add_doc(
        user_id=user_id,
        doc_id=doc_id,
        metadata={"filename": filename, "size": len(data), "location": location, "chars": len(text)},
    )
    return {
        "doc_id": doc_id,
        "filename": filename,
        "size": len(data),
        "chars_extracted": len(text),
        "location": location,
    }


def handle_delete_query(user_id: str, query_id: int, userstore) -> dict:
    if hasattr(userstore, 'delete_query'):
        userstore.delete_query(user_id, query_id)
        return {"status": "deleted", "query_id": query_id}
    return {"status": "error", "detail": "User store does not support deleting queries yet."}

def handle_query(
    user_id: str,
    question: str,
    ai_client,
    userstore,
    vector_store,
    vector_backend: str,
    bedrock_kb_id: str,
) -> dict:
    """RAG flow: retrieve user's relevant chunks → call AI with context → log + return."""
    import time
    import uuid
    from backend import validators
    
    t0 = time.time()
    
    # helper for early return
    def _make_response(ans: str, status: str, citations: list = None, meta: dict = None):
        t_total_end = time.time()
        userstore.log_query(user_id=user_id, query=question, answer=ans)
        
        meta = meta or {}
        if "latency_ms" not in meta:
            meta["latency_ms"] = {"total": int((t_total_end - t0) * 1000)}
            
        return {
            "query_id": str(uuid.uuid4()),
            "status": status,
            "data": {
                "answer": ans,
                "citations": citations or [],
                "metadata": meta
            }
        }
    
    if vector_backend == "bedrock_kb":
        # Production path: let Bedrock do retrieve + generate in one call
        result = ai_client.retrieve_and_generate(query=question, kb_id=bedrock_kb_id)
        return _make_response(result["answer"], "success", result.get("citations", []))
        
    # ---------------------------------------------------------
    # LOCAL PATH (Phase 2 with Check 1, 2, 3)
    # ---------------------------------------------------------
    
    # B0. Input Guardrail
    if not validators.input_guardrail(question):
        return _make_response(
            ans="Vui lòng đặt câu hỏi cụ thể hơn liên quan đến nội dung tài liệu.",
            status="rejection",
            meta={"is_answerable": False, "reason": "Input Guardrail Failed: Greeting or too short"}
        )
        
    # B1. Retrieval
    t_ret_start = time.time()
    chunks = vector_store.search(question, top_k=3)
    t_ret_end = time.time()
    latency_retrieval = int((t_ret_end - t_ret_start) * 1000)
    
    # Ensure chunk_id is extracted correctly from metadata for validators
    for c in chunks:
        if "metadata" in c and "chunk_id" in c["metadata"]:
            c["doc_id"] = c["metadata"]["chunk_id"] # temporary remap to allow validators to use 'doc_id' field as chunk id
            
    # B2. Check 1: Evidence Sufficiency
    if not validators.check_1_sufficiency(chunks):
        return _make_response(
            ans="Tôi không tìm thấy đủ thông tin trong tài liệu để trả lời câu hỏi này.",
            status="rejection",
            meta={
                "is_answerable": False,
                "reason": "Check 1 Failed: Evidence insufficient",
                "latency_ms": {"retrieval": latency_retrieval}
            }
        )
        
    # B3. Generation
    t_gen_start = time.time()
    res = ai_client.generate_with_citations(question, chunks)
    t_gen_end = time.time()
    latency_generation = int((t_gen_end - t_gen_start) * 1000)
    
    base_meta = {
        "is_answerable": True,
        "latency_ms": {
            "retrieval": latency_retrieval,
            "generation": latency_generation
        }
    }
    
    # B4. Check 2: Citation Validity
    check2_status = validators.check_2_citations(res.get("citations", []), chunks)
    if check2_status == "MISSING":
        base_meta["reason"] = "Check 2 Failed: No citation provided"
        return _make_response(res["answer"], "rejection", res.get("citations"), base_meta)
    elif check2_status == "INVALID":
        base_meta["reason"] = "Check 2 Failed: Hallucinated citation"
        return _make_response(res["answer"], "ambiguous", res.get("citations"), base_meta)
        
    # B5. Check 3: Claim Grounding (Answer-level aggregation)
    # Split the answer into claims (naively by sentence for now)
    import re
    sentences = [s.strip() for s in re.split(r'[.!?\n]', res["answer"]) if s.strip()]
    
    # We aggregate Check 3 status over all claims that have a citation
    check3_results = []
    for claim in sentences:
        # Extract cited chunk ids from this specific claim
        cited_in_claim = re.findall(r"\[(.*?)\]", claim)
        if not cited_in_claim:
            continue
            
        # Build evidence text for just the chunks cited in this claim
        # If no specific chunk matched, or to be safe, we can just pass all chunks
        # that were cited.
        evidence_texts = []
        for cid in cited_in_claim:
            for c in chunks:
                if c.get("doc_id", "") == cid:
                    evidence_texts.append(c.get("text", ""))
                    
        claim_evidence = " ".join(evidence_texts)
        if not claim_evidence:
            continue
            
        status = validators.check_3_grounding(claim, chunks=[{"text": claim_evidence}])
        check3_results.append(status)
        
    if not check3_results:
        # Fallback if no claims could be parsed properly but check 2 passed
        overall_grounding = "GROUNDED"
    elif "CONTRADICTION" in check3_results:
        overall_grounding = "CONTRADICTION"
    elif "AMBIGUOUS" in check3_results:
        overall_grounding = "AMBIGUOUS"
    else:
        overall_grounding = "GROUNDED"

    if overall_grounding == "CONTRADICTION":
        base_meta["reason"] = "Check 3 Failed: Contradiction detected"
        return _make_response(res["answer"], "rejection", res.get("citations"), base_meta)
    elif overall_grounding == "AMBIGUOUS":
        base_meta["reason"] = "Check 3 Failed: Ambiguous grounding"
        return _make_response(res["answer"], "ambiguous", res.get("citations"), base_meta)
        
    # B6. Output Guardrail
    if not validators.output_guardrail(res):
        base_meta["reason"] = "Output Guardrail Failed"
        return _make_response(res["answer"], "ambiguous", res.get("citations"), base_meta)
        
    # B7. Status (Success)
    return _make_response(res["answer"], "acceptance", res.get("citations"), base_meta)


def handle_list_docs(user_id: str, userstore) -> dict:
    return {"user_id": user_id, "docs": userstore.list_docs(user_id)}


def handle_recent_queries(user_id: str, userstore, limit: int = 10) -> dict:
    return {"user_id": user_id, "queries": userstore.recent_queries(user_id, limit=limit)}
