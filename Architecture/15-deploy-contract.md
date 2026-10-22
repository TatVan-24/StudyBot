# System Design Overview & Operations Flow (Contracts)

---

## 1. Cloud vs. Local Split

### 1.1. Core Principles

```text
AWS = Durable Control Plane          | Local = Rebuildable AI/Data Plane
-------------------------------------|---------------------------------------
Auth, API, durable storage           | Parse, chunk, embed, retrieve, LLM
State, jobs, messages, flashcards    | Vector index, model cache
Queue, DLQ, log, metric, alarm       | Temporary files, local log
```

**Crucial Point:** AWS **never** opens inbound connections to the local machine. The local worker **actively** polls and calls the cloud.

### 1.2. Detailed Component Split

| Component | Cloud (AWS) | Local |
|---|---|---|
| **Frontend Assets** | S3 + CloudFront + OAC | — |
| **Identity** | Cognito User Pool + App Client | — |
| **API** | API Gateway HTTP API + JWT Authorizer | — |
| **Lambda Functions** | 6 functions | — |
| **Original Documents** | S3 Bucket (Private) | — |
| **DynamoDB** | 7 tables + GSIs | — |
| **Queue** | 2 SQS + 2 DLQs | — |
| **Worker** | — | Python process |
| **Parser** | — | TXT, MD, PDF |
| **Chunker** | — | StructureAwareChunker |
| **Embedding** | — | mpnet-base-v2 (768d) |
| **Vector Store** | — | SQLite (`m3_index.db`) |
| **BM25 Index** | — | `rank_bm25` (in-memory) |
| **Retriever** | — | Hybrid (Dense + Sparse) |
| **Reranker** | — | BGE Cross-Encoder |
| **LLM** | — | Groq / OpenAI / Gemini |
| **Guardrails** | — | Input/Output regex + NLI |
| **Model Cache** | — | Local disk |

### 1.3. Data Placement

| Data | Location | Authoritative Source |
|---|---|---|
| Frontend assets | Frontend S3 | Source repository |
| Identity | Cognito | Cognito |
| Original documents | Document S3 | S3 |
| Documents/Sessions/Jobs | DynamoDB | DynamoDB table |
| Chat answers + citations | `StudyBotMessages` | Messages table |
| Flashcards | `StudyBotFlashcards` | Flashcards table |
| Job notification | SQS | *Not authoritative* |
| Parsed chunks + embeddings | Local Vector Store | Rebuildable derived index |
| Model files | Local model cache | Model source/release |

**Principle:** If the local index is lost → download original documents from S3 → re-ingest.

---

## 2. Workflow 1 — Document Upload

### 2.1. Flow Diagram

```mermaid
sequenceDiagram
    participant B as User Browser
    participant API as API Gateway + Auth
    participant L_Doc as Lambda (studybot-document)
    participant S3 as S3 Document Bucket
    participant L_Ingest as Lambda (studybot-ingestion)
    participant SQS as SQS (document-queue)
    participant W as Local Worker

    B->>API: 1. POST /documents/uploads
    API->>API: 2. Verify JWT -> user_id
    API->>L_Doc: Forward request
    L_Doc->>DB (DynamoDB): 3. Write document_id, status=UPLOADING
    L_Doc->>L_Doc: 4. Generate short-lived presigned POST
    L_Doc-->>B: 5. Response 202 + presigned URL
    B->>S3: 6. Browser uploads directly to S3
    S3-->>L_Ingest: 7. ObjectCreated Event
    L_Ingest->>DB (DynamoDB): 8. Update status=INGEST_QUEUED
    L_Ingest->>SQS: 9. Send job (job_type=INGEST_DOCUMENT)
    W->>SQS: 10. Long-poll queue
    SQS-->>W: Receive job_id
    W->>DB (DynamoDB): 11. Read & claim job
    W->>S3: 12. Get object
    W->>W: 13. Parse -> Chunk -> Embed -> Index
    W->>DB (DynamoDB): 14. Update status=ACTIVE, chunk_count
    W->>SQS: 15. DeleteMessage
    B->>API: 16. Frontend polling GET /jobs/{job_id} -> COMPLETED
```

### 2.2. Document Status Lifecycle

