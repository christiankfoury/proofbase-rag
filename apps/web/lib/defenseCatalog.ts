import { defenseEvidence, defenseStage } from "@/lib/defenseEvidence";

export type DefenseStatus =
  | "implemented"
  | "measured"
  | "planned"
  | "production_dependency"
  | "independent_validation_required";

export type DefenseEvidence = {
  label: string;
  href: string;
  detail: string;
};

export type DefenseCatalogItem = {
  id: string;
  title: string;
  phase: string;
  status: DefenseStatus;
  summary: string;
  boundary: string;
  evidence: DefenseEvidence[];
  limitations: string[];
  last_verified: string;
};

export const defenseStatusCatalog: Record<
  DefenseStatus,
  { label: string; explanation: string }
> = {
  implemented: {
    label: "Implemented",
    explanation: "Present in the local-demo code path and backed by named verification evidence.",
  },
  measured: {
    label: "Measured",
    explanation: "Implemented and reported with a named run, sample, date, and stated limitations.",
  },
  planned: {
    label: "Planned",
    explanation: "Approved roadmap work that is not implemented or verified yet.",
  },
  production_dependency: {
    label: "Production dependency",
    explanation: "Requires an infrastructure, provider, policy, data-ownership, or operational decision.",
  },
  independent_validation_required: {
    label: "Independent validation required",
    explanation: "Cannot be completed or certified by this implementation project alone.",
  },
};

