# RAG Pipeline Design & Workflow (M1 - M6)

Tài liệu này mô tả chi tiết luồng xử lý dữ liệu (Data Pipeline) và kiến trúc của hệ thống RAG (Retrieval-Augmented Generation) tại tầng Local Worker, tính đến hết Milestone 6. Hệ thống đã hoàn thiện Data Ingestion, Information Retrieval, Decision Gate, LLM Generation và hệ thống Input/Output Guardrails.

---

## 1. Overall RAG Pipeline Architecture (Current — M6)

Bức tranh toàn cảnh từ tài liệu thô đến khi user nhận được kết quả. Pipeline giờ đã tích hợp LLM Generation cùng bộ 3 Checks và Guardrails (M6).

```mermaid
flowchart TD
    classDef storage fill:#f9f9f9,stroke:#333,stroke-width:2px,stroke-dasharray: 5 5
    classDef process fill:#e1f5fe,stroke:#01579b,stroke-width:2px
    classDef query fill:#fff3e0,stroke:#e65100,stroke-width:2px
    classDef gate fill:#ede7f6,stroke:#6a1b9a,stroke-width:2px
    classDef guardrail fill:#fce4ec,stroke:#c2185b,stroke-width:2px

    subgraph INGESTION [Data Ingestion Pipeline — M1/M2/M3]
        direction TB
        Raw[Raw Documents] -->|M1: Parser| Blocks[Parsed Blocks]
        Blocks -->|M2: Chunker| Chunks[Text Chunks ≤ 512 tokens]
        Chunks -->|M3: Embedder| Vectors[768d Dense Vectors]
    end

    subgraph STORAGE [Local Storage]
        DB[(SQLite Vector Store)]
        BM25_Index[(BM25 Sparse Index)]
    end

    subgraph GUARD_IN [Input Guardrail — M6]
        direction TB
        UserQ([User Query]) --> T1_Inj[T1: Injection Detection\nRegex Patterns]
        T1_Inj --> T2_Val[T2: Query Validation]
        T2_Val --> T3_Sess[T3: Session/Doc Validation]
    end

    subgraph RETRIEVAL [Query & Retrieval Pipeline — M4]
        direction TB
        PreProcess[Query Pre-processing] --> Q_Embed[MPNet Embedding]
        PreProcess --> Q_Token[Tokenization]

        Q_Embed -->|Dense Search Top-20| KNN[Exact KNN L2 Distance]
        Q_Token -->|Sparse Search Top-20| BM25[BM25 Scoring]

        KNN --> Pool[(Candidate Pool)]
        BM25 --> Pool

        Pool --> ScoreFusion[Min-Max Score Fusion]
        ScoreFusion --> BaselineRank[Baseline Ranking]
    end

    subgraph M5_GATE [Decision Gate — M5]
        direction TB
        BaselineRank --> BGEScore[BGE Reranker\nBAI/bge-reranker-v2-m3]
        BGEScore --> GateDecision{Decision Gate}
        GateDecision --> FinalEvidence[Final Evidence]
    end

    subgraph GENERATION [Generation & Verification — M6]
        direction TB
        FinalEvidence --> Check1[Check 1: Evidence Sufficiency]
        Check1 -->|Pass| LLM[LLM Generation]
        Check1 -->|Fail| Reject1[Reject: Insufficient]

        LLM --> Check2[Check 2: Citation Validity]
        Check2 -->|MISSING| RefusalGate[Truthful Refusal Gate\nrefusal.py classify\u28024-way\u2803]
        Check2 -->|INVALID| Amb[Ambiguous: Hallucinated citation]
        Check2 -->|VALID| Check3[Check 3: Claim Grounding\nmDeBERTa NLI]

        RefusalGate -->|truthful_refusal| StatusRefusal([status: refusal])
        RefusalGate -->|false_refusal| Reject2[Reject: False Refusal]
        RefusalGate -->|format_error| Reject3[Reject: No citation]

        Check3 -->|Grounded/Ambiguous| GuardOut[Output Guardrail\nPII, Sec, Leak]
        Check3 -->|Contradiction| Reject4[Reject: Hallucination]

        GuardOut --> FinalResult([Final API Contract\nstatus: acceptance / ambiguous / rejection / refusal])
    end

    Vectors --> DB
    Chunks --> BM25_Index
    Chunks --> DB
    DB --> KNN
    BM25_Index --> BM25

    T3_Sess -->|Valid| PreProcess
    T3_Sess -->|Invalid| Reject0[Reject: Invalid Input]
    FinalEvidence --> Check1

    class Raw,Blocks,Chunks,Vectors,UserQ,FinalResult,LLM query
    class INGESTION,RETRIEVAL,GENERATION process
    class DB,BM25_Index storage
    class M5_GATE gate
    class GUARD_IN guardrail
```

