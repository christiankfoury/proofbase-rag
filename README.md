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
| Observability | Structured JSONL request logs, audit log, OpenTelemetry planned |
| Deployment | Docker, Azure Container Apps or Azure App Service |

## Phase 14 Docker Quickstart

Phase 14 makes the project Docker-ready for local demos. It is Azure-ready, not deployed to Azure.

Create a local `.env` file and add your OpenAI key:

```powershell
Copy-Item .env.example .env
```

Start Postgres with pgvector, FastAPI, and the Next.js dashboard:

```powershell
docker compose up --build
```

In a second terminal, initialize the database:

```powershell
docker compose run --rm api python scripts/setup_db.py
```

Ingest the synthetic Markdown corpus:

```powershell
docker compose run --rm api python scripts/ingest_markdown.py --apply-schema --chunking-strategy section_based
```

Run the smoke test:

```powershell
docker compose run --rm api python scripts/run_smoke_test.py --api-base-url http://api:8000
```

Open:

- Dashboard: `http://localhost:3000`
- API: `http://localhost:8000`
- API health: `http://localhost:8000/health`
- API readiness: `http://localhost:8000/ready`

If port `3000` is already in use, set `WEB_PORT=3001` in `.env` and open `http://localhost:3001`. If port `8000` is already in use, set `API_PORT` and update `NEXT_PUBLIC_API_BASE_URL` for host-side access.

Run evaluation commands inside the API container:

```powershell
docker compose run --rm api python scripts/run_retrieval_experiments.py
docker compose run --rm api python scripts/run_answer_quality_eval.py
docker compose run --rm api python scripts/run_permission_eval.py
docker compose run --rm api python scripts/run_memory_eval.py
docker compose run --rm api python scripts/run_multi_doc_eval.py
docker compose run --rm api python scripts/export_dashboard_data.py
```

Required environment variables are documented in [Phase 14 Environment Variables](docs/phase-14/environment-variables.md). The main local variables are `DATABASE_URL`, `OPENAI_API_KEY`, `OPENAI_MODEL`, `OPENAI_CHAT_MODEL`, `OPENAI_EMBEDDING_MODEL`, `DEFAULT_TOP_K`, `LOG_LEVEL`, `OBSERVABILITY_LOG_PATH`, `AUDIT_LOG_PATH`, `NEXT_PUBLIC_API_BASE_URL`, `API_PORT`, and `WEB_PORT`.

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

## Phase 7 Artifacts

Phase 7 improves answer generation after retrieval by adding structured response types, citation validation, confidence scoring, safer not-found behavior, and answer-quality evaluation.

- [Answer Generation Design](docs/phase-7/answer-generation-design.md)
- [Citation Validation Design](docs/phase-7/citation-validation-design.md)
- [Confidence Scoring](docs/phase-7/confidence-scoring.md)
- [Phase 7 Evaluation Results](docs/phase-7/evaluation-results.md)
- [Failed Question Analysis](docs/phase-7/failed-question-analysis.md)
- [Phase 7 Checklist](docs/phase-7/checklist.md)

Run Phase 7 answer-quality evaluation:

```powershell
python scripts/run_answer_quality_eval.py
```

## Phase 8 Artifacts

Phase 8 hardens enterprise permissions: role-based document access, permission-filtered retrieval, chunk-level permission inheritance, restricted refusals, audit logs, and permission leakage evaluation.

- [Permissions Implementation](docs/phase-8/permissions-implementation.md)
- [Permission Filtering Design](docs/phase-8/permission-filtering-design.md)
- [Audit Logging](docs/phase-8/audit-logging.md)
- [Phase 8 Permission Evaluation Results](docs/phase-8/permission-evaluation-results.md)
- [Phase 8 Checklist](docs/phase-8/checklist.md)

Run Phase 8 permission setup and evaluation:

```powershell
python scripts/ingest_markdown.py --apply-schema --chunking-strategy section_based
python scripts/run_permission_eval.py
```

## Phase 9 Artifacts

Phase 9 adds permission-safe session memory and deterministic query rewriting for follow-up questions.

- [Conversation Memory Design](docs/phase-9/conversation-memory-design.md)
- [Query Rewriting Design](docs/phase-9/query-rewriting-design.md)
- [Memory Permission Safety](docs/phase-9/memory-permissions-safety.md)
- [Phase 9 Memory Evaluation Results](docs/phase-9/memory-evaluation-results.md)
- [Failed Memory Question Analysis](docs/phase-9/failed-memory-question-analysis.md)
- [Phase 9 Checklist](docs/phase-9/checklist.md)

