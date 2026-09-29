# M6 Generation & Refusal API Evaluation Report

Báo cáo đánh giá tích hợp Generation (M6) với LLM OpenAI Claude-3.5 qua API nội bộ.

## 1. Tóm tắt chỉ số (Metrics)

- **Tốc độ xử lý trung bình (API Latency):** 80.71s/query
- **Tỷ lệ Refusal:** 2/3 (67%)
- **System Identity:** Claude-3.5-Sonnet (thông qua mwapi), sử dụng `OpenAIAdapter`.

## 2. Chi tiết Test Cases

### Answerable Case
- **Query:** `vector database là gì?`
- **Status:** `ambiguous`
- **Latency:** 85.66s
- **Số lượng Citation:** 2
- **Answer:**
> Vector Database là hệ thống cơ sở dữ liệu chuyên biệt được sinh ra để lưu trữ, quản lý và tìm kiếm dữ liệu dưới định dạng mảng số (vector) [sha256:4671c1d2d20b59de]. Khác với SQL lưu dữ liệu dạng bảng, Vector DB thực hiện tìm kiếm bằng cách so sánh sự tương đồng về khoảng cách trong không gian toán học nhiều chiều [sha256:4671c1d2d20b59de].
> 
> Vector Database đóng vai trò quan trọng trong việc giúp hệ thống RAG (Retrieval-Augmented Generation) hoạt động thực tế với hàng triệu tài liệu, sau các bước Chunking và Embedding [sha256:b0faebffc898711a].
> 
> Trong Vector Database (ví dụ Qdrant), có một số thành phần cấu trúc tương ứng với các khái niệm trong SQL:
> - Collection: tương đương Table, chứa tập hợp các vector, được cấu hình cố định về số chiều (Dimension) và hàm tính khoảng cách (Distance) [sha256:4671c1d2d20b59de].
> - Point (Vector Point): tương đương một Row, gồm một ID và mảng vector đi kèm [sha256:4671c1d2d20b59de].
> - Payload (Metadata): trường thông tin phụ đi kèm vector, thường ở dạng JSON, hỗ trợ tính năng Payload Filtering nhanh nhờ cơ chế indexing [sha256:4671c1d2d20b59de].

### Unanswerable Case
- **Query:** `giải thích chi tiết thuật toán băm (hashing) trong blockchain`
- **Status:** `rejection`
- **Latency:** 156.38s
- **Lý do từ chối (Reason):** Check 1 Failed: Evidence insufficient
- **Answer:**
> Tôi không tìm thấy đủ thông tin trong tài liệu để trả lời câu hỏi này.

### Cross-document Case
- **Query:** `so sánh vector database và quá trình chunking`
- **Status:** `rejection`
- **Latency:** 0.10s
- **Lý do từ chối (Reason):** Check 1 Failed: Evidence insufficient
- **Answer:**
> Tôi không tìm thấy đủ thông tin trong tài liệu để trả lời câu hỏi này.

