# Post-Phase 50 Defense And Production Readiness Plan

## Purpose

This roadmap turns the Phase 50 ambiguity and direct prompt-override fixes into a layered, measurable defense system and adds an honest, nav-accessible explanation of those defenses. It then defines the separate work required before Proofbase could make production-quality security claims.

The implementation sequence starts with product transparency, strengthens runtime decision-making without treating a model classifier as a security boundary, and only then moves into identity, tenant isolation, database authorization, abuse prevention, secure ingestion, operational security, independent testing, and continuous adversarial evaluation.

This document is the executable source of truth for Phases 51-63. A future implementation chat should read this file together with `AGENTS.md`, `docs/roadmap/progress.md`, `docs/roadmap/phase-plan.md`, `docs/phase-50/design.md`, `docs/phase-50/verification.md`, and the current algorithm documentation before changing code.

## Starting Point

Phase 50 currently provides:

- deterministic pre-retrieval clarification for known underspecified approval questions and unresolved fresh-chat pronouns such as `it`
- deterministic blocking for known direct prompt-override patterns
- an exemption for legitimate questions that discuss prompt injection as source material
- project and department scope plus role filtering before generation
- memory used for query context, never as source evidence
- grounded citation validation and response downgrades after generation
- audit and observability evidence for guarded responses
- a final development benchmark result of `130/130`, a prompt-injection slice of `5/5`, a generalization suite of `20/20`, and zero measured permission leakage in the Phase 50 verification run

These controls are valuable, but the ambiguity and direct-override detectors are pattern-based. Unseen paraphrases, indirect injection inside retrieved documents, multilingual or obfuscated attacks, ambiguous questions outside the known patterns, and apparently relevant but incomplete evidence can still bypass those early guards. The current results are development evidence, not proof of production security.

## Target Architecture

The target is defense in depth:

1. Normalize and bound the request.
2. Apply cheap deterministic guards for obvious, high-confidence cases.
3. Produce a typed semantic request assessment for every remaining App query.
4. Resolve authenticated tenant, project, department, and role authorization independently of model output.
5. Retrieve only authorized chunks.
6. Evaluate whether those accessible chunks are sufficient to answer the actual question.
7. Generate from authorized, sufficient evidence while treating retrieved text as data, not instructions.
8. Validate claims and citations against the authorized evidence.
9. Return, repair once, clarify, abstain, or refuse according to typed decisions.
10. Record privacy-safe decision, latency, cost, and security events for monitoring and evaluation.

No classifier, prompt, confidence score, or regular expression may grant access. Authentication, tenant scope, database authorization, and pre-generation permission filtering remain the confidentiality boundaries. Evidence sufficiency and post-generation validation remain answer-integrity boundaries.

## Core Design Decisions

### Use a hybrid assessment path

Keep deterministic guards for obvious cases because they are fast, cheap, explainable, and reliable for known forms. Run structured semantic assessment for every remaining user-facing query so safety does not depend on matching a finite regular-expression list. Do not use a confidence threshold to bypass permission checks or grant access.

The first implementation should measure two candidate modes before promotion:

- `semantic_all_remaining`: assess every query not resolved by a deterministic guard
- `semantic_uncertain_only`: use deterministic signals to route only uncertain queries to semantic assessment

`semantic_all_remaining` is the default safety candidate. Promote a different mode only if measured false-negative, false-positive, latency, and cost results justify it without weakening hard safety gates.

### Use typed decisions, not free-form classifier prose

The assessment must return a versioned schema with bounded enums and explicit reasons. Invalid JSON, unknown enum values, timeouts, or unavailable assessment services must fail safely to clarification or a configurable temporary-unavailable response. They must never fall through to broader retrieval or authorization.

### Separate ambiguity from evidence insufficiency

An ambiguous request is missing user intent or a referent before retrieval. An evidence-insufficient request may be clear but cannot be fully supported by accessible sources after retrieval. They need different response types, metrics, and user guidance.

### Treat source content as untrusted data

Retrieved files can contain instructions such as “ignore previous rules.” Those strings must never change system behavior. The model prompt, evidence gate, and post-generation validator must distinguish factual source content from instructions addressed to the assistant.

