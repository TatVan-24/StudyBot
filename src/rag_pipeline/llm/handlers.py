"""Endpoint handlers. Pure business logic — knows nothing about FastAPI or AWS specifics."""
import io
import uuid
import json
import re
import time
from datetime import datetime
from pathlib import Path
from typing import Optional

LOG_DIR = Path("_data/logs")
LOG_DIR.mkdir(parents=True, exist_ok=True)


# ── Helpers ───────────────────────────────────────────────────────────────────

def _default_strategy() -> dict:
    return {"retrieval": "dense", "rerank": None, "gate": None}


def _default_scores() -> dict:
    return {"retrieval_top1": None, "rerank_top1": None, "answerability_score": None}


def _build_scores(chunks: list) -> dict:
    if not chunks:
        return _default_scores()
    return {
        "retrieval_top1": round(chunks[0].get("score", 0.0), 4),
        "rerank_top1": None,
        "answerability_score": None,
    }


def _write_query_log(response: dict, user_id: str, query: str):
    log_file = LOG_DIR / f"{datetime.utcnow().strftime('%Y-%m-%d')}.jsonl"
    meta = response.get("metadata", {})
    record = {
        "timestamp": datetime.utcnow().isoformat() + "Z",
        "user_id": user_id,
        "query": query,
        "session_id": response.get("session_id"),
        "status": meta.get("status"),
        "answer": meta.get("answer"),
        "strategy": meta.get("strategy"),
        "scores": meta.get("scores"),
        "citations": meta.get("citations"),
        "metrics": meta.get("metrics"),
        "reason": meta.get("reason"),
    }
    with open(log_file, "a", encoding="utf-8") as f:
        f.write(json.dumps(record, ensure_ascii=False) + "\n")


def _make_response(
    session_id: str,
    user_id: str,
    query: str,
    answer: str,
    status: str,
    citations: list = None,
    strategy: dict = None,
    scores: dict = None,
    latency: dict = None,
    reason: str = None,
    model_used: str = None,
    userstore=None,
    skip_log: bool = False,
) -> dict:
    """Build Output Contract 8.2 response. Optionally logs to DB + JSONL file."""
    response = {
        "session_id": session_id,
        "user_id": user_id,
        "metadata": {
            "status": status,
            "answer": answer,
            "strategy": strategy or _default_strategy(),
            "scores": scores or _default_scores(),
            "citations": citations or [],
            "metrics": {"latency_ms": latency or {}},
        },
    }
    if reason:
        response["metadata"]["reason"] = reason
    if model_used:
        response["metadata"]["model_used"] = model_used

    if not skip_log and userstore:
        turn_index = userstore.next_turn_index(session_id)
        userstore.log_query(
            session_id=session_id,
            turn_index=turn_index,
            user_id=user_id,
            query=query,
            answer=answer,
            status=status,
            reason=reason,
        )
        userstore.update_session_activity(session_id)

    _write_query_log(response, user_id, query)
    return response


# ── Text extraction ────────────────────────────────────────────────────────────

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
- ALWAYS place citations inline immediately after the relevant claim, e.g., "S3 Glacier costs $0.004/GB [sha256:abc123]."
- NEVER use Markdown footnotes [^1], [^2].
- NEVER write a "References", "Chú thích", or footnote definitions section.
- Every factual claim MUST have exactly one [chunk_id] citation at the end.
- EXCEPTION: refusal sentences do NOT need citations.
- Only cite chunks provided in the context.

CITATION PRECISION:
- ONLY cite chunks that contain the EXACT information of your claim.
- DO NOT cite chunks that merely share a topic.
- If no chunk contains the specific information → rewrite the claim to match a chunk, or drop the claim.
- WRONG: claim says "millions of records" but cites chunk without that number.
- CORRECT: claim says "S3 = $0.004/GB" cites chunk containing "$0.004".

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
    """Extract plain text from PDF or .txt upload.

    Handles UTF-16LE/BE BOMs — common when files are created by PowerShell
    `echo "..." > file.txt` on Windows (which writes UTF-16LE by default).
    """
    name = filename.lower()
    if name.endswith(".pdf"):
        try:
            from pypdf import PdfReader
        except ImportError:
            return "(pypdf not installed — install requirements.txt)"
        reader = PdfReader(io.BytesIO(data))
        return "\n\n".join(page.extract_text() or "" for page in reader.pages)

    # Detect BOM for text files
    if data[:2] == b'\xff\xfe':       # UTF-16 LE
        return data[2:].decode("utf-16-le", errors="replace")
    if data[:2] == b'\xfe\xff':       # UTF-16 BE
        return data[2:].decode("utf-16-be", errors="replace")
    if data[:3] == b'\xef\xbb\xbf':   # UTF-8 BOM
        return data[3:].decode("utf-8", errors="replace")

    # Default: UTF-8
    try:
        return data.decode("utf-8", errors="replace")
    except Exception:
        return ""


