# Phase 56 Decision Gate: Production Identity And Tenancy

Phase 55 is complete. No Phase 56 implementation is authorized until the following production choices are explicit.

## Decisions required

1. **Identity provider and hosting context**
   - Name the OIDC provider (for example, Microsoft Entra ID) and where the web/API workloads will run.
   - State the expected issuer, audience/application registration ownership, and whether conditional access is provider-managed.

2. **Tenant and data ownership model**
   - Define what a tenant represents and which entity owns projects, departments, uploads, chats, reviews, feedback, audit events, and evaluations.
   - Decide whether a user may belong to more than one tenant and how a tenant is selected per session/request.

3. **Seeded demo data boundary**
   - Choose whether `Northstar Analytics` remains available only in an isolated demo deployment, becomes a dedicated demo tenant, or is removed from production migrations.

4. **Session and authentication assurance**
   - Specify maximum and idle session duration, MFA expectations, conditional-access expectations, step-up requirements, and whether refresh tokens are server-held.

5. **Provisioning, revocation, and offboarding**
   - Choose just-in-time versus administrator/SCIM provisioning, role/membership ownership, revocation timing, offboarding behavior, and retention/deletion expectations.

## Boundary while pending

- Local demo identity remains explicitly non-production.
- No OIDC provider, tenant semantics, migration strategy, MFA/session policy, or offboarding workflow is inferred.
- Phase 57 database authorization cannot be designed honestly until tenant ownership and membership rules are fixed.
- The Phase 55 sealed holdout remains unexecuted and supports no new generalization claim.
