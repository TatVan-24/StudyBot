# ADR-001: Serverless AWS Control Plane with Local AI Worker

- Status: Accepted
- Date: 2026-08-21

## Context

StudyBot must support asynchronous document processing, session-scoped RAG, citations, flashcards and deletion. Bedrock is unavailable to the current AWS account, the project has limited credits, and local hardware can run embedding and LLM workloads. The local machine may be offline.

## Decision

Use an event-driven serverless AWS control plane and a local AI/data plane:

- AWS: Cognito, API Gateway, Lambda, S3, DynamoDB, SQS, CloudFront and CloudWatch.
- Local: parser, chunker, embedding model, vector database, retriever and LLM.
- SQS transports minimal job references; DynamoDB is authoritative.
- The local worker long-polls AWS over outbound TLS. No inbound laptop endpoint is exposed.
- Frontend polls job state; SSE/token streaming is deferred.

## Consequences

Positive:

- Low idle cloud cost and no always-on inference server.
- Jobs survive local-worker downtime for the configured queue retention period.
- Original documents and user-facing state remain durable on AWS.
- AI components remain replaceable by a future managed/cloud inference service.

Negative:

- AI work stops while the local worker is offline.
- Interactive responses are asynchronous rather than token-streamed.
- Local credentials, index persistence and rebuild require explicit operations.
- At-least-once delivery requires lease, fencing and idempotency logic.

## Alternatives considered

- EC2 backend plus local AI: simpler SSE but adds fixed cost and does not remove local-worker dependency.
- Cloud RAG plus local LLM: improves index availability but adds cloud embedding/vector cost and networking complexity.
- Fully managed Bedrock RAG: unavailable to the current account and reduces control over the learning objectives.