# ── Upload ────────────────────────────────────────────────────────────────────

def handle_upload(
    user_id: str,
    filename: str,
    data: bytes,
    storage,
    userstore,
    vector_store,
    session_id: Optional[str] = None,
) -> dict:
    """Store file, ingest into vector store, register in session.

    - session_id provided → add doc to existing session (max 10 check).
    - session_id missing  → auto-create new session named after the file.
    """
    doc_id = str(uuid.uuid4())
    key = f"{user_id}/{doc_id}/{filename}"
    location = storage.put(key, data)
    text = _extract_text(filename, data)

    # ── Session resolution ─────────────────────────────────────────────────
    if session_id:
        session = userstore.get_session(session_id, user_id)
        if not session:
            return {"error": "Session not found or unauthorized", "status": 404}
        if userstore.count_session_docs(session_id) >= 10:
            return {"error": "Session document limit (10) reached", "status": 400}
    else:
        title = filename.rsplit(".", 1)[0] if "." in filename else filename
        session_id = userstore.create_session(user_id, title=title)

    # ── Ingest into vector store ───────────────────────────────────────────
    if text.strip():
        vector_store.ingest(
            doc_id=doc_id,
            text=text,
            metadata={"user_id": user_id, "filename": filename},
            user_id=user_id,
            session_id=session_id,
        )

    # ── Persist in userstore ───────────────────────────────────────────────
    userstore.add_doc(
        user_id=user_id,
        doc_id=doc_id,
        metadata={"filename": filename, "size": len(data), "location": location, "chars": len(text)},
    )
    userstore.add_doc_to_session(session_id, doc_id)

    return {
        "doc_id": doc_id,
        "session_id": session_id,
        "filename": filename,
        "size": len(data),
        "chars_extracted": len(text),
        "location": location,
    }


# ── Query ─────────────────────────────────────────────────────────────────────