```mermaid
stateDiagram-v2
    [*] --> UPLOADING
    UPLOADING --> INGEST_QUEUED
    INGEST_QUEUED --> PROCESSING
    PROCESSING --> ACTIVE: Ingestion succeeds
    PROCESSING --> FAILED: Ingestion fails
    ACTIVE --> [*]
    FAILED --> [*]
```

### 2.3. Storage Locations

| Data | Storage Location |
|---|---|
| Original File | S3 Document Bucket |
| Document Metadata | `StudyBotDocuments` (DynamoDB) |
| Job State | `StudyBotJobs` (DynamoDB) |
| Job Notification | `studybot-document-queue` (SQS) |
| Job Payload | DynamoDB (SQS only has `job_id` + `job_type`) |
| Parsed Blocks | Local `bundle_all/blocks.jsonl` |
| Chunks | Local `chunks.jsonl` |
| Embeddings | Local SQLite (`m3_index.db`) |
| BM25 Index | Local in-memory |

### 2.4. Upload Security Mechanisms

| Mechanism | Purpose |
|---|---|
| Presigned POST | Short-lived URL, restricts key/content-type/size. |
| Extension + MIME Check | Preliminary check at API level. |
| Magic bytes + parser validation | Actual verification during ingestion by the worker. |
| Private Bucket + Block Public Access | Ensures nobody can read objects directly. |
| CloudFront OAC | Only allows the frontend bucket to be read via CF. |

---

## 3. Workflow 2 — Query

### 3.1. Flow Diagram

```mermaid
sequenceDiagram
    participant B as User Browser
    participant API as API Gateway + Auth
    participant L_Query as Lambda (studybot-query)
    participant SQS as SQS (interactive-queue)
    participant DB as DynamoDB
    participant W as Local Worker

    B->>API: 1. POST /sessions/{id}/questions
    API->>API: 2. Verify JWT -> user_id
    API->>L_Query: Forward request
    L_Query->>DB: 3. Write job_id, job_type=ANSWER_QUERY
    L_Query->>SQS: 4. Send SQS notification (job_id, job_type)
    L_Query-->>B: 5. Response 202 + job_id
    B->>API: 6. Polling GET /jobs/{job_id}
    
    W->>SQS: 7. Long-poll queue
    SQS-->>W: Receive job_id
    W->>DB: 8. Read job -> conditional claim (lease token)
    W->>W: 9. Input Guardrail (T1/T2/T3)
    W->>W: 10. Retrieval (Dense + Sparse -> Fusion -> CE Rerank -> Gate)
    W->>W: 11. Check 1: Evidence Sufficiency
    W->>W: 12. LLM Generation
    W->>W: 13. Check 2 & 3: Citation Validity + NLI Grounding
    W->>W: 14. Output Guardrail
    W->>DB: 15. Write answer, citations, status to Messages & Jobs
    W->>SQS: 16. DeleteMessage
    B->>API: 17. Frontend polling returns COMPLETED with answer
```

### 3.2. Output Status Definitions

| Status | Meaning |
|---|---|
| `acceptance` | Answered successfully; evidence is strong enough. |
| `ambiguous` | Low confidence; high risk of hallucination. |
| `rejection` | System error (guardrail triggered, invalid citations, false refusal). |
| `refusal` | Context insufficient to answer (truthful refusal). |

### 3.3. Storage Locations

| Data | Storage Location |
|---|---|
| User Query | `StudyBotMessages` (DynamoDB) |
| Answer + Citations | `StudyBotMessages` (Authoritative) |
| Job State | `StudyBotJobs` (DynamoDB) |
| Polling Result Copy | `StudyBotJobs.result` |
| Job Notification | SQS (*Not authoritative*) |
| RAG Telemetry | Local worker log |
| Audit Trail | Local JSONL (`_data/logs/YYYY-MM-DD.jsonl`) |

### 3.4. Job Structure in DynamoDB

