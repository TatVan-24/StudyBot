# M6 — Generation and Local Application Contract

## 1. Object

**Generation Pipeline + Local Application Integration cho hệ thống RAG.**

Contract này định nghĩa cách thức tích hợp toàn bộ Ingestion & Retrieval Pipeline (M1-M5) vào một ứng dụng thực tế chạy cục bộ (FastAPI), sau đó bổ sung module Generation (LLM) để tổng hợp câu trả lời từ bằng chứng (Evidence) một cách đáng tin cậy.

## 2. Purpose

Mục tiêu của M6 được chia thành 3 cấu phần cốt lõi tạo nên **Answer đáng tin**:

```text
                    M6
                     │
        ┌────────────┼────────────┐
        ↓            ↓            ↓
   Generation     Refusal      Integration
   có kiểm soát   trung thực
        │            │
        └──────┬─────┘
               ↓
       Answer đáng tin
```

### Bài toán 1: Generation có kiểm soát
```text
Retrieved context + System instruction
              ↓
         LLM Generation
              ↓
    Answer + Citations
```
**Yêu cầu:**
- Chỉ dùng context được retrieve.
- Citation chỉ trỏ vào chunk đã retrieve — không bịa.
- Nếu context không đủ → từ chối trung thực, không hallucinate.

### Bài toán 2: Truthful Refusal
```text
Query → Retrieve → Context đủ?
                      ├── Có → Generate answer
                      └── Không → "Tôi không tìm thấy thông tin..."
```
Đây là bài toán khó: Làm sao biết context "đủ" hay "không đủ"? (Zero-hit, MRR quá thấp, hoặc LLM tự phát hiện).

### Bài toán 3: App integration
```text
Upload TXT → Parse → Chunk → Index
                              ↓
Query → Retrieve → Generate → Answer + Citations
```
**Ràng buộc:** Dùng FastAPI/adapter có sẵn — không viết lại app.

---

## 3. Current State

- **Retrieval Pipeline (M1–M5): FROZEN.** Đã có khả năng đưa ra Top-K Chunks tốt nhất dựa trên Decision Gate.
- **App Skeleton (Phase 1): DONE.** Đã dựng xong pipeline xương sống qua API (Upload TXT → Parse → Chunk → Index → Query → Retrieve).
- **Generation (Phase 2): DOING.** Đã chốt Output Contract, Prompt Template, chuẩn bị thiết kế Storage Schema (Sessions & Turns) để đấu nối LLM.

---

## 4. Expected State

Một ứng dụng API cục bộ hoàn chỉnh có thể:
1. Nhận file upload, tự động Parse → Chunk → Index.
2. Nhận User Query, thực hiện Guardrails → Retrieval → LLM Generation → Trả về JSON chứa Answer và mảng Citations minh bạch.

---

## 5. Sub-tasks & Phased Execution

Để giảm thiểu rủi ro, M6 được chia làm 2 giai đoạn:

### Giai đoạn 1: Integration Skeleton (Nền tảng) - ✅ HOÀN THÀNH (19/09/2026)
**Mục tiêu:** Dựng khung end-to-end trước, chưa cần Generation thông minh.
- **Quy trình:** `Upload TXT → Parse → Chunk → Index → Query → Retrieve → [PLACEHOLDER] → Answer`
- **Việc cần làm:**
  1. Kiểm tra FastAPI/adapter có sẵn — hiểu cấu trúc.
  2. Xác định endpoint hiện có (upload, query).
  3. Dựng pipeline: `upload → index → query → retrieve`.
  4. Chưa cần LLM — chỉ cần trả về Text của Top-1 Chunk làm "answer" giả (Placeholder).
- **Exit Giai đoạn 1:** `Upload TXT → query → nhận được chunk (chưa phải answer) thông qua API`.
- **Lý do thực hiện trước:** Biết được input/output format, kiểm chứng retrieval trong app có hoạt động không, tạo bộ khung vững chắc để test Generation.

### Giai đoạn 2: Intelligent Generation & Refusal
- Áp dụng Input/Output Contract mới (Base Input tối giản và Output 3 trạng thái: acceptance, rejection, ambiguous).
- Kết nối LLM nội bộ (Ollama / llama.cpp / API).
- Thiết kế Prompt Template.
- Triển khai Refusal Logic & Citation Formatting.
- Đấu nối LLM vào vị trí `[PLACEHOLDER]` của Giai đoạn 1.