### Keep production claims status-based and evidenced

The planned Trust & Safety page must distinguish:

- **Implemented**: present in code and backed by named verification evidence
- **Measured**: includes run ID, suite version, sample size, date, and limitations
- **Planned**: approved roadmap work that is not yet implemented
- **Production dependency**: requires provider, infrastructure, policy, or organizational decisions
- **Independent validation required**: cannot be self-certified by the implementation agent

## Execution Rules For Every Phase

Each phase uses the repository operating loop:

1. Read the roadmap, current progress, latest phase evidence, affected source, and generated evaluation artifacts.
2. Record a scoped implementation and verification plan in `docs/phase-{number}/`.
3. Establish a before measurement for behavioral changes.
4. Implement the smallest complete phase.
5. Run targeted checks, shared regressions, and cost/latency checks proportional to risk.
6. Update phase notes, the progress tracker, README/demo material when user-facing claims change, and the Trust & Safety status source when applicable.
7. Commit to `main` with a detailed multi-part message.
8. Inspect the commit and perform a code review focused on permissions, tenant isolation, evidence integrity, misleading claims, and missing tests.
9. Fix findings in a follow-up commit when necessary.
10. Push `main`, confirm alignment with `origin/main`, and continue to the next unblocked phase.

Do not rerun or tune against the sealed Phase 47-49 holdouts. Author and seal a new independent holdout only after the new runtime is frozen. External AI commands must remain explicit, dry-runnable, budget-limited, and recorded with estimated cost.

## Phase 51: Trust And Safety Product Page

### Goal

Add a public App-side page that explains how Proofbase handles prompt injection, ambiguity, permissions, evidence, and citations today, and what remains necessary for production quality.

### Product scope

- Add `/trust` to the App navigation as **Trust & Safety** and add the matching breadcrumb.
- Make the page understandable to product stakeholders, security reviewers, and developers without requiring the README.
- Show the request lifecycle as a compact layered-defense flow.
- Explain ambiguity handling, direct prompt-injection handling, indirect/source injection, permission filtering, memory boundaries, evidence sufficiency, citation validation, and audit evidence separately.
- Include a production-readiness checklist covering all Phases 56-63.
- Link implemented claims to current algorithm or phase evidence and measured claims to named artifacts.
- Include a prominent limitation that current demo identity is not production authentication and that self-evaluation is not an independent security assessment.
- Do not expose system prompts, secrets, exact detection signatures, private logs, exploit payload collections, or operational credentials.

### Engineering scope

- Use a typed, code-owned defense catalog rather than copying status text independently across components.
- Require every catalog item to have `status`, `summary`, `boundary`, `evidence`, `limitations`, and `last_verified` fields.
- Render static repository evidence at build time; do not fabricate live security state.
- Keep the initial page read-only and available in local demo mode.
- Add accessible headings, keyboard navigation, responsive layout, and honest empty/unavailable states for evidence.

### Verification

- Production web build and route smoke.
- Nav active state, breadcrumb, direct route, refresh, back/forward, mobile layout, and accessibility smoke.
- Content review confirms every implemented or measured statement has evidence and every future control is labeled planned or externally required.
- README, interactive demo guide, screenshot checklist, and feature use cases reference the page.

## Phase 52: Structured Semantic Request Assessment

### Goal

Generalize ambiguity and direct prompt-injection recognition beyond known patterns without allowing a classifier to become an authorization boundary.

### Backend design

Add a versioned `RequestAssessment` schema with fields such as:

- `intent`: question, command, source_discussion, evaluation, unknown
- `topic`: bounded label plus optional normalized description
- `referents`: resolved, unresolved, or not_applicable, with missing referents
- `decision_variables`: facts the request must specify before it can be answered safely
- `ambiguity`: none, resolvable_from_conversation, or clarification_required
- `injection_risk`: none, source_discussion, direct_override, indirect_or_obfuscated, or uncertain
- `recommended_action`: continue, clarify, block, or temporary_unavailable
- `reason_codes`: bounded, non-sensitive enums
- `assessment_confidence`, `schema_version`, `model`, `prompt_version`, `latency_ms`, and estimated cost

