# RAG Pipeline Design & Workflow (M1 - M4)

Tài liệu này mô tả chi tiết luồng xử lý dữ liệu (Data Pipeline) và kiến trúc của hệ thống RAG (Retrieval-Augmented Generation) tại tầng Local Worker, tính đến hết Milestone 4. Hệ thống hiện tại tập trung hoàn toàn vào Data Ingestion và Information Retrieval, chưa bao gồm Generation (LLM).

## 1. Overall RAG Pipeline Architecture

Bức tranh toàn cảnh quá trình một tài liệu thô đi vào hệ thống cho đến khi user thực hiện query.

```mermaid
flowchart TD
    %% Define Styles
    classDef storage fill:#f9f9f9,stroke:#333,stroke-width:2px,stroke-dasharray: 5 5
    classDef process fill:#e1f5fe,stroke:#01579b,stroke-width:2px
    classDef query fill:#fff3e0,stroke:#e65100,stroke-width:2px
    
    %% Ingestion Flow
    subgraph INGESTION [Data Ingestion Pipeline]
        direction TB
        Raw[Raw Documents: TXT, MD, PDF] -->|M1: Parser| Blocks[Parsed Blocks with Metadata]
        Blocks -->|M2: Chunker| Chunks[Text Chunks <= 512 tokens]
        Chunks -->|M3: Embedder| Vectors[768d Dense Vectors]
    end
    
    %% Storage
    subgraph STORAGE [Local Storage]
        DB[(SQLite Database)]
        BM25_Index[(BM25 Sparse Index)]
    end
    
    %% Retrieval Flow
    subgraph RETRIEVAL [Query & Retrieval Pipeline - M4]
        direction TB
        UserQ([User Query]) --> PreProcess[Query Pre-processing]
        PreProcess --> Q_Embed[MPNet Embedding]
        PreProcess --> Q_Token[Tokenization]
        
        Q_Embed -->|Dense Search| KNN[Exact KNN L2 Distance]
        Q_Token -->|Sparse Search| BM25[BM25 Scoring]
        
        KNN --> ScoreFusion[Min-Max Score Fusion]
        BM25 --> ScoreFusion
        
        ScoreFusion --> TopK[Top-K Candidates]
    end
    
    %% Connections
    Vectors --> DB
    Chunks --> BM25_Index
    Chunks --> DB
    
    DB --> KNN
    BM25_Index --> BM25
    
    TopK -.->|Wait for M5/M6| LLM([Local LLM Generation])
    
    class Raw,Blocks,Chunks,Vectors,UserQ,TopK,LLM query
    class INGESTION,RETRIEVAL process
    class DB,BM25_Index storage
```

---

## 2. Milestone Breakdown

Dưới đây là sơ đồ chi tiết (Zoom-in) vào từng Milestone trong quá trình xây dựng RAG Pipeline.

### M1: Parser Workflow
Nhiệm vụ: Chuyển đổi dữ liệu phi cấu trúc thành các Block có cấu trúc, bảo toàn Lineage (nguồn gốc) và Metadata.

```mermaid
sequenceDiagram
    participant S3 as AWS S3 / Local File
    participant P as Document Parser
    participant V as Schema Validator
    participant B as ParsedBlock

    S3->>P: Read raw bytes (bundle_all.md)
    activate P
    P->>P: Extract text content
    P->>P: Identify structures (Headings, Lists, Tables)
    P->>V: Validate against strict Pydantic schema
    activate V
    alt Validation Failed
        V-->>P: Throw Error (Corrupt data)
    else Validation Passed
        V-->>P: OK
    end
    deactivate V
    P->>B: Create Block (ID, text, metadata, page_num)
    deactivate P
```

### M2: Chunker Workflow
Nhiệm vụ: Cắt ParsedBlocks thành các Chunk có kích thước phù hợp với cửa sổ ngữ cảnh (Context Window) của Embedding Model, không làm rách câu.

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
    
    Build --> Meta[Attach Lineage: source_block_id]
    Meta --> Final[Ready for Embedding]
    
    style Check fill:#ffcccc,stroke:#cc0000
    style Final fill:#cce5ff,stroke:#0066cc
