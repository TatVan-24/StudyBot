# M5 Step 3: Detailed Model Comparison Report

Báo cáo này phân tích chi tiết hiệu suất của 3 mô hình Cross-Encoder đã được thử nghiệm trong M5 Step 3, lấy `ms-marco-MiniLM-L-6-v2` (thuần tiếng Anh) làm chuẩn (baseline model) để đánh giá sự vượt trội của các mô hình đa ngôn ngữ (`mMARCO` và `BGE-M3`).

## 1. Tổng quan các Model được thử nghiệm
- **Model Chuẩn (MiniLM)**: `cross-encoder/ms-marco-MiniLM-L-6-v2` (Thuần tiếng Anh, ~90MB)
- **mMARCO**: `cross-encoder/mmarco-mMiniLMv2-L12-H384-v1` (Đa ngôn ngữ, ~471MB)
- **BGE**: `BAAI/bge-reranker-v2-m3` (Đa ngôn ngữ, SOTA, ~2.27GB)

---

## 2. Bảng So Sánh Chi Tiết Từng Model (vs MinMax Baseline)

### 2.1. Kết quả của model MiniLM (`ms-marco-MiniLM-L-6-v2`)
*Ghi chú: Model này thất bại thảm hại do không hiểu được semantic của tiếng Việt và thuật ngữ AWS.*

**--- Group A ---**
Metric          | MinMax Baseline      | Cross-Encoder        | Change    
---------------------------------------------------------------------------
mrr_first       | 0.2714               | 0.1980               | -0.0733 ▼
mrr_full        | 0.1869               | 0.1026               | -0.0843 ▼
cov_10          | 0.5758               | 0.3825               | -0.1933 ▼

**--- Group B ---**
Metric          | MinMax Baseline      | Cross-Encoder        | Change
---------------------------------------------------------------------------
mrr_first       | 0.1319               | 0.2417               | +0.1097 ▲
mrr_full        | 0.0312               | 0.0125               | -0.0187 ▼
cov_10          | 0.3312               | 0.2146               | -0.1167 ▼

**--- Strong Anchors ---**
Metric          | MinMax Baseline      | Cross-Encoder        | Change
---------------------------------------------------------------------------
mrr_first       | 1.0000               | 0.7064               | -0.2936 ▼
cov_10          | 0.5794               | 0.5703               | -0.0092 -

### 2.2. Kết quả của model mMARCO (`mmarco-mMiniLMv2-L12-H384-v1`)

**--- Group A ---**
Metric          | MinMax Baseline      | Cross-Encoder        | Change
---------------------------------------------------------------------------
mrr_first       | 0.2714               | 0.5116               | +0.2402 ▲
mrr_full        | 0.1869               | 0.3667               | +0.1798 ▲
cov_10          | 0.5758               | 0.5836               | +0.0078 -

**--- Group B ---**
Metric          | MinMax Baseline      | Cross-Encoder        | Change
---------------------------------------------------------------------------
mrr_first       | 0.1319               | 0.4792               | +0.3472 ▲
mrr_full        | 0.0312               | 0.2500               | +0.2188 ▲
cov_10          | 0.3312               | 0.4646               | +0.1333 ▲

**--- Strong Anchors ---**
Metric          | MinMax Baseline      | Cross-Encoder        | Change
---------------------------------------------------------------------------
mrr_first       | 1.0000               | 0.7077               | -0.2923 ▼
cov_10          | 0.5794               | 0.4837               | -0.0957 ▼

### 2.3. Kết quả của model BGE (`BAAI/bge-reranker-v2-m3`)

**--- Group A ---**
Metric          | MinMax Baseline      | Cross-Encoder        | Change
---------------------------------------------------------------------------
mrr_first       | 0.2714               | 0.6967               | +0.4253 ▲
mrr_full        | 0.1869               | 0.4187               | +0.2317 ▲
cov_10          | 0.5758               | 0.7252               | +0.1494 ▲

**--- Group B ---**
Metric          | MinMax Baseline      | Cross-Encoder        | Change
---------------------------------------------------------------------------
mrr_first       | 0.1319               | 0.6000               | +0.4681 ▲
mrr_full        | 0.0312               | 0.2500               | +0.2188 ▲
cov_10          | 0.3312               | 0.4146               | +0.0833 ▲

