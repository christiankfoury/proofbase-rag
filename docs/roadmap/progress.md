# Roadmap Progress Tracker

This file is the durable source of truth for roadmap progress. At the start of each phase, read this file with `agent.md`, `docs/roadmap/phase-plan.md`, the latest `docs/phase-*` notes, and recent Git history.

Update this tracker before committing each phase. Keep entries factual: record what was implemented, what was verified, what was skipped, and which commit or commits contain the work.

## Current Position

- Current phase: Phase 24, Algorithm Quality Lab.
- Last completed phase: Phase 23, Project-Scoped RAG.
- Last verification focus: scoped retrieval plumbing, API import, web build, and Docker Compose config.
- Next expected work: make retrieval/profile comparisons measurable and reviewable without hiding known failures.

## Phase Status

| Phase | Status | Commit Reference | Verification | Notes |
| --- | --- | --- | --- | --- |
| 18: App And Dev/Admin Navigation Split | Complete | `955d49f` | Frontend/product routing documented in Phase 18 notes. | App and Dev/Admin surfaces split. |
| 19: Project Workspace Model And UI | Complete | `efca8b1`, `ba015cb`, `91a6b11` | API/backend checks and web build completed during phase work. | Added Postgres-backed projects and seeded `Northstar Analytics`. |
| 20: Department Workspaces | Complete | `d4e2105` | API/backend checks and web build completed during phase work. | Added project-local departments, seeded corpus mapping, and department UI. |
| Docker verification after Phase 20 | Complete | `4a3cd61` | `docker compose` stack built and started inside the Compose network; API `/health` and `/ready` passed; web rendered; project and department CRUD passed. | Host ports were not exposed because another local container owned port 5432. OpenAI-backed ingestion/eval was not run. |
| 21: Document Library And File Ingestion Planning | Complete | `586212f` | Targeted Python compile, API import smoke check, web production build, and `docker compose config` passed. Live Postgres document-library checks and OpenAI-backed ingestion/eval were skipped. | Added department document library UI, read-only document endpoints, ingestion job schema, seeded Markdown ingestion job upsert path, version metadata, and Markdown preview. |
| 22: PDF And Document Extraction Pipeline | Complete | `fcbab93` | Targeted Python compile, API import, PDF extractor import, generated sample PDF extraction, web production build, and `docker compose config --quiet` passed. Live multipart upload against Postgres and OpenAI-backed ingestion/eval were skipped. | Added PDF-only upload, deterministic Markdown extraction, local raw file storage, pending-review document versions, and no-index-before-review behavior. |
| 23: Project-Scoped RAG | Complete | Pending | Targeted Python compile, API import, web production build, and `docker compose config --quiet` passed. Live scoped query checks against Postgres and OpenAI-backed evals were skipped. | Added strict project and optional department scope to query retrieval, response payloads, observability, and the `/chat` App surface while preserving global Dev/Admin query behavior. |
| 24: Algorithm Quality Lab | Next | Pending | Pending | Make retrieval/profile comparisons measurable and reviewable. |
| 25: Result Verification And Human Review | Planned | Pending | Pending | Add review workflow for answers, citations, and feedback-to-eval candidates. |
| 26: Recruiter Presentation Polish | Planned | Pending | Pending | Align App, Dev/Admin, README, demo guide, screenshots, and limitations. |
| 27: Auth And Deployment Readiness | Planned | Pending | Pending | Move toward production-shaped auth, membership, permissions, and deployment readiness. |

## Update Rules

- Mark a phase `In progress` when implementation starts.
- Mark a phase `Complete` only when implementation and verification are done and no known review issue remains.
- Record commit references after they are known. If a phase commit cannot reference itself, add the commit hash in the next tracker update or a small follow-up tracker commit when needed.
- If push fails after a phase is marked complete, fix the cause and update this tracker in a follow-up commit if the failure changes phase status.
- Record skipped checks explicitly, especially OpenAI-backed checks, unavailable services, or host-port conflicts.
- Record follow-up fix commits next to the phase they affect.
- If repo evidence contradicts this tracker, correct the tracker in the same commit that advances or repairs the phase.