| Field | Purpose |
|---|---|
| `job_id` | Partition Key |
| `job_type` | Job category (`ANSWER_QUERY`, `INGEST_DOCUMENT`, etc.) |
| `job_version` | Contract version |
| `worker_id` | Identifier of worker holding the claim |
| `lease_token` | Fencing token |
| `lease_expires_at` | Lease expiration timestamp |
| `attempt_count` | Number of execution attempts |
| `max_attempts` | Maximum allowed attempts |
| `last_error` | Most recent error message |
| `next_attempt_at` | Backoff timestamp for next attempt |
| `result` | Small denormalized copy for client polling |

---

## 4. Workflow 3 — Generate Flashcards

### 4.1. Flow Diagram

```mermaid
sequenceDiagram
    participant B as User Browser
    participant L_Flash as Lambda (studybot-flashcard)
    participant SQS as SQS (interactive-queue)
    participant DB as DynamoDB
    participant W as Local Worker

    B->>L_Flash: POST /sessions/{id}/flashcards
    L_Flash->>DB: Write Job
    L_Flash->>SQS: Send job notification
    L_Flash-->>B: Response 202 + job_id
    W->>SQS: Receive job
    W->>DB: Claim job & read session/documents
    W->>W: Generate flashcards via LLM
    W->>DB: Write to StudyBotFlashcards
    W->>DB: Update Job status
    W->>SQS: DeleteMessage
    B->>DB: Frontend polls GET /jobs/{job_id}
```

**Storage Details:**
- Flashcards are stored in `StudyBotFlashcards` (DynamoDB).
- GSI: `DocumentFlashcards(document_id, flashcard_id)`.

---

## 5. Workflow 4 — Delete Document

### 5.1. Flow Diagram

```mermaid
sequenceDiagram
    participant B as User Browser
    participant L_Doc as Lambda (studybot-document)
    participant SQS as SQS (document-queue)
    participant DB as DynamoDB
    participant W as Local Worker
    participant S3 as S3 Bucket

    B->>L_Doc: DELETE /documents/{id}
    L_Doc->>DB: Update Document status=DELETE_QUEUED
    L_Doc->>DB: Write Job
    L_Doc->>SQS: Send job notification
    L_Doc-->>B: Response 202 + job_id
    W->>SQS: Receive job
    W->>W: Delete vectors from SQLite & local chunks
    W->>S3: Delete object from S3
    W->>DB: Update Document status=DELETED
    W->>DB: Update Job status
    W->>SQS: DeleteMessage
```

**Critical Rule:** `DELETE_QUEUED` **immediately** excludes the document from retrieval, even while physical cleanup is pending.

### 5.2. Delete Status Lifecycle

```mermaid
stateDiagram-v2
    ACTIVE --> DELETE_QUEUED
    DELETE_QUEUED --> DELETING
    DELETING --> DELETED: Cleanup succeeds
    DELETING --> DELETE_FAILED: Cleanup fails
    DELETED --> [*]
```

---

## 6. Workflow 5 — Session Management

- `POST /sessions` → Create a new session.
- `GET /sessions` → List all sessions for a user.
- `GET /sessions/{id}` → Get session details.
- `POST /sessions/{id}/documents/{doc_id}` → Attach a document to a session.
- `DELETE /sessions/{id}/documents/{doc_id}` → Detach a document from a session.

**Storage Details:**
- Sessions are stored in `StudyBotSessions`.
- Session-Document mappings are in `StudyBotSessionDocuments`.
- GSI `UserSessions(user_id, updated_at)`.
- GSI `DocumentSessions(document_id, session_id)`.

---

## 7. Workflow 6 — Message History

- `GET /sessions/{id}/messages`

**Storage Details:**
- Messages are stored in `StudyBotMessages`.
- Key format: `(session_id, created_at#message_id)`.
- The assistant message identity is derived from the `job_id`.

---

## 8. Internal Local Worker Flow

### 8.1. SQS + DynamoDB Synchronization Pattern

```mermaid
sequenceDiagram
    participant W as Worker
    participant SQS as SQS
    participant DB as DynamoDB

    W->>SQS: ReceiveMessage
    W->>DB: Conditional Claim (inject new lease_token)
    
    rect rgb(200, 220, 240)
    Note over W,DB: Processing Loop
        W->>SQS: Extend Visibility Timeout
        W->>DB: Extend lease_expires_at
    end
    
    W->>DB: Commit Results (Condition: lease_token must match)
    W->>SQS: DeleteMessage
```