export const currentDefenseCatalog: DefenseCatalogItem[] = [
  {
    id: "ambiguity",
    title: "Ambiguity handling",
    phase: "Phases 50 and 52",
    status: "measured",
    summary: "Deterministic fast paths and a typed semantic assessor route unresolved requests to clarification before retrieval.",
    boundary: "Clarification narrows intent only. It never grants project, department, role, document, or tool access.",
    evidence: [
      {
        label: "Algorithm guide",
        href: "/algorithm",
        detail: "Explains the request, memory, retrieval, generation, and validation boundaries.",
      },
      {
        label: "Phase 50 regression evidence",
        href: "/dev-admin/runs",
        detail: "The current 130-question development regression and focused suites are visible in Dev & Admin.",
      },
    ],
    limitations: [
      "The 48-case request-assessment suite is visible development evidence, not unseen generalization proof.",
      "Semantic assessment adds a provider dependency; unavailable, invalid, refused, or timed-out assessments fail safely without retrieval.",
    ],
    last_verified: "2026-08-26",
  },
  {
    id: "direct-injection",
    title: "Direct prompt-override handling",
    phase: "Phases 50 and 52",
    status: "measured",
    summary: "Known requests to ignore evidence, invent facts, suppress citations, or bypass access are blocked before retrieval.",
    boundary: "The guard can block or clarify a request. It cannot alter identity, scope, permissions, or available evidence.",
    evidence: [
      {
        label: "Prompt-injection outcomes",
        href: "/dev-admin/runs",
        detail: `Run ${defenseStage("Request assessment").run_id} measured ${defenseStage("Request assessment").unsafe_outcomes} unsafe continuations across ${defenseStage("Request assessment").sample_size} fixed cases.`,
      },
      {
        label: "Audit evidence",
        href: "/dev-admin/audit",
        detail: "Guarded requests emit bounded security events without storing prompt or source text in audit metadata.",
      },
    ],
    limitations: [
      "The measured suite includes direct, encoded, obfuscated, multilingual, mixed, and memory-poisoning cases, but cannot prove coverage of every future attack.",
      "Exact detection signatures and exploit payloads are intentionally not published on this page.",
    ],
    last_verified: "2026-08-26",
  },
  {
    id: "source-injection",
    title: "Indirect and source-injection handling",
    phase: "Phases 38-55",
    status: "measured",
    summary: "Retrieved text is framed as evidence, and generated output is checked for effects of instructions embedded in authorized source content.",
    boundary: "Legitimate questions about hostile source text can continue, but source instructions do not grant access or replace system behavior.",
    evidence: [
      {
        label: "Generation and citation controls",
        href: "/algorithm",
        detail: "Shows how authorized context reaches generation and how returned citations are matched to retrieved chunks.",
      },
      {
        label: "Current answer evidence",
        href: "/dev-admin/failed-questions",
        detail: "Historical adversarial-source cases and their review context remain inspectable.",
      },
    ],
    limitations: [
      "The semantic validator is development evidence and cannot prove detection of every indirect or multilingual source instruction.",
      "A conservative source-discussion false positive remains visible in the Phase 54 fixed suite.",
    ],
    last_verified: "2026-08-26",
  },
  {
    id: "permission-filtering",
    title: "Permission filtering before generation",
    phase: "Phases 8-50",
    status: "measured",
    summary: "Project, department, indexed-version, and document-role filters run before chunks can reach answer generation.",
    boundary: "Permissions are enforced independently of model output. A classifier, prompt, score, or citation cannot grant access.",
    evidence: [
      {
        label: "Permission safety",
        href: "/dev-admin/permission-safety",
        detail: "Phase 52 measured zero permission leakage, restricted citations, and unauthorized chunks reaching generation in its focused suite.",
      },
      {
        label: "Permission demo",
        href: "/dev-admin/permission-demo",
        detail: "Compares the same restricted question across local demo roles.",
      },
    ],
    limitations: [
      "Identity and membership use local demo controls, not production SSO or tenant isolation.",
      "A focused synthetic permission suite is not a substitute for production authorization testing.",
    ],
    last_verified: "2026-08-26",
  },
  {
    id: "memory",
    title: "Conversation memory boundary",
    phase: "Phases 9, 36, 46",
    status: "measured",
    summary: "Previous turns can help rewrite a follow-up query, but they are never accepted as source evidence.",
    boundary: "Every rewritten query still passes through current project, department, role, retrieval, and citation controls.",
    evidence: [
      {
        label: "Memory evaluation",
        href: "/dev-admin/memory-evaluation",
        detail: "The focused 20-case memory suite reports its query-rewrite, answer, citation, and permission results separately.",
      },
      {
        label: "Algorithm guide",
        href: "/algorithm",
        detail: "Explains the difference between conversational context and retrieved evidence.",
      },
    ],
    limitations: [
      "Measured performance is tied to the named synthetic suite and does not cover every long conversation.",
      "Production session ownership and retention require the Phase 56 identity and tenant decisions.",
    ],
    last_verified: "2026-08-26",
  },
  {
    id: "semantic-request-assessment",
    title: "Structured semantic request assessment",
    phase: "Phase 52",
    status: "measured",
    summary: "Every request not resolved by a deterministic fast path receives a strict-schema ambiguity and injection assessment before retrieval.",
    boundary: "The assessor may narrow behavior to continue, clarify, block, or fail safely. It receives no role, scope, permission, document, chunk, secret, or tool authority and cannot expand authorization.",
    evidence: [
      {
        label: "Phase 52 candidate",
        href: "/dev-admin/runs",
        detail: `Run ${defenseStage("Request assessment").run_id} passed ${defenseStage("Request assessment").sample_size}/${defenseStage("Request assessment").sample_size} fixed cases with ${defenseStage("Request assessment").unsafe_outcomes} unsafe outcomes, ${(defenseStage("Request assessment").p95_latency_ms / 1000).toFixed(3)} s p95, and $${defenseStage("Request assessment").estimated_cost_usd.toFixed(6)} cost.`,
      },
    ],
    limitations: [
      "This is a routing and integrity control, not authentication, authorization, content moderation, or evidence sufficiency.",
      "The development suite is visible and was used for remediation; the sealed Phase 47-49 holdouts remain unchanged and were not rerun.",
    ],
    last_verified: "2026-08-26",
  },
  {
    id: "evidence-sufficiency",
    title: "Permission-aware evidence sufficiency",
    phase: "Phase 53",
    status: "measured",
    summary: "A deterministic-first, strict-schema post-permission gate classifies accessible evidence as sufficient, partial, missing, or conflicting before normal generation.",
    boundary: "The gate sees authorized chunks only, cannot retrieve or grant access, removes any non-authorized model reference, and never names an inaccessible source.",
    evidence: [
      {
        label: "Phase 53 fixed suite",
        href: "/dev-admin/runs",
        detail: `Run ${defenseStage("Evidence sufficiency").run_id} measured ${(defenseStage("Evidence sufficiency").accuracy * 100).toFixed(1)}% action accuracy across ${defenseStage("Evidence sufficiency").sample_size} cases, ${defenseStage("Evidence sufficiency").unsafe_outcomes} unsafe outcomes, ${(defenseStage("Evidence sufficiency").p95_latency_ms / 1000).toFixed(3)} s p95, and $${defenseStage("Evidence sufficiency").estimated_cost_usd.toFixed(6)} cost.`,
      },
      {
        label: "Phase 53 live regression",
        href: "/dev-admin/runs",
        detail: "Run phase53-live-query-regression-v5 passed benchmark 1.1 at 130/130 with answer and citation accuracy 1.000, hallucination 0.000, and zero failed-safe evidence assessments.",
      },
      {
        label: "Permission evaluation",
        href: "/dev-admin/permission-safety",
        detail: "Run phase53-permission-evaluation kept permission leakage, unauthorized exposure, restricted citations, and unauthorized chunks reaching generation at 0.000 across 20 restricted cases.",
      },
    ],
    limitations: [
      "The visible 30-case suite was used for development and is not an independent or sealed security evaluation.",
      "The semantic gate adds provider latency and availability dependency; the live regression measured 3411.041 ms mean evidence-assessment latency.",
      "The Phase 47-49 sealed holdouts were not rerun, so Phase 53 does not make a new generalization claim.",
    ],
    last_verified: "2026-08-26",
  },
  {
    id: "citation-validation",
    title: "Claim, citation, and source-instruction validation",
    phase: "Phase 54",
    status: "measured",
    summary: "Generated claims, exact facts, citations, conflicts, and indirect source-instruction effects are checked before any candidate answer is returned.",
    boundary: "Validation and its single bounded repair use only the permission-filtered chunks already supplied to generation; neither path can retrieve, widen scope, or introduce a source.",
    evidence: [
      {
        label: "Phase 54 fixed suite",
        href: "/dev-admin/runs",
        detail: `Run ${defenseStage("Post-generation validation").run_id} measured ${(defenseStage("Post-generation validation").accuracy * 100).toFixed(1)}% action accuracy across ${defenseStage("Post-generation validation").sample_size} cases, ${defenseStage("Post-generation validation").unsafe_outcomes} unsafe outcomes, ${(defenseStage("Post-generation validation").p95_latency_ms / 1000).toFixed(3)} s p95, and $${defenseStage("Post-generation validation").estimated_cost_usd.toFixed(6)} cost.`,
      },
      {
        label: "Phase 54 live regression",
        href: "/dev-admin/runs",
        detail: "Run phase54-live-query-regression-v5 passed benchmark 1.1 at 130/130 with answer and citation accuracy 1.000, hallucination 0.000, four bounded repairs, and zero validator fail-safes or final downgrades.",
      },
    ],
    limitations: [
      "The visible fixed suite was used for development; 1/24 legitimate source-discussion cases was conservatively sent to repair and remains a false-positive backlog.",
      "The validator adds an external-model availability dependency and measured $0.063432 cost across the 130-case regression.",
      "This self-evaluation is not an independent penetration test or a fresh generalization claim; the Phase 47-49 holdouts were not rerun.",
    ],
    last_verified: "2026-08-26",
  },
  {
    id: "audit-evidence",
    title: "Audit and review evidence",
    phase: "Phases 12, 25, 50, 55",
    status: "measured",
    summary: "Security decisions, bounded cross-stage traces, aggregate outcomes, feedback, reviews, and guarded-request evidence are visible to the Dev/Admin role.",
    boundary: "The public page links to bounded evidence views; it does not publish private logs, prompt text, source text, or credentials.",
    evidence: [
      {
        label: "Defense readiness",
        href: "/dev-admin/defense-readiness",
        detail: `${defenseEvidence.manifest.sample_size} fixed cases, ${defenseEvidence.runtime.sample_size} runtime questions, and ${defenseEvidence.permission.sample_size} permission checks are consolidated under one generated evidence schema.`,
      },
      {
        label: "Audit log",
        href: "/dev-admin/audit",
        detail: "Shows local security and workflow events under the existing demo-admin boundary.",
      },
      {
        label: "Observability",
        href: "/dev-admin/observability",
        detail: "Shows current request latency, confidence, and cost-oriented telemetry.",
      },
    ],
    limitations: [
      "Local logs are not tamper-evident production security monitoring.",
      "Monitoring ownership, destination, alerts, and incident response require a later production decision gate.",
    ],
    last_verified: "2026-08-26",
  },
];

