# Phase 18 App And Dev/Admin Navigation Design

## Goal

Phase 18 reframes the frontend from a flat evaluation dashboard into two clear surfaces:

- App: the user-facing knowledge assistant surface.
- Dev/Admin: the technical proof surface for evaluation, failures, safety, observability, feedback, and audit review.

This phase intentionally does not add project CRUD, department CRUD, document upload, database schema changes, or new RAG behavior.

## Route Decisions

| Surface | Route | Purpose |
|---|---|---|
| App | `/` | Assistant-first App Home. |
| App | `/chat` | Existing live assistant demo. |
| Dev/Admin | `/dev-admin` | Previous measured RAG progress overview. |
| Dev/Admin | `/dev-admin/runs` | Evaluation run comparison. |
| Dev/Admin | `/dev-admin/evaluation/runs/[run_id]` | Per-question run explorer. |
| Dev/Admin | `/dev-admin/failed-questions` | Failed-question backlog. |
| Dev/Admin | `/dev-admin/retrieval-playground` | Retrieval and multi-doc comparison. |
| Dev/Admin | `/dev-admin/permission-demo` | Role comparison for restricted questions. |
| Dev/Admin | `/dev-admin/multi-doc` | Multi-document reasoning metrics. |
| Dev/Admin | `/dev-admin/observability` | Live request logs and cost/latency summary. |
| Dev/Admin | `/dev-admin/feedback` | Feedback summaries. |
| Dev/Admin | `/dev-admin/audit` | Security-relevant audit events. |
| Deep Evaluation | `/dev-admin/retrieval-experiments` | Retrieval experiment detail. |
| Deep Evaluation | `/dev-admin/prompt-experiments` | Prompt experiment detail. |
| Deep Evaluation | `/dev-admin/permission-safety` | Permission safety detail. |
| Deep Evaluation | `/dev-admin/memory-evaluation` | Memory evaluation detail. |

Old Dev/Admin URLs are intentionally not preserved or redirected in this phase.

## App Home Content

The App Home uses Assistant First positioning:

- primary CTA: `Ask the assistant`
- secondary CTA: `View Dev/Admin proof`
- measured trust signals for permissions, citations, benchmark runs, and observability
- planned next capabilities for Projects, Departments, Documents, and Algorithm Verification

The page must not imply that project CRUD, department CRUD, or upload flows already exist.

## Sidebar Groups

The sidebar has three groups:

- App: Home, Assistant.
- Dev/Admin: Overview, Runs, Failed Questions, Retrieval Playground, Permission Demo, Multi-Doc, Observability, Feedback, Audit Logs.
- Deep Evaluation: Retrieval Experiments, Prompt Experiments, Permission Safety, Memory Evaluation.

This keeps the product story visible first while preserving direct access to the engineering proof.

## Non-Goals

- No backend API changes.
- No database schema changes.
- No production authentication changes.
- No RAG behavior changes.
- No fake project or department data.
- No redirects for moved routes.

## Verification Notes

Frontend build is the required automated check for this phase. Manual route checks should confirm the new App Home, stable `/chat`, moved Dev/Admin pages, and intentionally broken old Dev/Admin URLs.

