# Phase 4 Architecture Overview

## Purpose

Phase 4 defines the technical architecture for the Proofbase before implementation begins. The system is designed as an enterprise-grade RAG knowledge agent with measurable retrieval quality, cited answers, permissions, evaluation runs, prompt versioning, feedback, audit logs, latency/cost tracking, and recruiter-facing metrics.

This phase is documentation-only. No application code, migrations, frontend pages, backend endpoints, or scripts are implemented here.

## Source Inputs

- Synthetic documents: `data/synthetic-documents/`
- Benchmark dataset: `data/evaluation/benchmark-questions.json`

The Phase 2 synthetic documents are the first ingestion source. The Phase 3 benchmark is the first evaluation source.

## System Components

| Component | Responsibilities |
|---|---|
| Frontend | Chat UI, citation display, feedback controls, document admin UI, evaluation dashboard, prompt versions page, access control page, audit logs page, recruiter-facing project overview |
| Backend | FastAPI API, auth/session handling, ingestion orchestration, retrieval, answer generation, citation validation, benchmark runner, prompt lookup, permission checks, metrics logging |
| PostgreSQL | Users, roles, documents, document versions, permissions, chunks, embeddings, chat sessions, prompt versions, retrieval logs, answer logs, citations, evaluation results, feedback, audit logs |
| pgvector | Stores chunk embeddings and supports vector similarity search |
| PostgreSQL full-text search | Supports keyword retrieval over chunk text with `tsvector` and GIN indexes |
| Azure Blob Storage | Stores raw uploaded files, archived sources, and optional extracted text snapshots |
| OpenAI API | Embeddings, answer generation, optional query rewriting, optional citation validation, optional evaluation judging |
| Evaluation runner | Loads benchmark questions, runs them through the RAG pipeline, logs results, calculates metrics, compares system configurations |
| Observability | Request IDs, traces, latency, token usage, estimated cost, retrieval traces, model calls, refusal reasons, permission failures, errors |

## User Question Flow

1. User asks a question in the chat UI.
2. Frontend sends `session_id`, `message`, and authenticated user context to FastAPI.
3. Backend resolves the user and roles from auth.
4. Backend selects active prompt version and retrieval configuration.
5. Retrieval applies role/document permission filters before retrieving chunks.
6. Retrieval runs `vector_only`, `keyword_only`, `hybrid`, or `hybrid_rerank`.
7. Backend logs the retrieval run and retrieved chunks.
8. Backend formats retrieved context with document title, document ID, section heading, chunk ID, version, and citation metadata.
9. LLM generates an answer, refusal, not-found response, or clarification question.
10. Citation validation checks whether cited chunks support answer claims.
11. Backend calculates citation confidence and logs answer run, citations, latency, token usage, estimated cost, and refusal reason.
12. Frontend displays answer, citations, confidence indicators, and feedback controls.

Critical rule: unauthorized chunks must never be passed to the LLM.

## Admin Upload Flow

1. Admin uploads a document.
2. Backend stores the raw file in Azure Blob Storage.
3. Backend creates `documents` and `document_versions` records.
4. Ingestion detects file type and extracts text.
5. Markdown metadata is parsed for Phase 5.
6. Text is normalized into sections and headings.
7. Document permissions are applied from metadata or admin input.
8. Section-based chunks are created for Phase 5.
9. Embeddings are generated and stored with pgvector.
10. Full-text `tsvector` values are generated for chunks.
11. The document version status becomes `indexed`.
12. Ingestion events and failures are logged.

## Answer and Citation Behavior

- If no relevant chunks are found, return `say_not_found`.
- If chunks are found but confidence is low, say the available documents do not provide enough support or ask a clarifying question.
- If the user lacks permission, return `refuse_no_access` without revealing restricted details.
- If the question is ambiguous, ask a clarifying question and cite the relevant policy constraint when safe.
- If multiple documents are needed, synthesize only from retrieved accessible chunks and cite each source.

## Recruiter-Facing Architecture Story

The architecture demonstrates a production-minded AI system rather than a simple chatbot:

- Normalized document storage and versioning.
- pgvector and PostgreSQL keyword search.
- Hybrid retrieval path.
- Role-based permissions enforced before generation.
- Citations tied to chunks and document versions.
- Prompt and evaluation versioning.
- Benchmark-driven quality measurement.
- Latency, cost, and feedback tracking.