---

## 6. Input

- FastAPI/adapter code có sẵn trong thư mục dự án (`src/starter_apps` hoặc tương tự).
- Frozen Retrieval Pipeline (các class từ `evaluation/scripts/` sẽ được refactor/chuyển vào codebase chính).
- `test-v1.jsonl` và `test-v3.jsonl` để làm smoke test.

---

## 7. Technical Workflow

Đây là luồng xử lý chi tiết từ lúc nhận Query đến khi trả về Answer:

```text
INPUT GUARDRAIL
├── T1: Injection (regex — chỉ detect known patterns)
├── T2: Query validation (rỗng/khoảng trắng)
└── T3: Session/Document validation
        ↓
M5 Retrieval + Decision Gate
        ↓
Retrieved Evidence → M6 Evidence Evaluation → answerability_score
        ↓
        ├── Threshold → acceptance / ambiguous / rejection
        ↓
LLM Generation (nếu acceptance/ambiguous)
        ↓
OUTPUT GUARDRAIL
├── T1: Sensitive data (PII / API key / credential)
├── T2: Prompt / System leakage
├── T3: Evidence / Citation / Hallucination (answer + citation + score)
└── T4: Output Contract (schema + status)
        ↓
status: acceptance / ambiguous / rejection
```

**Lưu ý:**
- Điểm `answerability_score` và các ngưỡng HIGH/LOW sẽ được xác định thông qua dataset evaluation. Không dùng cứng threshold 0.5/0.2 từ M5.

---

## 8. API Contracts (Input / Output)

### 8.1 Base Input Contract (Query)
Chỉ yêu cầu 3 field tối giản. Mọi trạng thái khác (document_ids, standalone_query, v.v.) được quản lý ngầm bởi Session/System.

```json
{
  "session_id": "sess_123",
  "user_id": "user_123",
  "query": "Nó có giá bao nhiêu?"
}
```
**Nguyên tắc mở rộng:** Chỉ thêm (optional) khi có nhu cầu thực tế (ví dụ: `document_ids` khi muốn chọn doc cụ thể, `top_k` khi muốn điều chỉnh số lượng kết quả).

### 8.2 API Response (Output Contract)
Phản hồi API có 3 trạng thái (`status`):
- `acceptance`: Query trả lời được, evidence đủ mạnh.
- `rejection`: Query không trả lời được (không có evidence).
- `ambiguous`: Confidence thấp, nguy cơ hallucination.

```json
{
  "session_id": "sess_123",
  "user_id": "user_123",
  "metadata": {
    "status": "acceptance",
    "answer": "Giá lưu trữ AWS S3 Glacier là $0.004/GB/tháng.",
    "strategy": {
      "retrieval": "dense",
      "rerank": "bge",
      "gate": "pass"
    },
    "scores": {
      "retrieval_top1": 0.82,
      "rerank_top1": 0.65,
      "answerability_score": 0.65
    },
    "citations": [
      {
        "chunk_id": "chk_123",
        "doc_id": "doc_abc",
        "heading_context": ["AWS S3", "Pricing"]
      }
    ],
    "metrics": {
      "latency_ms": {
        "retrieval": 120,
        "generation": 1080,
        "total": 1200
      }
    }
  }
}
```

---

## 9. Verification & Estimation Methods

- **Giai đoạn 1 Check:** Khởi động server (uvicorn), POST một file `.txt`, POST một query, nhận về đoạn văn bản từ tài liệu thông qua API thành công.
- **Giai đoạn 2 Check:** 
  - Answerable case: Có answer và citation hợp lệ.
  - Unanswerable case: Từ chối trung thực, không hallucinate.
  - Cross-document case: Citation trỏ đến nhiều file (nếu có).

---

## 10. Format Report

Cuối M6, cần báo cáo:
- Tốc độ xử lý (API latency).
- Tỷ lệ Refusal chính xác (trên test-v1).
- Độ chính xác của Citation (không bịa đặt chunk_id).
- System Identity (LLM dùng loại gì, prompt ra sao).
