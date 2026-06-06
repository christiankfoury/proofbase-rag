# Screenshots Checklist

Capture screenshots after running the Docker stack and exporting dashboard data.

## Required Screenshots

- Dashboard overview at `/`.
- Retrieval comparison at `/retrieval-experiments`.
- Runs table at `/runs`.
- Failed-question backlog at `/failed-questions`.
- Prompt experiment comparison at `/prompt-experiments`.
- Permission safety page at `/permission-safety`.
- Memory evaluation page at `/memory-evaluation`.
- Multi-document comparison page at `/multi-doc`.
- Feedback page at `/feedback`.
- Observability page at `/observability`.
- Audit page at `/audit`.

## API Response Captures

The current product does not include a polished chat UI, so capture API responses for answer examples:

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
2. Switch to permission safety.
3. Switch to multi-doc comparison.
4. Run a restricted API query.
5. Show `refuse_no_access` and `unauthorized_chunks_reached_generation: false`.

## Capture Guidance

- Do not create fake cloud screenshots.
- Do not show real API keys or local `.env` values.
- Do not include raw runtime logs unless they are intentionally sanitized.
- Prefer the dashboard pages and API response snippets over terminal walls of text.
- If using port `3001` locally, crop or caption the screenshot so the non-default port does not distract from the demo.