Run Phase 9 memory evaluation:

```powershell
python scripts/ingest_markdown.py --apply-schema --chunking-strategy section_based
python scripts/run_memory_eval.py
```

## Phase 10 Artifacts

Phase 10 adds a recruiter-friendly evaluation dashboard and run comparison layer using real metrics exported from Phases 6-9.

- [Evaluation Dashboard Design](docs/phase-10/evaluation-dashboard-design.md)
- [Run Comparison Design](docs/phase-10/run-comparison-design.md)
- [Dashboard API Design](docs/phase-10/dashboard-api-design.md)
- [Evaluation Results Summary](docs/phase-10/evaluation-results-summary.md)
- [Recruiter Demo Notes](docs/phase-10/recruiter-demo-notes.md)
- [Phase 10 Checklist](docs/phase-10/checklist.md)
- [Dashboard Summary JSON](data/evaluation/dashboard-summary.json)

Generate dashboard data and comparison summary:

```powershell
python scripts/export_dashboard_data.py
python scripts/compare_eval_runs.py
```

Run the API and dashboard:

```powershell
uvicorn apps.api.app.main:app --reload
cd apps/web
npm install
npm run dev
```

Open the dashboard at `http://127.0.0.1:3000`.

Current honest metric summary:

- Best retrieval configuration: `vector-section`
- Retrieval hit rate: `0.975`
- Precision@k: `0.650`
- MRR: `0.980`
- Answer accuracy: `0.829`
- Citation accuracy: `0.857`
- Hallucination rate: `0.156`
- Permission leakage rate: `0.000`
- Memory answer accuracy: `1.000`

## Phase 11 Artifacts

Phase 11 adds prompt versioning and experiment tracking so answer-generation prompt changes can be evaluated against the benchmark and compared for regressions.

- [Prompt Versioning Implementation](docs/phase-11/prompt-versioning-implementation.md)
- [Experiment Tracking Design](docs/phase-11/experiment-tracking-design.md)
- [Prompt Experiment Results](docs/phase-11/prompt-experiment-results.md)
- [Prompt Regression Analysis](docs/phase-11/prompt-regression-analysis.md)
- [Phase 11 Checklist](docs/phase-11/checklist.md)
- [Prompt Versions](apps/api/app/prompts/versions)

Run prompt experiments and compare versions:

```powershell
python scripts/run_prompt_experiment.py --prompt-version all
python scripts/compare_prompt_versions.py
python scripts/export_dashboard_data.py
python scripts/compare_eval_runs.py
```

Prompt experiment outputs are written to:

```text
data/evaluation/prompt-experiments/
```

## Phase 12 Artifacts

Phase 12 adds a production-style feedback and observability layer: answer ratings, structured request logs, per-request timing traces, extended audit coverage, and dashboard views for feedback, observability, and audit events.

- [Feedback Loop Design](docs/phase-12/feedback-loop-design.md)
- [Observability Design](docs/phase-12/observability-design.md)
- [Audit Log Design](docs/phase-12/audit-log-design.md)
- [Feedback-to-Evaluation Workflow](docs/phase-12/feedback-to-evaluation-workflow.md)
- [Phase 12 Checklist](docs/phase-12/checklist.md)

Submit feedback on an answer:

```powershell
Invoke-WebRequest -Uri http://localhost:8000/feedback -Method POST `
  -ContentType "application/json" -UseBasicParsing `
  -Body '{
    "question": "What is the parental leave policy?",
    "answer": "Employees receive up to 12 weeks...",
    "user_role": "Employee",
    "rating": "thumbs_down",
    "feedback_category": "incorrect_answer",
    "user_comment": "Missing the adoptive parent eligibility."
  }'
```

View feedback summary:

```powershell
Invoke-WebRequest -Uri http://localhost:8000/feedback/summary -UseBasicParsing
```

Generate observability summary from request logs:

```powershell
python scripts/generate_observability_summary.py
```

Export negative feedback as benchmark review candidates:

```powershell
python scripts/export_feedback_candidates.py
```

Candidates are written to `data/evaluation/feedback-candidates.json`. All items have `needs_human_review: true` and must be reviewed before being added to `benchmark-questions.json`.

View audit events:

```powershell
Invoke-WebRequest -Uri http://localhost:8000/audit/events -UseBasicParsing
Invoke-WebRequest -Uri http://localhost:8000/audit/summary -UseBasicParsing
```

Dashboard pages added in Phase 12:

