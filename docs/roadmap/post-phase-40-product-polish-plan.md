# Post-Phase 40 Product Polish Plan

Status: Phases 41-46 from this plan are complete. The larger-generalization-suite backlog item has been promoted to Phase 47 in `docs/roadmap/phase-47-independent-generalization-holdout-plan.md`. Use `docs/roadmap/progress.md` as the current source of truth for next work.

## Purpose

This roadmap is the executable source of truth after the completed Phase 39/40 remediation and polish work. It focuses on the next three product-quality improvements:

1. Recruiter/demo polish so the App side feels immediately understandable.
2. AI Markdown cleanup for uploads, with explicit human control before indexing.
3. Memory and ambiguity generalization beyond benchmark-shaped questions.

The order is intentional. First make the product easier to understand in a short demo, then improve the uploaded-document workflow, then deepen conversational quality with a broader non-benchmark probe suite.

Do not treat this plan as permission to weaken permission filtering, hide known limitations, or change benchmark expectations casually. Permission filtering before generation remains a hard requirement for every phase.

OpenAI external calls are approved for this roadmap run. Use the explicit approval flags required by existing scripts, prefer dry-runs and local tests first, and record live OpenAI-backed checks and estimated costs in the relevant phase docs.

## Execution Loop For Every Phase

Each phase below must use the standard autonomous loop:

1. Plan.
2. Implement.
3. Verify.
4. Commit to `main` with a detailed multi-part message.
5. Review the commit with `git show --stat --oneline HEAD`, `git show --name-only HEAD`, `git show --check HEAD`, and relevant file diffs.
6. Perform a code review of the last commit, leading with bugs, regressions, security risks, missing tests, or misleading claims.
7. Push `main`.
8. Continue to the next phase from this plan unless a new correctness, permission, or secret-handling issue is more urgent.

Before each commit, update `docs/roadmap/progress.md` and the relevant `docs/phase-{number}` notes with what changed, what was verified, what was skipped, and any remaining limitation.

Phase completion is not a natural stopping point. After a successful push and clean post-push status check, start the next queued phase from this plan in the same autonomous run. Stop only when the queue is complete, the user explicitly asks to pause or report status only, or a real blocker requires user input under `AGENTS.md`.

## Shared Rules

- Preserve role, project, and department permission filtering before chunks reach generation.
- Do not change benchmark expected answers, expected sources, expected behavior, prompts, retrieval ranking, or metrics unless a benchmark or implementation defect is proven and documented.
- Keep memory as query context only; memory must never become source evidence.
- OpenAI-backed operations are approved for this roadmap run and must still use explicit script approval flags where required. Upload cleanup should occur only after an editor clicks a cleanup action; eval scripts should keep explicit approval flags such as `--allow-external-ai`.
- Do not add fake activity, fake metrics, fake AI-quality claims, or demo-only behavior that looks production-ready.
- Every product-facing quality claim must name the run, sample size, benchmark/probe version, and skipped checks when applicable.
- If a phase changes algorithm behavior, capture before/after artifacts and rerun permission safety.

## Phase 41: Recruiter Demo Project Home

Goal: make the project workspace first screen feel like a real App-side product surface.

User-facing outcome:

- `Northstar Analytics` opens to a polished project home/dashboard.
- The first screen shows useful App-side concepts without requiring Dev/Admin knowledge.
- Recruiters can understand projects, departments, documents, upload status, and scoped asking in under one minute.

Scope:

- Improve the project workspace first screen with:
  - scoped ask entry point
  - department shortcuts
  - recent or representative documents
  - upload/indexing status summary
  - clear project quality/status summary without inflated claims
- Add suggested question chips scoped to the selected project or department.
- Improve empty, loading, and API-offline states.
- Keep Dev/Admin pages unchanged except for links needed to explain proof.

Out of scope:

- New retrieval logic.
- New benchmark expectations.
- AI Markdown cleanup.
- Production auth or hosted storage.

Verification:

```powershell
cd apps/web; npm run build
python -m compileall apps/api/app scripts
docker compose config --quiet
```

Recommended manual check:

- Open `/projects`.
- Open `Northstar Analytics`.
- Confirm the first viewport explains the product path without relying on internal docs.
- Confirm project/department scoped chat links still apply scope visibly.

Required docs:

- `docs/phase-41/checklist.md`
- `docs/phase-41/verification.md`
- Update `docs/demo/interactive-demo-guide.md` and screenshot checklist if visible demo flow changes.
- Update `docs/roadmap/progress.md`.

Acceptance criteria:

- The App-side project home is more useful than a pure admin/detail page.
- Suggested questions and links preserve project/department scope.
- No new quality claim is shown without an existing metric source.

## Phase 42: Guided Demo Flow And Answer Proof

Goal: make the short demo path obvious: project -> department -> upload/review -> ask -> inspect proof.

User-facing outcome:

- A reviewer can follow a guided route through the product without reading the README first.
- Answer proof is easier to reach from App-side chat, not only Dev/Admin pages.
- The demo explains citations, permission scope, confidence, and audit/evaluation proof in plain UI terms.

