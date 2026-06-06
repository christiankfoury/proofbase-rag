# Phase 14 Checklist

## Docker Local Setup

- [x] API Dockerfile added.
- [x] Web Dockerfile added.
- [x] Root `.dockerignore` added.
- [x] Docker Compose includes Postgres with pgvector, API, and web.
- [x] Postgres, API, and web health checks configured.
- [x] Postgres first-run schema init configured.
- [x] Repeatable schema setup command added.

## Configuration

- [x] Root `.env.example` updated.
- [x] `apps/api/.env.example` added.
- [x] `apps/web/.env.example` added.
- [x] `OPENAI_MODEL` and `OPENAI_CHAT_MODEL` supported.
- [x] Observability log path made configurable.
- [x] Audit log path documented as future JSONL export; audit remains in Postgres.

## Health and Smoke Tests

- [x] `GET /health` preserved.
- [x] `GET /ready` added.
- [x] `scripts/setup_db.py` added.
- [x] `scripts/run_smoke_test.py` added.
- [x] Smoke test covers health, readiness, DB counts, query shape, and permission refusal.

## Documentation

- [x] Docker local setup documented.
- [x] Deployment architecture documented.
- [x] Azure readiness plan documented.
- [x] Environment variables documented.
- [x] Health checks documented.
- [x] Smoke test behavior documented.
- [x] README updated with Phase 14 quickstart and commands.

## CI

- [x] GitHub Actions workflow added for Python compile, frontend build, and Docker image builds.
- [x] OpenAI-backed evaluations intentionally excluded from CI.

## Verification

- [x] Python compile check run.
- [x] Frontend build verified inside Docker image build.
- [x] Docker Compose config checked.
- [x] Docker images built locally.
- [x] Local stack started.
- [ ] Ingestion rerun skipped because it sends document contents to OpenAI embeddings.
- [x] Smoke test run in `--skip-query` mode.
- [ ] Full OpenAI-backed smoke query not run.
