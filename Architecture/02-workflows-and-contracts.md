# Workflows and Contracts

## Cloud–local protocol

```mermaid
sequenceDiagram
    participant FE as Frontend
    participant API as API Gateway + Lambda
    participant DB as DynamoDB
    participant Q as SQS
    participant W as Local Worker

    FE->>API: Submit command
    API->>DB: Write Job + authoritative payload
    API->>Q: Send job reference
    API-->>FE: 202 + job_id
    W->>Q: Long-poll
    Q-->>W: job_id + job_type
    W->>DB: Read and atomically claim Job
    W->>W: Execute workflow
    W->>DB: Commit result and terminal state
    W->>Q: DeleteMessage
    FE->>API: GET /jobs/{job_id}
    API->>DB: Get Job
    API-->>FE: State/result
```

Canonical SQS notification:

```json
{
  "schema_version": 1,
  "job_id": "job_123",
  "job_type": "ANSWER_QUERY"
}
```

The notification contains no PDF, chunks, question or authoritative document list. The worker reads current data from DynamoDB.

## Queues

| Queue | Job types | DLQ |
|---|---|---|
| `studybot-interactive-queue` | `ANSWER_QUERY`, `GENERATE_FLASHCARDS` | `studybot-interactive-dlq` |
| `studybot-document-queue` | `INGEST_DOCUMENT`, `DELETE_DOCUMENT` | `studybot-document-dlq` |

## Document lifecycle

```mermaid
stateDiagram-v2
    [*] --> UPLOADING
    UPLOADING --> INGEST_QUEUED
    INGEST_QUEUED --> PROCESSING
    PROCESSING --> ACTIVE: ingestion succeeds
    PROCESSING --> FAILED: ingestion fails
    ACTIVE --> DELETE_QUEUED
    DELETE_QUEUED --> DELETING
    DELETING --> DELETED: cleanup succeeds
    DELETING --> DELETE_FAILED: cleanup fails
    DELETED --> [*]
```

`DELETE_QUEUED` immediately excludes a document from retrieval even if physical cleanup is pending.

## Job lifecycle

```mermaid
stateDiagram-v2
    [*] --> QUEUED
    QUEUED --> PROCESSING: claim lease
    PROCESSING --> COMPLETED: success
    PROCESSING --> FAILED: permanent failure
    PROCESSING --> RETRY_PENDING: transient failure
    RETRY_PENDING --> QUEUED: backoff elapsed
    COMPLETED --> [*]
    FAILED --> [*]
```

All claims and terminal updates are conditional. The job stores `worker_id`, `lease_token`, `lease_expires_at`, `attempt_count`, `max_attempts`, `last_error` and `next_attempt_at`.

## Job contracts

| Job type | Required context/payload | Result |
|---|---|---|
| `INGEST_DOCUMENT` | `user_id`, `document_id` | `chunk_count` |
| `ANSWER_QUERY` | `user_id`, `session_id`, `question` | answer/refusal and citations |
| `GENERATE_FLASHCARDS` | `user_id`, `session_id`, `count`, `difficulty` | `generated_count` |
| `DELETE_DOCUMENT` | `user_id`, `document_id` | `deleted_vector_count` |

Each contract includes `job_version`. Unsupported versions fail without executing business operations.

## Workflow summary

```mermaid
flowchart LR
    FE["Frontend"] -->|"presigned upload"| S3["Document S3"]
    S3 --> IL["Ingestion Lambda"] --> DQ["Document queue"] --> W["Local worker"]
    W -->|"parse/chunk/embed"| V["Local vector DB"]

    FE -->|"question"| QL["Query Lambda"] --> IQ["Interactive queue"] --> W
    W -->|"answer/citations"| DB["DynamoDB"]

    FE -->|"flashcards"| FL["Flashcard Lambda"] --> IQ
    W -->|"cards"| DB

    FE -->|"delete"| DL["Document Lambda"] --> DQ
    W -->|"delete vectors/object"| S3
```

## Public API surface

| Area | Endpoints |
|---|---|
| Documents | `POST /documents/uploads`, `GET /documents`, `GET /documents/{id}`, `DELETE /documents/{id}` |
| Sessions | `POST /sessions`, `GET /sessions`, `GET /sessions/{id}`, attach/detach document routes |
| Query | `POST /sessions/{id}/questions`, `GET /sessions/{id}/messages` |
| Flashcards | `POST /sessions/{id}/flashcards`, `GET /sessions/{id}/flashcards` |
| Jobs | `GET /jobs/{job_id}` |

Commands that start AI/background work return `202 Accepted` and a `job_id`. File bytes upload directly to S3 using a constrained presigned POST.

