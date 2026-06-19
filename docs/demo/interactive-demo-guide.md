# Interactive Demo Guide

This guide walks through the recruiter-facing interactive demo pages added after the Docker and portfolio packaging phases.

## Start The Demo

```powershell
docker compose up --build
docker compose run --rm api python scripts/setup_db.py
docker compose run --rm api python scripts/ingest_markdown.py --apply-schema --chunking-strategy section_based
```

Open `http://localhost:3000`.

## Pages To Show

| Page | URL | What it demonstrates |
|---|---|---|
| App Home | `/` | Product framing with Projects as the primary App entry point. |
| Projects | `/projects` | Project CRUD, seeded Northstar workspace, corpus coverage, quality status, and project audit events. |
| Department Workspace | `/projects/00000000-0000-0000-0000-000000000019/departments/00000000-0000-0000-0000-000000002001` | Department icon, access defaults, document library, PDF upload for Markdown review, active version metadata, extracted Markdown preview, edit, and archive controls. |
| Chat Demo | `/chat` | Live scoped RAG query, project and department selection, role selection, citations, confidence, latency, retrieved context, and feedback. |
| Dev/Admin Overview | `/dev-admin` | Final metrics and evaluation-first proof. |
| Evaluation | `/dev-admin/runs` | Run comparison across retrieval, answer quality, permissions, memory, and prompts. |
| Run Detail | `/dev-admin/evaluation/runs/phase11-answer-generation-v1` | Per-question benchmark rows when detailed JSON exists. |
| Failed Questions | `/dev-admin/failed-questions` | Expandable failure analysis with expected answer, actual answer, citations, and fixes. |
| Algorithm Quality Lab | `/dev-admin/retrieval-playground` | Named retrieval profiles, historical metrics, live source/citation coverage, known failures, and review notes. |
| Permission Demo | `/dev-admin/permission-demo` | Same restricted question across Employee, Sales Representative, Manager, and HR Admin. |
| Multi-Doc | `/dev-admin/multi-doc` | Phase 13 before/after multi-document metrics. |
| Observability | `/dev-admin/observability` | Live request logs, latency, confidence, and token summaries. |
| Feedback | `/dev-admin/feedback` | Human feedback summaries. |
| Audit Logs | `/dev-admin/audit` | Security-relevant audit events. |

## Recommended Query Scenes

1. Project workspace
   - Page: `/projects`
   - Project: `Northstar Analytics`
   - Expected: seeded corpus coverage with derived departments, document count, indexed chunk count, global quality status, and project-scoped assistant entry points.

2. Department workspace
   - Page: `/projects/00000000-0000-0000-0000-000000000019/departments/00000000-0000-0000-0000-000000002001`
   - Department: `People Operations`
   - Expected: icon label, description, default roles, current document roles, document count, indexed document list, PDF upload form, version metadata, access roles, ingestion status, extracted Markdown preview, and honest pending-review status for new uploads.

3. Normal factual answer
   - Page: `/chat`
   - Project: `Northstar Analytics`
   - Department: `All departments`
   - Role: `Employee`
   - Question: `Where does Northstar Analytics have offices?`
   - Expected: `answer` with HR citation.

4. Missing information
   - Page: `/chat`
   - Project: `Northstar Analytics`
   - Role: `Employee`
   - Question: `What is Northstar's sabbatical policy?`
   - Expected: `not_found`, with no invented policy.

5. Permission refusal
   - Page: `/chat`
   - Project: `Northstar Analytics`
   - Role: `Employee`
   - Question: `What is the promotion calibration process?`
   - Expected: `refuse_no_access`.

6. Authorized role contrast
   - Page: `/dev-admin/permission-demo`
   - Question: `What is the promotion calibration process?`
   - Expected: Employee and Sales Representative refuse; Manager should answer if the manager source is retrieved; HR Admin is shown according to actual access.

7. Memory follow-up
   - Page: `/chat`
   - Use the memory scenario button.
   - Expected: follow-up rewrite uses prior vacation context.

8. Multi-document reasoning
   - Page: `/chat` or `/dev-admin/retrieval-playground`
   - Project: `Northstar Analytics` when using `/chat`
   - Role: `Employee`
   - Question: `If I work remotely, what approval and device security expectations apply?`
   - Expected: synthesis from HR and IT policy sources.

9. Known failure
   - Page: `/dev-admin/failed-questions`
   - Expand `MULTI-005`.
   - Expected: shows the known open retrieval miss honestly.

## Demo Notes

- The chat page is a demo UI over the existing API. It is not production authentication.
- Projects are durable workspaces, and `/chat` sends the selected project scope to retrieval.
- Department workspaces include document libraries and PDF-to-Markdown review uploads. `/chat` can strictly narrow retrieval to one department inside the selected project.
- Uploaded PDFs are extracted for review only; approval, chunking, embeddings, and retrieval indexing remain future work.
- Metrics and benchmark details come from existing evaluation JSON and Markdown outputs.
- Querying requires `OPENAI_API_KEY`.
- Retrieved context only shows chunks returned by the permission-filtered query API.