- `/feedback` — ratings, category breakdown, recent negative feedback
- `/observability` — latency, tokens, confidence from live request logs
- `/audit` — action counts and recent audit events

Observability fields tracked per request: `request_id`, `user_role`, `session_id`, `question` (truncated), `rewritten_question`, `retrieval_mode`, `chunking_strategy`, `top_k`, `retrieved_chunk_ids`, `retrieved_document_ids`, `response_type`, `citation_count`, `final_confidence`, `retrieval_latency_ms`, `generation_latency_ms`, `total_latency_ms`, `prompt_version`, `model`, `input_tokens`, `output_tokens`, `estimated_cost` (null — pricing not hardcoded).

Audit events logged: `restricted_query_refused`, `unauthorized_chunks_reached_generation`, `permission_filtered_retrieval`, `unauthorized_candidate_blocked`, `feedback_submitted`, `evaluation_run_started`, `evaluation_run_completed`, `prompt_version_changed`.

## Phase 13 Artifacts

Phase 13 improves multi-document reasoning by adding query decomposition, multi-source retrieval, and grouped evidence context. It also makes the observability dashboard live — no manual script required.

- [Multi-Document Reasoning Design](docs/phase-13/multi-document-reasoning-design.md)
- [Query Decomposition Design](docs/phase-13/query-decomposition-design.md)
- [Live Observability Design](docs/phase-13/live-observability-design.md)
- [Multi-Document Failure Analysis](docs/phase-13/multi-document-failure-analysis.md)
- [Phase 13 Checklist](docs/phase-13/checklist.md)

Run multi-document evaluation (baseline vs multi-doc comparison):

```powershell
python scripts/run_multi_doc_eval.py
```

Results are written to `data/evaluation/multi-doc-eval.json`. Export to dashboard:

```powershell
python scripts/export_dashboard_data.py
```

Run full benchmark regression check after multi-doc changes:

```powershell
python scripts/run_prompt_experiment.py --prompt-version v1
```

Dashboard page added in Phase 13:

- `/multi-doc` — baseline vs multi-doc comparison table, fixed/broken/still-failing question cards, hallucination regression warning if applicable

Phase 13 results (10 MULTI questions, baseline → multi-doc):

- Answer accuracy: `0.700` → `0.850` (+0.150)
- Citation accuracy: `0.750` → `0.900` (+0.150)
- Response type accuracy: `0.900` → `1.000`
- All sources cited rate: `0.600` → `0.800`
- Failed questions: `4` → `2`
- Hallucination rate: `0.667` → `0.700` (+0.033, known tradeoff — documented)

Full benchmark regression check confirmed no regressions on FACT, PERM, MISS, AMB, or MEM questions.

Known limitations:
- MULTI-005 still failing — SALES-002 (Implementation Timeline) not retrieved by vector search for this question; retrieval miss, not a generation issue
- Multi-doc detection is heuristic — questions that don't match keyword patterns take the single-doc fast path even if they need multiple documents
- Hallucination rate slightly higher in multi-doc mode — synthesized cross-document answers produce inferences the citation validator cannot fully match back to individual chunks

## Phase 14 Artifacts

Phase 14 packages the existing enterprise RAG system for reproducible local demos and documents an Azure-ready deployment path without claiming cloud deployment.

- [Docker Local Setup](docs/phase-14/docker-local-setup.md)
- [Deployment Architecture](docs/phase-14/deployment-architecture.md)
- [Azure Readiness Plan](docs/phase-14/azure-readiness-plan.md)
- [Environment Variables](docs/phase-14/environment-variables.md)
- [Health Checks](docs/phase-14/health-checks.md)
- [Smoke Test Results](docs/phase-14/smoke-test-results.md)
- [Phase 14 Checklist](docs/phase-14/checklist.md)

Phase 14 adds:

- Docker Compose services for pgvector Postgres, FastAPI, and Next.js.
- API and web Dockerfiles.
- `GET /ready` database/schema readiness endpoint.
- Repeatable database setup and smoke-test scripts.
- Environment variable examples without secrets.
- Lightweight CI for Python compile, frontend build, and Docker image builds.
- Azure-ready deployment plan for Container Apps, Azure Database for PostgreSQL, ACR, Key Vault, and future Blob Storage.

Known deployment limitations:

- Azure deployment has not been performed yet.
- Production authentication and SSO remain deferred.
- Audit events persist in Postgres; durable cloud audit/log export remains future work.
- Raw document storage still uses repository files, not Azure Blob Storage.
- Evaluations and ingestion require `OPENAI_API_KEY` for embedding and generation calls.

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
