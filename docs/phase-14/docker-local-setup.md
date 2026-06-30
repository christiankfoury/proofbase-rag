# Phase 14 Docker Local Setup

## Goal

Run the Proofbase locally with reproducible containers for PostgreSQL with pgvector, the FastAPI API, and the Next.js dashboard.

## Services

| Service | Container | Port | Purpose |
|---|---|---:|---|
| `postgres` | `pgvector/pgvector:pg16` | `5432` | PostgreSQL database with pgvector |
| `api` | `apps/api/Dockerfile` | `8000` | FastAPI RAG API, ingestion, and evaluation scripts |
| `web` | `apps/web/Dockerfile` | `3000` | Next.js evaluation and observability dashboard |

## First-Time Setup

Create a local environment file:

```powershell
if (-not (Test-Path .env)) { Copy-Item .env.example .env }
```

Set `OPENAI_API_KEY` in `.env`. Do not rerun `Copy-Item .env.example .env` against an existing `.env`; it overwrites local secrets. Do not commit real secrets. Docker Compose mounts this value as a local secret and the API reads it through `OPENAI_API_KEY_FILE`, so `docker compose config` should not render the raw key.

Build and start the stack:

```powershell
docker compose up --build
```

In a second terminal, apply the schema:

```powershell
docker compose run --rm api python scripts/setup_db.py
```

Ingest the synthetic Markdown documents:

```powershell
docker compose run --rm api python scripts/ingest_markdown.py --apply-schema --chunking-strategy section_based
```

Run the smoke test:

```powershell
docker compose run --rm api python scripts/run_smoke_test.py --api-base-url http://api:8000
```

## URLs

- API health: `http://localhost:8000/health`
- API readiness: `http://localhost:8000/ready`
- Dashboard: `http://localhost:3000`

If a host port is already in use, set `API_PORT` or `WEB_PORT` in `.env` and restart Compose. For example, `WEB_PORT=3001` exposes the dashboard at `http://localhost:3001`.

## Evaluation Commands

Run these from the API container after ingestion:

```powershell
docker compose run --rm api python scripts/run_retrieval_experiments.py
docker compose run --rm api python scripts/run_answer_quality_eval.py
docker compose run --rm api python scripts/run_permission_eval.py
docker compose run --rm api python scripts/run_memory_eval.py
docker compose run --rm api python scripts/run_multi_doc_eval.py
docker compose run --rm api python scripts/export_dashboard_data.py
```

The legacy retrieval, answer-quality, and multi-document evaluators are guarded by default. Add `--dry-run` to inspect the planned run without OpenAI calls, or add the relevant explicit approval flag only when a live run is intended:

```powershell
docker compose run --rm api python scripts/run_retrieval_experiments.py --allow-external-embeddings
docker compose run --rm api python scripts/run_answer_quality_eval.py --allow-external-ai
docker compose run --rm api python scripts/run_multi_doc_eval.py --allow-external-ai
```

## Reset

To reset local database state, stop the stack and remove the Postgres volume:

```powershell
docker compose down -v
```

Then start the stack and rerun setup and ingestion.
