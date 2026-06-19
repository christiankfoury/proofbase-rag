# Phase 15 Checklist

## Interactive Demo

- [x] Add `/chat` live query demo.
- [x] Add role selector and demo presets.
- [x] Show response type, answer, confidence, citations, validation notes, permission check, and latency.
- [x] Add retrieved context inspector with content previews.
- [x] Add feedback controls wired to the existing feedback API.
- [x] Add memory follow-up scenario.

## Permission And Retrieval

- [x] Add `/dev-admin/permission-demo` role comparison page.
- [x] Use promotion calibration as the default restricted question.
- [x] Add `/dev-admin/retrieval-playground` comparison for vector, keyword, hybrid, and forced multi-doc modes.
- [x] Keep outputs sourced from the existing query API.

## Evaluation Exploration

- [x] Add `/dev-admin/evaluation/runs/[run_id]`.
- [x] Add filters for question type, passed/failed, failure type, and response type.
- [x] Show unavailable details honestly for aggregate-only runs.
- [x] Improve `/dev-admin/failed-questions` with expandable enriched failure details.
- [x] Highlight `MULTI-005` as a known open issue.

## Backend Support

- [x] Add configurable local CORS.
- [x] Add query latency fields to API response.
- [x] Add retrieved chunk previews.
- [x] Add `multi_doc_mode`.
- [x] Add read-only evaluation detail endpoints.

## Documentation

- [x] Add interactive demo guide.
- [x] Add Phase 15 interactive UX notes.
- [x] Update README demo routes and limitations.

## Verification

- [x] `python -m compileall apps scripts`
- [x] `cd apps/web && npm run build`
- [x] `docker compose config`
- [x] `docker compose build`
- [ ] Manual `/chat` query check with `OPENAI_API_KEY`
- [ ] Manual `/dev-admin/permission-demo` role comparison
- [ ] Manual `/dev-admin/retrieval-playground` comparison
- [ ] Manual `/dev-admin/evaluation/runs/phase11-answer-generation-v1`
- [ ] Manual `/dev-admin/failed-questions` expanded `MULTI-005`
