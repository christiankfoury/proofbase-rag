# Portfolio Case Study: Enterprise Knowledge Agent

## Problem

Enterprise knowledge assistants need to answer employee questions from internal documents without leaking restricted information or inventing unsupported policy. A basic PDF chatbot can retrieve text and generate answers, but it usually does not prove retrieval quality, citation correctness, permission safety, missing-information behavior, or regression risk.

Enterprise Knowledge Agent was built to demonstrate the engineering work behind a realistic internal AI assistant.

## Why Basic RAG Is Not Enough

A basic RAG demo usually stops at upload, retrieve, and answer. This project adds the controls that matter in enterprise settings:

- Role-based access before generation.
- Citation validation.
- Confidence scoring.
- Missing-information refusal behavior.
- Multi-document synthesis.
- Session memory that does not bypass permissions.
- Benchmark-driven evaluation.
- Observability and audit logs.
- Dockerized reproducible local setup.

The goal was not to maximize feature count. The goal was to make quality, safety, and operational behavior measurable.

## Architecture

The system uses a Next.js dashboard, FastAPI backend, PostgreSQL with pgvector, OpenAI embeddings and generation, and a custom evaluation harness.

Documents are synthetic Markdown files with metadata for title, department, access roles, restricted status, and effective dates. The ingestion pipeline parses Markdown, chunks documents by section, embeds chunks, and stores them in Postgres/pgvector. Queries are retrieved, permission-filtered, grouped into context, passed to answer generation, validated for citations, scored for confidence, and logged for observability and audit review.

The dashboard surfaces evaluation results, failed questions, retrieval comparisons, prompt experiments, permission safety, memory evaluation, multi-document performance, feedback, observability, and audit events.

## Evaluation-First Approach

Before optimizing the system, I created a 60-question benchmark covering:

- Simple factual questions.
- Multi-document questions.
- Permission-restricted questions.
- Missing-information questions.
- Ambiguous questions.
- Conversation-memory follow-ups.

Each phase improved one measurable part of the system and preserved the evaluation artifacts. This made the project easier to debug and easier to explain.

## Experiments Performed

- Compared vector, keyword, and hybrid retrieval.
- Compared section-based and fixed-size chunking.
- Added structured answer response types.
- Added citation validation and confidence scoring.
- Added permission-filtered retrieval and leakage evaluation.
- Added session memory and query rewriting.
- Added prompt versioning and prompt experiments.
- Added multi-document query decomposition and grouped evidence.
- Added live observability and audit views.
- Added Docker Compose and Azure-ready deployment documentation.

## Results

Retrieval:

- Best retrieval configuration: `vector-section`
- All-sources retrieval hit: `0.975`
- Precision@k: `0.650`
- MRR: `0.980`

Answer quality:

- Answer accuracy: `0.829`
- Citation accuracy: `0.857`
- Hallucination rate: `0.156`

Permission safety:

- Permission leakage rate: `0.000`
- Blocked-answer accuracy: `1.000`
- Unauthorized chunk exposure rate: `0.000`

Memory:

- Memory answer accuracy: `1.000`
- Memory citation accuracy: `1.000`
- Memory permission leakage: `0.000`

Multi-document reasoning:

- Answer accuracy improved from `0.700` to `0.850`
- Citation accuracy improved from `0.750` to `0.900`
- Response type accuracy improved from `0.900` to `1.000`
- Failed questions dropped from `4` to `2`
- Hallucination rate moved from `0.667` to `0.700`, a documented tradeoff

Deployment readiness:

- Docker Compose config and image builds passed.
- API health and readiness checks passed.
- Smoke test passed in the latest user run.
- Azure deployment is planned and documented, not claimed as complete.

## Tradeoffs

The strongest retrieval configuration was vector-only section-based retrieval. Hybrid retrieval did not clearly outperform vector search on this benchmark, which is a useful result: evaluation prevented adding complexity without evidence.

Multi-document reasoning improved answer and citation accuracy, but the hallucination metric increased slightly. That tradeoff is documented rather than hidden.

The project uses deterministic and heuristic scoring rather than a human judge for some answer-quality signals. That makes evaluation repeatable and affordable, but it is not a substitute for human review.

## What I Learned

- RAG quality needs benchmarks, not intuition.
- Permission filtering must happen before generation.
- Citation quality and answer quality should be measured separately.
- Hybrid retrieval is not automatically better.
- Memory should rewrite the query, not become trusted evidence.
- Multi-document synthesis needs different prompting and confidence thresholds than single-document answers.
- A portfolio AI project is stronger when it shows failures, tradeoffs, and iteration.

## Future Improvements

- Deploy the Dockerized stack to Azure.
- Add production authentication with Clerk or Auth.js.
- Add Azure Blob Storage for raw documents and durable logs.
- Add PDF and DOCX ingestion.
- Add real enterprise connectors such as SharePoint, Slack, Teams, or Google Drive.
- Evaluate Azure AI Search or reranking for remaining retrieval misses.
- Extend cost estimation beyond chat-generation tokens to embeddings, ingestion, and cloud infrastructure.
- Build an admin UI for ingestion, permissions, and evaluation review.

## Short Website Summary

Enterprise Knowledge Agent is a full-stack enterprise RAG system with role-based permissions, citation-grounded answers, benchmark-driven evaluation, observability, Docker packaging, and Azure-ready deployment planning. It demonstrates the engineering required to move beyond a basic chatbot toward a measurable internal AI assistant.
