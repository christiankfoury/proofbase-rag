# Agent Operating Guide

## Project Summary

Enterprise Knowledge Agent is a portfolio-grade enterprise RAG system. It simulates a secure internal company assistant over synthetic HR, IT/security, sales, manager, HR admin, and IT admin documents.

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
4. Commit to main.
5. Review the commit.
6. Perform a code review.
7. Repeat.

## Operating Autonomy

The agent should operate autonomously by default. It should make its own implementation plan internally, choose the best reasonable product and engineering decisions from the repo context, and proceed without asking the user to review or approve the plan.

Ask the user only when a decision is genuinely blocking, risky, costly, irreversible, or would materially change the project direction. Examples include real auth provider choice, production storage provider choice, AI-cost-heavy workflows, benchmark rubric changes, or permission model changes that cannot be inferred safely from existing docs.

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
- questions that block a correct implementation

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

OpenAI-backed commands require a configured `OPENAI_API_KEY`. If a check is skipped because it would call OpenAI or needs unavailable local services, state that explicitly in the final response and in relevant phase notes.

### 4. Commit To Main

Default project workflow: commit verified work to `main`.

Before committing:

- run `git status --short`
- inspect changed files
- stage only intentional files
- avoid committing `.env`, runtime logs, secrets, or unrelated user changes
- write a concrete commit message

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

### 7. Loop

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
- Keep Dev/Admin routes under `/dev-admin`.
- Do not add fake metrics, fake activity, or unverified AI quality claims.
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
- Current demo guide: `docs/demo/interactive-demo-guide.md`
- Current failure analysis: `docs/phase-17/failed-question-cause-analysis.md`
- Main API entrypoint: `apps/api/app/main.py`
- Main frontend shell: `apps/web/app/layout.tsx`
