# Enterprise Knowledge Agent Demo Script

This demo is designed for recruiters and engineering interviewers. It uses the existing Next.js dashboard plus API calls because the current project does not include a polished end-user chat UI.

## Setup

Start the Docker stack:

```powershell
docker compose up --build
```

Initialize and ingest:

```powershell
docker compose run --rm api python scripts/setup_db.py
docker compose run --rm api python scripts/ingest_markdown.py --apply-schema --chunking-strategy section_based
```

Open:

- Dashboard: `http://localhost:3000`
- API health: `http://localhost:8000/health`
- API readiness: `http://localhost:8000/ready`

If port `3000` is busy, set `WEB_PORT=3001` and open `http://localhost:3001`.

## Scene 1: Evaluation Dashboard Overview

Open: `http://localhost:3000`

Point out:

- This is an evaluation dashboard, not a marketing page.
- The system is measured across retrieval, answers, citations, permissions, hallucination, and memory.
- Headline metrics are exported from real benchmark outputs.

Expected recruiter takeaway:

> This project was built like an evaluated enterprise AI system, not a one-off chatbot.

## Scene 2: Normal HR Question With Citations

Role: `Employee`

Question:

```text
Where does Northstar Analytics have offices?
```

Command:

```powershell
Invoke-WebRequest -Uri http://localhost:8000/query -Method POST `
  -ContentType "application/json" -UseBasicParsing `
  -Body '{"question":"Where does Northstar Analytics have offices?","user_role":"Employee","retrieval_mode":"vector_only","chunking_strategy":"section_based"}'
```

Expected behavior:

- `response_type` is `answer`.
- Answer cites `HR-001`.
- Response includes `final_confidence`, citations, and retrieved chunks.

Point out:

- The system answers from retrieved evidence.
- Citations are structured, not just free-text footnotes.
- The response includes confidence and retrieval metadata for debugging.

## Scene 3: Permission Refusal As Employee

Role: `Employee`

Question:

```text
What is the promotion calibration process?
```

Command:

```powershell
Invoke-WebRequest -Uri http://localhost:8000/query -Method POST `
  -ContentType "application/json" -UseBasicParsing `
  -Body '{"question":"What is the promotion calibration process?","user_role":"Employee","retrieval_mode":"vector_only","chunking_strategy":"section_based"}'
```

Expected behavior:

- `response_type` is `refuse_no_access`.
- `permission_check.unauthorized_chunks_reached_generation` is `false`.
- Restricted manager-only chunks do not reach generation.

Point out:

- Permissions are enforced before the model sees evidence.
- The permission evaluation reached `0.000` leakage.

## Scene 4: Same Restricted Question As Manager

Role: `Manager`

Question:

```text
What is the promotion calibration process?
```

Command:

```powershell
Invoke-WebRequest -Uri http://localhost:8000/query -Method POST `
  -ContentType "application/json" -UseBasicParsing `
  -Body '{"question":"What is the promotion calibration process?","user_role":"Manager","retrieval_mode":"vector_only","chunking_strategy":"section_based"}'
```

Expected behavior:

- The system can answer because the Manager role can access manager-only guidance.
- Citations should point to manager-accessible documents such as `MGR-002`.

Point out:

- This demonstrates role-aware behavior, not a hardcoded refusal.
- The same question has different valid outcomes depending on the role.

## Scene 5: Missing Information Refusal

Role: `Employee`

Question:

```text
What is Northstar's sabbatical policy?
```

Command:

```powershell
Invoke-WebRequest -Uri http://localhost:8000/query -Method POST `
  -ContentType "application/json" -UseBasicParsing `
  -Body '{"question":"What is Northstar''s sabbatical policy?","user_role":"Employee","retrieval_mode":"vector_only","chunking_strategy":"section_based"}'
```

Expected behavior:

- `response_type` is `not_found` or equivalent missing-information behavior.
- The answer does not invent a sabbatical policy.

Point out:

- The project evaluates missing-information behavior.
- Refusing unsupported questions is a core enterprise requirement.

## Scene 6: Session Memory Follow-Up

Role: `Employee`

Create a session:

```powershell
$session = Invoke-RestMethod -Uri http://localhost:8000/chat/sessions -Method POST `
  -ContentType "application/json" `
  -Body '{"user_role":"Employee"}'
```

Initial question:

```powershell
Invoke-RestMethod -Uri http://localhost:8000/query -Method POST `
  -ContentType "application/json" `
  -Body (@{
    question = "How many paid vacation days do full-time employees receive each calendar year?"
    user_role = "Employee"
    session_id = $session.session_id
    retrieval_mode = "vector_only"
    chunking_strategy = "section_based"
  } | ConvertTo-Json)
```

Follow-up:

```powershell
Invoke-RestMethod -Uri http://localhost:8000/query -Method POST `
  -ContentType "application/json" `
  -Body (@{
    question = "Can I carry any unused days into next year?"
    user_role = "Employee"
    session_id = $session.session_id
    retrieval_mode = "vector_only"
    chunking_strategy = "section_based"
  } | ConvertTo-Json)
```

Expected behavior:

- The follow-up is rewritten using session memory.
- The answer cites `HR-002`.
- Memory is used for rewriting, not as source evidence.

Point out:

- Memory evaluation reached `1.000` answer and citation accuracy.
- Permission filtering still applies after memory rewrite.

## Scene 7: Multi-Document Reasoning And Metrics

Role: `Employee`

Question:

```text
If I work remotely, what approval and device security expectations apply?
```

Command:

```powershell
Invoke-WebRequest -Uri http://localhost:8000/query -Method POST `
  -ContentType "application/json" -UseBasicParsing `
  -Body '{"question":"If I work remotely, what approval and device security expectations apply?","user_role":"Employee","retrieval_mode":"vector_only","chunking_strategy":"section_based"}'
```

Expected behavior:

- The system synthesizes from remote-work and device-security sources.
- Expected source documents are `HR-003` and `IT-002`.

Then open:

- `/dev-admin/multi-doc`
- `/dev-admin/retrieval-experiments`
- `/dev-admin/permission-safety`
- `/dev-admin/memory-evaluation`
- `/dev-admin/failed-questions`
- `/dev-admin/observability`

Point out:

- Multi-doc answer accuracy improved from `0.700` to `0.850`.
- Multi-doc citation accuracy improved from `0.750` to `0.900`.
- Failed multi-doc questions dropped from `4` to `2`.
- The dashboard also shows the remaining tradeoff: hallucination rate moved from `0.667` to `0.700`.

## Closing Pitch

End with:

> The project shows a complete enterprise AI engineering loop: define the product, build the RAG pipeline, measure it, improve weak cases, enforce permissions, observe behavior, containerize it, and package it for deployment review.
