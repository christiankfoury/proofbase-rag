# Agent Operating Guide

## Project Summary

Proofbase is a portfolio-grade enterprise RAG system. It simulates a secure internal company assistant over synthetic HR, IT/security, sales, manager, HR admin, and IT admin documents.

The current implementation includes:

- FastAPI backend in `apps/api`.
- Next.js frontend in `apps/web`.
- PostgreSQL and pgvector retrieval.
- OpenAI embeddings and answer generation.
- Markdown ingestion from `data/synthetic-documents`.
- Vector, keyword, hybrid, and multi-document retrieval paths.
- Role-filtered retrieval before generation.
- Citation formatting, citation validation, and confidence scoring.
- Session memory used for query rewriting, not source evidence.
- Prompt versioning and prompt experiments.
- Feedback, audit logs, observability, and cost estimates.
- Evaluation artifacts under `data/evaluation` and `docs/phase-*`.
- Docker Compose local setup and Azure-ready deployment documentation.

The current frontend is strongest as a Dev/Admin and evaluation dashboard. The next product direction is to make the project feel like a real application by adding an App side for projects, departments, uploaded knowledge, and project-scoped assistant workflows, while preserving the existing Dev/Admin side for evaluation, ingestion, permissions, observability, and algorithm review.

## Current Known Product Gap

The engine is credible, but the product presentation is still too engineering-oriented. Most visible pages are evaluation, observability, audit, failed questions, and retrieval playground pages. Those are valuable for the Dev/Admin side, but recruiters also need to see the end-user application:

- Create and manage projects.
- Open a project workspace.
- Create departments inside a project.
- Assign department icons.
- Upload files into departments.
- Convert source files into clean indexed text or Markdown.
- Ask questions scoped to a project or department.
- Compare algorithm behavior with evidence, metrics, and failure explanations.

## Operating Loop

The agent should work in a strict loop:

1. Plan.
2. Implement.
3. Verify.
4. Commit to main with a detailed commit message.
5. Review the commit.
6. Perform a code review.
7. Push main.
8. Repeat.

Completing and pushing one phase is not a stopping point. After the post-push status check, immediately start the next queued phase in the same autonomous run unless:

- the roadmap queue is empty
- the user explicitly asks to pause, stop, or only report status
- a blocker has repeated enough times that meaningful progress is impossible
- a new correctness, permission, secret-handling, data-ownership, or AI-cost decision requires user input under the rules below

When a phase finishes cleanly, do not send a final response that merely summarizes completion if the next phase is already known. Instead, record the completed phase in the tracker, then begin the next phase by reading the required roadmap and phase context.

Track durable progress in `docs/roadmap/progress.md`. At the start of each phase, read that file together with `docs/roadmap/phase-plan.md`, `docs/roadmap/phases-improvement.md`, and the latest `docs/phase-*` notes to confirm the current phase, completed phases, verification status, commit references, and next step. Update the progress tracker during each phase before committing. If the tracker conflicts with repository evidence, inspect the repo history and phase docs, then repair the tracker as part of the phase.

## Operating Autonomy

The agent should operate autonomously by default. It should make its own implementation plan internally, choose the best reasonable product and engineering decisions from the repo context, and proceed without asking the user to review or approve the plan.


For normal phase work, prefer decisive execution:

- read the relevant files
- decide based on existing patterns and roadmap intent
- implement the smallest complete version that advances the phase
- verify honestly
- commit and review
- continue to the next phase

Do not pause at "here is the plan" unless the user explicitly asks for plan-only mode.

## Evaluation Lens

Every phase should be judged through the eyes of someone reviewing the project as a portfolio application, recruiter demo, or engineering-manager screen.

Prioritize:

- clear product value before internal tooling
- an App-side experience that feels like a real usable product
- Dev/Admin depth that proves safety, quality, and operational maturity
- honest limitations instead of inflated claims
- measurable RAG quality and permission safety
- clean implementation that is easy to explain in an interview
- demoability within a few minutes

When there is a tradeoff between a technically interesting feature and a more presentable product slice, choose the product slice unless the technical feature is required to keep claims honest.

## Post-Phase 27 Improvement Focus

After Phase 27, `docs/roadmap/phases-improvement.md` defined the completed evaluation-driven sequence:

- Phase 28: dashboard transparency and metric context.
- Phase 29: benchmark schema cleanup and validation.
- Phase 30: enterprise document expansion.
- Phase 31: benchmark expansion.
- Phase 32: expanded baseline run.
- Phase 33: Precision@k improvement.
- Phase 34: hallucination and abstention reduction.
- Phase 35: citation accuracy improvement.
- Phase 36: permission and memory evaluation expansion.
- Phase 37: regression scorecard.

