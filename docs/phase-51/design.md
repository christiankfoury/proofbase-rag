# Phase 51 Trust And Safety Product Page Design

## Goal

Add a public App-side `/trust` page that explains Proofbase's current defense boundaries, names the evidence behind measured claims, and keeps production dependencies visibly incomplete.

## Product Surface

- Add **Trust & Safety** to the App navigation and breadcrumb map.
- Present the target request lifecycle as separate routing, authorization, retrieval, sufficiency, generation, and validation layers.
- Explain ambiguity, direct injection, source injection, permissions, memory, evidence sufficiency, citations, and audit evidence independently.
- Show the Phase 56-63 production-readiness backlog with the roadmap's status vocabulary.
- Lead with the local-demo identity and self-evaluation limitations.

## Engineering Design

- `apps/web/lib/defenseCatalog.ts` is the typed, code-owned source for page status content.
- Every catalog item requires `status`, `summary`, `boundary`, `evidence`, `limitations`, and `last_verified`, plus stable identity and phase fields.
- Evidence links use existing App and Dev/Admin routes. The page renders repository-backed static content at build time and does not invent live security state.
- Planned items render an explicit no-evidence state rather than empty metrics.
- The page exposes reasoned boundaries and high-level controls, not system prompts, detector signatures, payload collections, private logs, source text, or secrets.

## Verification Plan

- Run the Next.js production build and TypeScript checking through the build.
- Inspect the generated route list for `/trust` and smoke the built route when a server is available.
- Check navigation active state and breadcrumb registration by source inspection and browser smoke where available.
- Review every implemented/measured claim for named evidence, date, sample/run scope, and limitations.
- Review every future control for Planned, Production dependency, or Independent validation required labeling.
- Run shared Python compile, benchmark schema validation, Docker Compose config, and `git diff --check` even though runtime RAG behavior is unchanged.

## Non-Goals

- No request-routing, retrieval, generation, permission, prompt, or evaluation behavior changes.
- No production authentication, tenant isolation, monitoring, file scanning, penetration-test, or release-gate claim.
- No OpenAI-backed evaluation is required because Phase 51 changes only static product transparency.