---

## 2. Milestone Breakdown

### M1: Parser Workflow
Nhiệm vụ: Chuyển đổi tài liệu thô thành Parsed Blocks có cấu trúc, bảo toàn Lineage và Metadata.

```mermaid
sequenceDiagram
    participant S as Source File (TXT / MD / PDF)
    participant P as Document Parser
    participant V as Schema Validator
    participant B as ParsedBlock

    S->>P: Read raw bytes
    activate P
    P->>P: Extract text content
    P->>P: Identify structures (Headings, Lists, Tables, Code)
    P->>V: Validate against Pydantic schema
    activate V
    alt Validation Failed
        V-->>P: Throw Error (Corrupt data)
    else Validation Passed
        V-->>P: OK
    end
    deactivate V
    P->>B: Create Block (block_id, text, metadata, locator)
    deactivate P
```

**Status:** ✅ CLOSED — TXT, MD, PDF parsers validated. 1910 blocks → `bundle_all/blocks.jsonl`.

---

### M2: Chunker Workflow
Nhiệm vụ: Cắt Parsed Blocks thành Chunks ≤ 512 tokens, bảo toàn `source_block_ids` để Lineage tracking.

```mermaid
flowchart LR
    Block[Parsed Block] --> Check{Token count > 512?}
    Check -->|No| AsIs[Keep as single Chunk]
    Check -->|Yes| Split[Intra-block Splitting]
    Split --> S1[Split by Paragraph]
    S1 --> S2[Split by Sentence]
    S2 --> S3[Overlap window]
    AsIs --> Build[Build Chunk Object]
    S3 --> Build
    Build --> Meta[Attach Lineage: source_block_ids]
    Meta --> Final[Ready for Embedding]

    style Check fill:#ffcccc,stroke:#cc0000
    style Final fill:#cce5ff,stroke:#0066cc
```

**Status:** ✅ CLOSED — 1972 chunks, 100% coverage, 0 schema violations. `evaluation/runs/m2-final`.

---

### M3: Embedding & Indexing Workflow
Nhiệm vụ: Chuyển Text Chunks thành 768d vectors và lưu vào SQLite.

```mermaid
flowchart TD
    subgraph Vectorization
        C[Text Chunks] --> MPNet[sentence-transformers/\nparaphrase-multilingual-mpnet-base-v2]
        MPNet -->|Batch encode| V[768-dimensional Vectors]
    end

    subgraph Persistence
        V --> SQLite[(Local SQLite DB\nm3_index.db)]
        C --> SQLite
        SQLite -->|Schema| T_Embeds[Table: embeddings\nchunk_id + BLOB vector + source_block_ids]
    end
```

**Status:** ✅ CLOSED — 1972 chunks indexed. 6 invariants passed. `evaluation/index/m3_index.db`.

---

### M4: Hybrid Retrieval — Score Fusion Workflow
Nhiệm vụ: Tìm kiếm và xếp hạng Candidates liên quan nhất với query. Baseline retrieval cho M5.

```mermaid
flowchart TD
    Query[/User Query/] --> Split[ ]

    subgraph Dense Retrieval
        Split --> EmbedQ[Embed Query via MPNet]
        EmbedQ --> L2[KNN L2 Distance on SQLite]
        L2 --> DenseTop20[Dense Top-20]
    end

    subgraph Sparse Retrieval
        Split --> TokenizeQ[Tokenize Query]
        TokenizeQ --> BM25Calc[BM25 Scoring]
        BM25Calc --> BM25Top20[BM25 Top-20]
    end

    DenseTop20 --> Union[Union + Dedup\nCandidate Pool]
    BM25Top20 --> Union

    Union --> Norm1[Min-Max Norm Dense]
    Union --> Norm2[Min-Max Norm BM25]

    Norm1 --> Fusion
    Norm2 --> Fusion

    subgraph Fusion Engine
        Fusion{Score = 0.4×Dense + 0.6×BM25}
        Fusion --> BaselineRank[Rank by Fused Score]
    end

    BaselineRank --> Output[Baseline Top-K]

    style Fusion fill:#ffe0b2,stroke:#f57c00
```

**Status:** ✅ CLOSED — Fixed alpha rejected (ADR-005). Baseline frozen at α=0.4. Holdout: MRR First = 88.58. `evaluation/results/m4_holdout_results.jsonl`.

