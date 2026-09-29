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

### Giai đoạn 2: Intelligent Generation & Refusal - ✅ HOÀN THÀNH (28/09/2026)
**Mục tiêu:** Tích hợp sinh văn bản có kiểm soát, trích dẫn minh bạch và gác cổng (guardrails) nghiêm ngặt để chống ảo giác (hallucination).
- **Quy trình:** `Retrieve → Check 1 (Sufficiency) → LLM Generation → Check 2 (Citation Validity) → Check 3 (Claim Grounding) → Output Guardrails`
- **Thành quả đạt được:**
  - Áp dụng thành công Output Contract (3 trạng thái: `acceptance`, `rejection`, `ambiguous`).
  - Hoàn thiện **3-Checks Architecture** bọc quanh LLM:
    - **Check 1:** Answerability/Sufficiency (Dựa trên BGE Top-1 & Gap).
    - **Check 2:** Citation Format & Validity (Chuẩn hoá Markdown footnotes `[^1]` thành inline `[chunk_id]`, ép chặt Set Membership).
    - **Check 3:** NLI Claim Grounding (Sử dụng `mDeBERTa-v3`, áp dụng kỹ thuật Local Evidence Extraction chống Token Truncation/Dilution, và chốt chặt Conservative Aggregation Policy).
  - Thiết kế System Prompt nâng cao: Áp dụng rule `CITATION PRECISION` với Procedure Self-check bắt buộc để chặn đứng hành vi keyword-driven citation của LLM.

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

**Kiến trúc Sinh Trích Dẫn & 3 Chốt chặn (3 Checks Architecture) quanh LLM:**

```text
     Retrieve (Cung cấp Evidence)
        ↓
┌─────────────────────────────────────┐
│  CHECK 1: Evidence Sufficiency      │  ← TRƯỚC LLM
│  "Evidence có đủ mạnh không?"       │
│  Output: answerability_score        │
└─────────────────────────────────────┘
        ↓
        ├── Không → rejection
        └── Có / chưa chắc
                  ↓
             LLM Generate
        (Sinh Answer + Gắn Citation [chunk_id])
                  ↓
┌─────────────────────────────────────┐
│  CHECK 2: Citation Validity         │  ← SAU LLM
│  "Citation ID có thuộc Evidence?"   │
│  Deterministic, no ML               │
└─────────────────────────────────────┘
                  ↓
┌─────────────────────────────────────┐
│  CHECK 3: Claim Grounding           │  ← SAU LLM
│  "Claim có được evidence support?"  │
│  Đây mới là hallucination check     │
└─────────────────────────────────────┘
                  ↓
             Final Output
```
**Lưu ý:**
- Điểm `answerability_score` và các ngưỡng HIGH/LOW sẽ được xác định thông qua dataset evaluation. Không dùng cứng threshold 0.5/0.2 từ M5.

### 7.1. Kết quả Evidence Sufficiency Gate (M6 Check 1)

Dựa trên quá trình đánh giá 35 human-annotated cases (dev set), Gate quyết định Sufficiency (Answerability) đã được đóng băng (frozen) như sau:

**Rule (Frozen):**
```text
is_sufficient = (BGE_top1 >= 0.23) AND (BGE_gap >= 0.02)
```

> ⚠️ **Trạng thái triển khai:** Rule trên đã frozen về mặt thiết kế, nhưng **hiện đang bị BYPASS trong code** (`handlers.py`, flag `[TEMP BYPASS — Fix A]`). Lý do bypass: threshold `BGE_top1=0.23` calibrate cho pipeline có rerank BGE; pipeline hiện tại chỉ chạy dense MPNet nên threshold không phù hợp.
>
> Hệ quả: Evidence Sufficiency Gate hiện chỉ reject khi `chunks == []` (zero-hit). Answerability thực tế được đánh giá bởi **Truthful Refusal Gate** (xem section 7.3).
>
> Rollback khi cần: uncomment block `validators.check_1_sufficiency(chunks)` trong `handlers.py`.

**Validation (35 cases):**
- Accuracy : 91.43%
- Precision: 88.89%
- Recall   : 94.12%
- F1       : 91.43%
- Refusal% : 48.57%
- TP: 16 | FP: 2 | TN: 16 | FN: 1

