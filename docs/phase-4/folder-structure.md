# Recommended Folder Structure

The project should evolve into a production-style monorepo while staying manageable for a solo developer.

```text
apps/
  web/
    app/
    components/
    lib/
    styles/
    tests/
  api/
    app/
      api/
      core/
      db/
      ingestion/
      retrieval/
      generation/
      evaluation/
      prompts/
      permissions/
      observability/
      schemas/
      services/
    tests/
packages/
  shared/
    types/
    constants/
data/
  synthetic-documents/
  evaluation/
docs/
  phase-1/
  phase-2/
  phase-3/
  phase-4/
infra/
  docker/
  azure/
  db/
scripts/
  ingestion/
  evaluation/
  dev/
```

## Phase 5 Starting Point

Phase 5 should begin with:

- `apps/api/` for FastAPI backend setup.
- `infra/db/` for PostgreSQL and pgvector setup.
- `scripts/evaluation/` for benchmark runner entry points.

The frontend can be scaffolded after the baseline RAG pipeline produces measurable metrics.

## Folder Responsibilities

| Folder | Responsibility |
|---|---|
| `apps/web` | Next.js app, project overview, chat UI, admin UI, evaluation dashboard |
| `apps/api` | FastAPI backend, ingestion, retrieval, generation, evaluation, permissions |
| `packages/shared` | Shared TypeScript types and constants when frontend/backend contracts stabilize |
| `data/synthetic-documents` | Synthetic company documents used for ingestion |
| `data/evaluation` | Benchmark dataset and future evaluation fixtures |
| `docs` | Product, dataset, benchmark, and architecture specs |
| `infra/docker` | Dockerfiles and compose files |
| `infra/azure` | Azure deployment templates and configuration notes |
| `infra/db` | Database migration files after Phase 5 starts |
| `scripts/ingestion` | Developer scripts for loading local documents |
| `scripts/evaluation` | Developer scripts for running benchmark evaluations |
| `scripts/dev` | Local setup and utility scripts |