**--- Strong Anchors ---**
Metric          | MinMax Baseline      | Cross-Encoder        | Change
---------------------------------------------------------------------------
mrr_first       | 1.0000               | 0.7756               | -0.2244 ▼
cov_10          | 0.5794               | 0.5813               | +0.0018 -

---

## 3. Thống Kê So Sánh (Lấy MiniLM làm chuẩn)

Phần này phân tích **mMARCO** và **BGE** đã thay đổi hiệu suất như thế nào so với model chuẩn **MiniLM**. Điều này làm nổi bật tác động của việc trang bị năng lực đa ngôn ngữ (Multilingual) và quy mô mô hình lớn hơn.

| Nhóm / Metric | MiniLM (Chuẩn) | mMARCO vs MiniLM | BGE vs MiniLM | Đánh giá |
| :--- | :--- | :--- | :--- | :--- |
| **Group A: MRR First** | 0.1980 | `0.5116` (+0.3136) | **`0.6967` (+0.4987)** | Khả năng nhặt target ở Group A tăng vọt khi có Multilingual. BGE cực kỳ vượt trội. |
| **Group A: MRR Full** | 0.1026 | `0.3667` (+0.2641) | **`0.4187` (+0.3161)** | BGE gom các block liên quan tốt gấp 4 lần MiniLM. |
| **Group A: Cov@10** | 0.3825 | `0.5836` (+0.2011) | **`0.7252` (+0.3427)** | BGE phủ sóng gần như toàn bộ target trong Top-10. |
| **Group B: MRR First** | 0.2417 | `0.4792` (+0.2375) | **`0.6000` (+0.3583)** | Ở đáy pool, cả mMARCO và BGE đều bới target lên rất xuất sắc. |
| **Group B: Cov@10** | 0.2146 | **`0.4646` (+0.2500)** | `0.4146` (+0.2000) | mMARCO có độ bao phủ Top-10 cho nhóm khó (Group B) nhỉnh hơn BGE một chút. |
| **Strong Anchors: MRR First** | 0.7064 | `0.7077` (+0.0013) | **`0.7756` (+0.0692)** | *Collateral Damage*. Tuy BGE đỡ tệ hơn MiniLM, nhưng nó vẫn làm mất 22.4% MRR so với Baseline ban đầu (1.0). |
| **Strong Anchors: Cov@10** | 0.5703 | `0.4837` (-0.0866) | **`0.5813` (+0.0110)** | MiniLM và BGE bảo toàn được Cov@10 cho Anchors, nhưng mMARCO lại làm rơi rớt bớt evidence khỏi Top 10. |

### 3.1. Phân tích Insight từ bảng so sánh:
1. **Sự sụp đổ của MiniLM**: Khi thiếu năng lực đa ngôn ngữ, mô hình Reranker thậm chí làm kết quả tệ hơn cả thuật toán đếm từ BM25 (dìm Group A MRR First từ 0.27 xuống 0.19).
2. **Sức mạnh của Multilingual (mMARCO)**: Chỉ cần trang bị khả năng đa ngôn ngữ trên cùng kiến trúc nhỏ, mMARCO lập tức đảo ngược tình thế, kéo MRR First của Group A lên 0.5116.
3. **Quy mô mô hình (BGE-M3)**: Khi tăng kích thước mô hình (567M params), BGE đạt được độ chính xác rất cao ở Group A và Group B (MRR First ~0.7 và 0.6). Tuy nhiên, **NÓ VẪN KHÔNG GIẢI QUYẾT ĐƯỢC COLLATERAL DAMAGE** trên Strong Anchors (vẫn làm tụt từ 1.0 xuống 0.77).

=> **Kết luận cuối cùng**: Tín hiệu "Collateral Damage" hoàn toàn **không phải do model dở (MiniLM)**, mà nó tồn tại dai dẳng ở mọi cấp độ Reranker, từ nhỏ nhất đến SOTA lớn nhất. Đây chính là bản chất của sự đánh đổi khi dùng Cross-Encoder trên corpus này!