**Lease Token = Fencing Token:** An old worker cannot overwrite a job that has been reclaimed by another worker after a timeout.

### 8.2. Failure Handling Strategy

```mermaid
flowchart TD
    E[Job Error] --> C{Classify Error}
    C -->|Transient| T[RETRY_PENDING]
    T -->|Backoff + Jitter| Q[QUEUED]
    T -->|Max Attempts Exhausted| D[Send to DLQ + FAILED]
    C -->|Permanent| P[Commit FAILED + Acknowledge]
```

| Error Type | Examples |
|---|---|
| **Transient** | Network timeouts, AWS throttling, temporary model/vector-store failures. |
| **Permanent** | Document corruption, invalid payloads, resource unauthorized. |

### 8.3. Idempotency Rules

- Ingestion upserts are stable based on `document_id + index_version`.
- Assistant message IDs are deterministically derived from `job_id`.
- Flashcard batches are tied to `job_id`.
- Deleting vectors or S3 objects that no longer exist is treated as a success.
- If a message is redelivered after reaching a terminal state, the worker simply acknowledges (deletes) it without re-executing side effects.

---

## 9. RAG Pipeline Flow (M1–M6)

### 9.1. Ingestion Pipeline

```mermaid
flowchart TD
    S3[Raw Documents on S3] -->|Download| M1[M1: Parser]
    M1 -->|Extract| PB[Parsed Blocks\nid, text, meta, locator]
    PB --> M2[M2: StructureAware Chunker]
    M2 --> C[Chunks\n<= 512 tokens]
    C --> M3[M3: Embedder\nmpnet-base-v2]
    M3 --> V[768d Dense Vectors\n+ BM25 Data]
    V --> DB[(Local Storage\nSQLite + BM25 InMemory)]
```

### 9.2. Query Pipeline

```mermaid
flowchart TD
    Q[User Query] --> G1[Input Guardrail T1/T2/T3]
    G1 --> M4[M4: Hybrid Retrieval]
    
    subgraph Retrieval
    M4 --> D[Dense: MPNet KNN Top-20]
    M4 --> S[Sparse: BM25 Top-20]
    D --> F[Fusion: Min-Max α=0.4]
    S --> F
    end
    
    F --> M5[M5: Decision Gate]
    
    subgraph Gate
    M5 --> CE[BGE Cross-Encoder Rerank]
    CE --> Cnd{Score >= 0.20 OR\nBaseline Rank <= 1}
    end
    
    Cnd -->|Pass| M6[M6: Generation & Verification]
    
    subgraph Verification
    M6 --> C1[Check 1: Evidence Sufficiency]
    C1 --> LLM[LLM Generation]
    LLM --> C2[Check 2: Citation Validity]
    C2 --> C3[Check 3: Claim Grounding NLI]
    C3 --> G2[Output Guardrail]
    end
    
    G2 --> Final[Final Status:\nacceptance/ambiguous/rejection/refusal]
```

---

## 10. System Interaction Flows (Summary)

### 10.1. User → System

| # | Trigger | Lambda | Queue | Local Worker Role |
|---|---|---|---|---|
| 1 | Upload document | `studybot-document` | Document | Ingest |
| 2 | List documents | `studybot-document` | — | — |
| 3 | Delete document | `studybot-document` | Document | Delete |
| 4 | Create session | `studybot-session` | — | — |
| 5 | Attach/detach doc | `studybot-session` | — | — |
| 6 | Ask question | `studybot-query` | Interactive | Answer |
| 7 | View message history| `studybot-query` | — | — |
| 8 | Generate flashcards | `studybot-flashcard`| Interactive | Generate |
| 9 | View flashcards | `studybot-flashcard`| — | — |
| 10| Poll job status | `studybot-job` | — | — |

### 10.2. System → System (AWS Internal)

| # | Trigger | Source | Target |
|---|---|---|---|
| 11| S3 ObjectCreated | S3 | Lambda `studybot-ingestion-event` |
| 12| Ingestion event | Lambda | DynamoDB + SQS Document Queue |
| 13| Job created | Lambda | SQS Notification |
| 14| JWT Auth | Cognito | API Gateway Authorizer |
| 15| Invocation | API Gateway| Respective Lambda |