def handle_query(
    session_id: str,
    user_id: str,
    query: str,
    ai_client,
    userstore,
    vector_store,
    vector_backend: str,
    bedrock_kb_id: str,
) -> dict:
    """Session-scoped RAG flow with Output Contract 8.2.

    Input contract:  { session_id, user_id, query }
    Output contract: { session_id, user_id, metadata: { status, answer, ... } }
    """
    from src.backend import validators
    from src.backend import refusal as refusal_mod

    t0 = time.time()

    # Shared early-exit helper
    def _reject(answer: str, reason: str, latency: dict = None) -> dict:
        return _make_response(
            session_id=session_id,
            user_id=user_id,
            query=query,
            answer=answer,
            status="rejection",
            reason=reason,
            latency=latency or {"total": int((time.time() - t0) * 1000)},
            userstore=userstore,
        )

    def _ambiguous(answer: str, citations: list, reason: str, latency: dict) -> dict:
        return _make_response(
            session_id=session_id,
            user_id=user_id,
            query=query,
            answer=answer,
            status="ambiguous",
            citations=citations,
            reason=reason,
            latency=latency,
            userstore=userstore,
        )

    def _refusal_response(answer: str, citations: list, reason: str, latency: dict) -> dict:
        """Trả về status='refusal' — LLM từ chối hợp lệ do context không đủ."""
        return _make_response(
            session_id=session_id,
            user_id=user_id,
            query=query,
            answer=answer,
            status="refusal",
            citations=citations,
            reason=reason,
            latency=latency,
            userstore=userstore,
        )

    # ── Bedrock path (production) ──────────────────────────────────────────
    if vector_backend == "bedrock_kb":
        result = ai_client.retrieve_and_generate(query=query, kb_id=bedrock_kb_id)
        return _make_response(
            session_id=session_id,
            user_id=user_id,
            query=query,
            answer=result["answer"],
            status="acceptance",
            citations=result.get("citations", []),
            latency={"total": int((time.time() - t0) * 1000)},
            userstore=userstore,
        )

    # ── Local path ────────────────────────────────────────────────────────

    # [1] Validate session
    session = userstore.get_session(session_id, user_id)
    if not session:
        return _make_response(
            session_id=session_id,
            user_id=user_id,
            query=query,
            answer="Session không tồn tại hoặc bạn không có quyền truy cập.",
            status="rejection",
            reason="Session not found or unauthorized",
            userstore=userstore,
            skip_log=True,
        )

    # [2] Check session has docs
    session_docs = userstore.get_session_docs(session_id)
    if not session_docs:
        return _reject(
            answer="Session này chưa có tài liệu nào. Vui lòng upload tài liệu trước.",
            reason="No documents in session",
        )

    # [3] Input Guardrail
    passed, reason = validators.input_guardrail(query)
    if not passed:
        return _reject(
            answer="Yêu cầu không hợp lệ. Vui lòng đặt câu hỏi cụ thể về tài liệu.",
            reason=f"Input Guardrail: {reason}",
        )

    # [4] Session-scoped retrieval
    t_ret = time.time()
    chunks = vector_store.search(query, top_k=3, session_id=session_id)
    latency_retrieval = int((time.time() - t_ret) * 1000)

    # Remap chunk_id for validators
    for c in chunks:
        if "metadata" in c and "chunk_id" in c["metadata"]:
            c["doc_id"] = c["metadata"]["chunk_id"]

    # [5] Check 1: Evidence Sufficiency
    # ═══════════════════════════════════════════════════════════
    # [TEMP BYPASS — Fix A] Bỏ threshold check, chỉ check có chunks
    # Lý do: threshold 0.55 calibrate cho BGE, không phù hợp dense MPNet
    # Rollback: comment block dưới, uncomment block trên
    # ═══════════════════════════════════════════════════════════
    if not chunks:
        return _reject(
            answer="Tôi không tìm thấy tài liệu nào trong session này.",
            reason="No chunks retrieved",
            latency={"retrieval": latency_retrieval, "total": int((time.time() - t0) * 1000)},
        )
    # if not validators.check_1_sufficiency(chunks):
    #     return _reject(
    #         answer="Tôi không tìm thấy đủ thông tin trong tài liệu để trả lời câu hỏi này.",
    #         reason="Check 1 Failed: Evidence insufficient",
    #         latency={"retrieval": latency_retrieval, "total": int((time.time() - t0) * 1000)},
    #     )
    # [TEMP BYPASS END]

    # [6] Generation
    t_gen = time.time()
    res = ai_client.generate_with_citations(query, chunks)
    latency_generation = int((time.time() - t_gen) * 1000)
    latency_total = int((time.time() - t0) * 1000)

    base_latency = {
        "retrieval": latency_retrieval,
        "generation": latency_generation,
        "total": latency_total,
    }

    # [7] Check 2: Citation Validity
    check2 = validators.check_2_citations(res.get("citations", []), chunks)

    # ── Truthful Refusal Gate ──────────────────────────────────────────────
    # Chạy TRƯỚC khi reject vì MISSING citation, để phân biệt:
    #   - truthful_refusal (context không đủ)  → status=refusal
    #   - false_refusal    (context đủ)        → status=rejection với reason rõ
    #   - format error     (không phải refusal) → status=rejection như cũ
    cls = refusal_mod.classify(res["answer"], query, chunks)
    if cls["refused"]:
        print(f"[REFUSAL] label={cls['label']} refused={cls['refused']} "
              f"sufficient={cls['context_sufficient']} "
              f"top1={cls['diagnostics']['top1_score']} "
              f"lex={cls['diagnostics']['lexical_ratio']} "
              f"mode={cls['diagnostics']['mode']}")

        if cls["label"] == "truthful_refusal":
            return _refusal_response(
                answer=res["answer"],
                citations=res.get("citations", []),
                reason="Truthful refusal: context insufficient",
                latency=base_latency,
            )
        elif cls["label"] == "false_refusal":
            return _reject(
                res["answer"],
                "False refusal: context sufficient but LLM refused",
                base_latency,
            )

    if check2 == "MISSING":
        # format error (không có refusal pattern)
        return _reject(
            res["answer"],
            "Check 2 Failed: No citation provided",
            base_latency,
        )
    elif check2 == "INVALID":
        return _ambiguous(res["answer"], res.get("citations", []), "Check 2 Failed: Hallucinated citation", base_latency)

    # [8] Check 3: Claim Grounding — chỉ reject khi CONTRADICTION rõ ràng
    # AMBIGUOUS từ NLI → coi như GROUNDED (NLI yếu với tiếng Việt technical)

    _FOOTNOTE_DEF = re.compile(
        r'^\s*\[\^(\d+)\]:\s*\[?([a-zA-Z0-9_\-:]+)\]?\s*.*$',
        re.MULTILINE
    )

    def _normalize_citations(answer: str) -> str:
        """Convert Markdown footnote [^1] → inline [sha256:...]; bỏ definition lines."""
        if not answer or "[^" not in answer:
            return answer

        # Build footnote map
        footnote_map = {}
        for m in _FOOTNOTE_DEF.finditer(answer):
            footnote_map[m.group(1)] = m.group(2)

        if not footnote_map:
            return answer

        # Replace inline [^N] → [chunk_id]
        def repl(m):
            n = m.group(1)
            return f"[{footnote_map[n]}]" if n in footnote_map else m.group(0)

        result = re.sub(r'\[\^(\d+)\]', repl, answer)
        result = _FOOTNOTE_DEF.sub('', result)
        return result.strip()

    def _merge_bullets(text: str) -> str:
        """
        Gộp bullet list với parent line để tránh split riêng từng bullet.
        "text:\n- A\n- B\n- C"  →  "text: - A - B - C"
        """
        lines = text.split("\n")
        out = []
        buffer_bullet = []

        for line in lines:
            stripped = line.strip()
            is_bullet = bool(re.match(r'^[\*\-•]\s+', stripped))

            if is_bullet:
                buffer_bullet.append(stripped)
            else:
                if buffer_bullet:
                    merged = " ".join(buffer_bullet)
                    if out:
                        out[-1] = out[-1].rstrip() + " " + merged
                    else:
                        out.append(merged)
                    buffer_bullet = []
                if stripped:
                    out.append(stripped)

        if buffer_bullet:
            merged = " ".join(buffer_bullet)
            if out:
                out[-1] = out[-1].rstrip() + " " + merged
            else:
                out.append(merged)

        return "\n".join(out)

    def _split_claims(text: str) -> list[str]:
        """
        Split answer into claims. Không cắt số thập phân, list marker, footnote def.
        """
        # Split chỉ khi: .!? + khoảng trắng + chữ hoa/số/markdown, HOẶC blank line
        parts = re.split(
            r'(?<=[.!?])\s+(?=[A-ZÀ-Ỹ0-9"*\-])|\n{2,}',
            text
        )
        out = []
        for p in parts:
            p = p.strip()
            if not p:
                continue
            # Bỏ footnote definition lines
            if re.match(r'^\[\^\d+\]:', p):
                continue
            out.append(p)
        return out

    answer_normalized = _normalize_citations(res["answer"])
    answer_normalized = _merge_bullets(answer_normalized)
    res["answer"] = answer_normalized          # ghi lại để response trả về consistent
    sentences = _split_claims(answer_normalized)
    check3_results = []
    for claim in sentences:
        cited_ids = re.findall(r"\[(.*?)\]", claim)
        if not cited_ids:
            continue
        evidence_texts = [
            c.get("text", "") for cid in cited_ids for c in chunks if c.get("doc_id", "") == cid
        ]
        claim_evidence = " ".join(evidence_texts)
        if not claim_evidence:
            continue
        check3_results.append(validators.check_3_grounding(claim, chunks=[{"text": claim_evidence}]))

    if "CONTRADICTION" in check3_results:
        overall_grounding = "CONTRADICTION"
    else:
        overall_grounding = "GROUNDED"

    print(f"[CHECK 3] results={check3_results}")
    print(f"[CHECK 3] overall={overall_grounding}")

    if overall_grounding == "CONTRADICTION":
        return _reject(res["answer"], "Check 3 Failed: Contradiction detected", base_latency)
    elif overall_grounding == "AMBIGUOUS":
        return _ambiguous(res["answer"], res.get("citations", []), "Check 3 Failed: Ambiguous grounding", base_latency)

    # [9] Output Guardrail
    if not validators.output_guardrail(res):
        return _ambiguous(res["answer"], res.get("citations", []), "Output Guardrail Failed", base_latency)

    # [10] Success
    return _make_response(
        session_id=session_id,
        user_id=user_id,
        query=query,
        answer=res["answer"],
        status="acceptance",
        citations=res.get("citations", []),
        strategy={"retrieval": "dense", "rerank": None, "gate": "pass"},
        scores=_build_scores(chunks),
        latency=base_latency,
        model_used=res.get("model_used"),
        userstore=userstore,
    )


