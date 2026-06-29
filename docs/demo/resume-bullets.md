# Resume Bullets

## Concise Bullets

- Built a Dockerized enterprise RAG assistant with project workspaces, department document libraries, FastAPI, Next.js, PostgreSQL/pgvector, OpenAI APIs, RBAC, citations, observability, and Azure-ready deployment docs.
- Created a 130-question benchmark source corpus with current benchmark v1.1 retrieval and answer-quality runs plus separate permission and memory suites measuring retrieval, answer accuracy, citation accuracy, permission leakage, memory, multi-document reasoning, adversarial prompts, and conflicting-source cases.
- Improved standalone multi-document answer accuracy from `0.850` to `0.925`, citation accuracy from `0.850` to `0.925`, and hallucination rate from `0.050` to `0.000` in the multi-document evaluation artifact.

## Detailed Bullets

- Designed and implemented an enterprise RAG system over a synthetic company knowledge base with Markdown ingestion, section-based chunking, pgvector embeddings, retrieval experiments, cited answer generation, and confidence scoring.
- Built role-based permission filtering that prevents restricted chunks from reaching generation, achieving `0.000` permission leakage and `1.000` blocked-answer accuracy on the restricted benchmark.
- Developed a custom benchmark dashboard covering retrieval quality, answer accuracy, citation accuracy, hallucination rate, permission safety, memory behavior, sample sizes, run IDs, and failed-question analysis.
- Added session-level memory through query rewriting while preserving current-role permission filtering, reaching `1.000` memory answer accuracy, citation accuracy, and response type accuracy.
- Containerized the project with Docker Compose for PostgreSQL/pgvector, FastAPI, and Next.js; added health/readiness endpoints, smoke tests, CI build checks, and Azure-ready deployment documentation.

## Short Project Description

Enterprise Knowledge Agent is a full-stack enterprise RAG portfolio project that demonstrates project-scoped knowledge workspaces, secure retrieval, role-based permissions, citation-grounded answer generation, benchmark-driven iteration, human review, observability, Dockerized local deployment, and Azure-ready architecture.

## Longer Project Description

Enterprise Knowledge Agent simulates a secure internal company AI assistant over synthetic HR, IT/security, sales, manager, finance, legal, engineering, support, operations, HR admin, and IT admin documents. The project goes beyond a PDF chatbot by adding project workspaces, department document libraries, scoped retrieval, PDF-to-Markdown review uploads, optional AI Markdown cleanup drafts, approval-gated local indexing, a 130-question benchmark source corpus, retrieval experiments, citation validation, confidence scoring, role-based permissions, permission leakage evaluation, session memory, prompt versioning, feedback, human review, observability, audit logs, multi-document reasoning, a Next.js App and Dev/Admin UI, Dockerized local setup, smoke tests, CI, and Azure-ready deployment documentation. Final measured results include `0.922` all-sources retrieval hit, `0.778` Precision@k, `1.000` answer accuracy, `1.000` citation accuracy, `0.000` hallucination rate, `0.000` permission leakage, `1.000` memory answer accuracy, and `0` failed questions in the current 130-question live `/query` answer-quality scorecard run.
