# M5 Candidate Analysis

Tài liệu này phân tích chi tiết các Candidate Interventions được đề xuất từ `M5-decision-gate.md`, tuân thủ nguyên tắc: Không chọn trước solution, mà đánh giá dựa trên cơ chế, trade-off, và failure modes để đưa ra quyết định dựa trên bằng chứng (Evidence-based Decision).

---

## Step 2A: Query-side Strategies (Candidate 1)

Nhóm giải pháp này tập trung can thiệp vào layer **Query Representation** nhằm khắc phục **Query-Evidence Alignment Gap** trước khi bước vào tiến trình Retrieval.

*   **M4 Evidence**: Case 002 ("infrastructure bill" ↔ "chi phí lưu trữ"), Case 003 ("delay" ↔ "bottleneck"), Case 012 ("static IP" ↔ "EIP").
*   **Research Question**: Bằng cách nào để làm giàu (enrich) User Query nhằm tăng độ khớp (alignment) với terminology trong Document?

### Constraint Check: Loại bỏ LLM-based Strategies
Dựa trên Constraint Kiến trúc: **"Query-time LLM is not allowed in the M5 retrieval path"**, các kỹ thuật sinh văn bản tại thời điểm truy vấn bao gồm:
1. **LLM Query Reformulation / Rewriting**
2. **HyDE (Hypothetical Document Embeddings)**
→ Đã bị **LOẠI (REJECTED)** khỏi danh sách Candidate do vi phạm nghiêm trọng về Latency/Cost và phá vỡ kiến trúc Retrieval.

### Candidate 1: Non-LLM Query Expansion
**Technical Mechanism**: Giữ nguyên User Query gốc, đồng thời bổ sung các từ đồng nghĩa (synonyms), thuật ngữ chuyên ngành (technical terms) có liên quan vào phía sau query trước khi đưa vào hệ thống Retrieval.

**Research Question mới (Mấu chốt của giải pháp này)**:
> *Nếu không gọi LLM ở query-time, nguồn technical terminology này sẽ được lấy từ đâu, xây dựng thế nào và có thực sự khắc phục được các M4 failure cases (Case 002, 003, 012) hay không?*

**Các nguồn Terminology tiềm năng cần nghiên cứu**:
- **Synonym Dictionary**: Từ điển đồng nghĩa tĩnh lập bằng tay.
- **Domain Glossary**: Bảng chú giải thuật ngữ chuyên ngành (AWS/Observability).
- **Corpus-derived Terminology**: Từ khóa được trích xuất offline (chạy LLM batch pipeline 1 lần) từ chính corpus và build thành lookup table.
- **Rule-based mapping**: Các Regex hoặc Rule map trực tiếp các keyword phổ biến (ví dụ: `static IP` → `Elastic IP`).

**Cách giải quyết Alignment Gap**: Tăng diện tích tiếp xúc từ vựng (lexical surface). Ví dụ user hỏi "static IP", hệ thống tra bảng và tự động append "Elastic IP, EIP, remappable, EC2". BM25 sẽ bắt được target nhờ các từ khóa mới này.

**Trade-offs & Failure Modes**:
*   [+] Không thêm LLM latency/cost vào query-time.
*   [+] Giữ được trọn vẹn query gốc của user (bảo vệ được Strong Anchor như Case 015).
*   [-] **Nguồn Terminology**: Yêu cầu công sức engineering lớn để build và duy trì một Knowledge Base đáng tin cậy.
*   [-] **Query Drift**: Expansion quá rộng có thể khiến BM25 và Dense kéo về hàng loạt tài liệu rác chứa từ mới.
*   [-] **Từ vựng rỗng**: Expansion quá hẹp sẽ không lấp được vocabulary gap.
*   [-] **Giới hạn ngữ nghĩa**: Có thể không giải quyết được các semantic mismatch ở tầng cấu trúc sâu (như Case 002 nơi khác biệt nằm ở cách diễn đạt nguyên nhân-kết quả).

---

## 2. Candidate 2: Cross-Encoder Reranking
Giải pháp nhằm khắc phục **Ranking Weakness**.