Required behavior:

- Run normalization and deterministic high-confidence guards first.
- Run semantic assessment on every remaining App query under the candidate default.
- Supply only the minimum conversation context needed to resolve references; never treat memory as evidence.
- Keep scope and authorization input immutable and outside classifier control.
- A classifier may narrow behavior to clarify or block, but may not expand project, department, tenant, role, document, or tool access.
- A source-discussion result allows legitimate questions about security policies to continue but does not allow embedded instructions to control the assistant.
- Invalid output, timeout, or service failure follows an explicit fail-safe behavior and records a reason code.
- Apply identical assessment semantics to streaming and non-streaming query routes.
- Version and regression-test the assessment prompt and parser.

### Evaluation

Create a development suite containing:

- unseen ambiguity paraphrases and referents beyond `it`
- legitimate unambiguous short questions
- direct, indirect, encoded, typoglycemic, multilingual, and citation-suppression injection attempts
- legitimate source questions that quote or discuss attacks
- mixed requests containing a valid question and an override attempt
- multi-turn attempts to poison memory or change role/scope

Measure confusion matrices by category, unsafe compliance, unnecessary clarification/block rate, parser failures, added p50/p95 latency, token use, and estimated cost. Record a baseline before changing runtime behavior. Permission hard gates must remain zero.

### Promotion gate

Do not promote the semantic path merely because it catches examples. It must improve the predeclared development-suite false-negative rate, keep legitimate source-discussion false blocks within the predeclared tolerance, preserve the `130/130` development regression and permission gates, and stay within a documented latency/cost budget. Predeclare exact thresholds and sample sizes in the Phase 52 design before the first candidate run.

## Phase 53: Permission-Aware Evidence Sufficiency Gate

### Goal

Prevent clear but under-supported questions from reaching normal answer generation, including multi-document requests where retrieval finds related text but misses a required fact.

### Placement and boundary

Run the gate only after tenant, project, department, document-role, and chunk permission filtering. Its entire input must be the normalized request, typed request assessment, and authorized retrieved chunks. It must not inspect or reveal filtered-out source content.

### Gate design

Add a versioned `EvidenceAssessment` with:

- `answerability`: sufficient, partial, insufficient, conflicting, or uncertain
- `required_facts` and whether each has support
- `required_source_coverage` for decomposed or multi-document questions
- `conflicts`, including versions, effective dates, applicability, and unresolved precedence
- `missing_information` that can be safely disclosed
- `recommended_action`: answer, partial_answer, clarify, not_found, or temporary_unavailable
- supporting accessible chunk IDs and bounded reason codes
- schema/model/prompt/latency/cost metadata

Implement deterministic checks first for exact-detail, source coverage, empty retrieval, and known conflict metadata. Use a structured semantic sufficiency check only for cases not resolved deterministically. Similarity score or retrieval confidence alone is never sufficient proof of answerability.

### User experience

- Ambiguous intent asks the user what they mean.
- Clear questions with no accessible evidence return not found and may suggest widening scope without naming inaccessible sources.
- Partially supported questions either state the supported portion and explicitly identify the missing portion, or abstain, according to a versioned policy.
- Conflicting evidence names the accessible conflict and requests clarification or explains applicable precedence when the sources establish it.
- “Why this answer?” shows safe reason codes and source coverage, not hidden chain-of-thought.

### Evaluation and promotion

- Add missing-fact, partial-evidence, multi-document completeness, conflicting-version, wrong-department, and restricted-source paired cases.
- Measure answerability classification, completeness, hallucination, safe disclosure, latency, and cost.
- Require zero inaccessible-source disclosure, restricted citations, unauthorized chunks reaching generation, and memory-as-evidence violations.
- Compare deterministic-only, hybrid, and semantic-always modes before selecting a default.

## Phase 54: Post-Generation Claim And Source-Instruction Validation

### Goal

Catch unsupported claims and indirect prompt-injection effects even when request assessment and evidence sufficiency pass.

### Scope