**Signals đã khám phá:**
| Signal | Vai trò | Kết quả |
|--------|---------|---------|
| `BGE_top1_score` | Relevance — chunk có liên quan không? | ✅ Giữ (threshold 0.23) |
| `BGE_score_gap` | Confidence — BGE có phân biệt rõ top1/top2 không? | ✅ Giữ (threshold 0.02) |
| `QA_score` (ms-marco) | Answerability — chunk có trả lời được query không? | ❌ Reject: không có incremental value nhất quán |

**Failure Cases còn lại (không sửa):**
| Case | Loại | Failure Mode |
|------|------|--------------|
| 015  | FP   | Relevant-but-incomplete: BGE cao nhưng thiếu answer entity (model name) |
| 033  | FP   | Entity mismatch: Collector vs. SDK unifier |
| 001  | FN   | Semantic negation: BGE đánh giá thấp quan hệ phủ định |

> **Quyết định:** Chi phí để fix 3 case trên không tương xứng với lợi ích. Không thêm signal/model mới vào Phase 1. Scale stability là hypothesis chưa được kiểm chứng do thiếu annotated data ở quy mô lớn hơn.

### 7.2. Kết quả Claim Grounding (M6 Check 3)

Để phát hiện Ảo giác (Hallucination) từ LLM, hệ thống sử dụng mô hình NLI đa ngôn ngữ. Claim (phát biểu của LLM) và Evidence (chunk) sẽ được đưa qua NLI để phân loại.

**Rule (Frozen for MVP):**
- Mô hình NLI: `MoritzLaurer/mDeBERTa-v3-base-mnli-xnli` (Hỗ trợ tốt Tiếng Việt - Tiếng Anh).
- Ngưỡng phân loại (Thứ tự kiểm tra nghiêm ngặt):
  1. **CONTRADICTION được ưu tiên tối đa:** Nếu $P_C \ge 0.70 \rightarrow$ `CONTRADICTION` (Bất chấp giá trị của $P_E$).
  2. **GROUNDED:** Nếu $P_C < 0.70$ và $P_E \ge 0.50 \rightarrow$ `GROUNDED`.
  3. **AMBIGUOUS:** Nếu $P_C < 0.70$ và $P_E < 0.50 \rightarrow$ `AMBIGUOUS` (Thường xảy ra khi $P_N$ quá cao, tức là NLI nhận định Evidence không đủ để chứng minh Claim, nhưng cũng không mâu thuẫn).

**Các trường hợp đặc biệt cần lưu ý ở Check 3:**
1. **Phạm vi Evidence (Per-claim Evidence thay vì Shared Evidence):**
   - **Quyết định thiết kế:** Mỗi Claim (câu) sinh ra từ LLM chỉ được đối chiếu (NLI) với **duy nhất các chunk mà Claim đó trực tiếp cite** (`[chunk_id]`).
   - **Lý do:** NLI model xét toàn bộ Evidence như một khối thống nhất. Nếu nhét toàn bộ các chunk trả về từ Retrieval (Shared Evidence) vào mọi Claim, các chunk lạc đề sẽ làm "loãng" ngữ cảnh, khiến mô hình NLI bị kéo tụt xác suất Entailment và dẫn tới `AMBIGUOUS` một cách oan uổng.
   - **Hệ quả:** Các công cụ Diagnostic và Evaluation bắt buộc phải bóc tách Evidence theo từng Claim (Per-claim dump) giống hệt Production, tuyệt đối không dùng chung toàn bộ Retrieved Chunks.
2. **Lỗi Tokenizer Truncation (Input > 512 tokens):**
   - Khi tổng độ dài Evidence và Claim vượt quá 512 tokens, tokenizer (với chiến lược `longest_first`) sẽ tự động cắt bớt phần đuôi của chuỗi dài hơn (luôn luôn là Evidence).
   - **Hậu quả:** Claim vẫn được giữ nguyên, nhưng Evidence có thể bị mất đi phần thông tin quan trọng nhất nằm ở cuối.
