import sys
import os

# Ensure the src directory is in the path
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from generation import generate_answer

def main():
    print("=== BẮT ĐẦU TEST SINH CÂU TRẢ LỜI ===")
    
    # Giả lập input (giống với định dạng từ Check 1)
    evidence_list = [
        {
            "chunk_id": "sha256:63f8f2ea527a9f8b",
            "document_name": "ML_Architecture.md",
            "text": "**Vấn đề**: Việc phải dùng hai hệ thống/đường dẫn khác nhau để tính toán cùng một loại dữ liệu (Batch chậm cho Training và Real-time nhanh cho Inference) sẽ dễ dẫn đến tình trạng lệch pha dữ liệu (Drift) giữa lúc huấn luyện và lúc chạy thực tế."
        },
        {
            "chunk_id": "sha256:16b68db2dff9a21d",
            "document_name": "Observability.md",
            "text": "--> **Giải pháp**: OpenTelemetry(OTel) gom tất cả vào 1 bộ SDK duy nhất --> output đi đến bất kì backend nào. Components của OTel: SDK: thư viện embedded trong service, code emit telemetry qua SDK"
        }
    ]
    
    # Câu hỏi 1: Có thể trả lời được
    query_1 = "Tại sao lại có hiện tượng lệch pha dữ liệu (drift) và OpenTelemetry giúp giải quyết vấn đề xuất dữ liệu như thế nào?"
    print(f"\n[Câu hỏi 1]: {query_1}")
    print("Đang gọi Claude...")
    res_1 = generate_answer(query_1, evidence_list)
    
    print("-> Câu trả lời:")
    print(res_1["answer"])
    print("\n-> Citations Map:")
    for c in res_1["citations"]:
        print(f"[{c['citation_id']}] {c['chunk_id']}")

    print("\n" + "="*50)
    
    # Câu hỏi 2: Không thể trả lời (Unanswerable case)
    query_2 = "Giá của dịch vụ AWS S3 Glacier là bao nhiêu?"
    print(f"\n[Câu hỏi 2 (Unanswerable)]: {query_2}")
    print("Đang gọi Claude...")
    res_2 = generate_answer(query_2, evidence_list)
    
    print("-> Câu trả lời:")
    print(res_2["answer"])
    
if __name__ == "__main__":
    main()