Those phases made the dashboard and benchmark defensible, expanded the source corpus and tests, captured measured before/after runs, and produced the current regression scorecard.

## Post-Phase 37 Remediation Focus

After Phase 37, continue with `docs/roadmap/post-phase-37-remediation-plan.md`. The next sequence is remediation-driven:

- Phase 38: answer-quality failure remediation.
- Phase 39: multi-document and ambiguity orchestration.
- Phase 40: uploaded-document Local E2E workflow.

Start from the current measured answer-quality backlog: `phase35-citation-alignment-v7`, benchmark `1.1`, sample size `130`, and `16` failed questions. Keep the code-first benchmark policy: do not change expected answers, expected behavior, or expected sources unless a clear benchmark defect is proven and documented separately.

For Phase 38, target `<=8` failed answer-quality cases without weakening citation standards, hallucination controls, or permission safety. For Phase 39, use strict ambiguity behavior: when intent is underspecified, return a clarifying question instead of answering. For Phase 40, complete upload -> review -> approve/index -> ask with local/Postgres storage and guarded OpenAI embeddings; keep Azure Blob Storage and AI Markdown cleanup as future improvements.

## Post-Phase 40 Product Polish Focus

After Phase 40 and the Phase 39/40 polish/audit-backlog work are complete, continue with `docs/roadmap/post-phase-40-product-polish-plan.md`. The next sequence is product-polish driven:

- Phase 41: recruiter demo project home.
- Phase 42: guided demo flow and answer proof.
- Phase 43: guarded AI Markdown cleanup draft.
- Phase 44: AI cleanup metadata, cost, and review diff.
- Phase 45: generalization probe suite baseline.
- Phase 46: memory and ambiguity generalization remediation.

Keep the order unless a new correctness, permission, or secret-handling issue becomes more urgent. Recruiter/demo polish comes first because the App side must communicate product value quickly. AI Markdown cleanup must remain explicitly editor-triggered, reviewable, and non-indexing until approval. Memory and ambiguity work must start with a non-benchmark baseline before remediation, and memory must remain query context only, never source evidence.

OpenAI external calls are approved for this roadmap run. Use the explicit approval flags required by existing scripts, prefer dry-runs and local tests first, and record live OpenAI-backed checks and estimated costs in the relevant phase docs.

For every Phase 41-46 implementation, use the full operating loop: plan, implement, verify, commit to `main` with a detailed multi-part message, review the commit, perform a code review of the last commit, push `main`, then continue to the next planned phase. Update `docs/roadmap/progress.md` and the relevant `docs/phase-{number}` notes before committing each phase.

Do not stop after Phase 41, 42, 43, 44, or 45 just because the commit was pushed. Treat the push as the handoff point into the next phase. Send a final user-facing summary only when the active queue is complete, the user asks for status-only output, or a real blocker prevents continuing.

## Post-Phase 50 Defense And Production Readiness Focus

After Phase 50, continue with `docs/roadmap/post-phase-50-defense-and-production-readiness-plan.md`. The next sequence is:

- Phase 51: Trust And Safety Product Page.
- Phase 52: Structured Semantic Request Assessment.
- Phase 53: Permission-Aware Evidence Sufficiency Gate.
- Phase 54: Post-Generation Claim And Source-Instruction Validation.
- Phase 55: Defense Evaluation, Observability, And Page Evidence.
- Phases 56-63: production-shaped OIDC identity and tenancy, database authorization, rate limiting, secure file processing, secrets/log controls, monitoring and incident response, security-assessment readiness, and ongoing adversarial release gates.

Preserve deterministic guards as fast paths, but do not rely on pattern matching as the sole ambiguity or prompt-injection defense. Semantic assessment is a routing/integrity control and must never grant identity, tenant, scope, role, document, or tool access. Evidence sufficiency runs only after permission filtering, and post-generation validation uses only authorized evidence.

Proceed autonomously through Phases 51-55 using the full operating loop and predeclared evaluation gates. For Phases 56-63, prioritize production-shaped controls that can be verified locally and labeled honestly. Pause for the tenant/data decisions required by Phase 56 and at the roadmap's external-integration gates. Do not present a local test double, self-review, or checklist as a completed production control.

Before any Azure resource, paid service, Marketplace purchase, premium licence, or other billable infrastructure is created, satisfy the roadmap's mandatory financial-safety gate and obtain explicit user approval. Local implementation and undeployed infrastructure-as-code do not authorize cloud provisioning. Independent penetration testing is optional for the portfolio track and must remain `Independent validation required` unless a qualified external assessor completes it.

Keep the Phase 47-49 sealed holdouts immutable. A future generalization claim requires a newly authored and sealed holdout after the new runtime is frozen.

## Algorithm Explanation And Audit Mode

