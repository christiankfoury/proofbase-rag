# Phase 56: OIDC Identity And Tenant Model

## User-approved decisions

- A tenant represents one customer organization and owns projects, departments, uploaded knowledge, chats, reviews, feedback, audit events, and tenant-scoped evaluations.
- Platform benchmark definitions and global regression evidence remain platform-owned.
- Users may belong to multiple tenants; every request selects one tenant and must prove an active membership.
- Northstar Analytics is isolated in the `northstar-demo` tenant and remains a demo/development fixture, not production migration data.
- Sessions have an eight-hour absolute limit and a 30-minute idle limit. Refresh tokens, when a hosted provider is connected, are server-held.
- Production policy expects provider MFA and conditional access, with step-up authentication for tenant administration and sensitive exports.
- Provisioning is administrator/invitation-led. JIT is limited to pre-authorized memberships; SCIM remains a future adapter.
- Membership removal or user disablement revokes active sessions immediately. Historical records retain immutable actor IDs while profile data is minimized.
- Microsoft Entra ID is the optional future provider behind the provider-neutral OIDC boundary. No provider or cloud resource was connected in this phase.

## Local implementation

The API now separates three identity modes:

- `local_demo`: the existing portfolio selector, allowed only outside production.
- `oidc_fixture`: strict locally signed bearer-token fixtures for integration tests.
- `oidc`: the hosted-provider boundary. It fails closed until a real provider adapter is connected and verified.

The local fixture verifier checks signature, algorithm, issuer, audience, subject, issued-at, expiry, not-before, optional nonce, token age, and revocation. Authorization transactions produce high-entropy state and nonce values and persist only hashes. The session contract uses HTTP-only, secure-in-production, same-site cookies with CSRF validation when a cookie-backed hosted flow is added.

`APP_ENVIRONMENT=production` rejects `local_demo` and `oidc_fixture`. Demo identity headers are rejected outside demo mode. A verified token does not grant tenant access by itself: the selected `X-Tenant-Id` must be present in the token and map to an active internal tenant membership.

## Data model

Phase 56 adds tenants, tenant memberships, external issuer/subject identities, server session metadata, authorization transactions, and token revocations. Tenant ownership is added and backfilled for projects, departments, project memberships, documents, versions, ingestion jobs, chunks, embeddings, chats, feedback, and audit events. Evaluation rows accept nullable tenant ownership so global platform benchmarks remain distinct from tenant-owned evaluation data.

All existing Northstar application rows are backfilled to the dedicated demo tenant. New projects are created inside the authenticated tenant and grant the creator an owner project membership. New uploaded-document, chunk, chat, feedback, and audit rows carry the active tenant ID.

## Offboarding boundary

The identity store can atomically disable a tenant membership and revoke that user’s active server sessions. Privilege changes have a separate session-revocation operation so stale authorization is not retained. Tenant content is not deleted merely because one user leaves; tenant retention policy governs content lifecycle.

## Honest limitations

- No live Entra ID or other hosted OIDC provider is connected.
- The local fixture uses HS256 exclusively for deterministic tests; it is not a hosted-provider signing configuration.
- MFA, conditional access, step-up, token exchange, refresh-token encryption, and provider logout cannot be claimed until a hosted provider is connected end to end.
- Database row-level enforcement is Phase 57. Phase 56 establishes tenant ownership and request identity but does not claim that application filters alone provide database isolation.
- No Azure resources, paid services, premium licences, or Marketplace products were created.
