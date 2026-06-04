# Enterprise Knowledge Agent

Enterprise Knowledge Agent is a portfolio-grade enterprise RAG project that simulates a secure internal company AI assistant. Employees can ask questions across company knowledge and receive accurate, cited, permission-aware answers.

The project is intentionally designed to show more than a basic PDF chatbot. It focuses on enterprise behaviors recruiters expect from production AI systems: document ingestion, retrieval quality, citations, role-based permissions, evaluation-driven development, latency and cost tracking, and measurable improvement across experiments.

## Recruiter Positioning

Built an enterprise RAG knowledge assistant with hybrid retrieval, RBAC, citations, citation validation, and evaluation-driven quality improvements.

This project demonstrates full-stack AI engineering across Next.js, TypeScript, Tailwind, FastAPI, PostgreSQL, pgvector, OpenAI APIs, Docker, and Azure-oriented deployment planning.

## Product Goal

Enterprise Knowledge Agent helps internal employees find trusted company knowledge without exposing restricted information or inventing unsupported answers. It supports realistic internal use cases across HR, IT/security, sales enablement, and manager-only knowledge.

The system should prove that it can:

- Retrieve relevant internal documents.
- Answer with cited evidence.
- Refuse unsupported or unauthorized questions.
- Respect role-based permissions.
- Measure retrieval, answer quality, citation quality, security, latency, and cost.
- Show measurable improvement from baseline RAG to improved enterprise RAG.

## Target Stack

| Area | Technology |
|---|---|
| Frontend | Next.js, TypeScript, Tailwind |
| Backend | Python, FastAPI |
| AI/RAG | OpenAI API, LangGraph or LangChain only where useful |
| Database | PostgreSQL, pgvector |
| Search | PostgreSQL full-text search first, Azure AI Search later if useful |
| Auth | Clerk or Auth.js |
| Cloud | Azure |
| Storage | Azure Blob Storage |
| Evaluation | Custom evaluation runner, optional LangSmith |
| Observability | OpenTelemetry or LangSmith traces |
| Deployment | Docker, Azure Container Apps or Azure App Service |

## Phase 1 Artifacts

Phase 1 defines the product before implementation. The goal is to make the system specific, measurable, and recruiter-friendly before writing application code.

- [Product Scope](docs/phase-1/product-scope.md)
- [Personas and Access Model](docs/phase-1/personas-and-access.md)
- [Use Cases](docs/phase-1/use-cases.md)
- [Success Metrics](docs/phase-1/success-metrics.md)
- [Evaluation and Benchmark Plan](docs/phase-1/evaluation-benchmark-plan.md)
- [Version Plan and Risks](docs/phase-1/version-plan-and-risks.md)
- [Phase 1 Completion Checklist](docs/phase-1/checklist.md)

## Phase 2 Artifacts

Phase 2 defines the synthetic enterprise knowledge base used for RAG retrieval, permissions, citations, and future benchmark design.

- [Synthetic Dataset Specification](docs/phase-2/synthetic-dataset-spec.md)
- [Document Inventory](docs/phase-2/document-inventory.md)
- [Access Control Matrix](docs/phase-2/access-control-matrix.md)
- [Document Writing Guidelines](docs/phase-2/document-writing-guidelines.md)
- [Phase 2 Completion Checklist](docs/phase-2/checklist.md)
- [Synthetic Documents](data/synthetic-documents)

## Phase 3 Artifacts

Phase 3 defines the evaluation benchmark used to measure retrieval quality, answer accuracy, citation accuracy, refusal behavior, permission safety, hallucination resistance, and conversation-memory handling.

- [Benchmark Design](docs/phase-3/benchmark-design.md)
- [Question Taxonomy](docs/phase-3/question-taxonomy.md)
- [Evaluation Schema](docs/phase-3/evaluation-schema.md)
- [Scoring Rubric](docs/phase-3/scoring-rubric.md)
- [Phase 3 Completion Checklist](docs/phase-3/checklist.md)
- [Benchmark Questions](data/evaluation/benchmark-questions.json)

## Phase 4 Artifacts

