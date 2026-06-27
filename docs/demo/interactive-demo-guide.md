# Interactive Demo Guide

This guide walks through the recruiter-facing interactive demo pages added after Docker And Azure Readiness (Phase 14) and portfolio packaging work.

## Start The Demo

```powershell
docker compose up --build
docker compose run --rm api python scripts/setup_db.py
docker compose run --rm api python scripts/ingest_markdown.py --apply-schema --chunking-strategy section_based
```

Open `http://localhost:3000`.

## Five-Minute Presentation Path

1. Open `/demo` and follow the guided demo checklist.
2. Open `/projects`, then select `Northstar Analytics`; use the first-screen project home to show scoped ask, department shortcuts, representative documents, upload/indexing status, and suggested questions.
3. Open a seeded department and inspect document inventory, access roles, active version metadata, PDF extraction, editable Markdown review, optional AI cleanup draft, cleanup provenance, before/after diff, approval/indexing controls, and Markdown preview.
4. Open `/chat` from a guided link, project-home suggested question, or department shortcut, ask a scoped question, and show `Why this answer?` proof with citations plus retrieved context.
5. Open `/dev-admin/retrieval-playground` to compare algorithm profiles and known failures.
6. Open `/dev-admin/failed-questions` or `/dev-admin/feedback` to show human review labels without claiming automatic benchmark promotion.

## Pages To Show

| Page | URL | What it demonstrates |
|---|---|---|
| App Home | `/` | Product framing with Projects as the primary App entry point. |
| Guided Demo | `/demo` | Five-minute product path from project home to department evidence, upload/review status, scoped answer, answer proof, and Dev/Admin evidence. |
| Projects | `/projects` | Project CRUD, seeded Northstar workspace, scoped ask entry points, department shortcuts, representative documents, upload/indexing status, quality status, and project audit events. |
| Department Workspace | `/projects/00000000-0000-0000-0000-000000000019/departments/00000000-0000-0000-0000-000000002001` | Department icon, access defaults, document library, PDF upload for Markdown review, optional AI cleanup draft, cleanup provenance, extraction/current-review diff, active version metadata, extracted Markdown preview, edit, and archive controls. |
| Chat Demo | `/chat` | Live scoped RAG query, project and department selection, role selection, `Why this answer?` proof, citations, confidence, latency, retrieved context, and feedback. |
| Dev/Admin Overview | `/dev-admin` | Final metrics with run IDs, timestamps, sample sizes, benchmark version, category breakdown, and evaluation-first proof. |
| Evaluation | `/dev-admin/runs` | Run comparison across retrieval, answer quality, permissions, memory, and prompts with explicit pass/fail counts. |
| Run Detail | `/dev-admin/evaluation/runs/phase11-answer-generation-v1` | Per-question benchmark rows for Answer Generation v1 (`phase11-answer-generation-v1`) when detailed JSON exists. |
| Failed Questions | `/dev-admin/failed-questions` | Expandable failure analysis with expected answer, actual answer, citations, fixes, and human review labels. |
| Algorithm Quality Lab | `/dev-admin/retrieval-playground` | Named retrieval profiles, historical metrics, live source/citation coverage, known failures, and review notes. |
| Permission Demo | `/dev-admin/permission-demo` | Same restricted question across Employee, Sales Representative, Manager, and HR Admin. |
| Multi-Doc | `/dev-admin/multi-doc` | Multi-Document Reasoning (Phase 13) before/after metrics. |
| Observability | `/dev-admin/observability` | Live request logs, latency, confidence, and token summaries. |
| Feedback | `/dev-admin/feedback` | Human feedback summaries and negative-feedback review decisions. |
| Audit Logs | `/dev-admin/audit` | Security-relevant audit events. |

## Recommended Query Scenes

1. Project workspace
   - Page: `/projects`
   - Project: `Northstar Analytics`
   - Expected: seeded corpus coverage with derived departments, document count, indexed chunk count, scoped assistant entry points, suggested questions, representative documents, upload/indexing status, global quality status, and project audit events.

2. Department workspace
   - Page: `/projects/00000000-0000-0000-0000-000000000019/departments/00000000-0000-0000-0000-000000002001`
   - Department: `People Operations`
   - Expected: icon label, description, default roles, current document roles, document count, indexed document list, PDF upload form, version metadata, access roles, ingestion status, extracted Markdown preview, optional cleanup action on pending/failed uploads, cleanup provenance, review diff, and honest pending-review status for new uploads.

3. Normal factual answer
   - Page: `/chat`
   - Project: `Northstar Analytics`
   - Department: `All departments`
   - Role: `Employee`
   - Question: `Where does Northstar Analytics have offices?`
   - Expected: `answer` with HR citation and visible `Why this answer?` proof.

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
   - Expected: shows the known open retrieval miss honestly and lets an evaluator save answer/citation labels without changing the benchmark.

## Demo Notes

- The chat page uses local demo auth over the existing API. It derives App query role server-side, but it is not production authentication or SSO.
- Projects are durable workspaces, and `/chat` sends the selected project scope to retrieval.
- Department workspaces include document libraries and PDF-to-Markdown review uploads. `/chat` can strictly narrow retrieval to one department inside the selected project.
- Uploaded PDFs are extracted into editable Markdown for review; an editor can optionally request AI cleanup as a review draft, inspect metadata and diff, revert to deterministic extraction, but must explicitly approve/index before chunking, embeddings, and retrieval visibility.
- Human review labels are persisted for failed questions and negative feedback, but approved candidates are not exported into benchmark JSON automatically yet.
- Metrics and benchmark details come from existing evaluation JSON and Markdown outputs; dashboard sample sizes are shown explicitly because retrieval/answer-quality, permission, and memory runs use different suites.
- Querying requires `OPENAI_API_KEY`.
- Retrieved context only shows chunks returned by the permission-filtered query API.
