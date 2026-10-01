import json
import re
import sys
from pathlib import Path

# Fix path to allow importing src
sys.path.append(str(Path(__file__).parent.parent.parent.parent))

from src.backend.app import userstore, ai_client, vector_store
from src.rag_pipeline.llm.handlers import handle_query
from src.backend import validators

USER_ID = "eval_english_user"
QUERY = "What is a Vector Database?" # GND-01

def main():
    print("=== ANALYZE GND-01 CHECK 3 TRUNCATION ===")

    # 1. Setup Session
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

    # 2. To trace Check 3 internally
    original_check3 = validators.check_3_grounding
    check3_trace = []
    def traced_check3(answer: str, chunks: list):
        evidence_text = " ".join([c.get("text", "") for c in chunks])
        check3_trace.append({
            "claim": answer,
            "evidence": evidence_text
        })
        return original_check3(answer, chunks)

    validators.check_3_grounding = traced_check3

    # 3. Run Query
    handle_query(
        session_id=session_id,
        user_id=USER_ID,
        query=QUERY,
        ai_client=ai_client,
        userstore=userstore,
        vector_store=vector_store,
        vector_backend="local",
        bedrock_kb_id=""
    )

    # 4. Analyze Check 3 Trace
    if not check3_trace:
        print("\n=> KHÔNG CÓ CHECK 3 NÀO ĐƯỢC CHẠY (Có thể Check 2 đã đánh rớt).")
        return

    classifier = validators.get_nli_classifier()
    tokenizer = classifier.tokenizer

    print(f"\n[2] Phân tích {len(check3_trace)} câu claim đi vào Check 3:\n")
    for i, trace in enumerate(check3_trace):
        claim = trace['claim']
        evidence = trace['evidence']

        print(f"--- CLAIM {i+1} ---")
        print(f"Text Claim: {claim}")

        enc_ev = tokenizer(evidence, add_special_tokens=False)
        enc_cl = tokenizer(claim, add_special_tokens=False)

        encoded = tokenizer(evidence, claim)
        total_tokens = len(encoded['input_ids'])

        print(f"Tokens Evidence: {len(enc_ev['input_ids'])}")
        print(f"Tokens Claim: {len(enc_cl['input_ids'])}")
        print(f"Total Tokens: {total_tokens}")

        if total_tokens > 512:
            print(f"⚠️ VƯỢT MAX LENGTH (512). Tokenizer sẽ cắt bỏ {total_tokens - 512} tokens của Evidence.")

            # Decode phần evidence bị giữ lại
            encoded_truncated = tokenizer(evidence, claim, truncation=True, max_length=512)
            seq_ids = encoded_truncated.sequence_ids()
            evidence_tokens_kept = seq_ids.count(0)

            print(f"Evidence còn lại: {evidence_tokens_kept} tokens.")

            # Giải mã chính xác đoạn Evidence được NLI nhìn thấy
            trunc_ids = encoded_truncated['input_ids']
            evidence_ids = [tid for tid, sid in zip(trunc_ids, seq_ids) if sid == 0]
            seen_evidence = tokenizer.decode(evidence_ids, skip_special_tokens=True)

            print(f"\n[EVIDENCE NLI NHÌN THẤY]:\n{seen_evidence[:200]} ... {seen_evidence[-200:]}")

            # Tìm đoạn bị cắt
            full_evidence_ids = tokenizer(evidence)['input_ids']
            lost_ids = enc_ev['input_ids'][evidence_tokens_kept:]
            if lost_ids:
                lost_evidence = tokenizer.decode(lost_ids, skip_special_tokens=True)
                print(f"\n[EVIDENCE BỊ CẮT MẤT]:\n{lost_evidence}")

        else:
            print("=> KHÔNG BỊ TRUNCATION.")

        print("\n[3] RAW NLI SCORES:")
        inputs = {"text": evidence, "text_pair": claim}
        outputs = classifier(inputs)
        scores_list = outputs[0] if isinstance(outputs[0], list) else outputs

        p_entail = 0.0
        p_contra = 0.0
        p_neutral = 0.0

        for item in scores_list:
            label = item['label'].lower()
            score = item['score']
            if 'entailment' in label or label == 'label_1':
                p_entail = score
            elif 'contradiction' in label or label == 'label_0':
                p_contra = score
            else:
                p_neutral = score

        print(f"  - Entailment   : {p_entail:.4f}")
        print(f"  - Neutral      : {p_neutral:.4f}")
        print(f"  - Contradiction: {p_contra:.4f}")

        if p_contra >= 0.70:
            print("  => Kết quả Check 3 mong đợi: CONTRADICTION")
        elif p_entail >= 0.50:
            print("  => Kết quả Check 3 mong đợi: GROUNDED")
        else:
            print("  => Kết quả Check 3 mong đợi: AMBIGUOUS")

        print("\n")

if __name__ == '__main__':
    main()
