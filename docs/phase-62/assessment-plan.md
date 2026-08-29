# Security Assessment Plan And Rules Of Engagement

Status: preparation complete; **Independent validation required** before any external-assessment claim.

## Authorized scope

- Browser UI, FastAPI endpoints, tenant selection, OIDC adapter boundary, PostgreSQL/RLS, Redis limiter contract, upload/quarantine/parser workflow, external-AI boundary, admin routes, security events, Docker images, and repository build/dependency configuration.
- Use a disposable, isolated test environment with synthetic data only. Production, personal accounts, third-party tenants, provider control planes, and any Azure subscription are out of scope unless separately authorized in writing.

## Test identities and data

- At least two customer-organization tenants, each with owner, admin, contributor/editor, viewer/member, and no-membership identities.
- Cross-product pairs must cover read, create, update, archive/delete, upload, approve/index, query, citation, audit, monitoring, and signed-file access.
- Use only generated PDFs, harmless scanner fixtures, synthetic prompts, and synthetic corpus content. No live credential, malware, employee/customer data, regulated data, or destructive payload is permitted.

## Permitted techniques

- authenticated and unauthenticated route enumeration; object/function authorization tests; token claim, expiry, revocation, and tenant-switch tests
- bounded input, upload, parser-timeout, request-rate, concurrency, and cost-admission tests within preapproved limits
- SAST, dependency/SBOM, container, DAST, configuration, source-injection, memory-poisoning, citation-suppression, and safe prompt-injection tests
- read-only cloud/provider configuration review only after the relevant external integration and access are separately approved

## Prohibited without new written approval

- phishing, social engineering, credential stuffing with real identities, persistence, destructive deletion, denial-of-service, data extraction, live malware, third-party scanning, or testing outside the named host/accounts
- creating Azure resources, paid services, premium licences, Marketplace purchases, or increasing provider quotas
- opening, rerunning, selectively sampling, or tuning against Phase 47-49 or other sealed holdouts outside an approved release protocol

## Safety and stop conditions

Stop immediately on suspected cross-tenant content disclosure, credential exposure, service instability, unexpected external cost, access beyond the approved environment, or evidence that test data is not synthetic. Preserve content-free evidence, revoke test sessions, close AI admission, and contact the incident commander.

## Contacts and schedule gate

The assessment owner, qualified independent assessor, incident commander, privacy/legal contact, tenant-notification authority, test hosts, dates, source IPs, concurrency ceiling, cost ceiling, and emergency channel are all **unassigned**. They must be completed and explicitly approved before optional independent testing begins.

## Deliverables

A valid independent engagement produces a signed scope/authorization, methodology, evidence-backed report, severity and affected-control mapping, triaged disposition, remediation evidence, and independent retest of critical/high findings. Public disclosure is limited to approved date, scope, disposition summary, and limitations.