# ── Session handlers ──────────────────────────────────────────────────────────

def handle_list_sessions(user_id: str, userstore) -> dict:
    return {"user_id": user_id, "sessions": userstore.list_sessions(user_id)}


def handle_get_session(session_id: str, user_id: str, userstore) -> dict:
    session = userstore.get_session(session_id, user_id)
    if not session:
        return {"error": "Session not found", "status": 404}
    return {
        "session": session,
        "documents": userstore.get_session_docs(session_id),
        "turns": userstore.list_session_turns(session_id),
    }


def handle_delete_session(session_id: str, user_id: str, userstore) -> dict:
    deleted = userstore.delete_session(session_id, user_id)
    if not deleted:
        return {"status": "error", "reason": "Session not found or unauthorized"}
    return {"status": "deleted", "session_id": session_id}


# ── Doc / Query helpers ───────────────────────────────────────────────────────

def handle_list_docs(user_id: str, userstore) -> dict:
    return {"user_id": user_id, "docs": userstore.list_docs(user_id)}


def handle_recent_queries(user_id: str, userstore, limit: int = 10) -> dict:
    return {"user_id": user_id, "queries": userstore.recent_queries(user_id, limit=limit)}


def handle_delete_query(user_id: str, query_id: int, userstore) -> dict:
    if hasattr(userstore, "delete_query"):
        userstore.delete_query(user_id, query_id)
        return {"status": "deleted", "query_id": query_id}
    return {"status": "error", "detail": "User store does not support deleting queries."}