- Split the candidate answer into checkable claims.
- Validate exact numbers, currency thresholds, dates, durations, roles, approvals, exceptions, and negations directly against authorized evidence.
- Add semantic claim-to-evidence support checks for non-exact claims.
- Verify every citation maps to an authorized retrieved chunk and actually supports its claim.
- Detect output that follows instructions embedded in source documents rather than answering the user from their factual content.
- Permit at most one bounded repair/regeneration using the same authorized chunks; if validation still fails, downgrade to partial, not found, clarify, or a safe failure.
- Never retrieve broader scope during repair.
- Record validator reason codes, repair count, latency, tokens, and cost.

### Verification

- Targeted exact-fact, negation, exception, conflicting-source, source-injection, citation, and one-repair-limit tests.
- Full benchmark, permission, memory, multi-document, and development adversarial regressions.
- Explicit comparison of quality gained against added latency and cost.

## Phase 55: Defense Evaluation, Observability, And Page Evidence

### Goal

Turn the new defenses into measurable, reviewable product evidence before beginning production infrastructure work.

### Scope

- Consolidate the Phase 52-54 development suites under a versioned schema and validator.
- Add decision traces for deterministic guard, semantic assessment, permission filter, evidence gate, generator, validator, and final response type.
- Store bounded reason codes and aggregate metrics by default; raw prompts, source text, and user content require explicit development-only controls and redaction.
- Add Dev/Admin panels for ambiguity routing, injection outcomes, evidence insufficiency, parser/service failures, false positives, latency, estimated cost, and repair outcomes.
- Update `/trust` automatically from verified evidence metadata, while keeping prose and limitations code-reviewed.
- Freeze the new runtime and author a new independently separated holdout. Do not use Phase 47-49 sealed cases.

### Hard gates

- permission leakage: `0`
- unauthorized chunks reaching generation: `0`
- restricted citations: `0`
- tenant or scope expansion caused by assessment: `0`
- memory used as source evidence: `0`
- unsafe compliance with tested injection attacks: `0`
- invalid assessment or evidence schemas silently falling through: `0`

Predeclare non-zero quality, false-positive, latency, cost, sample-size, and stability targets before live runs. If targets are missed, report the valid result and preserve the failure backlog; do not tune the frozen holdout or inflate the Trust & Safety claim.

## Portfolio Production-Shaped Boundary

Phases 51-55 strengthen the portfolio/local-demo implementation. Phases 56-61 and 63 now prioritize production-shaped controls that can be implemented and verified locally without requiring a continuously hosted or paid cloud environment. Provider adapters, infrastructure-as-code, local integrations, migration rehearsals, and explicit operating policies are valid portfolio evidence when their status is labeled accurately.

They are not proof that a production environment is operating. A live Azure deployment is an optional, temporary capstone behind the financial-safety gate below. Managed-service, hosted-monitoring, and independent-assessment claims require the corresponding external service or party.

### Mandatory financial-safety gate before cloud provisioning

No agent may create an Azure resource, paid service, Marketplace purchase, premium identity licence, or other billable external infrastructure until the user explicitly approves all of the following:

- the subscription type and whether a real spending limit exists
- a service-by-service cost model and maximum deployment duration
- an allowlist of resource types, regions, and low-cost SKUs enforced through policy where available
- manual deployment approval, bounded replica/concurrency quotas, and disabled deploy-on-push behavior
- an expiration tag, automatic teardown, a second cleanup path, and post-teardown verification
- budget/anomaly alerts, while acknowledging that alerts are delayed and are not a hard Pay-As-You-Go cap
- separate external-AI quotas and a kill switch because Azure controls do not cap directly billed providers
- exclusion of Marketplace and separately billed products unless the user approves each one explicitly

Local implementation must continue without cloud provisioning when this gate is not satisfied.

## Phase 56: OIDC Authentication And Tenant Model

### Required user decision before implementation

Choose the tenant semantics and authentication boundary. A provider-neutral OIDC implementation with local signed-token fixtures is the portfolio default; Microsoft Entra ID configuration and live hosting remain optional. Decide:

- what constitutes a tenant and who owns projects and uploaded data
- whether users may belong to multiple tenants
- how existing seeded demo data is migrated or isolated
- required session duration, MFA/conditional-access expectations, and offboarding behavior
- whether a later live identity integration should target Microsoft Entra ID or another OIDC provider

Do not claim production authentication from local demo cookies, fixtures, or an unconnected provider adapter.

### Scope

- Verify issuer, audience, signature, expiry, nonce/state, and required claims server-side.
- Map immutable provider subject and tenant claims to internal identities and memberships.
- Use secure, HTTP-only, same-site session handling with CSRF protection where applicable.
- Add `tenant_id` ownership to projects, departments, documents, versions, chunks, memberships, chats, reviews, feedback, audit events, and evaluation data that is tenant-owned.
- Make tenant-aware foreign keys and uniqueness constraints explicit.
- Separate local demo mode from production configuration and refuse demo identity headers/cookies in production.
- Define provisioning, role changes, revocation, offboarding, and data-retention behavior.
- Provide an OIDC configuration boundary that can target Entra ID without requiring Azure resources during local implementation.

### Verification

- Authentication integration tests with local signed-token fixtures for valid, expired, wrong-issuer, wrong-audience, tampered, revoked, and missing tokens.
- Cross-tenant ID enumeration and direct-route tests.
- Session fixation, CSRF, logout, privilege-change, and disabled-user tests.
- Migration/backfill and rollback rehearsal on non-production data.

## Phase 57: Database-Enforced Authorization And Tenant Isolation

### Goal

Make accidental omission of an application filter insufficient to expose another tenant’s data.

### Scope

- Define a request-scoped database tenant/user context in a transaction.
- Enforce tenant and role policies using PostgreSQL row-level security or an equivalently reviewed database policy layer.
- Apply policies to every tenant-owned table, including document chunks, vector/keyword retrieval, chats, reviews, audit data, and background ingestion jobs.
- Keep service accounts least-privileged; separate migration ownership from runtime access and prevent the runtime role from bypassing RLS.
- Make storage keys, caches, queues, and temporary files tenant-scoped.
- Add invariant checks preventing cross-tenant foreign-key relationships.
- Audit denied cross-tenant attempts without revealing target existence.

### Verification

- Run tests directly through the database role, not only API endpoints.
- Inject intentionally missing application filters and prove database denial.
- Cover list, get, create, update, archive, retrieval, background jobs, exports, and observability.
- Require zero cross-tenant rows, chunks, citations, cache hits, storage reads, and log disclosures.
- Obtain a focused code and policy review before promotion.

## Phase 58: Rate Limiting, Quotas, And Cost Abuse Controls

### Scope

- Implement a distributed limiter contract and verify it with a local Redis-compatible service. A managed Redis deployment remains optional and must not be claimed until connected and tested.
- Limit by authenticated identity, tenant, IP risk context, endpoint, and expensive operation.
- Add chat, streaming, upload, cleanup, embedding, indexing, evaluation, and admin-operation limits.
- Bound request size, question length, conversation length, upload count/size, concurrent streams, retries, and background jobs.
- Add tenant budgets and circuit breakers for external AI cost.
- Return safe `429` responses with retry guidance and no internal capacity details.
- Protect login and token endpoints according to the identity provider’s guidance.
- Audit and monitor sustained abuse while avoiding unbounded high-cardinality telemetry.

### Verification

- Burst, sustained, concurrent, distributed-instance, retry, and tenant-isolation tests.
- Confirm one tenant cannot exhaust another tenant’s quota.
- Confirm denied work does not call embeddings/chat APIs or start ingestion.

## Phase 59: Secure File Processing And Storage

### Required user decision before implementation

Choose supported file formats, maximum sizes/pages, retention policy, and whether original files may contain regulated or personal data. Local quarantine plus a scanner interface is the portfolio default. Production object storage and a hosted malware scanner are optional external integrations behind the financial-safety gate.

### Scope

