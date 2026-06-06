# Phase 14 Health Checks

## API Liveness

Endpoint:

```text
GET /health
```

Expected response:

```json
{
  "status": "ok"
}
```

This confirms the FastAPI process is running. It does not check the database.

## API Readiness

Endpoint:

```text
GET /ready
```

Ready response:

```json
{
  "status": "ready",
  "database": "connected",
  "schema": "ok",
  "pgvector": "enabled",
  "document_count": 0,
  "chunk_count": 0
}
```

`document_count` and `chunk_count` may be zero before ingestion. After the demo ingestion command, both should be greater than zero.

Not-ready responses use HTTP `503` and include a structured reason such as missing tables, missing pgvector, or database unavailable.

## Docker Health Checks

- Postgres uses `pg_isready`.
- API uses `/health`.
- Web checks that `http://127.0.0.1:3000` responds.

## Manual Verification

```powershell
Invoke-WebRequest http://localhost:8000/health -UseBasicParsing
Invoke-WebRequest http://localhost:8000/ready -UseBasicParsing
```

Open the dashboard at:

```text
http://localhost:3000
```