def handle_detach_doc(doc_id: str, session_id: str, user_id: str, userstore) -> dict:
    session = userstore.get_session(session_id, user_id)
    if not session:
        return {"status": "error", "reason": "Session not found"}
    success = userstore.remove_doc_from_session(session_id, doc_id)
    if success:
        return {"status": "detached", "doc_id": doc_id}
    return {"status": "error", "reason": "Doc not found in session"}


def handle_delete_doc_global(doc_id: str, user_id: str, userstore, vector_store, storage) -> dict:
    metadata = userstore.delete_doc_global(user_id, doc_id)
    if not metadata:
        return {"status": "error", "reason": "Doc not found"}
        
    location = metadata.get("location")
    if location:
        try:
            import os
            if os.path.exists(location):
                os.remove(location)
        except Exception as e:
            print(f"Error deleting file {location}: {e}")
            
    if hasattr(vector_store, "delete_doc"):
        try:
            vector_store.delete_doc(doc_id)
        except Exception as e:
            print(f"Error deleting vector for {doc_id}: {e}")
            
    return {"status": "deleted", "doc_id": doc_id}


def handle_progress_summary(user_id: str, userstore, log_dir: Path) -> dict:
    total_queries = getattr(userstore, 'count_queries', lambda uid: 0)(user_id)
    total_sessions = getattr(userstore, 'count_sessions', lambda uid: 0)(user_id)
    recent_queries = userstore.recent_queries(user_id, limit=5)
    
    status_counts = {"acceptance": 0, "ambiguous": 0, "rejection": 0, "refusal": 0}
    latencies = []
    
    for log_file in log_dir.glob("*.jsonl"):
        try:
            with open(log_file, "r", encoding="utf-8") as f:
                for line in f:
                    if not line.strip(): continue
                    try:
                        record = json.loads(line)
                        if record.get("user_id") == user_id:
                            st = record.get("status")
                            if st in status_counts:
                                status_counts[st] += 1
                            metrics = record.get("metrics") or {}
                            lat = metrics.get("latency_ms", {}).get("total")
                            if lat is not None:
                                latencies.append(lat)
                    except Exception:
                        pass
        except Exception:
            pass
            
    total_log_queries = sum(status_counts.values()) or 1
    status_distribution = {k: round(v / total_log_queries * 100, 1) for k, v in status_counts.items()}
    
    latency_p50 = 0
    latency_p95 = 0
    if latencies:
        latencies.sort()
        latency_p50 = latencies[int(len(latencies) * 0.50)]
        latency_p95 = latencies[int(len(latencies) * 0.95)]
        
    return {
        "total_queries": total_queries,
        "total_sessions": total_sessions,
        "status_distribution": status_distribution,
        "latency_p50": latency_p50,
        "latency_p95": latency_p95,
        "recent_queries": recent_queries
    }
