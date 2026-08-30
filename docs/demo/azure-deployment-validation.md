# Temporary Azure Deployment Validation

Date: 2026-08-30

Proofbase was manually deployed as a temporary demonstration environment using the exact application revision represented by image tag `38667f0`.

## Validated topology

- Azure Container Registry stored separate API and web images.
- Azure Database for PostgreSQL Flexible Server 16 hosted the application schema and pgvector extension.
- Azure Container Apps hosted the FastAPI API and Next.js web application in one environment.
- Managed identity with `AcrPull` provided image access without enabling registry admin credentials.
- The web container used port `3000`; the API container used port `8000`.

## Observed results

- API `/health`: HTTP `200` with `{"status":"ok"}`.
- API `/ready`: HTTP `200` with database connected, schema valid, and pgvector enabled.
- Synthetic ingestion: `19` documents, `119` chunks, `119` embeddings, and `0` failures.
- The web application loaded successfully and completed an application-to-API query flow.

## Claim boundary

This was a manually validated, temporary demonstration deployment. It does not change the Phase 63 production decision. Hosted OIDC, external monitoring and on-call ownership, hosted malware scanning, production availability evidence, human release review, and independent penetration testing remain external requirements. Resource tags record a planned deletion date, but Azure tags do not perform automatic teardown.

No tenant IDs, subscription IDs, credentials, public IP addresses, database passwords, API keys, or resource hostnames are recorded here.