---

### M5: Decision Gate Workflow — CLOSED ✅
Nhiệm vụ: Kiểm soát sự đánh đổi Rescue ↔ Regression khi dùng CE Reranker. Gate deterministic, không tune sau Holdout.

```mermaid
flowchart TD
    BaselinePool[Baseline Candidate Pool\nTop-20 Dense ∪ BM25] --> BGEReranker

    subgraph BGE Reranking
        BGEReranker[BGE Cross-Encoder\nbge-reranker-v2-m3\nfloat32 / CPU]
        BGEReranker --> Scores[Raw Logit Scores\naligned to baseline pool]
        Scores --> BGETop1[BGE Top-1\nchunk_id + score]
    end

    BGETop1 --> Signal1[Signal 1:\nbge_top1_score]
    BGETop1 --> Signal2[Signal 2:\nbaseline_rank_of_bge_top1]

    Signal1 --> Gate{Decision Gate\nFROZEN}
    Signal2 --> Gate

    Gate -->|score >= 0.20\nOR baseline_rank <= 1| PassBGE[PASS → select BGE Top-1]
    Gate -->|score < 0.20\nAND baseline_rank > 1| FailFallback[FAIL → fallback to Baseline Top-1]

    PassBGE --> Final[Final Evidence]
    FailFallback --> Final

    Final --> Classify[Classify Outcome]
    Classify --> Rescue[RESCUE:\nGated rank < Baseline rank]
    Classify --> Regression[REGRESSION:\nBaseline rank==1 → Gated rank>1]
    Classify --> GenDeg[GENERAL DEGRADATION:\nnon-SA rank worsening]
```

**Frozen Rule:**
```python
selected = (
    bge_top1
    if (bge_top1_score >= 0.20 or baseline_rank_of_bge_top1 <= 1)
    else baseline_top1
)
```

**Holdout Results (test-v2.jsonl — 24 cases):**

| System | Rescue | Regression | MRR First | Cov@10 |
|--------|-------:|----------:|--------:|------:|
| Baseline | — | 0 | 88.58 | 0.6256 |
| BGE-only | 4 | 1 | 86.54 | 0.6673 |
| **Gated** | **4** | **1** | **87.88** | **0.6673** |

**H6 = SUPPORTED ON HOLDOUT** (Rescue retention 100% ≥ 90%, Regression 1 ≤ 1)

**Status:** ✅ CLOSED — ADR-006. Artifacts: `m5_holdout_trace.jsonl`, `m5_holdout_report.md`.

> `H6 SUPPORTED ≠ Gate approved for production.` (ADR-006 §9.4)

---

---

### M6: LLM Generation, Verification & Guardrails
Nhiệm vụ: Tích hợp LLM sinh câu trả lời kèm trích dẫn, đảm bảo an toàn đầu vào/đầu ra, và xác thực bằng 3 Checks (Evidence, Citation, Grounding).

**Input Guardrail (T1/T2/T3):** Chặn Prompt Injection, System Leakage, và Query rỗng bằng bộ quy tắc Regex và Logic.

**Kiến trúc Sinh Trích Dẫn và Hậu Kiểm (Controlled Generation):**
Sự tách biệt rõ ràng trách nhiệm giữa việc sinh ra trích dẫn và xác thực trích dẫn:
- **Retrieval (Cấp Evidence):** Tìm kiếm và cung cấp các chunk văn bản (Evidence) có sẵn `chunk_id` cho LLM.
- **LLM Citation Generation (Sinh Answer & Reference):** LLM tự động đọc Evidence, sinh ra câu trả lời và bắt buộc chèn marker `[chunk_id]` vào cuối mỗi factual claim để báo cho hệ thống biết nó đang dựa vào chunk nào. (LLM có thể không trích dẫn, trích dẫn sai ID, hoặc trích dẫn ID có thật nhưng sai nội dung).
- **Check 1 (Evidence Sufficiency):** Kiểm tra số lượng/chất lượng Evidence đầu vào trước khi gọi LLM.
- **Check 2 (Citation Validity - Hậu kiểm ID):** Parser dùng regex quét `[chunk_id]` từ LLM output. Kiểm tra xem các ID này có THỰC SỰ tồn tại trong danh sách Evidence ban đầu hay không. (Ngăn chặn Hallucination ID ảo).
- **Check 3 (Claim Grounding - Hậu kiểm Nội dung):** Nếu Check 2 Pass, dùng NLI (`mDeBERTa`) đối chiếu từng câu khẳng định của LLM với nội dung của `chunk_id` tương ứng xem có thực sự Support hay không. (Ngăn chặn Hallucination nội dung). Phân loại: GROUNDED, AMBIGUOUS, CONTRADICTION.