### 10.3. Cloud ↔ Local

| # | Direction | Mechanism |
|---|---|---|
| 16| Local → SQS | Long-poll outbound via TLS |
| 17| Local → DynamoDB | `GetItem` / Conditional `UpdateItem` |
| 18| Local → S3 | `GetObject` / `DeleteObject` |
| 19| Local → DynamoDB | Heartbeat updates (`last_seen_at`) |
| 20| Local → SQS | Extend visibility timeout, `DeleteMessage` |

### 10.4. Internal Local Worker Execution

| # | Step | Input | Output |
|---|---|---|---|
| 21| Parse | Raw file | `blocks.jsonl` |
| 22| Chunk | Blocks | `chunks.jsonl` |
| 23| Embed | Chunks | Vectors |
| 24| Index | Vectors + Chunks | SQLite + BM25 |
| 25| Retrieve| Query | Top-K chunks |
| 26| Rerank | Top-K chunks | Reranked chunks |
| 27| Generate| Evidence | Answer + citations |
| 28| Verify | Answer | Final status |

---

## 11. Observability Flow

### 11.1. Signals Monitored

| Area | Key Signals |
|---|---|
| **Lambda** | Invocations, errors, duration, throttles. |
| **SQS** | Visible/in-flight messages, oldest-message age, DLQ depth. |
| **Jobs** | Count of created, completed, failed, retried jobs by type. |
| **Worker** | Heartbeat age, active jobs count, lease-extension failures. |
| **RAG Runtime**| Latency (parsing/embedding/retrieval/generation), retrieved chunks, refusal rates, citation maps. |

### 11.2. Correlation IDs

- `job_id`: The primary correlation ID bridging the API, Queue, and Worker.
- `request_id`: Correlates the originating API Gateway call.

### 11.3. Alert Triggers

| Alert | Condition |
|---|---|
| DLQ not empty | Any message lands in the DLQ. |
| Queue age high | Message age exceeds defined SLO. |
| Lambda Error/Throttle | Error or throttle rates spike. |
| Worker Stale | Heartbeat is stale AND queue has pending work. |
| Lease Failures | High rate of lease-extension failures. |

---

## 12. CI/CD + Deployment Flow

### 12.1. Terraform Bootstrap

```mermaid
flowchart TD
    Man[Manual Console Creation] --> S3B[S3 Bucket State]
    Man --> DBL[DynamoDB Lock Table]
    S3B --> TB[Terraform bootstrap/]
    DBL --> TB
    
    subgraph Bootstrap
    TB --> Imp[Import resources]
    TB --> LS[Local State]
    TB --> PD[prevent_destroy]
    end
    
    TB --> Env[Environments/dev/]
    
    subgraph Environment Deploy
    Env --> Bck[backend 's3']
    Env --> Mod[Invoke 8 Modules]
    end
```

### 12.2. Terraform Module Structure

```text
infrastructure/
├── bootstrap/          ✅ (Completed)
├── modules/
│   ├── storage/        <- (In Progress)
│   ├── auth/
│   ├── database/
│   ├── messaging/
│   ├── compute/
│   ├── api/
│   ├── observability/
│   └── frontend/
└── environments/dev/
```

---

## 13. Core Guiding Principles

| # | Principle | Source Ref |
|---|---|---|
| 1 | AWS never opens inbound connections to local. | ADR-001 |
| 2 | SQS is strictly for notifications; DynamoDB is the source of truth. | 01, 02 |
| 3 | System assumes at-least-once delivery; never exactly-once. | 04 |
| 4 | Lease tokens act as strict fencing tokens. | 04 |
| 5 | Conditional writes are mandatory for all claim/terminal updates. | 02, 04 |
| 6 | Local index must be entirely rebuildable from S3. | 01, 03 |
| 7 | Implement least-privilege IAM (1 specific role per Lambda). | 03 |
| 8 | `user_id` is strictly derived from JWT, never from request body. | 03 |
| 9 | Logs exclude tokens, credentials, presigned URLs, and payload content. | 03 |
| 10| Avoid high-cardinality IDs as metric dimensions. | 04 |
| 11| Fixed alpha fusion rejected; use Decision Gate instead. | ADR-005, ADR-006 |
| 12| Conservative aggregation: if any check is AMBIGUOUS -> overall is AMBIGUOUS. | 14 |
| 13| Evidence must be per-claim; no shared evidence across claims. | 14 |
| 14| Terraform state must be remote and locked. | ADR-002 |