When the user starts a new chat to understand whether the algorithm makes sense, treat it as a documentation and reasoning pass before changing behavior.

Primary goal:

- Read the actual code paths for ingestion, retrieval, permission filtering, query orchestration, answer generation, citation validation, confidence scoring, memory rewriting, and evaluation.
- Explain the algorithm in beginner-readable Markdown documents under `docs/algorithm/`.
- Identify confusing design choices, hidden assumptions, and possible improvement areas, but do not change runtime behavior unless the user explicitly asks.

Required source review:

- `apps/api/app/main.py`
- `apps/api/app/retrieval`
- `apps/api/app/services`
- `apps/api/app/prompts`
- `apps/api/app/evaluation`
- `scripts/run_*eval*.py`
- `scripts/export_dashboard_data.py`
- `data/evaluation`
- relevant `docs/phase-*` notes for the current measured runs

Recommended document set:

- `docs/algorithm/README.md`: reading order and mental model.
- `docs/algorithm/end-to-end-flow.md`: request lifecycle from user question to answer.
- `docs/algorithm/retrieval-and-ranking.md`: vector, keyword, hybrid, rerank, top-k, and source coverage.
- `docs/algorithm/permissions-and-scope.md`: project, department, role, and pre-generation filtering.
- `docs/algorithm/generation-citations-confidence.md`: prompt versioning, answer types, citation selection, validation, and confidence.
- `docs/algorithm/memory-and-multi-doc.md`: memory rewrite boundaries, multi-document orchestration, and ambiguity behavior.
- `docs/algorithm/evaluation-metrics.md`: benchmark structure, metrics, run IDs, dashboards, and what each score does or does not prove.
- `docs/algorithm/review-findings.md`: plain-language findings, risks, tradeoffs, and recommended next improvements.

Documentation rules:

- Keep explanations grounded in the code and measured artifacts.
- Use diagrams or step lists when they make the flow easier to understand.
- Distinguish implemented behavior from planned behavior.
- Do not invent algorithm strengths or production claims.
- Preserve zero permission leakage as a hard design requirement.
- If the docs identify a bug or questionable design, record it as a finding with file references and suggested verification instead of silently changing code.

### 1. Plan

Before changing code, read the relevant context:

- `README.md`
- the latest `docs/phase-*` files
- roadmap docs in `docs/roadmap`
- affected source files
- generated evaluation outputs when algorithm behavior is involved

The plan must identify:

- user-facing goal
- affected App or Dev/Admin surface
- backend/data model impact
- evaluation or verification method
- docs that must be updated

Keep this plan internal unless the user asks to see it. Ask the user questions only when a decision changes product behavior, data ownership, permissions, evaluation meaning, or AI cost in a way that cannot be resolved from repo context. Do not ask questions for details that can be discovered from the repo or reasonably decided from the roadmap.

### 2. Implement

Keep changes scoped to the current phase. Prefer the existing project patterns:

- FastAPI route and service patterns in `apps/api/app/main.py` and package modules.
- Retrieval abstractions under `apps/api/app/retrieval`.
- Evaluation helpers under `apps/api/app/evaluation`.
- Prompt versions under `apps/api/app/prompts/versions`.
- Next.js app routes under `apps/web/app`.
- Shared frontend components under `apps/web/components`.

Do not add fake metrics, fake evaluation wins, or placeholder claims that look complete. Mark incomplete values as pending, null, skipped, or future work.

### 3. Verify

Run the smallest checks that prove the change works, then broaden when the change affects shared behavior.

Common checks:

```powershell
python -m compileall apps scripts
cd apps/web; npm run build
docker compose config
```

RAG/evaluation checks depend on the change:

```powershell
python scripts/run_retrieval_experiments.py
python scripts/run_answer_quality_eval.py
python scripts/run_permission_eval.py
python scripts/run_memory_eval.py
python scripts/run_multi_doc_eval.py
python scripts/export_dashboard_data.py
```

For benchmark-schema work after Phase 29 adds the validator, also run:

```powershell
python scripts/validate_benchmark.py
```

OpenAI-backed commands require a configured `OPENAI_API_KEY`. If a check is skipped because it would call OpenAI or needs unavailable local services, state that explicitly in the final response and in relevant phase notes.

### 4. Commit To Main

Default project workflow: commit verified work to `main`.

Before committing:

- run `git status --short`
- inspect changed files
- stage only intentional files
- avoid committing `.env`, runtime logs, secrets, or unrelated user changes
- write a detailed commit message that explains the product change, engineering change, verification performed, and any known limitation or skipped check

Use a multi-part commit message for phase work, for example:

