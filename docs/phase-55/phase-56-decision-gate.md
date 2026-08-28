# Phase 56 Decision Gate: OIDC Identity And Tenancy

Phase 55 is complete. The user approved the decision package on 2026-08-28, and Phase 56 proceeded locally. A live identity provider or Azure deployment is not required for the portfolio implementation.

## Approved decision record

- Tenant: one customer organization owning its projects and tenant-scoped data; global benchmark definitions remain platform-owned.
- Membership: multi-tenant users with one explicitly selected tenant per request/session.
- Demo data: Northstar remains in a dedicated demo-only tenant and is excluded from production migrations by default.
- Session: eight-hour absolute and 30-minute idle limits, server-held refresh tokens, provider MFA/conditional access, and step-up for sensitive administration/exports.
- Provisioning: administrator/invitation-led, pre-authorized JIT only, future SCIM adapter, immediate access/session revocation on offboarding, immutable historical actor IDs, and tenant-policy content retention.
- Provider boundary: provider-neutral OIDC locally; Microsoft Entra ID is the optional future target. No live integration was authorized.

## Decisions required

1. **Authentication boundary**
   - Use provider-neutral OIDC with local signed-token fixtures by default.
   - Optionally name a future provider such as Microsoft Entra ID; do not provision it as part of this decision.
   - Keep issuer, audience, claim mapping, and provider configuration explicit and production-safe.

2. **Tenant and data ownership model**
   - Define what a tenant represents and which entity owns projects, departments, uploads, chats, reviews, feedback, audit events, and evaluations.
   - Decide whether a user may belong to more than one tenant and how a tenant is selected per session/request.

3. **Seeded demo data boundary**
   - Choose whether `Northstar Analytics` remains available only in an isolated demo deployment, becomes a dedicated demo tenant, or is removed from production migrations.

4. **Session and authentication assurance**
   - Specify maximum and idle session duration, MFA expectations, conditional-access expectations, step-up requirements, and whether refresh tokens are server-held.

5. **Provisioning, revocation, and offboarding**
   - Choose just-in-time versus administrator/SCIM provisioning, role/membership ownership, revocation timing, offboarding behavior, and retention/deletion expectations.

## Financial-safety gate for optional cloud work

Cloud provisioning requires a separate explicit approval after documenting the subscription/spending-limit behavior, cost model, allowed services/SKUs, quotas, manual deployment, expiration, automatic teardown, cleanup verification, budget alerts, Marketplace exclusions, and separate external-AI limits. Without that approval, implementation remains local and infrastructure-as-code remains undeployed.

## Boundary after approval

- Local demo identity and signed-token fixtures remain explicitly non-production.
- Tenant semantics, migration strategy, session policy, and offboarding behavior are recorded above and implemented locally in Phase 56.
- Phase 57 may implement database authorization against the approved ownership and membership rules.
- No Azure resource, paid service, Marketplace product, or premium licence may be created from this decision gate.
- The Phase 55 sealed holdout remains unexecuted and supports no new generalization claim.