---

## 14. Notable Implementation Points

1. If the local worker goes offline, AI tasks halt, but jobs survive in SQS (retention period).
2. The system uses Frontend polling for status, not SSE/streaming (deferred execution).
3. **Check 1** (Evidence Sufficiency) is currently **BYPASSED** in the code (`handlers.py`).
4. The refusal threshold is currently in `log_only` mode and is not enforcing the threshold.
5. DOCX/PPTX parsers are not yet implemented (slated for M7).
6. Cross-Encoder (CE) inference requires ~25-40 minutes on CPU for 35 evaluation cases.
7. The CE must run in a subprocess on Windows (to avoid `0xC0000005` access violations).
8. Supported "H6" on Holdout **does not equal** Gate approved for production.

---

## 15. Local Worker Deep-Dive & Beginner Foundations

### 15.1. Why Local Worker is Essential (Root Problem)
When a user uploads a PDF, the system must:
1. Extract content from the PDF.
2. Segment text into chunks.
3. Compute dense vector embeddings for each chunk.
4. Persist vectors and metadata into the vector database.

Steps 2–4 take 30 seconds to 5 minutes depending on document size and hardware.

**Why not handle this entirely inside AWS Lambda?**
- **Execution Timeout & Cost:** Lambda max timeout is 15 minutes, and billed on execution duration.
- **Hardware Limitations:** Embedding models and local cross-encoders require substantial CPU/GPU and memory (exceeding lightweight Lambda specs or driving excessive costs).
- **Outbound-Only Principle:** The Local Worker actively pulls work from AWS; AWS never needs direct inbound access into the local network.

```text
Lambda: "Got work! job_123 needs file processing"
   │
   ▼ (Sends message)
SQS Queue: "job_123 waiting"
   │
   ▼ (Long poll)
Local Worker: "Claimed job_123"
   ├─ 1. Download PDF from S3
   ├─ 2. Parse PDF (structure-aware)
   ├─ 3. Chunk text
   ├─ 4. Embed (local model)
   ├─ 5. Upsert to Vector Store (Qdrant / SQLite)
   ├─ 6. Update DynamoDB: document status = ACTIVE, job status = COMPLETED
   └─ 7. Delete message from SQS
```

---

### 15.2. Core Concepts Explained

#### 1. SQS (Message Queue as a Safe Buffer)
- Analogy: A reliable post office mailbox.
- Lambda drops a lightweight notification (`job_id` + `job_type`).
- If the Worker is temporarily offline, SQS buffers messages safely up to 4 days (or configured retention) without losing tasks.

#### 2. Long Polling (`WaitTimeSeconds = 20`)
- **Short Polling:** Querying continuously every second wastes requests (up to 3,600 reqs/hr of mostly empty responses).
- **Long Polling:** Worker requests: *"Any messages? I will wait up to 20 seconds for one."*
- Connection remains open until a message arrives or 20 seconds elapse. Reduces empty request volume by ~95%, slashing latency and AWS API costs.

#### 3. Visibility Timeout
- When the Worker pulls a message, SQS **hides** it for 30 seconds instead of immediately deleting it.
- **Normal completion:** Worker finishes within 30s and calls `DeleteMessage` -> message removed permanently.
- **Worker crashes:** If the worker crashes or disconnects, the 30s timeout expires and the message automatically reappears for another worker to retry.
- **Long jobs:** For processing taking longer than 30s, worker calls `ChangeMessageVisibility` periodically to extend the window.

#### 4. Lease Token (Fencing Token Pattern)
- SQS Standard guarantees **at-least-once** delivery, meaning duplicate deliveries can occur.
- **Race Condition Risk:** Worker A takes a job, stalls or loses network connection; message reappears; Worker B picks up the job. Worker A later revives and attempts to write stale results over Worker B's work.
- **Solution:** Every time a worker claims a job, it generates a unique random `lease_token` (e.g. `uuid4`) and updates DynamoDB.
- **Commit Guard:** DynamoDB enforces a conditional check: `attribute_exists(job_id) AND lease_token = :my_token`. If Worker B claimed the job, Worker A's write is rejected cleanly.

