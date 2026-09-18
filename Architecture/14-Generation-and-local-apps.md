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
- **App Skeleton:** Có source code của một app FastAPI cũ (từ dự án trước), nhưng chưa được đấu nối với RAG pipeline mới.
- **Generation:** Chưa có code, chưa kết nối LLM, chưa định nghĩa Prompt.

---

## 4. Expected State

Một ứng dụng API cục bộ hoàn chỉnh có thể:
1. Nhận file upload, tự động Parse → Chunk → Index.
2. Nhận User Query, thực hiện Guardrails → Retrieval → LLM Generation → Trả về JSON chứa Answer và mảng Citations minh bạch.

---

## 5. Sub-tasks & Phased Execution

Để giảm thiểu rủi ro, M6 được chia làm 2 giai đoạn:

### Giai đoạn 1: Integration Skeleton (Nền tảng) - Đang thực hiện
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
                  USER QUERY
                      │
                Input Guardrail
                      │
          ┌───────────┴───────────┐
          │                       │
     User Query             Internal Query
          │                       │
       Embed                   Embed
          │                       │
      Retrieval               Retrieval
          └───────────┬───────────┘
                      ↓
               Candidate Context
                      ↓
             Context / Input Gate
                      ↓
              LLM Generation
                      ↓
                Output Guardrail
                      ↓
              Answer + Citations
```

---

## 8. Criteria Output / Output Format

### 8.1 API Response (Answerable)
```json
{
  "status": "answered",
  "query": "...",
  "answer": "...",
  "citations": [
    {
      "chunk_id": "...",
      "document_id": "...",
      "locator": {"type": "txt", "start_line": 42},
      "excerpt": "..."
    }
  ]
}
```

### 8.2 API Response (Unanswerable)
```json
{
  "status": "refused",
  "query": "...",
  "answer": "Tôi không tìm thấy thông tin liên quan trong tài liệu được cung cấp.",
  "citations": [],
  "refusal_reason": "zero_hit | low_confidence | llm_refused"
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