```

### M3: Embedding & Indexing Workflow
Nhiệm vụ: Chuyển đổi Text Chunks thành các vector toán học và lưu trữ an toàn trong Local Database.

```mermaid#left
flowchart TD
    subgraph Vectorization
        C[Text Chunks] --> MPNet[sentence-transformers/paraphrase-multilingual-mpnet-base-v2]
        MPNet -->|Batch encode| V[768-dimensional Vectors]
    end
    
    subgraph Persistence
        V --> SQLite[(Local SQLite DB)]
        C --> SQLite
        SQLite -->|Schema| T_Chunks[Table: chunks]
        SQLite -->|Schema| T_Embeds[Table: embeddings BLOB]
    end
    
    %% Assertions
    T_Chunks -.->|Foreign Key| T_Blocks[Table: parsed_blocks]
```

### M4: Retrieval & Score Fusion Workflow (Hybrid Search)
Nhiệm vụ: Tìm kiếm và xếp hạng (Ranking) các Chunk liên quan nhất với truy vấn của người dùng. Đây là điểm chốt chặn trước khi đưa ngữ cảnh cho LLM.

```mermaid
flowchart TD
    Query[/User Query/] --> Split
    
    subgraph Branch 1: Dense Retrieval
        Split --> EmbedQ[Embed Query using MPNet]
        EmbedQ --> FetchVec[(SQLite Embeddings)]
        FetchVec --> L2[Calculate L2 Distance]
        L2 --> DenseScores[Dense Candidate Scores]
    end
    
    subgraph Branch 2: Sparse Retrieval
        Split --> TokenizeQ[Tokenize Query]
        TokenizeQ --> FetchInv[(BM25 Inverted Index)]
        FetchInv --> TFIDF[Calculate BM25 Algorithm]
        TFIDF --> SparseScores[Sparse Candidate Scores]
    end
    
    DenseScores --> Norm1[Min-Max Normalization 0..1]
    SparseScores --> Norm2[Min-Max Normalization 0..1]
    
    Norm1 --> Fusion
    Norm2 --> Fusion
    
    subgraph Fusion Engine
        Fusion{Alpha Weighting}
        Fusion -->|Score = α * Dense + 1-α * Sparse| FinalRank
        FinalRank[Rank Candidates by Combined Score]
    end
    
    FinalRank --> Guardrail{Pass Quality Gate?}
    Guardrail -->|Yes| Output[Top-K Evidences]
    Guardrail -->|No| Reject[Fallback / Empty Context]
    
    style Guardrail fill:#ffe0b2,stroke:#f57c00
    style Reject fill:#ffcdd2,stroke:#d32f2f
```

---

## 3. Current Limitations (Triggering M5)
Mặc dù M1-M4 đã hoàn thiện Data Pipeline, sơ đồ M4 (Retrieval) đang bộc lộ điểm nghẽn tại bước `Split` và `Guardrail`:
1. M4 không có khả năng tự động bắt cầu từ vựng (Alignment Gap).
2. Điểm số kết hợp (Fusion Engine) thường xuyên thất bại trong việc đưa Target lên Top 1-2 khi gặp nhiễu (Ranking Weakness).
3. Do đó, cần một chiến dịch Can thiệp (M5) nhắm thẳng vào kiến trúc của M4 để vượt qua Guardrail.

---

## 4. Proposed M5 Architecture (with Cross-Encoder Reranking)
*Lưu ý: Đây là sơ đồ hệ thống đang được thử nghiệm trong M5 Step 3. Cross-Encoder hoạt động như một màng lọc ngữ nghĩa lớp 2, thay thế cho MinMax Fusion trực tiếp.*

```mermaid
graph TD
    User([User]) -->|Input Query| Q[Query Processor]
    
    Q --> DenseRet[Dense Retriever]
    Q --> SparseRet[BM25 Retriever]
    
    DenseRet -->|Top-20 Chunks| Pool
    SparseRet -->|Top-20 Chunks| Pool
    
    subgraph M5 Intervention: Reranking
        Pool[(Candidate Pool<br>Union Top-20)]
        Pool --> CE[Cross-Encoder Reranker]
        Q -.->|Context| CE
        CE -->|Cross-Attention Scoring| ReRank[Reranked List]
    end
    
    ReRank --> Guardrail{Pass Quality Gate?}
    Guardrail -->|Yes| Output[Top-K Evidences]
    Guardrail -->|No| Reject[Fallback / Empty Context]
    
    style CE fill:#e1bee7,stroke:#8e24aa,stroke-width:2px
    style Pool fill:#bbdefb,stroke:#1976d2
    style Guardrail fill:#ffe0b2,stroke:#f57c00
    style Reject fill:#ffcdd2,stroke:#d32f2f
```
