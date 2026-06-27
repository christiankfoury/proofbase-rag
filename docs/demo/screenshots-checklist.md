# Screenshots Checklist

Capture screenshots after running the Docker stack and exporting dashboard data.

## Five-Minute Demo Screenshots

- App Home at `/` showing the four-step demo path.
- Project workspace list at `/projects`.
- Seeded `Northstar Analytics` project home at `/projects/00000000-0000-0000-0000-000000000019`, with scoped ask entry point, suggested questions, department shortcuts, representative documents, and upload/indexing summary visible.
- Seeded department detail with document library, PDF upload form, version metadata, and Markdown preview at `/projects/00000000-0000-0000-0000-000000000019/departments/00000000-0000-0000-0000-000000002001`.
- Chat demo at `/chat` with project scope, role, answer, citations, confidence, latency, and retrieved context visible.
- Algorithm Quality Lab at `/dev-admin/retrieval-playground` showing named profile comparison and known failure visibility.
- Failed-question inspection at `/dev-admin/failed-questions` with answer/citation review controls visible.
- Feedback review at `/dev-admin/feedback` with negative-feedback review controls visible.

## Supporting Proof Screenshots

- Dev/Admin overview at `/dev-admin`.
- Deep retrieval comparison at `/dev-admin/retrieval-experiments`.
- Runs table at `/dev-admin/runs`.
- Prompt experiment comparison at `/dev-admin/prompt-experiments`.
- Permission safety page at `/dev-admin/permission-safety`.
- Memory evaluation page at `/dev-admin/memory-evaluation`.
- Multi-document comparison page at `/dev-admin/multi-doc`.
- Observability page at `/dev-admin/observability`.
- Audit page at `/dev-admin/audit`.

## Chat Response Captures

Use `/chat` to capture answer examples:

- Normal answer with citation:
  - Project: `Northstar Analytics`
  - Department: `All departments`
  - Role: `Employee`
  - Question: `Where does Northstar Analytics have offices?`
- Department-scoped answer:
  - Project: `Northstar Analytics`
  - Department: a seeded department with matching source coverage
  - Role: `Employee`
  - Question: a department-relevant policy question
- Permission refusal:
  - Project: `Northstar Analytics`
  - Role: `Employee`
  - Question: `What is the promotion calibration process?`
- Authorized restricted answer:
  - Project: `Northstar Analytics`
  - Role: `Manager`
  - Question: `What is the promotion calibration process?`
- Missing information:
  - Project: `Northstar Analytics`
  - Role: `Employee`
  - Question: `What is Northstar's sabbatical policy?`
- Multi-document answer:
  - Project: `Northstar Analytics`
  - Role: `Employee`
  - Question: `If I work remotely, what approval and device security expectations apply?`

## Optional GIF

Record a short GIF that shows:

1. Open App Home.
2. Open `Northstar Analytics`.
3. Open a department document library.
4. Ask a scoped `/chat` question and show citations.
5. Switch to Algorithm Quality Lab.
6. Open a failed question and show human review labels.

## Capture Guidance

- Do not create fake cloud screenshots.
- Do not show real API keys or local `.env` values.
- Do not include raw runtime logs unless they are intentionally sanitized.
- Prefer dashboard pages and response snippets over terminal walls of text.
- If using port `3001` locally, crop or caption the screenshot so the non-default port does not distract from the demo.
- Capture implemented review and extraction states only; do not mock successful indexing for uploaded PDFs.
