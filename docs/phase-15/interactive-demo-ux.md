# Phase 15 Interactive Demo UX

## Goal

Turn the existing evaluation dashboard into an interactive enterprise RAG demo that reviewers and engineers can use to test the system, inspect evidence, compare retrieval modes, verify permissions, submit feedback, and investigate benchmark failures.

## Implemented Scope

- Added browser-safe local CORS support through configurable `CORS_ALLOWED_ORIGINS`.
- Extended `/query` responses with latency fields and retrieved chunk previews.
- Added `multi_doc_mode` to `/query` with `auto`, `off`, and `force` modes. The default `auto` preserves existing behavior.
- Added read-only evaluation detail APIs:
  - `/evaluation/runs/{run_id}/questions`
  - `/evaluation/failed-questions/enriched`
- Added interactive frontend pages:
  - `/chat`
  - `/dev-admin/permission-demo`
  - `/dev-admin/retrieval-playground`
  - `/dev-admin/evaluation/runs/[run_id]`
- Reworked `/dev-admin/failed-questions` into an expandable inspector.
- Updated top navigation for guided demo flow.

## What Stayed Out Of Scope

- No new retrieval algorithm.
- No backend redesign.
- No production authentication.
- No fake metrics or generated screenshots.
- No Azure deployment claim.

## Page Behavior

### `/chat`

The chat demo lets a reviewer select a role, enter a question, choose retrieval mode, choose prompt version, choose multi-doc mode, and inspect:

- response type
- answer
- confidence scores
- citations
- supported and unsupported claims
- validation notes
- latency
- permission check
- retrieved context
- feedback submission

### `/dev-admin/permission-demo`

Runs the same permission-sensitive question across four roles and compares:

- response type
- answer preview
- citation count
- unauthorized chunk exposure
- permission result

### `/dev-admin/retrieval-playground`

Runs one question through:

- vector only
- keyword only
- hybrid
- forced multi-doc

The page shows answers, citations, top retrieved chunks, latency, and confidence side by side.

### `/dev-admin/evaluation/runs/[run_id]`

Shows run metadata and per-question rows when detailed JSON exists. Prompt experiment runs have rows; older aggregate-only runs show a clear unavailable message.

### `/dev-admin/failed-questions`

Expands each failure into expected answer, actual answer, expected sources, actual citations, retrieved documents, scores, and recommended fix. `MULTI-005` is highlighted as a known open issue.

## Limitations

- Live queries require `OPENAI_API_KEY`.
- The app is unauthenticated and role selection is for demo/testing.
- Some historical evaluation runs only have summary data.
- `MULTI-005` remains an open retrieval issue.
- The UI uses existing APIs and does not replace a production enterprise chat experience.
