import sys
from pathlib import Path

# Fix path to allow importing src
sys.path.append(str(Path(__file__).parent.parent.parent.parent))

from src.rag_pipeline.llm.validators import get_nli_classifier

def main():
    print("=== TEST CHECK 3 NLI TRUNCATION BEHAVIOR ===")
    classifier = get_nli_classifier()

    # Giả lập Evidence dài 500 tokens
    evidence = " ".join(["Đây là câu evidence."] * 100)

    # Giả lập Claim dài 50 tokens
    claim = " ".join(["Đây là claim."] * 10)

    inputs = {"text": evidence, "text_pair": claim}

    print("\n1. Tokenize thử bằng Tokenizer của pipeline:")
    tokenizer = classifier.tokenizer

    # Tokenize riêng biệt để biết độ dài ban đầu
    enc_ev = tokenizer(inputs["text"], add_special_tokens=False)
    enc_cl = tokenizer(inputs["text_pair"], add_special_tokens=False)
    print(f"- Số token Evidence ban đầu: {len(enc_ev['input_ids'])}")
    print(f"- Số token Claim ban đầu: {len(enc_cl['input_ids'])}")

    # Tokenize gộp không truncate
    encoded = tokenizer(inputs["text"], inputs["text_pair"])
    print(f"- Tổng số token khi chưa truncate: {len(encoded['input_ids'])}")

    # Decode lại để xem nếu truncate thì cái gì bị mất
    encoded_truncated = tokenizer(inputs["text"], inputs["text_pair"], truncation=True, max_length=512)
    trunc_ids = encoded_truncated['input_ids']
    print(f"- Tổng số token NẾU truncate=True: {len(trunc_ids)}")

    # Tìm xem Claim còn lại bao nhiêu token
    # mDeBERTa phân tách text và text_pair bằng [SEP] (token_id của [SEP] thường là 2, hoặc ta có thể dùng sequence_ids)
    try:
        seq_ids = encoded_truncated.sequence_ids()
        evidence_tokens = seq_ids.count(0)
        claim_tokens = seq_ids.count(1)
        print(f"\n=> SAU TRUNCATION:")
        print(f"   - Số token Evidence còn lại: {evidence_tokens}")
        print(f"   - Số token Claim còn lại: {claim_tokens}")
        if claim_tokens < len(enc_cl['input_ids']):
            print(f"   => Claim BỊ CẮT MẤT {len(enc_cl['input_ids']) - claim_tokens} tokens.")
        else:
            print("   => Claim CÒN NGUYÊN. Chỉ Evidence bị cắt.")
    except Exception as e:
        print(f"Không thể trích xuất sequence_ids: {e}")

    decoded = tokenizer.decode(trunc_ids)

    print("\n2. Thử chạy qua Pipeline:")
    try:
        outputs = classifier(inputs)
        print("Pipeline chạy THÀNH CÔNG (không crash).")
        print("Kết quả:", outputs)
    except Exception as e:
        print("Pipeline CRASH với lỗi:", e)

if __name__ == "__main__":
    main()