export const productionReadinessCatalog: DefenseCatalogItem[] = [
  {
    id: "production-identity",
    title: "OIDC identity and tenant ownership",
    phase: "Phase 56",
    status: "implemented",
    summary: "Adds a provider-neutral OIDC boundary, strict local signed-token verification, explicit tenant ownership, session policy, and revocation/offboarding contracts.",
    boundary: "Production rejects demo/fixture identity modes; a hosted provider must still be connected before production authentication is claimed.",
    evidence: [
      { label: "Identity and scope guide", href: "/algorithm", detail: "Explains the tenant, membership, permission-filtering, and evidence boundaries." },
      { label: "Defense readiness", href: "/dev-admin/defense-readiness", detail: "Keeps local implementation evidence separate from hosted-provider claims." },
    ],
    limitations: ["No live identity provider, MFA, conditional-access policy, refresh-token exchange, or provider logout is connected; database enforcement is Phase 57."],
    last_verified: "2026-08-28",
  },
  {
    id: "database-authorization",
    title: "Database-enforced tenant authorization",
    phase: "Phase 57",
    status: "planned",
    summary: "Add tenant-aware keys, constraints, policies, and cross-tenant isolation tests below the application layer.",
    boundary: "Application filtering alone will not be presented as completed production tenant isolation.",
    evidence: [],
    limitations: ["Depends on the Phase 56 tenant model and migration design."],
    last_verified: "Not yet verified",
  },
  {
    id: "abuse-controls",
    title: "Distributed rate and cost controls",
    phase: "Phase 58",
    status: "planned",
    summary: "Apply per-identity and per-tenant request, token, upload, and cost budgets with bounded failure behavior.",
    boundary: "A local in-process limiter will not be described as a distributed production control.",
    evidence: [],
    limitations: ["Production budgets, shared state, ownership, and alert thresholds are not selected."],
    last_verified: "Not yet verified",
  },
  {
    id: "secure-files",
    title: "Secure file processing and storage",
    phase: "Phase 59",
    status: "planned",
    summary: "Use quarantine, a scanner contract, isolated parsing, lifecycle states, and tenant-scoped storage boundaries.",
    boundary: "Rejected or unapproved content must never become searchable evidence.",
    evidence: [],
    limitations: ["Formats, limits, regulated-data stance, and retention require a user decision; hosted storage and scanning remain optional external integrations."],
    last_verified: "Not yet verified",
  },
  {
    id: "secrets-privacy",
    title: "Secrets, privacy, and log controls",
    phase: "Phase 60",
    status: "planned",
    summary: "Add a secret-provider boundary, production-safe startup checks, centralized redaction, least-privilege log access, and retention controls.",
    boundary: "Local providers and repository-level redaction are not connected managed secret or privacy controls.",
    evidence: [],
    limitations: ["Managed identity, provider data-use, retention, access ownership, and rotation remain external operational dependencies."],
    last_verified: "Not yet verified",
  },
  {
    id: "monitoring-response",
    title: "Security monitoring and incident response",
    phase: "Phase 61",
    status: "planned",
    summary: "Emit privacy-safe structured events through a provider-neutral sink and add alerts, escalation policy, and tested runbooks.",
    boundary: "Local audit views are not a staffed production detection and response capability.",
    evidence: [],
    limitations: ["A live monitoring/SIEM destination, on-call owner, and notification channel remain optional external decisions."],
    last_verified: "Not yet verified",
  },
  {
    id: "penetration-test",
    title: "Security assessment readiness",
    phase: "Phase 62",
    status: "independent_validation_required",
    summary: "Prepare the threat model, internal prechecks, finding workflow, and retest process; keep external testing optional.",
    boundary: "An agent-authored review, checklist, local test double, or internal scan cannot satisfy this control.",
    evidence: [],
    limitations: ["Independent validation requires a separately approved assessor, authorization, scope, report, remediation, and retest."],
    last_verified: "Not yet verified",
  },
  {
    id: "release-gates",
    title: "Ongoing adversarial release gates",
    phase: "Phase 63",
    status: "planned",
    summary: "Run deterministic and budgeted semantic suites, preserve fresh sealed holdouts, and block releases on hard safety failures.",
    boundary: "Development suites and previously opened holdouts cannot be relabeled as fresh independent release evidence.",
    evidence: [],
    limitations: [`The ${defenseEvidence.holdout.case_count}-case Phase 55 holdout is sealed and unexecuted; it supports no claim until a future predeclared release protocol opens it without runtime tuning.`],
    last_verified: "Not yet verified",
  },
];

export const defenseLifecycle = [
  ["01", "Normalize and bound", "Limit request size and apply deterministic high-confidence guards."],
  ["02", "Assess intent", "Route ambiguity and injection risk without changing identity or access."],
  ["03", "Resolve authorization", "Derive project, department, and role scope independently of model output."],
  ["04", "Retrieve allowed chunks", "Search only active, indexed evidence that the current user may access."],
  ["05", "Check sufficiency", "Decide whether accessible evidence fully supports the clear request."],
  ["06", "Generate from evidence", "Treat source content as data and answer only from authorized context."],
  ["07", "Validate and respond", "Check claims and citations, then answer, clarify, abstain, or fail safely."],
] as const;
