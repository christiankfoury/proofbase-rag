# Architecture Diagram Guidance

## What The Diagram Should Show

The architecture diagram should make it clear that this is an evaluated enterprise RAG system, not only a chat completion wrapper.

Include:

- Next.js dashboard.
- FastAPI backend.
- PostgreSQL with pgvector.
- Markdown ingestion pipeline.
- Section-based chunking.
- OpenAI embeddings.
- Vector, keyword, and hybrid retrieval experiments.
- Role-based permission filtering before generation.
- Answer generation.
- Citation validation and confidence scoring.
- Session memory and query rewriting.
- Evaluation runner and benchmark data.
- Feedback, observability, and audit logs.
- Docker Compose local stack.
- Azure-ready deployment targets.

## Mermaid Diagram

```mermaid
flowchart LR
  Docs[Synthetic Markdown Documents] --> Loader[Markdown Loader]
  Loader --> Chunker[Section-Based Chunker]
  Chunker --> Embeddings[OpenAI Embeddings]
  Embeddings --> DB[(PostgreSQL + pgvector)]

  User[Reviewer / Demo User] --> Web[Next.js Evaluation Dashboard]
  Web --> API[FastAPI Backend]

  API --> Memory[Session Memory + Query Rewrite]
  Memory --> Retrieve[Vector / Keyword / Hybrid Retrieval]
  Retrieve --> Perms[Role-Based Permission Filter]
  Perms --> DB
  Perms --> Evidence[Evidence Context]
  Evidence --> Generator[OpenAI Answer Generation]
  Generator --> Validation[Citation Validation + Confidence]
  Validation --> API

  API --> Feedback[Feedback Store]
  API --> Audit[Audit Logs]
  API --> Logs[Observability JSONL]

  Benchmark[60-Question Benchmark] --> Eval[Evaluation Scripts]
  Eval --> Retrieve
  Eval --> Reports[Evaluation Reports + JSON]
  Reports --> Web
  Logs --> Web
  Audit --> Web

  Compose[Docker Compose] --> Web
  Compose --> API
  Compose --> DB
  Azure[Azure-Ready Plan] -. future target .-> Compose
```

## Diagram Notes

- Put permission filtering between retrieval and generation.
- Show evaluation scripts as first-class parts of the system.
- Show observability and audit as operational outputs.
- Label Azure as a readiness plan or future deployment target, not as completed deployment.
- Keep raw document storage as repository files today; Azure Blob Storage is future work.

## Suggested Caption

> Enterprise Knowledge Agent uses a FastAPI RAG backend, PostgreSQL/pgvector retrieval, role-based permission filtering, OpenAI generation, citation validation, and a Next.js evaluation dashboard. The system is evaluated with a 60-question benchmark and packaged with Docker for local demos and Azure-ready deployment planning.
