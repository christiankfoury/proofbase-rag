# Phase 14 Azure Readiness Plan

## Status

The project is Azure-ready. It has not been deployed to Azure in Phase 14.

## Deployment Targets

| Concern | Azure Target |
|---|---|
| Container images | Azure Container Registry |
| Backend API | Azure Container Apps or Azure App Service |
| Frontend dashboard | Azure Container Apps, Azure App Service, or Azure Static Web Apps if adapted |
| Database | Azure Database for PostgreSQL with pgvector support where available |
| Secrets | Azure Key Vault or Container Apps secrets |
| Raw document storage | Azure Blob Storage, future work |
| Logs | Container logs plus durable JSONL/blob export, future work |

## Production Configuration Checklist

- Store `OPENAI_API_KEY` and database credentials outside images.
- Use HTTPS-only public ingress.
- Restrict CORS and frontend origins to the deployed dashboard domain.
- Use a production database connection string with TLS.
- Add connection pooling before higher traffic demos.
- Persist audit logs and observability logs outside ephemeral container storage.
- Configure health probe to `/health`.
- Configure readiness probe to `/ready`.
- Set per-container CPU and memory limits.
- Configure scale min/max values for API and web containers.
- Configure OpenAI rate-limit handling and request timeout policy.
- Keep benchmark documents synthetic; do not upload real employee data.

## Suggested Deployment Sequence

1. Build API and web images locally or in CI.
2. Push images to Azure Container Registry.
3. Provision Azure Database for PostgreSQL and enable pgvector.
4. Run schema setup against the Azure database.
5. Configure API secrets and environment variables.
6. Deploy API container and verify `/health` and `/ready`.
7. Deploy web container with `NEXT_PUBLIC_API_BASE_URL` pointing to the API URL.
8. Run ingestion against the Azure database.
9. Run smoke test against the deployed API.
10. Export dashboard data and verify the dashboard.

## Not Included in Phase 14

- Live Azure deployment.
- Production authentication.
- Azure AI Search.
- Cloud storage migration.
- Managed identity implementation.
- Uptime or load-testing claims.
