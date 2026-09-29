import json
import re
import copy
from pathlib import Path
import sys

# Fix path to allow importing src
sys.path.append(str(Path(__file__).parent.parent.parent.parent))

from src.backend.app import userstore, ai_client, vector_store
from src.backend.handlers import handle_query
from src.backend import validators

USER_ID = "eval_english_user"
CASES_PATH = Path("src/tests/rag_pipeline/english_benchmark.jsonl")
DUMP_PATH = Path("outputs/e2e_dump.jsonl")

def _dump_case_for_diagnostic(
    case_id, query, res, chunks, expected_status,
    check1_status, check2_status, expected_check3, dump_path
):
    answer = res.get("answer", "")

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

    answer_normalized = _normalize_citations(answer)
    answer_normalized = _merge_bullets(answer_normalized)
    sentences = _split_claims(answer_normalized)
    claims_dump = []

    for i, claim in enumerate(sentences):
        cited_ids = re.findall(r"\[(.*?)\]", claim)

        if not cited_ids:
            claims_dump.append({
                "index": i, "text": claim,
                "cited_ids": [], "evidence_chunk_ids": [],
                "evidence_text": "",
                "skipped": True, "skip_reason": "no_citation",
            })
            continue

        # CHỈ lấy chunk mà claim này cite (KHÔNG dùng shared)
        matched_chunks = [
            c for cid in cited_ids
            for c in chunks if c.get("doc_id", "") == cid
        ]
        evidence_texts = [c.get("text", "") for c in matched_chunks]
        claim_evidence = " ".join(evidence_texts)

        if not claim_evidence:
            claims_dump.append({
                "index": i, "text": claim,
                "cited_ids": cited_ids, "evidence_chunk_ids": [],
                "evidence_text": "",
                "skipped": True, "skip_reason": "no_matching_evidence",
            })
            continue

        claims_dump.append({
            "index": i, "text": claim,
            "cited_ids": cited_ids,
            "evidence_chunk_ids": [
                c.get("chunk_id", c.get("doc_id")) for c in matched_chunks
            ],
            "evidence_text": claim_evidence,
            "skipped": False, "skip_reason": None,
        })

    record = {
        "case_id": case_id,
        "query": query,
        "answer": answer,
        "citations": res.get("citations", []),
        "claims": claims_dump,
        "retrieved_chunks": [
            {
                "chunk_id": c.get("chunk_id"),
                "doc_id": c.get("doc_id"),
                "text": c.get("text", ""),
                "score": c.get("score", 0.0),
            }
            for c in chunks
        ],
        "check1_status": check1_status,
        "check2_status": check2_status,
        "expected_status": expected_status,
        "expected_check3": expected_check3,
    }

    # Ensure output dir exists
    dump_path.parent.mkdir(parents=True, exist_ok=True)
    with open(dump_path, "a", encoding="utf-8") as f:
        f.write(json.dumps(record, ensure_ascii=False) + "\n")

def main():
    print("=== EXTRACTING E2E PER-CLAIM DUMP ===")

    # 1. Clear previous dump
    if DUMP_PATH.exists():
        DUMP_PATH.unlink()

    # 2. Setup Session
    sessions = userstore.list_sessions(USER_ID)
    session_id = None
    for s in reversed(sessions):
        if userstore.get_session_docs(s["session_id"]):
            session_id = s["session_id"]
            break

    if not session_id:
        print("Không tìm thấy session nào có document cho user:", USER_ID)
        return

    print(f"\n[1] Using Session ID: {session_id}")

    # 3. Load cases (only take cases meant for Check 3 like GND, AMB, CTR)
    with open(CASES_PATH, encoding="utf-8") as f:
        all_cases = [json.loads(line) for line in f if line.strip()]

    # Lọc ra các case thực sự cần đi qua Check 3 (bỏ qua INJ, SYS)
    cases = [c for c in all_cases if c["id"].startswith(("GND", "AMB", "CTR")) or c.get("expected") == "acceptance"]

    # Giới hạn 14 case để test nhanh
    cases = cases[:14]

    if not cases:
        print("Không tìm thấy case nào phù hợp cho Check 3 (GND/AMB/CTR).")
        return

    print(f"[*] Found {len(cases)} relevant cases for Check 3 diagnostic.")

    # 4. Tracing hooks setup
    original_search = vector_store.search
    original_generate = ai_client.generate_with_citations
    original_check2 = validators.check_2_citations

    for idx, case in enumerate(cases):
        print(f"Processing case {idx+1}/{len(cases)}: {case['id']}")

        # State for this iteration
        state = {
            "chunks": [],
            "res": {},
            "check2": "NOT_RUN"
        }

        def traced_search(*args, **kwargs):
            # We want the chunks AFTER handlers.py mutates them to have doc_id = chunk_id
            # So we keep the reference to the actual chunks array returned.
            chunks = original_search(*args, **kwargs)
            state["chunks"] = chunks
            return chunks

        def traced_generate(*args, **kwargs):
            res = original_generate(*args, **kwargs)
            state["res"] = res
            return res

        def traced_check2(citations, chunks):
            status = original_check2(citations, chunks)
            state["check2"] = status
            return status

        vector_store.search = traced_search
        ai_client.generate_with_citations = traced_generate
        validators.check_2_citations = traced_check2

        # Execute
        handle_query(
            session_id=session_id,
            user_id=USER_ID,
            query=case["query"],
            ai_client=ai_client,
            userstore=userstore,
            vector_store=vector_store,
            vector_backend="local",
            bedrock_kb_id=""
        )

        # Dump
        _dump_case_for_diagnostic(
            case_id=case["id"],
            query=case["query"],
            res=state["res"],
            chunks=state["chunks"],
            expected_status=case["expected"],
            check1_status="PASS" if state["chunks"] else "FAIL",
            check2_status=state["check2"],
            expected_check3=case.get("metadata", {}).get("expected_check3"),
            dump_path=DUMP_PATH
        )

    print(f"\nDone! Dump saved to {DUMP_PATH}")

if __name__ == '__main__':
    main()