3. **Ảo giác Tri thức nền (Prior-knowledge Hallucination):**
   - LLM đôi khi sinh ra Claim chứa những khái niệm đúng về mặt kiến thức chung nhưng **không hề xuất hiện trong Evidence** (ví dụ: Evidence chỉ nói về Vector DB, nhưng LLM tự động so sánh với SQL DB).
   - **Hậu quả:** Mô hình NLI (vốn chỉ xét tính chặt chẽ tĩnh giữa Evidence và Claim) sẽ đánh giá Claim này là không được hậu thuẫn bởi Evidence ($P_N \approx 0.99, P_E \approx 0.00$), dẫn tới kết quả `AMBIGUOUS`. Đây là thiết kế **đúng** của Check 3 nhằm chống lại ảo giác ngoài lề.

**Validation (POC 14 cases):**
- **Grounded:** TP = 6, FP = 1, FN = 1
- **Contradiction:** TP = 6, FN = 1
- **Tổng quan:** Mô hình bắt đúng 12/14 cases (85.7%), đủ tin cậy để triển khai cho MVP Check 3.

### Check 3 Aggregation Policy (frozen)

Case-level status:
1. Nếu bất kỳ claim = CONTRADICTION → case = CONTRADICTION
2. Elif bất kỳ claim = AMBIGUOUS  → case = AMBIGUOUS
3. Elif check3_results rỗng      → case = GROUNDED (fallback)
4. Else (tất cả GROUNDED)        → case = GROUNDED

Rationale: Conservative. Thà reject case đúng còn hơn accept
          case có 1 claim sai. Áp dụng cho môi trường
          yêu cầu high precision (y tế, pháp lý, kỹ thuật).

### Truthful Refusal Gate

Chạy **sau Check 2 = MISSING** và **trước khi reject**. Mục đích: phân biệt 3 trường hợp mà trước đây đều được gộp chung vào `rejection`.

**4-way classification:**

| Label | Điều kiện | Status | Reason |
|---|---|---|---|
| `truthful_refusal` | LLM refuse + context không đủ | `refusal` | "Truthful refusal: context insufficient" |
| `false_refusal` | LLM refuse + context đủ | `rejection` | "False refusal: context sufficient but LLM refused" |
| `hallucination_risk` | LLM trả lời + context không đủ | tiếp pipeline | Check 3 bắt |
| `truthful_answer` | LLM trả lời + context đủ | tiếp pipeline | nominal path |

**Answerability Gate — Strict mode (Approach A):**
```
sufficient = (not zero_hit) AND (top1_score >= score_threshold)
Lexical overlap chỉ LOG, không ảnh hưởng quyết định.
```

**Threshold đã chốt: `score_threshold = 0.40`** (cập nhật 2026-09-29)

- Derive từ 13-case test: OOD max top1 = 0.4833, IN min top1 = 0.5713, gap = 0.088
- Xác nhận trên 130-case benchmark (87 IN + 43 OOD từ query logs thực tế):

| Threshold | TP | FN | TN | FP | Accuracy | F1 |
|---|---|---|---|---|---|---|
| **0.40** | **43** | **0** | **87** | **0** | **1.0000** | **1.0000** |
| 0.50 | 43 | 0 | 87 | 0 | 1.0000 | 1.0000 |
| 0.52 | 43 | 0 | 79 | 8 | 0.9385 | 0.9149 |
| 0.55 | 43 | 0 | 65 | 22 | 0.8308 | 0.7963 |

Chọn 0.40 thay vì 0.50: nằm ở rìa dưới của khoảng an toàn (0.40–0.51), ưu tiên tránh FP (reject oan IN) hơn FN, trong khi FN=0 tại mọi ngưỡng ≤ 0.60.

**TP/TN/FP/FN — Ý nghĩa và ưu tiên:**

| Ký hiệu | Ý nghĩa | Hậu quả nếu xảy ra |
|---|---|---|
| **TP** | OOD + reject | ✅ Đúng |
| **TN** | IN + accept | ✅ Đúng |
| **FP** | IN + reject oan | User bị từ chối sai — user khó chịu nhưng không nguy hiểm |
| **FN** | OOD + accept | LLM trả lời OOD — **hallucination risk**, nguy hiểm hơn FP |