Scope:

- Add a lightweight guided demo mode or demo checklist route.
- Add clearer "Why this answer?" access from chat results:
  - citations
  - retrieved source snippets
  - permission/scope context
  - confidence interpretation
  - links to relevant Dev/Admin proof when available
- Add document status timeline UI for uploaded documents:
  - uploaded
  - extracted
  - reviewed
  - indexed
  - failed
- Keep the Dev/Admin side honest about limitations and current metric provenance.

Out of scope:

- Changing answer generation prompts.
- Adding fake logs or fake user activity.
- Changing permission behavior.

Verification:

```powershell
cd apps/web; npm run build
python -m compileall apps/api/app scripts
docker compose config --quiet
```

Recommended manual check:

- Complete the documented demo path in five minutes or less.
- Ask a scoped question and inspect "Why this answer?" proof.
- Confirm a restricted or role-sensitive case still communicates permissions honestly.

Required docs:

- `docs/phase-42/checklist.md`
- `docs/phase-42/verification.md`
- Update `docs/demo/interactive-demo-guide.md`.
- Update `docs/demo/screenshots-checklist.md`.
- Update `docs/roadmap/progress.md`.

Acceptance criteria:

- The App demo has a clear beginning, middle, and proof moment.
- Proof surfaces are reachable without turning the whole App side into a metrics dashboard.
- No Dev/Admin metric is reworded into a stronger claim than the artifact supports.

## Phase 43: Guarded AI Markdown Cleanup Draft

Goal: let editors request AI cleanup of extracted upload Markdown while keeping deterministic extraction and human approval as the source of truth.

User-facing outcome:

- Pending or failed uploaded documents show a `Clean up Markdown` action.
- The editor explicitly clicks the action before any OpenAI cleanup call.
- Cleaned Markdown is returned into the review editor, not indexed automatically.
- The editor can review, edit, revert to deterministic extraction, then approve/index.

Scope:

- Add an editor-only backend endpoint for cleanup, for example:
  - `POST /projects/{project_id}/departments/{department_id}/documents/{document_id}/cleanup-markdown`
- Require the document to belong to the project/department and be pending review or failed.
- Use the current extracted Markdown as input.
- Add an explicit request/response schema with:
  - cleaned Markdown
  - model
  - estimated tokens/cost when available
  - source content hash
  - cleanup timestamp
- Store cleanup metadata without replacing the indexed version until approval.
- Add frontend action and loading/error states in the Markdown review panel.
- Keep approval/index unchanged except that it can use the reviewed Markdown already in the editor.

Out of scope:

- Automatic cleanup on upload.
- Indexing cleaned Markdown without editor approval.
- Persisted cross-process content cache.
- Azure Blob Storage.

Verification:

```powershell
python scripts/test_phase40_upload_indexing.py
python -m compileall apps/api/app scripts
cd apps/web; npm run build
docker compose config --quiet
```

Add focused tests for:

- cleanup endpoint rejects non-editor access
- cleanup endpoint rejects indexed or unavailable documents
- cleanup is approval-gated and does not run without the explicit action
- cleaned Markdown is returned to the editor but not indexed until approve/index
- empty or unsafe cleanup output is rejected

Approved live check:

```powershell
python scripts/run_phase40_upload_e2e.py --allow-external-ai
```

Required docs:

- `docs/phase-43/checklist.md`
- `docs/phase-43/verification.md`
- Design note describing deterministic extraction versus optional AI cleanup.
- Update `docs/roadmap/progress.md`.

Acceptance criteria:

- AI cleanup is human-triggered, reviewable, reversible, and not an automatic indexing step.
- Permission checks and project/department ownership checks run before cleanup.
- If OpenAI is unavailable or not approved, the deterministic review/index path still works.

## Phase 44: AI Cleanup Metadata, Cost, And Review Diff

Goal: make AI cleanup auditable and understandable enough for a portfolio reviewer and a future production migration.

User-facing outcome:

- Editors can see what changed between deterministic extraction and AI-cleaned Markdown.
- The UI shows cleanup metadata and estimated cost.
- Reviewers can tell whether a document was edited after AI cleanup before indexing.

Scope:

- Add before/after or diff-style review in the upload review panel.
- Add revert-to-extracted action.
- Track metadata such as:
  - cleanup model
  - cleanup timestamp
  - source hash
  - cleaned hash
  - estimated input/output tokens and cost
  - whether reviewer edited after cleanup
- Add audit events for cleanup requested, cleanup succeeded, cleanup failed, reverted, and approved/indexed after cleanup.
- Export or display cleanup status where useful in Dev/Admin or document details.

Out of scope:

- Changing chunking strategy.
- AI summarization that removes policy details.
- Persistent secret/content cache.

Verification:

```powershell
python -m compileall apps/api/app scripts
cd apps/web; npm run build
docker compose config --quiet
```

Add focused tests for:

- metadata persistence
- reviewer-edited-after-cleanup detection
- revert behavior
- audit events
- approve/index uses the current reviewed Markdown, not a hidden cleaned copy