#### 5. Idempotency ("Executing N times equals executing 1 time")
- Duplicate deliveries or retries must never corrupt data or create duplicate chunk vectors.
- Checks `document.status`: if already `ACTIVE`, skip redundant ingestion.
- Deterministic chunk and message IDs prevent duplicate records.

#### 6. Claim Job (Conditional Writes in DynamoDB)
- Workers do not execute immediately upon pulling from SQS. They must first atomically claim ownership in DynamoDB:
  - `status`: `QUEUED` -> `PROCESSING`
  - `worker_id`: `worker-local-1`
  - `lease_token`: `<random_token>`
  - `ConditionExpression`: `status = :queued`
- If two workers attempt to claim the same job, only one succeeds; the second receives `ConditionalCheckFailedException` and skips processing.

#### 7. Worker Heartbeat
- Worker writes periodically (e.g., every 30 seconds) to `StudyBotWorkers` table:
  - `worker_id`: `worker-local-1`
  - `last_seen_at`: ISO timestamp
  - `active_job`: current `job_id` or `null`
- Allows monitoring alarms to detect stalled or offline workers.

---

### 15.3. End-to-End Operational Lifecycle

```mermaid
sequenceDiagram
    autonumber
    actor User as User Browser
    participant S3 as S3 Document Bucket
    participant L as Lambda ingestion_event
    participant SQS as SQS document-queue
    participant DDB as DynamoDB (Documents & Jobs)
    participant W as Local Worker

    User->>S3: Upload PDF via Presigned POST
    S3->>L: S3 ObjectCreated Event
    L->>DDB: Update Doc (status=INGEST_QUEUED), Create Job (status=QUEUED)
    L->>SQS: SendMessage {schema_version: 1, job_id, job_type: INGEST_DOCUMENT}
    
    loop Long Polling (WaitTimeSeconds=20)
        W->>SQS: ReceiveMessage
    end
    SQS-->>W: Deliver message with job_id
    
    W->>DDB: Conditional Claim (status=QUEUED -> PROCESSING, set lease_token)
    alt Claim Failed (already taken)
        W->>SQS: DeleteMessage & skip
    else Claim Succeeded
        par Process & Keepalive
            loop Periodic Heartbeat & Lease Extension
                W->>SQS: Extend visibility timeout
                W->>DDB: Update worker heartbeat & extend lease_expires_at
            end
        and Core Ingestion
            W->>S3: GetObject (download PDF)
            W->>W: Parse -> StructureAware Chunking -> Embeddings -> Vector Store
        end
        W->>DDB: Conditional Commit (Verify lease_token matches, status=COMPLETED, Doc status=ACTIVE)
        W->>SQS: DeleteMessage(receipt_handle)
    end
```

---

### 15.4. Operational Baseline Decisions
- **Host Environment:** Local workstation (utilizing local CPU/RAM/model cache, zero cloud compute overhead).
- **Execution Command:** `python -m src.worker.main` running as a dedicated foreground process from project root with `.venv`.
- **Telemetry & Logging:** Dual output:
  - **Console (stdout):** Colorized live feedback of queue polling and progress.
  - **File:** Rotating JSONL logs at `_data/logs/worker-YYYY-MM-DD.jsonl` for audit trails and post-mortem debugging.
- **Rollout Strategy:** **Option C (Phased Implementation)**:
  - *Phase 1:* Minimalist Worker handling `INGEST_DOCUMENT` end-to-end (read queue, claim job, run parser/chunker/embedder, commit status, delete message).
  - *Phase 2:* Add lease token renewal, heartbeat background thread, retry backoff, and interactive handlers (`ANSWER_QUERY`, `GENERATE_FLASHCARDS`, `DELETE_DOCUMENT`).

---

## 16. Local Worker Ingestion (Worker A) — Implementation Specifications

### 16.1. Pipeline Contracts & Interfaces

