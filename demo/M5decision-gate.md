# Contract: Decision Gate Holdout Validation (M5)

## 1. Object
**Decision Gate (Decision under Uncertainty)** cho mô hình Reranker.

## 2. Purpose
Thiết lập giao thức (protocol) để kiểm chứng giả thuyết H6: *"A simple Gate can control the Rescue ↔ Regression trade-off"*. 
Bản hợp đồng này cố định các điều kiện thực nghiệm từ Development Set để tiến hành Validate trên tập Holdout. Mục đích không phải là chốt model BGE hay rule `0.20` cho production, mà là chứng minh cơ chế Gate có khả năng khái quát hóa (generalize).

## 3. Current State
- **Đã chứng minh:** Ranking là bottleneck, Cross-Encoder có thể giải quyết nhưng gây ra Collateral Regression.
- **Chưa chứng minh:** Threshold và Rule thu được trên tập Dev có hiệu quả tương tự trên tập Holdout hay không.
- **Quy tắc bị "đóng băng" (Frozen Rule) để thử nghiệm:** `(BGE_Top1_Score >= 0.20) OR (Baseline_Rank_of_BGE_Top1 <= 1)`.
- **Trạng thái:** Gate đang ở mức "promising control mechanism" chứ chưa phải "production routing policy".

## 4. Expected State
- Hoàn thành Validation trên tập Holdout với các biến số đã bị khóa chặt.
- Thu thập đủ dữ liệu để trả lời câu hỏi: Rule `0.20 + Rank 1` có giữ được tính đánh đổi (Rescue ↔ Regression) tương tự trên tập dữ liệu chưa từng thấy hay không?
- Nếu thành công, xác nhận Gate C là một cơ chế khả thi cho hệ thống production.

## 5. Sub-tasks
1. **Chốt Holdout Protocol:** Lựa chọn tập dữ liệu Holdout.
2. **Setup Validation Pipeline:** Đưa logic Frozen Rule vào script đánh giá độc lập (ví dụ `poc_holdout_validation.py`).
3. **Execution:** Chạy pipeline trên tập Holdout mà không điều chỉnh bất kỳ tham số nào.
4. **Acceptance Review:** Áp dụng hệ tiêu chí (Criteria) để ra quyết định cuối cùng.

## 6. Technique
- Sử dụng Raw Logits trực tiếp từ mô hình `BAAI/bge-reranker-v2-m3` để giả lập production reranker.
- Baseline Rank lấy từ hệ thống MinMax Fusion.
- Chạy Inference dưới dạng subprocess (CPU-safe) để loại trừ rủi ro Memory Segmentation Fault (Exit code -1073741819) đã ghi nhận trong lúc chạy sweep.

## 7. Input
- `/demo/M5decision-gate.md` (Tài liệu này).
- `evaluation/results/m5_final_hypotheses_conclusion.md` (Cơ sở lý luận H1-H6).
- Tập dữ liệu Holdout.

## 8. Workflow
1. Khởi tạo Pipeline Đánh giá Holdout.
2. Tiêm (Inject) Frozen Rule vào Pipeline.
3. Chạy Inference và Evaluation trên tập Holdout.
4. Xuất báo cáo Holdout Report.
5. Căn cứ vào Acceptance Criteria để đưa ra quyết định hợp nhất (Merge Decision).

## 9. Criteria Output - Output Format
**Acceptance Criteria (Tiêu chí chấp thuận):**
1. **Rescue Ratio:** Phải giữ được phần lớn khả năng rescue so với mức tối đa của BGE-only trên tập Holdout.
2. **Regression Constraint:** Phải giảm thiểu đáng kể số lượng Regression so với BGE-only.
3. **Overfitting Check:** Độ lệch MRR First giữa Dev và Holdout phải nằm trong biên độ chấp nhận được.

**Output Format:**
- File log kết quả JSONL chứa ranking cuối cùng.
- Bảng so sánh 3 hệ thống (Baseline / BGE-only / Gate-0.20) trên terminal.

## 10. Format Report
Báo cáo Holdout Report sẽ có cấu trúc:
1. **Holdout Protocol:** Khẳng định các biến số đã bị khóa.
2. **Trade-off Analysis:** Phân tích Rescue vs Regression trên tập Holdout.
3. **Generalization Check:** Đánh giá mức độ sụt giảm hiệu năng so với Dev Set.
4. **Final Decision:** Gate C có đủ điều kiện trở thành Production Mechanism hay không?