**Output Guardrail:** Chặn PII, Credentials, API Keys, Prompt Leakage lọt ra ngoài.

**Status:** ✅ HOÀN THÀNH (28/09/2026) — Tich̀ hợp Claude Haiku. 3-Checks Architecture (Evidence Sufficiency, Citation Validity, NLI Claim Grounding) hoàn thiện. Truthful Refusal Gate phân biệt 4 trạng thái. Conservative Aggregation Policy (any AMBIGUOUS → AMBIGUOUS). System Prompt với CITATION PRECISION Procedure Self-check.

---

## 3. Complete System Flow — M1 to M6

```mermaid
flowchart LR
    Raw[Raw\nDocuments] -->|Parse| Blocks
    Blocks -->|Chunk| Chunks
    Chunks -->|Embed| Vectors
    Vectors -->|Index| DB[(SQLite)]

    Query[User\nQuery] -->|T1/T2/T3| InGuard{Input\nGuardrail}
    InGuard -->|Pass| Dense[KNN Top-20]
    InGuard -->|Fail| RejectOut([Reject])

    Dense --> Pool[Candidate Pool]
    DB --> Dense

    Pool -->|Min-Max\nFusion| Baseline[Baseline\nRanking]

    Baseline -->|CE Score| BGE[BGE\nReranker]
    BGE --> Gate{Decision\nGate}

    Gate --> Evidence[Final\nEvidence]

    Evidence --> Check1{Check 1:\nSufficiency}
    Check1 -->|Pass| LLM[LLM\nGeneration]
    Check1 -->|Fail| RejectOut

    LLM --> Check23{Check 2/3:\nVerification}
    Check23 -->|Contradict| RejectOut
    Check23 -->|Pass/Amb| OutGuard{Output\nGuardrail}

    OutGuard -->|Fail| RejectOut
    OutGuard -->|Pass| FinalApi([Final API\nContract])

    style Gate fill:#ede7f6,stroke:#6a1b9a,stroke-width:3px
    style Evidence fill:#c8e6c9,stroke:#2e7d32,stroke-width:2px
    style LLM fill:#fff9c4,stroke:#f9a825,stroke-dasharray: 5 5
```

---

## 4. Known Limitations & Open Issues

| Component | Status | Limitation |
|-----------|--------|-----------|
| Decision Gate | ✅ CLOSED | H6 supported on Holdout but gate not production-approved yet |
| holdout_008 | Residual risk | BGE score=0.9960 but still caused regression — score ≠ always correct |
| Generation (M6) | ✅ CLOSED (28/09/2026) | 3-Checks + Truthful Refusal Gate hoàn thiện |
| Check 1 Bypass | Tech debt | check_1_sufficiency() bị comment out, threshold calibrate cho BGE không phù hợp MPNet. Cần re-calibrate sau khi có ≥ 50 case |
| Refusal Threshold | Tech debt | log_only mode, chưa tuân threshold. Cần ≥ 50 case có ground truth để derive từ ROC curve |
| DOCX / PPTX | ⏳ M7 | Parsers not implemented |
| CE Inference speed | Known | CPU float32 inference: ~25-40min for 35 cases |
| Process isolation | Workaround | CE must run in subprocess to avoid Windows `0xC0000005` |

---

## 5. Artifact Map

```text
evaluation/
├── datasets/
│   ├── test-v3.jsonl          ← M5 Development Set (35 cases)
│   └── test-v2.jsonl          ← M5 Holdout Set    (25 cases, FROZEN)
├── index/
│   └── m3_index.db            ← SQLite Vector Store (1972 chunks)
├── bundle_all/
│   └── blocks.jsonl           ← 1910 parsed blocks
├── results/
│   ├── m5_step5_raw_scores.json  ← Dev sweep CE scores
│   ├── m5_holdout_trace.jsonl    ← Holdout case-level trace
│   └── m5_holdout_report.md      ← Holdout aggregate report
└── scripts/
    ├── m5_step5_gate_sweep.py       ← Dev sweep
    ├── m5_step5_ce_runner.py        ← Dev CE subprocess
    ├── m5_step6_holdout_validation.py  ← Holdout main script
    └── m5_step6_ce_runner.py           ← Holdout CE subprocess

Architecture/
├── ADR-005-retrieval-fusion-decision.md  ← M4 decision
└── ADR-006-decision-gate-holdout.md      ← M5 decision (FROZEN)
```