```powershell
git commit -m "Add document library workspace" -m "Product: adds the department document library surface and document status metadata." -m "Engineering: adds the ingestion job model and links seeded corpus documents into department views." -m "Verification: ran API compile checks and web build; skipped OpenAI-backed ingestion because no new embeddings were required."
```

If the current branch is not `main`, ask before switching, merging, or committing directly to another branch.

### 5. Review The Commit

After committing, inspect the commit:

```powershell
git show --stat --oneline HEAD
git show --name-only HEAD
```

For code changes, also inspect the relevant diff:

```powershell
git show --check HEAD
git show HEAD -- <path>
```

Confirm the commit contains only the planned scope.

### 6. Code Review

Perform a self-review in code-review mode:

- lead with bugs, regressions, security risks, missing tests, or misleading metrics
- check permission filtering before generation
- check whether citations still point to accessible evidence
- check whether benchmark outputs prove the claimed improvement
- check whether App-side UX is understandable without reading internal docs
- check whether Dev/Admin pages remain honest about limitations

If review finds issues, fix them in a follow-up commit or clearly document the unresolved risk.

### 7. Push Main

After commit review and code review are complete, push `main` to its upstream remote unless the user has explicitly asked not to push or the review found an unresolved issue that should not leave the machine.

Before pushing:

- run `git status --short --branch`
- confirm the working tree is clean
- confirm `main` is the current branch
- confirm the local commit is the intended work

After pushing:

- run `git status --short --branch`
- confirm `main` is aligned with `origin/main`
- note any push failure or remote divergence clearly

### 8. Loop

After review, choose the next highest-value phase from the roadmap. Prefer work that makes the application more presentable while strengthening measured RAG quality.

## Product Rules

- Keep the App side user-centered and recruiter-presentable.
- Keep the Dev/Admin side detailed, auditable, and metric-driven.
- Prefer durable, real product concepts over fake UI. Seeded demo data is allowed only when it is honest and clearly tied to the synthetic corpus.
- Do not hide known failures such as unresolved multi-document or citation issues.
- Do not claim production auth, Azure deployment, or real enterprise connectors until implemented and verified.
- Treat conversation memory as query context only; retrieved documents remain the source of truth.
- Permission filtering must happen before chunks reach generation.
- Every algorithm change needs a before/after evaluation.

## Default Product Decisions

Use these defaults for future phases unless the repo has moved past them or the user gives a newer instruction:

- A project is a generic knowledge workspace.
- Persist durable concepts such as projects in Postgres when practical.
- Seed the existing synthetic corpus as `Northstar Analytics`.
- Prefer archive or soft-delete semantics before hard delete.
- Keep retrieval behavior unchanged until the project-scoped RAG phase.
- Keep `/chat` stable.
- Keep `/chat?project=...&department=...` scope behavior visible and understandable.
- Keep optional AI Markdown cleanup human-triggered, reversible, and separate from approve/index.
- Keep Dev/Admin routes under `/dev-admin`.
- Do not add fake metrics, fake activity, or unverified AI quality claims.
- Metric claims must include the run, sample size, benchmark version, and skipped checks when applicable.
- Update phase docs as part of each phase.

## When To Ask The User

Ask before implementing when the answer affects:

- whether projects represent clients, internal teams, demos, or knowledge bases
- whether departments are global templates or project-local categories
- whether users and permissions should be real auth or demo roles first
- whether uploaded files should be persisted locally, in Postgres, or in Azure Blob Storage
- whether PDF conversion should preserve layout, tables, images, or only text
- whether AI should rewrite extracted text into Markdown or only normalize deterministic extraction
- whether algorithm comparisons should optimize answer quality, latency, cost, citation coverage, or recall first
- whether remaining benchmark failures should be fixed by retrieval, prompting, chunking, reranking, or benchmark changes

## Useful Starting Points

- Project overview: `README.md`
- Future product plan: `docs/roadmap/app-admin-roadmap.md`
- Feature use cases: `docs/roadmap/feature-use-cases.md`
- Future phases: `docs/roadmap/phase-plan.md`
- Post-Phase 27 improvement roadmap: `docs/roadmap/phases-improvement.md`
- Post-Phase 37 remediation roadmap: `docs/roadmap/post-phase-37-remediation-plan.md`
- Post-Phase 40 product polish roadmap: `docs/roadmap/post-phase-40-product-polish-plan.md`
- Algorithm explanation audit plan: `docs/roadmap/algorithm-explanation-audit-plan.md`
- Roadmap progress tracker: `docs/roadmap/progress.md`
- Current demo guide: `docs/demo/interactive-demo-guide.md`
- Current failure analysis: `docs/phase-17/failed-question-cause-analysis.md`
- Main API entrypoint: `apps/api/app/main.py`
- Main frontend shell: `apps/web/app/layout.tsx`
