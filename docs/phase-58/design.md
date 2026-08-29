# Phase 58: Rate Limiting, Quotas, And Cost Abuse Controls

## Outcome

Proofbase now has one provider-neutral abuse-control contract for identity, tenant, direct client-IP risk context, operation, concurrency, and external-AI admission budgets. The contract has a process-local development backend and an atomic Redis backend verified against the free local Redis 7 Compose service.

## Enforced operations

Named policies cover pre-authentication requests, chat sessions, chat, streaming, feedback, upload, AI Markdown cleanup, embedding/indexing, evaluation review writes, and administrative mutations. Authentication is limited before identity resolution. Privileged operation quotas run only after membership/role authorization, so an unauthorized user cannot consume an editor or owner quota.

Chat and streaming reserve a conservative tenant external-AI amount before any semantic assessment, embedding, or generation call. Cleanup and indexing reserve their own admission amount before the external operation. A denied admission returns a generic `429` plus `Retry-After`; it does not reveal bucket capacity and does not call retrieval, generation, cleanup, embedding, or indexing work.

Streaming and indexing use expiring concurrency leases. External AI clients cap automatic retries. Request declarations, questions, conversations, uploads, review Markdown, feedback, and collection counts have explicit bounds. Repeated denial audit records are suppressed to one bounded event per tenant/user/operation/minute.

## Shared-store design

Redis fixed-window admission and sorted-set concurrency operations execute atomically with Lua scripts. Keys contain only a versioned scope, an opaque SHA-256-derived identifier, and a bounded operation name; tenant IDs, user IDs, and client addresses are not present in Redis keys.

The local Compose service is ephemeral, memory-bounded, and has no cloud dependency. Normal direct Python development defaults to the explicitly non-distributed memory backend. Production configuration rejects that backend and requires Redis or a separately reviewed shared-store adapter.

## Honest limitations

- No managed Redis, TLS/authenticated Redis endpoint, high availability, provider monitoring, or capacity test is connected.
- Direct client socket addresses are used as IP risk context. A production trusted-proxy/header policy remains deployment work.
- AI admission uses conservative reserved cost rather than provider-billing reconciliation. Per-operation production budgets, replenishment policy, and alert ownership remain deployment/Phase 61 decisions.
- The application rejects an oversized declared `Content-Length` and bounds parsed route payloads. A reverse-proxy/server streaming byte cap is still required for chunked-body protection in a hosted deployment.
- CLI evaluation runners retain their explicit approval and dollar-budget gates; they are not a multi-user API surface and do not claim shared Redis quota enforcement.
- No Azure resource, paid service, premium licence, Marketplace purchase, or managed cache was created.