- Upload to a quarantine area with randomized tenant-scoped keys behind a storage-provider interface.
- Validate extension, declared MIME, file signature, parser result, size, page count, compression ratio, and archive nesting; reject mismatches and unsupported active content.
- Scan for malware before parsing or making content available; use approved safe fixtures locally and label the scanner accurately.
- Run parsers in isolated workers/containers with no unnecessary network, read-only runtime, timeouts, CPU/memory/disk limits, and patched dependencies.
- Protect against path traversal, decompression bombs, parser exploits, oversized OCR, duplicate processing, and poisoned metadata.
- Encrypt in transit and at rest; use short-lived scoped access rather than public URLs.
- Define quarantine, clean, rejected, deleted, and legal-hold lifecycle states.
- Ensure rejected or unapproved content is never indexed or retrieved.
- Redact parser errors and securely remove temporary files.

### Verification

- Known-safe and approved malware-test fixtures, malformed PDFs, polyglots, MIME mismatches, traversal names, bombs, timeouts, large files, duplicate jobs, and deletion tests.
- Tenant storage-isolation and signed-access expiry tests.
- Dependency and container vulnerability scans with documented triage.

## Phase 60: Secrets, Privacy, And Log Controls

### Scope

- Implement a secret-provider boundary and production startup rejection of placeholder or development secrets. Managed secret-store and workload-identity claims require a connected provider; local verification must be labeled as such.
- Remove long-lived credentials where managed identity is available and define rotation/revocation procedures.
- Inventory sensitive data in prompts, uploads, chats, feedback, traces, audit events, and evaluation artifacts.
- Default logs to IDs, bounded reason codes, timings, counts, and hashes rather than full user prompts or source text.
- Add centralized redaction for authorization headers, cookies, API keys, connection strings, personal data, source content, and model payloads.
- Define role-based log access, encryption, retention, deletion, export, backup, and incident-preservation policies.
- Prevent secrets from entering client bundles, exception pages, Git history, Docker layers, CI artifacts, or telemetry.
- Document provider data-use and retention configuration for external AI services.

### Verification

- Automated secret scanning of repository, build output, container image, and representative logs.
- Redaction tests using seeded fake secrets and personal data.
- Rotation and revoked-secret rehearsal.
- Retention/deletion and least-privilege log-access tests.

## Phase 61: Security Monitoring And Incident Response

### Scope

- Define a security-event taxonomy for authentication failures, authorization denials, cross-tenant attempts, injection detections, evidence/validator failures, rate limits, upload malware, parser failures, admin changes, secret/config failures, and unusual cost.
- Emit structured, privacy-safe, correlation-ready events.
- Implement a provider-neutral monitoring/SIEM interface and a local structured-event sink. A live monitoring destination is optional and must not be claimed until end-to-end delivery is tested.
- Add alerts with documented thresholds, severity, owner, escalation, and false-positive handling.
- Create runbooks for account compromise, tenant-isolation concern, malicious upload, secret exposure, AI cost abuse, and suspected prompt-injection campaign.
- Make audit records tamper-evident or send them to storage the application runtime cannot rewrite.
- Define incident evidence retention and notification responsibilities.

### Verification

- Synthetic alert tests prove end-to-end delivery and paging/notification behavior.
- Tabletop exercises execute each high-severity runbook.
- Confirm monitoring cannot expose another tenant’s content or become a prompt/source exfiltration channel.

## Phase 62: Security Assessment Readiness And Optional Independent Testing

### Preparation scope

- Maintain a threat model and data-flow diagram covering browser, API, identity provider, PostgreSQL/pgvector, object storage, queues/workers, external AI, monitoring, and admin paths.
- Define assets, trust boundaries, abuse cases, rules of engagement, test environment, test accounts/tenants, data handling, and emergency contacts.
- Map scope to applicable OWASP ASVS, API Security, and LLM application risks without claiming certification solely from a checklist.
- Complete internal SAST, dependency, container, DAST, authorization, tenant-isolation, and adversarial prechecks.
- Set remediation severity and retest SLAs.

### Portfolio completion boundary

The portfolio phase is complete when the preparation scope, internal prechecks, finding triage workflow, and remediation/retest procedure are implemented and verified. It must be labeled `Independent validation required`.

### Optional external dependency