Required docs:

- `docs/phase-44/checklist.md`
- `docs/phase-44/verification.md`
- Update upload workflow docs and demo guide if the visible flow changes.
- Update `docs/roadmap/progress.md`.

Acceptance criteria:

- Cleanup provenance is visible and auditable.
- Editors keep final control over what is indexed.
- The UI does not overstate AI cleanup as correctness validation.

## Phase 45: Generalization Probe Suite Baseline

Goal: measure memory and ambiguity behavior on realistic multi-turn chat sequences outside the benchmark.

User-facing outcome:

- Dev/Admin can distinguish benchmark quality from broader conversational robustness.
- The project has a small, honest probe suite for normal user phrasing.

Scope:

- Create `scripts/run_generalization_eval.py`.
- Add about 20 realistic probes covering:
  - "that policy"
  - "same department"
  - "what about contractors?"
  - "compare those two"
  - "which one applies to me?"
  - project/department ambiguity
  - role ambiguity
  - topic ambiguity
  - document-reference ambiguity
- First run should be a baseline: do not change prompts or retrieval before measuring.
- Separate metrics for:
  - memory rewrite quality
  - clarification behavior
  - answer/citation quality
  - permission safety
  - memory-as-evidence violations
- Export artifacts under `data/evaluation` and a report under `docs/phase-45`.

Out of scope:

- Fixing failures before the baseline is captured.
- Folding probe results into benchmark v1.1.
- Changing benchmark expectations.

Verification:

```powershell
python scripts/run_generalization_eval.py --dry-run
python -m compileall apps/api/app scripts
python scripts/validate_benchmark.py
docker compose config --quiet
```

Approved live check:

```powershell
python scripts/run_generalization_eval.py --allow-external-ai
python scripts/run_permission_eval.py --phase phase-45 --run-id phase45-permission-evaluation --allow-external-embeddings
python scripts/export_dashboard_data.py
```

Required docs:

- `docs/phase-45/checklist.md`
- `docs/phase-45/generalization-baseline.md`
- `docs/phase-45/verification.md`
- Update dashboard/export docs if new artifacts are exported.
- Update `docs/roadmap/progress.md`.

Acceptance criteria:

- The suite can dry-run without OpenAI.
- Live execution is approval-gated.
- Results clearly separate benchmark performance from generalization probes.
- Memory is never credited as source evidence.

## Phase 46: Memory And Ambiguity Generalization Remediation

Goal: fix proven generalization failures from Phase 45 without weakening benchmark behavior or permission safety.

User-facing outcome:

- Follow-up questions feel more natural.
- Underspecified project, department, role, topic, or document references ask concise clarifying questions.
- Dev/Admin can see why the system clarified instead of answered.

Scope:

- Add or improve ambiguity detection for:
  - project scope
  - department scope
  - role applicability
  - unclear document references
  - unclear comparison targets
  - unclear "that/it/this" references
- Add a lightweight `clarification_reason` field where appropriate.
- Expose clarification reason in Dev/Admin and/or chat proof surfaces.
- Improve memory rewrite only where Phase 45 proves a defect.
- Add tests proving memory is query context only and never source evidence.
- Rerun Phase 45 probes and relevant benchmark/permission checks.

Out of scope:

- Broad prompt rewrites without a measured failure.
- Benchmark expectation changes unless a benchmark defect is separately documented.
- Treating memory content as citation evidence.

Verification:

```powershell
python scripts/run_generalization_eval.py --dry-run
python scripts/validate_benchmark.py
python -m compileall apps/api/app scripts
docker compose config --quiet
```

Approved live checks:

```powershell
python scripts/run_generalization_eval.py --allow-external-ai
python scripts/run_phase39_live_query_answer_quality.py --allow-external-ai
python scripts/run_permission_eval.py --phase phase-46 --run-id phase46-permission-evaluation --allow-external-embeddings
python scripts/export_dashboard_data.py
cd apps/web; npm run build
```

Required docs:

- `docs/phase-46/checklist.md`
- `docs/phase-46/remediation-results.md`
- `docs/phase-46/verification.md`
- Update algorithm docs if memory or clarification semantics change.
- Update `docs/roadmap/progress.md`.

Acceptance criteria:

- Phase 45 failures are reduced or honestly documented.
- Existing Phase 39 live answer-quality behavior does not regress.
- Permission leakage remains `0.000`; unauthorized chunks reaching generation remain `0.000`.
- `clarification_reason` helps explain non-answer behavior without exposing restricted information.

## Future Backlog After Phase 46

These are not part of the first post-Phase-40 polish sequence unless a later roadmap update promotes them:

- Azure Blob or hosted storage for uploaded source files.
- Production SSO and hosted auth.
- Larger non-benchmark generalization suite: promoted to planned Phase 47 Independent Generalization And Holdout Evaluation.
- Project-specific evaluation authoring.
- Exportable demo reports for recruiter walkthroughs.
- Multi-tenant deployment hardening.
