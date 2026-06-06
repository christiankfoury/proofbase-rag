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
| Overview | `/` | Final metrics and evaluation-first story. |
| Chat Demo | `/chat` | Live RAG query, role selection, citations, confidence, latency, retrieved context, and feedback. |
| Evaluation | `/runs` | Run comparison across retrieval, answer quality, permissions, memory, and prompts. |
| Run Detail | `/evaluation/runs/phase11-answer-generation-v1` | Per-question benchmark rows when detailed JSON exists. |
| Failed Questions | `/failed-questions` | Expandable failure analysis with expected answer, actual answer, citations, and fixes. |
| Retrieval Playground | `/retrieval-playground` | Vector, keyword, hybrid, and multi-doc comparison on the same question. |
| Permission Demo | `/permission-demo` | Same restricted question across Employee, Sales Representative, Manager, and HR Admin. |
| Multi-Doc | `/multi-doc` | Phase 13 before/after multi-document metrics. |
| Observability | `/observability` | Live request logs, latency, confidence, and token summaries. |
| Feedback | `/feedback` | Human feedback summaries. |
| Audit Logs | `/audit` | Security-relevant audit events. |

## Recommended Query Scenes

1. Normal factual answer
   - Page: `/chat`
   - Role: `Employee`
   - Question: `Where does Northstar Analytics have offices?`
   - Expected: `answer` with HR citation.

2. Missing information
   - Page: `/chat`
   - Role: `Employee`
   - Question: `What is Northstar's sabbatical policy?`
   - Expected: `not_found`, with no invented policy.

3. Permission refusal
   - Page: `/chat`
   - Role: `Employee`
   - Question: `What is the promotion calibration process?`
   - Expected: `refuse_no_access`.

4. Authorized role contrast
   - Page: `/permission-demo`
   - Question: `What is the promotion calibration process?`
   - Expected: Employee and Sales Representative refuse; Manager should answer if the manager source is retrieved; HR Admin is shown according to actual access.

5. Memory follow-up
   - Page: `/chat`
   - Use the memory scenario button.
   - Expected: follow-up rewrite uses prior vacation context.

6. Multi-document reasoning
   - Page: `/chat` or `/retrieval-playground`
   - Role: `Employee`
   - Question: `If I work remotely, what approval and device security expectations apply?`
   - Expected: synthesis from HR and IT policy sources.

7. Known failure
   - Page: `/failed-questions`
   - Expand `MULTI-005`.
   - Expected: shows the known open retrieval miss honestly.

## Demo Notes

- The chat page is a demo UI over the existing API. It is not production authentication.
- Metrics and benchmark details come from existing evaluation JSON and Markdown outputs.
- Querying requires `OPENAI_API_KEY`.
- Retrieved context only shows chunks returned by the permission-filtered query API.