*   **M4 Evidence**: Case 010 (Dense #3, BM25 #61), Case 018 (Dense #237, BM25 #37). Có lexical signal nhưng bị chìm trong distractors (các chunk không liên quan nhưng có chung vài từ khóa).
*   **Research Question**: Làm thế nào để phân biệt độ liên quan sâu (deep semantic matching) giữa các candidate đã được kéo về (Top-N)?
*   **Technical Mechanism**: Thay vì so sánh 2 vector độc lập (Bi-Encoder), Cross-Encoder nối trực tiếp `[Query] + [Document Chunk]` và đưa qua Transformer layers để Attention mechanism "nhìn" thấy sự tương quan từng từ, cho ra 1 điểm số (score) chính xác tuyệt đối.
*   **Candidate Strategy**: Lấy Top-50 hoặc Top-100 từ Hybrid (Dense + BM25) đưa qua mô hình Cross-Encoder (ví dụ: `ms-marco-MiniLM-L-6-v2` hoặc `bge-reranker`).
*   **Evidence / Documentation**: SentenceTransformers Documentation, chuẩn công nghiệp cho Multi-stage Retrieval.
*   **Trade-offs**: 
    *   Nặng về tính toán (Compute-heavy): Đòi hỏi $N$ lần inference qua Transformer model ở query-time.
    *   Latency tăng tuyến tính với $K$ (số lượng candidates cần rerank).
*   **Failure Modes**: 
    *   **Giới hạn Recall**: Cross-Encoder CHỈ CÓ THỂ sắp xếp lại những gì Bi-Encoder/BM25 đã tìm thấy. Nó sẽ **bất lực** với Case 014 (nằm tận Rank 398) nếu ta chỉ cắt Top-50 đem đi rerank.
*   **Constraint Impact**: Yêu cầu phải có GPU hoặc một model cực nhỏ để chạy Local mà không làm timeout hệ thống.

---

## 3. Candidate 3: Context / Chunk Representation (Parent-Child)
Giải pháp nhằm khắc phục **Context-dependent behavior**.

*   **M4 Evidence**: Case 006 ("Is Loki cheaper than ELK for logs?"), Case 009 ("Which tool is standard for Kubernetes?").
*   **Research Question**: Làm thế nào để không làm loãng semantic signal khi embed, nhưng vẫn giữ được toàn vẹn ngữ cảnh rộng khi trả về cho LLM hoặc khi so sánh?
*   **Technical Mechanism**: Chia document thành các Parent Chunks (lớn), sau đó chia tiếp thành các Child Chunks (nhỏ). Vectorize và Index các Child Chunks. Khi Query match với Child Chunk, hệ thống sẽ trả về Parent Chunk của nó.
*   **Candidate Strategy**: Parent-Child Indexing / Auto-merging Retriever.
*   **Evidence / Documentation**: LlamaIndex Advanced Retrieval patterns.
*   **Trade-offs**: 
    *   Tăng độ phức tạp của Storage/Database (phải map relationship Parent-Child).
    *   Tăng kích thước Vector Index nếu số lượng Child chunks quá lớn.
*   **Failure Modes**: Nếu Parent Chunk quá lớn, nó có thể vượt quá Context Window của LLM ở bước Generation, hoặc cung cấp quá nhiều thông tin nhiễu khiến LLM bị lạc hướng (Lost in the middle).
*   **Constraint Impact**: Bắt buộc phải **đập đi xây lại Index** (Re-index) và thay đổi cấu trúc ParsedBlock/Chunker đã frozen ở M1/M2.

---

## 4. Compare Candidates & USER DECISION

| Yếu tố | Query Rewrite / Expansion (HyDE) | Cross-Encoder Reranking | Parent-Child Chunking |
| :--- | :--- | :--- | :--- |
| **Cơ chế lỗi giải quyết** | Query-Evidence Alignment Gap | Ranking Weakness | Context-dependent behavior |
| **Khả năng giải quyết Failures** | Tốt cho Case 002, 003, 012 | Tốt cho Case 010, 018 | Tiềm năng cho Case 006, 009 |
| **Điểm mù (Blind spot)** | Dễ làm hỏng các Exact Match Query tốt | Không cứu được các case văng khỏi Top-N (Case 014) | Phải Re-index toàn bộ dữ liệu |
| **Trade-offs chính** | Tăng Latency & Cost (LLM API) | Tăng Compute & Latency (GPU/Local) | Tăng Storage & Complexity |
| **Tác động Kiến trúc** | Thêm LLM vào Retrieval phase | Thêm Model Inference vào Retrieval | Thay đổi Core Data Schema (Re-index) |

**QUYẾT ĐỊNH CỦA BẠN LÀ GÌ?**
*(Hãy xem xét bảng so sánh trên và chọn ra ĐÚNG 1 Candidate để chúng ta thiết kế Hypothesis và Controlled Experiment cho M5).*