Phase 4 defines the implementation-ready system architecture, database schema, ingestion design, retrieval design, permissions model, prompt versioning, evaluation runner, API design, and Phase 5 baseline RAG plan.

- [Architecture Overview](docs/phase-4/architecture-overview.md)
- [Database Schema](docs/phase-4/database-schema.md)
- [API Design](docs/phase-4/api-design.md)
- [Ingestion Pipeline](docs/phase-4/ingestion-pipeline.md)
- [Retrieval Pipeline](docs/phase-4/retrieval-pipeline.md)
- [Evaluation Runner Design](docs/phase-4/evaluation-runner-design.md)
- [Prompt Versioning Design](docs/phase-4/prompt-versioning-design.md)
- [Permissions Design](docs/phase-4/permissions-design.md)
- [Folder Structure](docs/phase-4/folder-structure.md)
- [Phase 4 Completion Checklist](docs/phase-4/checklist.md)

## Phase 5 Artifacts

Phase 5 implements the first working backend baseline RAG pipeline: Markdown ingestion, section-based chunks, OpenAI embeddings, pgvector storage, vector-only retrieval, cited answer generation, and benchmark execution.

- [Baseline RAG Implementation](docs/phase-5/baseline-rag-implementation.md)
- [Baseline Evaluation Results](docs/phase-5/baseline-evaluation-results.md)
- [Phase 5 Checklist](docs/phase-5/checklist.md)

Run the baseline setup:

```powershell
pip install -r requirements.txt
docker compose up -d
python scripts/ingest_markdown.py --apply-schema
uvicorn apps.api.app.main:app --reload
```

Run the baseline benchmark:

```powershell
python scripts/run_baseline_eval.py
```

## Phase 6 Artifacts

Phase 6 adds controlled retrieval experiments: PostgreSQL full-text keyword search, hybrid vector + keyword retrieval, fixed-size chunking experiments, and retrieval comparison reporting.

- [Retrieval Experiments](docs/phase-6/retrieval-experiments.md)
- [Hybrid Search Design](docs/phase-6/hybrid-search-design.md)
- [Phase 6 Evaluation Results](docs/phase-6/evaluation-results.md)
- [Phase 6 Checklist](docs/phase-6/checklist.md)

Run Phase 6 retrieval experiments:

```powershell
python scripts/ingest_markdown.py --apply-schema --chunking-strategy section_based
python scripts/ingest_markdown.py --chunking-strategy fixed_size --chunk-size 180 --chunk-overlap 40
python scripts/run_retrieval_experiments.py
```

## MVP Boundary

The MVP proves enterprise RAG quality, not breadth.

Included in MVP:

- Realistic synthetic company documents.
- Five roles: Employee, Sales Representative, Manager, HR Admin, IT/Admin.
- Document metadata for category, visibility, title, version, and effective date.
- Baseline RAG using PostgreSQL full-text search and/or pgvector.
- Cited answers and refusal behavior.
- A 60-question benchmark before chatbot implementation.
- Evaluation metrics for retrieval, answer quality, citations, permissions, latency, and cost.
- A recruiter demo flow showing baseline RAG, improved RAG, and enterprise controls.

Deferred:

- Slack, Teams, SharePoint, and Google Drive integrations.
- Fine-tuning.
- Real employee data.
- Complex multi-tenant SSO.
- Autonomous agents that take business actions.
- Azure AI Search before PostgreSQL search is measured.

## Version Roadmap

1. **Version 1: Baseline RAG**  
   Establish document ingestion, permissions, retrieval, citations, refusal behavior, and benchmark reporting.

2. **Version 2: Improved RAG**  
   Add hybrid retrieval, better chunking, metadata filtering, stricter prompting, and citation validation.

3. **Version 3: Enterprise RAG**  
   Add role-aware memory, prompt versioning, evaluation dashboard, observability, cost/latency tracking, and Azure deployment.

## Portfolio Narrative

This project is aimed at AI engineering and full-stack AI roles in Montreal, Toronto, and New York. The strongest demo story is:

> Baseline RAG was measured, weaknesses were identified, retrieval and prompting were improved, and the final system demonstrates enterprise-grade controls around citations, permissions, evaluation, latency, and cost.
