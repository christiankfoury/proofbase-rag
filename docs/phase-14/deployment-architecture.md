# Phase 14 Deployment Architecture

## Local Architecture

The local deployment uses Docker Compose:

- `postgres`: PostgreSQL 16 with pgvector extension support.
- `api`: FastAPI service that handles retrieval, generation, ingestion scripts, evaluation scripts, feedback, audit events, and observability summaries.
- `web`: Next.js service that reads API endpoints for dashboard, feedback, audit, and observability views.

The API connects to Postgres with `DATABASE_URL`. The web app connects to the API with `NEXT_PUBLIC_API_BASE_URL`.

## Azure-Ready Target Architecture

This project is Azure-ready, not deployed to Azure yet.

Recommended target services:

- Azure Container Registry for API and web images.
- Azure Container Apps for the API container.
- Azure Container Apps or Azure App Service for the web container.
- Azure Database for PostgreSQL for persisted application data, with pgvector enabled where supported.
- Azure Key Vault or Container Apps secrets for `OPENAI_API_KEY` and database credentials.
- Azure Blob Storage as a future target for raw document storage and durable observability/audit archives.

## Runtime Flow

1. Reviewer opens the Next.js dashboard.
2. Dashboard server components call the FastAPI API.
3. API reads evaluation data from the repository-mounted `data/` files and live state from Postgres.
4. `/query` retrieves permitted chunks from Postgres and calls OpenAI for embeddings or generation when needed.
5. Request observability is written to JSONL. Audit, feedback, memory, documents, chunks, and embeddings are stored in Postgres.

## Deployment Boundaries

Phase 14 does not add production authentication, Azure AI Search, production SSO, cloud deployment automation, or real Azure uptime claims.
