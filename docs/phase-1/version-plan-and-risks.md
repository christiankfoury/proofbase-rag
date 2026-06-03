# Version Plan and Risks

## Version 1: Baseline RAG

Features:

- Basic document ingestion for curated synthetic company docs.
- Role metadata on documents.
- PostgreSQL full-text search or simple vector retrieval.
- Single-turn Q&A.
- Citations from retrieved chunks.
- Basic refusal when no evidence is found.
- Evaluation runner and first benchmark report.

What is being tested:

- Can the system retrieve the right source?
- Can it answer with grounded citations?
- Can it avoid answering unauthorized or unsupported questions?

Expected output:

- Baseline dashboard or report with retrieval, answer, citation, permission, latency, and cost metrics.

Metrics to compare:

- Hit rate
- Precision@k
- Recall@k
- MRR
- Answer accuracy
- Citation accuracy
- Refusal accuracy
- Permission leakage rate

Recruiter-facing achievement:

> Built a measured baseline enterprise RAG assistant with citations, RBAC filtering, and benchmark-driven evaluation.

## Version 2: Improved RAG

Features:

- Hybrid retrieval combining PostgreSQL full-text and pgvector.
- Better chunking and metadata filtering.
- Query rewriting for enterprise policy questions.
- Improved answer prompt with stricter citation requirements.
- Citation validation heuristic or judge.
- Prompt/retrieval experiment tracking.

What is being tested:

- Does hybrid retrieval outperform baseline?
- Do citations become more accurate?
- Does hallucination decrease?

Expected output:

- Comparison report: baseline versus improved RAG.

Metrics to compare:

- Precision@k
- Recall@k
- MRR
- Answer accuracy
- Citation accuracy
- Hallucination rate
- Cost per answer

Recruiter-facing achievement:

> Improved RAG quality through hybrid retrieval and evaluation-backed experiments, showing measurable gains over a baseline.

## Version 3: Enterprise RAG

Features:

- Conversation memory with role-aware boundaries.
- Citation confidence scores.
- Prompt versioning.
- Admin/evaluation dashboard.
- Latency and cost tracking.
- Observability traces.
- Dockerized Azure deployment.
- Optional Azure Blob Storage and Azure AI Search comparison.

What is being tested:

- Can the system behave like a production internal AI assistant?
- Can quality, security, cost, and latency be monitored together?
- Can the demo show realistic enterprise workflows?

Expected output:

- Deployed recruiter-ready product demo with scripted enterprise scenarios and measurable evaluation history.

Metrics to compare:

- All previous metrics
- p50/p95 latency
- Cost per answer
- Feedback score
- Accepted answer rate
- Regression rate by prompt/retrieval version

Recruiter-facing achievement:

> Delivered a production-style enterprise AI knowledge assistant with RBAC, citations, evaluation dashboards, observability, and measurable quality improvement.

## Main Risks

| Risk | Why It Hurts | Avoidance Plan |
|---|---|---|
| Building a chatbot without evaluation | No proof that the system works or improves | Define benchmark questions before implementation |
| Too much tooling too early | Slows progress and hides core RAG issues | Start with FastAPI, PostgreSQL, pgvector/full-text, OpenAI; add LangGraph or Azure AI Search later only if useful |
| Weak synthetic documents | Demo feels fake and metrics become meaningless | Write realistic docs with overlapping policies, restricted sections, versions, and ambiguity |
| Vague success metrics | Cannot demonstrate improvement | Track concrete retrieval, answer, citation, permission, latency, and cost metrics |
| Poor citations | User cannot verify answers | Require every policy answer to cite specific source chunks |
| Permission leaks | Enterprise trust failure | Enforce role filters before generation and include explicit permission benchmark tests |
| No measurable improvement | Project looks like a static demo | Compare Version 1, Version 2, and Version 3 using the same benchmark |
| Overengineering | Solo project becomes too large | Keep MVP narrow: four use cases, synthetic docs, evaluation runner, baseline RAG |
| Hallucinated policy answers | Dangerous in HR/security contexts | Refuse when evidence is missing and measure faithfulness |
| Recruiter demo too technical | Hiring managers miss the value | Prepare scripted persona-based scenarios showing business value and metrics |