Chuyển từ "giết nhầm hơn bỏ sót": **FN tệ hơn FP** — ưu tiên giảm FN (tăng threshold), chấp nhận FP tăng nhẹ.

**TD-004 (mở):** Threshold 0.50 được chọn từ 130 case — chưa có ground truth người dùng thật. Cần re-validate sau khi có ≥ 200 case thật từ production logs.

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

**Quy tắc định dạng Citation (Trong Prompt & Post-processing):**
- **MVP Format (Hiện tại):** Sử dụng Inline `[chunk_id]` trực tiếp trong chuỗi sinh ra (VD: `S3 Glacier giá $0.004/GB [chk_123].`).
  - *Lý do:* Đảm bảo Check 2 (Citation Validity) đơn giản chỉ là kiểm tra Set Membership, và Check 3 (Claim Grounding) dễ dàng parse được citation ngay cạnh claim.
  - *Presentation Layer:* Chuỗi đầu ra vẫn giữ nguyên `[chunk_id]`. Việc biến đổi thành `[1]` hoặc tooltip sẽ do Frontend xử lý (ở các Phase sau) để không làm phức tạp hóa Check 2/3 trong M6.

### 8.2 API Response (Output Contract)
Phản hồi API có **4 trạng thái** (`status`):
- `acceptance`: Query trả lời được, evidence đủ mạnh.
- `rejection`: Query không xử lý được — do **lỗi hệ thống** (guardrail, citation invalid, false refusal, format error, v.v.).
- `ambiguous`: Confidence thấp, nguy cơ hallucination.
- `refusal`: Query không trả lời được vì **context không đủ** — nhưng đây là hành vi ĐÚNG (truthful refusal). Khác biệt với `rejection` ở chỗ: hệ thống làm đúng, chỉ là không có đủ tài liệu để trả lời.

```json
{
  "session_id": "sess_123",
  "user_id": "user_123",
  "metadata": {
    "status": "acceptance",
    "answer": "Giá lưu trữ AWS S3 Glacier là $0.004/GB/tháng [chk_123].",
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

---

## 11. Data Storage & Logging (Hybrid Approach)

Hệ thống lưu trữ áp dụng mô hình **Hybrid Approach** để cân bằng giữa hiệu năng phục vụ giao diện và nhu cầu phân tích dữ liệu chuyên sâu (AIOps):

**Nguyên tắc cốt lõi:**
- **DB = Source of truth**: Database SQLite (`user_queries`) chỉ lưu thông tin cơ bản (`query`, `answer`, `user`, `timestamp`) để phục vụ tính năng hiển thị lịch sử chat trên UI một cách nhẹ nhàng và nhanh chóng.
- **JSON Log = Audit trail**: Lưu toàn bộ các trường phản hồi (bao gồm `status`, `citations`, `reason`, `latency_ms`) theo định dạng JSONL (mỗi record một dòng) để phục vụ cho việc phân tích offline, debug và đo lường chất lượng mô hình.

**Cấu trúc thư mục logs:**
```text
_data/
├── users.db                    ← DB (query + answer)
└── logs/
    ├── 2026-09-24.jsonl        ← JSON log append-only theo ngày
    └── ...
```

**Định dạng JSONL (Audit Trail):**
```jsonl
{"timestamp": "2026-09-24T06:42:48Z", "query_id": "...", "user_id": "demo@...", "query": "...", "status": "ambiguous", "answer": "...", "citations": [...], "metadata": {"reason": "...", "latency_ms": {...}}}
```

**Lợi ích cụ thể của JSONL Log:**
1. **Lưu full response**: Ghi nhận nguyên vẹn toàn bộ đầu ra từ AI, đặc biệt là lý do rớt Guardrails/Checks (ví dụ: Check 1/2/3 failed).
2. **Append-Only Performance**: Tránh lock database khi có nhiều query đồng thời; không cần `ALTER TABLE` khi format thay đổi.
3. **AIOps Ready**: Có thể nạp nhanh chóng vào Pandas hoặc dùng lệnh `jq` để thống kê Tỷ lệ Ambiguous, phân tích Latency P95, đếm lỗi theo từng loại reason hoặc tiến hành Replay query.
