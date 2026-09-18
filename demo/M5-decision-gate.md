# M5 Decision Gate: Failure Mechanism Analysis

Tài liệu này tổng hợp các thất bại (failures) từ M4 Holdout Evaluation, tiến hành mổ xẻ nguyên nhân gốc rễ (Mechanism), và khoảng trống kiến thức (Knowledge Gap) trước khi phân tích các giải pháp can thiệp (Candidate Interventions) tiềm năng.

Mục tiêu của Decision Gate là **không chọn trước bất kỳ giải pháp nào** (kể cả Query Rewrite hay Cross-Encoder) cho đến khi chúng ta hoàn thành Candidate Analysis.

---

## 1. Architectural Constraint (Hard Limit)
**Query-time LLM is not allowed in the M5 retrieval path.**
- *Hệ quả*: Bất kỳ giải pháp nào đòi hỏi gọi LLM API tại thời điểm người dùng query (như LLM Query Rewrite, HyDE) đều bị loại khỏi danh sách Candidate ngay lập tức do vi phạm constraint về Latency/Dependency.

---

## 2. M4 Failure Mechanism → Layer Mapping

Dưới đây là bảng tổng hợp các cơ chế gây lỗi từ M4 Holdout, đã được định vị chính xác vào từng tầng kiến trúc để giới hạn không gian Candidate:

| Failure Mechanism             | Layer cần investigate                            | Candidate space                                       |
| ----------------------------- | ------------------------------------------------ | ----------------------------------------------------- |
| Query–Evidence Alignment Gap  | Query Representation / Retrieval                 | Non-LLM Query Expansion                               |
| Candidate Generation Weakness | Candidate Generation                             | Dense/Sparse/Hybrid improvement, query transformation |
| Ranking Weakness              | Ranking                                          | Cross-Encoder                                         |
| Context-dependent Behavior    | Chunk / Context Representation **(Cần RCA thêm)**| Parent-Child, Semantic Chunking (WIP)                 |
| Strong Anchor                 | —                                                | No intervention                                       |

---

## 2. Candidate Analysis (WIP)

*(Phần này sẽ được thực hiện cùng với User theo framework phân tích chi tiết: Input → Mechanism → Expected Output → Trade-off → Failure Mode → Constraint Impact).*

### 3.1 Context-dependent behavior: Yêu cầu kiểm tra thêm Evidence
Riêng đối với cơ chế **Context-dependent behavior** (Case 006, 009), chúng ta **không mặc định chọn Parent-Child**. Cần phải Isolate & Diagnose (Ví dụ: trace lại các chunk xung quanh hoặc xem lại câu hỏi) để xác định chính xác nguyên nhân là do *Chunking* thiếu thông tin, hay do *Query* thiếu context, hay do *Retrieval* bắt hụt.

### 3.2 Các Candidate Interventions cần phân tích (WIP)
- **Non-LLM Query Expansion** (Giải quyết Alignment Gap)
- **Cross-Encoder Reranking** (Giải quyết Ranking Weakness - chỉ áp dụng khi target đã lọt vào Top-N)
- **Candidate Generation Improvements** (Giải quyết Candidate Generation Weakness cho các case văng khỏi recall pool như 014)
