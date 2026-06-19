# Screenshots Checklist

Capture screenshots after running the Docker stack and exporting dashboard data.

## Required Screenshots

- App Home at `/`.
- Project workspace list at `/projects`.
- Seeded `Northstar Analytics` project detail at `/projects/00000000-0000-0000-0000-000000000019`.
- Seeded department detail with document library and Markdown preview at `/projects/00000000-0000-0000-0000-000000000019/departments/00000000-0000-0000-0000-000000002001`.
- Chat demo at `/chat`.
- Dev/Admin overview at `/dev-admin`.
- Retrieval comparison at `/dev-admin/retrieval-experiments`.
- Runs table at `/dev-admin/runs`.
- Failed-question backlog at `/dev-admin/failed-questions`.
- Prompt experiment comparison at `/dev-admin/prompt-experiments`.
- Permission safety page at `/dev-admin/permission-safety`.
- Memory evaluation page at `/dev-admin/memory-evaluation`.
- Multi-document comparison page at `/dev-admin/multi-doc`.
- Feedback page at `/dev-admin/feedback`.
- Observability page at `/dev-admin/observability`.
- Audit page at `/dev-admin/audit`.

## Chat Response Captures

Use `/chat` to capture answer examples:

- Normal answer with citation:
  - Role: `Employee`
  - Question: `Where does Northstar Analytics have offices?`
- Permission refusal:
  - Role: `Employee`
  - Question: `What is the promotion calibration process?`
- Authorized restricted answer:
  - Role: `Manager`
  - Question: `What is the promotion calibration process?`
- Missing information:
  - Role: `Employee`
  - Question: `What is Northstar's sabbatical policy?`
- Multi-document answer:
  - Role: `Employee`
  - Question: `If I work remotely, what approval and device security expectations apply?`

## Optional GIF

Record a short GIF that shows:

1. Open dashboard overview.
2. Switch to Dev/Admin permission safety.
3. Switch to Dev/Admin multi-doc comparison.
4. Run a restricted API query.
5. Show `refuse_no_access` and `unauthorized_chunks_reached_generation: false`.

## Capture Guidance

- Do not create fake cloud screenshots.
- Do not show real API keys or local `.env` values.
- Do not include raw runtime logs unless they are intentionally sanitized.
- Prefer the dashboard pages and API response snippets over terminal walls of text.
- If using port `3001` locally, crop or caption the screenshot so the non-default port does not distract from the demo.
