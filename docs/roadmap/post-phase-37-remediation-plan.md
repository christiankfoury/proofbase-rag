# Post-Phase 37 Remediation Plan

## Purpose

This roadmap is the next source of truth after the completed Phase 28-37 evaluation and credibility sequence. It focuses on the highest-value remaining gaps for the portfolio demo:

- reduce the current answer-quality failure backlog
- improve multi-document and ambiguity handling without weakening permission guarantees
- finish the uploaded-document product loop from upload to scoped question answering

The starting measurement is the Phase 35 current answer-quality run:

- Run ID: `phase35-citation-alignment-v7`
- Benchmark version: `1.1`
- Sample size: `130`
- Current failed questions: `16`
- Current answer accuracy: `0.919`
- Current citation accuracy: `0.950`
- Current hallucination rate: `0.000`

Do not treat this roadmap as permission to hide failures or move targets. Improvements must be measured against the current benchmark and recorded with run IDs, sample sizes, benchmark versions, and skipped checks.

## Documentation-First Algorithm Audit

The user may run a documentation-first algorithm explanation pass before Phase 39 implementation. That pass should use `docs/roadmap/algorithm-explanation-audit-plan.md`.

The audit should explain the current algorithm and identify risks without changing runtime behavior, benchmark labels, prompts, retrieval, or permission controls. If the audit finds a correctness or permission issue that should change Phase 39 priorities, update this roadmap and `docs/roadmap/progress.md` before implementation.

## Current Failure Matrix

The current answer-quality backlog comes from `data/evaluation/failed-questions/failed-questions.json`.

| Bucket | Count | Question IDs | Primary remediation |
| --- | ---: | --- | --- |
| Ambiguity failure | 5 | `AMB-006`, `AMB-007`, `AMB-008`, `AMB-009`, `AMB-010` | Add strict ambiguity detection before generation and return a clarifying question when the user intent is underspecified. |
| Multi-document failure | 3 | `MULTI-005`, `MULTI-008`, `MULTI-013` | Add query decomposition and source-coverage planning so each required source has a retrieval path before synthesis. |
| Wrong citation | 3 | `MULTI-004`, `MULTI-014`, `MULTI-017` | Improve exact supporting chunk selection and citation backfill from retrieved, permission-filtered chunks only. |
| Unsupported answer | 2 | `MULTI-020`, `ADV-001` | Tighten answer support checks and lower confidence or return partial answers when claims are not grounded. |
| Incomplete answer | 2 | `MULTI-007`, `ADV-005` | Improve expected-fact coverage and prompt the model to include all supported required facts. |
| Retrieval miss | 1 | `MEM-004` | Improve memory-aware query rewrite or retrieval handling for the expected source. |

## Phase 38: Answer-Quality Failure Remediation

Goal: reduce the current `16` failed answer-quality cases to `<=8` without weakening benchmark labels, citation standards, or permission safety.

Product outcome:

- Dev/Admin scorecard shows a smaller current failure backlog with the same benchmark version context.
- Failed-question review remains honest about any unresolved categories.
- The demo story can say the team remediated measured failures by root cause rather than hiding them.

Implementation direction:

- Build a Phase 38 failure matrix from the current failed-question artifact before changing behavior.
- Use a code-first benchmark policy: do not change expected answers, expected behavior, or expected sources unless a clear benchmark defect is proven and documented separately.
- Prioritize wrong citation, unsupported answer, incomplete answer, and the memory retrieval miss because these are likely to improve answer quality without broad retrieval architecture changes.
- Preserve strict permission filtering before generation and before citation backfill.

Acceptance criteria:

- Current answer-quality failures are `<=8` on benchmark `1.1`, or the phase documents why the target was not reached.
- Hallucination rate remains `0.000` or any regression is explicitly blocked from promotion.
- Permission leakage remains `0.000` on the permission suite.
- Dashboard exports show the new run ID, sample size, benchmark version, cost estimate, and failure bucket changes.

Verification:

```powershell
python scripts/validate_benchmark.py
python -m compileall apps scripts
python scripts/run_phase35_citation_candidate.py --dry-run
python scripts/run_phase35_citation_candidate.py --allow-external-ai --budget-usd 2
python scripts/run_permission_eval.py --retrieval-mode vector_lexical_rerank --top-k 5 --rerank-candidate-limit 20 --allow-external-embeddings
python scripts/export_dashboard_data.py
cd apps/web; npm run build
docker compose config
```

If the implementation creates a Phase 38-specific runner, use that runner instead of the Phase 35 candidate command and document the substitution in `docs/phase-38/verification.md`.

## Phase 39: Multi-Document And Ambiguity Orchestration

Goal: reduce the multi-document and ambiguity quality gaps with explicit control flow before generation.

Product outcome:

- Ambiguous user questions ask concise clarifying questions instead of over-answering.
- Multi-document questions retrieve and synthesize each required source more reliably.
- Dev/Admin evidence shows before/after behavior for multi-document and ambiguity cases.

Implementation direction:

- Add strict ambiguity behavior: when the question is underspecified and the benchmark expects `ask_clarifying_question`, return `response_type = clarify` instead of answering from available evidence.
- Add query decomposition and source-coverage planning for multi-document questions before generation.
- Require all retrieved chunks to pass role and scope filtering before they can be used for synthesis or citation.
- Keep `/chat` stable; orchestration changes should improve behavior without breaking existing request shape.

Acceptance criteria:

- Ambiguity failures from `AMB-006` through `AMB-010` are materially reduced.
- Multi-document failures from `MULTI-005`, `MULTI-008`, and `MULTI-013` are materially reduced.
- Any added source-coverage logic does not increase restricted-source exposure.
- Before/after artifacts identify which failures improved, which remained, and why.

Verification:

```powershell
python scripts/validate_benchmark.py
python scripts/run_multi_doc_eval.py
python scripts/run_phase35_citation_candidate.py --allow-external-ai --budget-usd 2
python scripts/run_permission_eval.py --retrieval-mode vector_lexical_rerank --top-k 5 --rerank-candidate-limit 20 --allow-external-embeddings
python scripts/export_dashboard_data.py
python -m compileall apps scripts
cd apps/web; npm run build
```

## Phase 40: Uploaded-Document Local E2E Workflow

Goal: finish the product loop that Phase 22 and Phase 23 started: upload -> review -> approve/index -> ask.

Product outcome:

- A project editor can upload a PDF into a department, review the extracted Markdown, approve it for indexing, and ask questions scoped to that department.
- The department workspace clearly shows pending, indexing, indexed, and failed states.
- The App side feels like a real knowledge workspace rather than a seeded-corpus-only demo.

Implementation direction:

- Add an approval/index endpoint for pending uploaded documents:
  - `POST /projects/{project_id}/departments/{department_id}/documents/{document_id}/approve-index`
  - Require project editor access.
  - Index the current pending-review version as-is.
  - Reuse the existing guarded OpenAI embedding pipeline.
  - Update `document_versions` and `ingestion_jobs` to `indexed` or `failed`.
  - Return the refreshed document record.
- Add frontend client support for the approval/index action.
- Add department document workspace UI states and actions for approving, indexing, retry visibility, and opening scoped chat.
- Add a department-workspace action that opens existing `/chat` with the same project and department context.
- Do not add editable Markdown review in the first Local E2E slice; approve the extracted Markdown as-is.

Acceptance criteria:

- Pending-review uploads are not searchable before approval.
- Approved uploads create chunks and embeddings and become searchable only within the correct project, department, and role scope.
- Failed indexing jobs leave clear status and error details without marking the document as indexed.
- `/chat` remains stable and uses the existing scoped retrieval behavior.

Verification:

```powershell
python -m compileall apps scripts
cd apps/web; npm run build
docker compose config
```

Upload-specific checks:

- Test approve/index with mocked embeddings.
- With local Postgres and `OPENAI_API_KEY` available, upload one sample PDF, approve it, verify the document is indexed, and ask a scoped question that cites the uploaded document.
- If live Postgres or OpenAI is unavailable, record the skipped check in `docs/phase-40/verification.md`.

## Required Documentation Updates

Each phase must update:

- `docs/roadmap/progress.md`
- a new `docs/phase-{phase-number}/checklist.md`
- a new `docs/phase-{phase-number}/verification.md`
- any design note needed to explain behavior, tradeoffs, skipped checks, or benchmark interpretation

When metrics change, also update:

- dashboard export artifacts
- demo or README claims that mention the affected metrics
- any scorecard copy that names the current run

## Future Improvements

These are intentionally out of scope for the first Local E2E upload phase.

### Azure-Ready Storage

Description: make upload storage abstract enough to support Azure Blob Storage and hosted deployment.

Pros:

- Strengthens the production deployment story.
- Makes the file-storage boundary cleaner for later Azure work.
- Reduces migration friction when moving beyond local demo files.

Cons:

- Slower to demo than Local E2E indexing.
- Adds infrastructure and configuration work before the core product loop is complete.
- Does not by itself let a reviewer ask questions over uploaded documents.

### AI Markdown Cleanup

Description: use OpenAI to rewrite or normalize extracted Markdown before human review and indexing.

Pros:

- Can make messy PDF extraction easier to review.
- May produce cleaner chunks for retrieval.
- Makes the upload workflow feel more polished for difficult source files.

Cons:

- Adds cost and another OpenAI-backed step to verify.
- Requires careful review UX so AI cleanup does not create unsupported content.
- Matters less until approve/index/ask works end to end.