The implementation agent can prepare the system and fix findings but cannot truthfully mark an independent penetration test complete. An independent-validation claim requires a qualified independent tester, a written report, triaged findings, remediation evidence, and an independent retest of material findings. The public page should report only the assessment date, scope, disposition summary, and limitations approved for disclosure.

## Phase 63: Ongoing Adversarial Evaluation And Release Gates

### Scope

- Run deterministic unit/regression suites on every change.
- Run budgeted semantic ambiguity, prompt-injection, indirect-source-injection, evidence-sufficiency, permission, memory, and multi-document suites on a controlled cadence.
- Separate development cases from newly authored sealed release holdouts.
- Never tune against or selectively rerun a sealed holdout; replace it with a newly authored suite for a later claim.
- Include multilingual/obfuscated attacks, source poisoning, memory poisoning, role/scope escalation, citation suppression, denial-of-service/cost abuse, and legitimate-security-question false positives.
- Record runtime commit, prompt/model versions, corpus hash, suite hash, provider configuration, sample size, failures, cost, latency, stability, and human adjudication.
- Make hard security gates block release automatically; make quality target misses produce an explicit review decision rather than silent promotion.
- Monitor production-safe aggregates for drift and use reviewed incidents/feedback to author future development cases, never automatic benchmark truth.
- Keep `/trust` synchronized with the latest approved evidence while retaining historical results and limitations.

### Release gates

At minimum, a production promotion must require:

- zero cross-tenant leakage or unauthorized generation in the release suite
- zero restricted citations and memory-as-evidence violations
- zero unsafe compliance in the predeclared injection suite
- no unresolved critical/high security findings
- all schemas and benchmark/evaluation data valid and complete
- latency, availability, and cost within predeclared budgets
- human review of all automated security failures and the predeclared sample of passes
- rollback instructions and monitoring readiness

## Decision Gates And Expected Pauses

The implementation agent should proceed autonomously through Phases 51-55 using existing project defaults and measured promotion gates. It must pause before decisions that materially change production ownership or external services:

1. Before Phase 56: tenant ownership/membership model, session behavior, offboarding, and seeded-data migration. A live identity provider is not required for local implementation.
2. Before any cloud provisioning: every item in the mandatory financial-safety gate, followed by explicit user approval.
3. Before Phase 59: accepted formats, regulated-data stance, and retention. Object storage and hosted scanning decisions are required only for optional external integration.
4. Before Phase 61 external integration: monitoring/SIEM destination, on-call owner, and notification channel. Local structured monitoring may proceed without them.
5. Before an optional Phase 62 independent assessment: assessor, scope, authorization, schedule, cost, and rules of engagement.

Provider-neutral interfaces, local test doubles, threat models, and decision documents may be prepared before those choices, but they must not be presented as completed production controls.

## Documentation Deliverables

Each phase must update the relevant subset of:

- `docs/phase-{number}/design.md`
- `docs/phase-{number}/verification.md`
- `docs/roadmap/progress.md`
- `README.md`
- `docs/demo/interactive-demo-guide.md`
- `docs/demo/screenshots-checklist.md`
- `docs/algorithm/end-to-end-flow.md`
- `docs/algorithm/permissions-and-scope.md`
- `docs/algorithm/generation-citations-confidence.md`
- `docs/algorithm/review-findings.md`
- a production threat model and incident runbooks introduced by Phases 56-62

The Trust & Safety page and documentation must use the same status vocabulary and must never imply that planned infrastructure, a development evaluation, or a self-review is an implemented or independently validated control.

## Definition Of Program Completion

Phases 51-55 are complete when the layered defenses are implemented, measured, visible, and honestly limited on the product page without weakening permission safety or current regression quality.

The portfolio track for Phases 56-63 is complete when OIDC-compatible identity, tenant isolation, database authorization, distributed abuse controls, secure file-processing boundaries, secrets/privacy controls, structured monitoring, security-assessment preparation, and adversarial release gates are implemented and verified with honest local evidence. Phase 62 may remain `Independent validation required`.

Production-operation claims remain separate: they require connected managed services, a real hosted identity provider, operational ownership, end-to-end monitoring, and any claimed independent assessment. A local implementation, test double, checklist, or agent-authored review must never be presented as that external evidence.
