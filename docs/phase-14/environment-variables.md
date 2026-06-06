# Phase 14 Environment Variables

## API

| Variable | Required | Example | Notes |
|---|---|---|---|
| `DATABASE_URL` | Yes | `postgresql://postgres:postgres@postgres:5432/enterprise_knowledge_agent` | Postgres connection string. Use `localhost` outside Docker and `postgres` inside Compose. |
| `OPENAI_API_KEY` | Yes for ingestion/query/evals | `sk-...` | Never commit real secrets. |
| `OPENAI_MODEL` | No | `gpt-4.1-mini` | Supported alias for chat model configuration. |
| `OPENAI_CHAT_MODEL` | No | `gpt-4.1-mini` | Backward-compatible chat model variable. Takes precedence over `OPENAI_MODEL`. |
| `OPENAI_EMBEDDING_MODEL` | No | `text-embedding-3-small` | Must match embedding dimensionality used by schema. |
| `DEFAULT_TOP_K` | No | `5` | Default retrieval count. |
| `LOG_LEVEL` | No | `INFO` | Reserved for runtime logging configuration. |
| `OBSERVABILITY_LOG_PATH` | No | `data/observability/request-logs.jsonl` | API request log path. Relative paths resolve from repo root. |
| `AUDIT_LOG_PATH` | No | `data/audit/audit-events.jsonl` | Reserved for future JSONL audit export; current audit events persist in Postgres. |
| `API_PORT` | No | `8000` | Docker Compose host port for the API. |

## Web

| Variable | Required | Example | Notes |
|---|---|---|---|
| `NEXT_PUBLIC_API_BASE_URL` | Yes | `http://localhost:8000` | Use `http://api:8000` inside Docker Compose. |
| `WEB_PORT` | No | `3000` | Docker Compose host port for the dashboard. |

## Local Files

- Root `.env.example`: shared Docker/local defaults.
- `apps/api/.env.example`: API-specific defaults.
- `apps/web/.env.example`: frontend-specific defaults.

Real `.env` files are local only and must not be committed.
