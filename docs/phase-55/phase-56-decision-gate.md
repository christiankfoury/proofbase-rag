# Phase 56 Decision Gate: OIDC Identity And Tenancy

Phase 55 is complete. Phase 56 may proceed locally after the product/data decisions below are explicit. A live identity provider or Azure deployment is not required for the portfolio implementation.

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

## Boundary while pending

- Local demo identity and signed-token fixtures remain explicitly non-production.
- No tenant semantics, migration strategy, MFA/session policy, or offboarding workflow is inferred.
- Phase 57 database authorization cannot be designed honestly until tenant ownership and membership rules are fixed.
- No Azure resource, paid service, Marketplace product, or premium licence may be created from this decision gate.
- The Phase 55 sealed holdout remains unexecuted and supports no new generalization claim.