| Component | Class / Function | Input Contract | Output Contract | Notes |
|---|---|---|---|---|
| **PDF Parser** | `opendataloader_pdf.run()` | `input_path: str, keep_line_breaks=True` | JSON String | Official PyPI tool; requires Java 11+. |
| **Parser Adapter** | `adapt_opendataloader_json_to_parsed_blocks()` | `(dict, document_id: str)` | `list[dict]` (Parsed Blocks) | Maps bounding boxes, tables, headers, and semantic types. |
| **Chunker** | `StructureAwareChunker.chunk()` | `(blocks, document_id, "pdf", config)` | `ChunkBundle` (`.chunks: List[Chunk]`) | `config = {"max_tokens": 512}`. Respects header hierarchies. |
| **Chunk Serialization** | `dataclasses.asdict(chunk)` | `Chunk` dataclass instance | `dict` | Prepares chunk records for vector store insertion. |
| **Embedder** | `EmbeddingEngine.encode()` | `texts: List[str]` | `np.ndarray (N, 768)` (float32, L2) | Uses `paraphrase-multilingual-mpnet-base-v2`. |
| **Index Metadata** | `IndexMeta(...)` | 7 attributes from `EmbeddingEngine` | `IndexMeta` (Pydantic model) | `model_name, revision, dimension, max_seq_length, normalization, index_version, created_at`. |
| **Vector Store** | `SQLiteVectorStore.upsert_index()` | `(meta: IndexMeta, chunks: list[dict], vectors: np.ndarray)` | None | Persists vectors and metadata into SQLite table `embeddings`. |

---

### 16.2. Local Storage & Path Architecture

To ensure operational hygiene and prevent contamination between experimental benchmarks and production ingestion:

| Resource | Target Path | Rationale |
|---|---|---|
| **Vector Database** | `_data/studybot_index.db` | Dedicated SQLite database for real worker jobs (does not pollute `m3_index.db` evaluation artifact). |
| **Temporary Files** | `_data/tmp/` | Holds ephemeral downloaded S3 PDFs; cleaned up immediately post-ingestion. |
| **Worker Logs** | `_data/logs/worker-YYYY-MM-DD.jsonl` | Daily rotating structured audit log file. |

---

### 16.3. Worker Codebase Organization (`src/worker/`)

```text
src/worker/
├── __init__.py        # Package identifier
├── config.py          # Centralized configuration & environment loader (fail-fast validation)
├── logger.py          # Dual logging pipeline (console stdout + structured JSONL)
├── ingest.py          # INGEST_DOCUMENT processor (S3 download -> OpenDataLoader -> Chunker -> MPNet -> SQLite)
└── main.py            # Long-polling daemon loop (SQS poll -> DynamoDB claim -> Ingest -> Commit -> Delete)
```

---

### 16.4. Worker Configuration Contract (`config.py`)

#### Required Variables (Fail-Fast with `KeyError` if absent):
- `AWS_REGION`: Deployment region (`ap-southeast-2`).
- `QUEUE_DOCUMENT_URL`: SQS document queue URL.
- `QUEUE_INTERACTIVE_URL`: SQS interactive queue URL.
- `TABLE_JOBS`: DynamoDB jobs table name (`studybot-dev-jobs`).
- `TABLE_DOCUMENTS`: DynamoDB documents table name (`studybot-dev-documents`).
- `TABLE_WORKERS`: DynamoDB worker heartbeat table (`studybot-dev-workers`).
- `BUCKET_DOCUMENT`: S3 document storage bucket name.

#### Optional Variables (With sensible defaults):
- `WORKER_ID`: Defaults to `"worker-local-1"`.
- `SQLITE_PATH`: Defaults to `"_data/studybot_index.db"`.
- `TEMP_DIR`: Defaults to `"_data/tmp"`.
- `LOG_DIR`: Defaults to `"_data/logs"`.
- `EMBEDDING_MODEL`: Defaults to `"sentence-transformers/paraphrase-multilingual-mpnet-base-v2"`.
- `CHUNKER_STRATEGY`: Defaults to `"structure"`.
- `CHUNKER_MAX_TOKENS`: Defaults to `512`.
- `CHUNKER_CONFIG`: Dict `{"max_tokens": 512}`.


