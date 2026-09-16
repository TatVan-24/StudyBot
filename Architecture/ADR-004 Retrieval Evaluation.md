# ADR 004: Retrieval Evaluation Strategy (M4)

## Status
Accepted

## Context
Trong pha đánh giá (Evaluation) hệ thống RAG (Retriever-Augmented Generation), việc đo lường độ chính xác của Retrieval phụ thuộc rất lớn vào cách định nghĩa "sự trùng khớp" (relevance) giữa Ground Truth và Retrieved Chunks. 
Đặc thù của StudyBot phục vụ nhiều use case (Q&A, Summarization, Flashcard), do đó một đoạn văn bản (Ground Truth) có thể rải rác trên nhiều block, và một Chunk bị giới hạn bởi số lượng token có thể không bao giờ chứa đủ toàn bộ Ground Truth.
Ngoài ra, các metric như Recall@K truyền thống (đếm số lượng chunks) thường bị đánh lừa bởi sự trùng lặp thông tin (Redundancy) - khi Retriever trả về nhiều chunks có chung một nội dung.

## Decision
Một Evaluation Contract toàn diện được thống nhất, bao gồm 5 quyết định cốt lõi:

1. **D1 - Lineage Binding (Late Binding & Runtime Querying)**: 
   Không sinh ra các file hoặc database mapping trung gian. Sự liên kết từ `Locator` (Ground Truth) đến `Chunk` được thực hiện ở thời điểm đánh giá thông qua việc kiểm tra trực tiếp metadata `source_block_ids` của Chunk trong SQLite Index.
2. **D2 - Relevance (Block Overlap)**: 
   Sự liên quan của một chunk không phải là nhị phân (Yes/No), mà là một tập hợp (Subset). Một chunk cung cấp một phần bằng chứng dựa trên phép giao: `chunk.source_block_ids ∩ target_block_ids`.
3. **D3 - Primary Metric (Cumulative Block Coverage@K)**: 
   Thay vì đếm số chunks, M4 đo lường tỷ lệ phần trăm các block của Ground Truth đã được bao phủ bởi tất cả các chunks từ Top 1 đến Top K. Metric này kháng hoàn toàn nhiễu do thông tin trùng lặp.
4. **D4 - Ranking Metric (Dual MRR)**: 
   Sử dụng đồng thời 2 chỉ số: `MRR_First_Hit` (Đo tốc độ tìm thấy mảnh bằng chứng đầu tiên) và `MRR_Full_Coverage` (Đo tốc độ bao phủ 100% bằng chứng). Khoảng cách giữa 2 chỉ số là cảnh báo về Redundancy và tín hiệu để áp dụng Maximal Marginal Relevance (MMR).
5. **D5 - Retrieval Scope (Global Search)**: 
   Quá trình đánh giá không áp dụng bộ lọc (filter) theo từng tài liệu. Mọi Query đều phải tìm kiếm trên toàn bộ Vector Index để đo lường năng lực chống nhiễu (distractors) thực tế của Embedding Model.

## Consequences
**Tích cực:**
- Tách bạch hoàn toàn logic chấm thi (Evaluation) khỏi chiến lược cắt văn bản (Chunking). Dù ở M5 có đổi thuật toán Chunker, cấu trúc chấm điểm của M4 vẫn giữ nguyên tính công bằng và có thể so sánh chéo (Cross-compare).
- Định hướng rõ ràng cho các pha cải thiện (Re-ranking) ở các Milestone sau.
- Zero maintenance overhead cho việc duy trì các Mapping Artifacts.

**Tiêu cực/Rủi ro:**
- Cumulative Coverage khắt khe hơn Recall truyền thống rất nhiều, điểm số ở các đợt chạy đầu tiên có thể rất thấp (đặc biệt là Full Coverage).
- Phụ thuộc hoàn toàn vào tính toàn vẹn của mảng `source_block_ids` trong Metadata của Vector Store. Nếu quá trình Ingestion bị lỗi và mất mảng này, toàn bộ Evaluation sẽ sụp đổ.

## Hậu kiểm từ M4-E (Hybrid Score Fusion)
Việc thiết lập Dual MRR (First Hit vs Full Coverage) đã chứng minh được giá trị thực tiễn cực lớn trong pha thử nghiệm M4-E:
- Bóc trần sự thật rằng Tối ưu hóa First-hit (nghiêng về Dense) có thể phá hủy hoàn toàn Full-coverage.
- Phát hiện ra "Regime Transition" quanh $\alpha \approx 0.5$ của thuật toán Min-Max Score Fusion.
- Biến `MRR Full` thành Primary Metric và `MRR First` thành Mandatory Guardrail để định hướng cho kiến trúc Production.
