# Phase 14 Smoke Test Results

## Implemented Smoke Test

Script:

```powershell
python scripts/run_smoke_test.py
```

Docker command:

```powershell
docker compose run --rm api python scripts/run_smoke_test.py --api-base-url http://api:8000
```

The script verifies:

- API `/health` returns `status: ok`.
- API `/ready` returns `status: ready`.
- Postgres contains at least one document and one chunk after ingestion.
- A normal query returns `response_type`, `answer`, `citations`, and `final_confidence`.
- A restricted Employee query refuses the promotion calibration question.
- Permission check reports no unauthorized chunks reached generation.

## Latest Verification Status

Verified on: 2026-06-06

Environment:

- Local Docker Compose stack on Windows.
- API exposed at `http://localhost:8000`.
- Dashboard exposed at `http://localhost:3001` because host port `3000` was already in use.
- Existing local Postgres Docker volume contained previously ingested data.

Commands run:

```powershell
python -m compileall apps scripts
docker compose config
docker compose build
docker compose up -d
docker compose run --rm api python scripts/setup_db.py
docker compose run --rm api python scripts/run_smoke_test.py --api-base-url http://api:8000 --skip-query
```

Results:

- Python compile check: passed.
- Docker Compose config: passed.
- Docker image build: passed for API and web.
- API container health: healthy.
- Postgres container health: healthy.
- Web container health: healthy.
- `GET /health`: passed.
- `GET /ready`: passed.
- Setup DB: passed; pgvector enabled, required tables present.
- DB content check: passed; 14 documents and 160 chunks present.
- Dashboard load check: passed with HTTP 200 on `http://localhost:3001`.
- Query checks: skipped in this run.

Skipped checks:

- `scripts/ingest_markdown.py` was not rerun because it sends document contents to the external OpenAI embeddings API.
- Full smoke query checks were skipped because `/query` sends prompt/context to the external OpenAI API.
- Full evaluation scripts were not run for the same OpenAI-backed model-call reason.

Non-cloud verification should record:

- Timestamp.
- Command run.
- Whether `OPENAI_API_KEY` was configured.
- Pass/fail result.
- Any skipped OpenAI-backed checks.

No Azure deployment, uptime, or performance claims are made in this file.
