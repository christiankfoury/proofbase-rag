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
    phase: "Phase 50",
    status: "implemented",
    summary: "Known underspecified approvals and unresolved fresh-chat referents return a clarification before retrieval.",
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
      "The current early ambiguity guard is pattern-based and does not cover every paraphrase or language.",
      "Structured semantic assessment is Phase 52 work and is not represented as implemented here.",
    ],
    last_verified: "2026-08-26",
  },
  {
    id: "direct-injection",
    title: "Direct prompt-override handling",
    phase: "Phase 50",
    status: "measured",
    summary: "Known requests to ignore evidence, invent facts, suppress citations, or bypass access are blocked before retrieval.",
    boundary: "The guard can block or clarify a request. It cannot alter identity, scope, permissions, or available evidence.",
    evidence: [
      {
        label: "Prompt-injection outcomes",
        href: "/dev-admin/runs",
        detail: "Run phase50-prompt-injection-regression passed 5/5 development cases with zero measured unsafe compliance.",
      },
      {
        label: "Audit evidence",
        href: "/dev-admin/audit",
        detail: "Guarded requests emit bounded security events without storing prompt or source text in audit metadata.",
      },
    ],
    limitations: [
      "Five development cases do not prove coverage of unseen, encoded, multilingual, or obfuscated attacks.",
      "Exact detection signatures and exploit payloads are intentionally not published on this page.",
    ],
    last_verified: "2026-08-26",
  },
  {
    id: "source-injection",
    title: "Indirect and source-injection handling",
    phase: "Phases 38-50",
    status: "implemented",
    summary: "Retrieved text is framed as evidence to answer from, not as instructions that can change assistant behavior.",
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
      "There is not yet a general semantic detector for indirect instructions in arbitrary retrieved content.",
      "Post-generation source-instruction validation is planned for Phase 54.",
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
        detail: "Phase 50 measured zero permission leakage, restricted citations, and unauthorized chunks reaching generation in its focused suite.",
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
    status: "planned",
    summary: "A typed assessment will generalize ambiguity and injection routing beyond known deterministic patterns.",
    boundary: "The future assessor may narrow behavior to continue, clarify, block, or fail safely; it will never expand authorization.",
    evidence: [
      {
        label: "Current algorithm boundary",
        href: "/algorithm",
        detail: "The current guide documents the implemented deterministic path that the planned assessor will augment.",
      },
    ],
    limitations: ["No semantic-assessment runtime, promoted model, latency result, or cost result exists yet."],
    last_verified: "Not yet verified",
  },
  {
    id: "evidence-sufficiency",
    title: "Permission-aware evidence sufficiency",
    phase: "Phase 53",
    status: "planned",
    summary: "A post-permission gate will decide whether accessible evidence is sufficient, partial, missing, or conflicting before normal generation.",
    boundary: "The future gate will inspect authorized chunks only and will not reveal that inaccessible sources exist.",
    evidence: [
      {
        label: "Current multi-document evidence",
        href: "/dev-admin/multi-doc",
        detail: "Current source-coverage measurements establish the starting point; they are not an implemented sufficiency gate.",
      },
    ],
    limitations: ["Similarity and retrieval confidence currently help rank evidence but do not prove full answerability."],
    last_verified: "Not yet verified",
  },
  {
    id: "citation-validation",
    title: "Citation and answer-support validation",
    phase: "Phases 7-50",
    status: "measured",
    summary: "Returned citations must map to retrieved chunks, and weak support can downgrade an answer.",
    boundary: "Validation uses only permission-filtered retrieved evidence; citation backfill cannot introduce a new source.",
    evidence: [
      {
        label: "Generation and citation guide",
        href: "/algorithm",
        detail: "Documents citation matching, backfill, support scoring, response downgrades, and confidence interpretation.",
      },
      {
        label: "Run comparison",
        href: "/dev-admin/runs",
        detail: "Phase 50 development regression reported 130/130 and citation accuracy 1.000 over benchmark 1.1.",
      },
    ],
    limitations: [
      "Citation support is a deterministic heuristic, not a proof that every natural-language claim is entailed.",
      "Semantic claim validation and bounded repair are planned for Phase 54.",
    ],
    last_verified: "2026-08-26",
  },
  {
    id: "audit-evidence",
    title: "Audit and review evidence",
    phase: "Phases 12, 25, 50",
    status: "implemented",
    summary: "Security-relevant decisions, feedback, reviews, and guarded-request outcomes are visible to the Dev/Admin role.",
    boundary: "The public page links to bounded evidence views; it does not publish private logs, prompt text, source text, or credentials.",
    evidence: [
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
    title: "Real identity and tenant ownership",
    phase: "Phase 56",
    status: "production_dependency",
    summary: "Replace local demo identity with a chosen OIDC provider and an explicit tenant/data-ownership model.",
    boundary: "Production must reject demo identity headers and cookies and derive tenant membership from verified identity claims.",
    evidence: [],
    limitations: ["Identity provider, tenant ownership, session/MFA expectations, and seeded-data migration require a user decision."],
    last_verified: "Not yet verified",
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
    status: "production_dependency",
    summary: "Use quarantine, malware scanning, isolated parsing, lifecycle states, and tenant-scoped object storage.",
    boundary: "Rejected or unapproved content must never become searchable evidence.",
    evidence: [],
    limitations: ["Storage, scanner, formats, limits, regulated-data stance, and retention require a user decision."],
    last_verified: "Not yet verified",
  },
  {
    id: "secrets-privacy",
    title: "Secrets, privacy, and log controls",
    phase: "Phase 60",
    status: "planned",
    summary: "Use workload identity, managed secrets, centralized redaction, least-privilege log access, and retention controls.",
    boundary: "Development placeholders and repository-level redaction are not managed production secret or privacy controls.",
    evidence: [],
    limitations: ["Provider data-use, retention, access ownership, and rotation procedures are not production-configured."],
    last_verified: "Not yet verified",
  },
  {
    id: "monitoring-response",
    title: "Security monitoring and incident response",
    phase: "Phase 61",
    status: "production_dependency",
    summary: "Deliver privacy-safe events to a selected monitoring destination with alerts, owners, escalation, and tested runbooks.",
    boundary: "Local audit views are not a staffed production detection and response capability.",
    evidence: [],
    limitations: ["Monitoring/SIEM destination, on-call owner, and notification channel require a user decision."],
    last_verified: "Not yet verified",
  },
  {
    id: "penetration-test",
    title: "Independent penetration testing",
    phase: "Phase 62",
    status: "independent_validation_required",
    summary: "A qualified external assessor must test the authorized production-like scope and independently retest material fixes.",
    boundary: "An agent-authored review, checklist, local test double, or internal scan cannot satisfy this control.",
    evidence: [],
    limitations: ["Assessor, authorization, scope, schedule, rules of engagement, report, and retest do not exist yet."],
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
    limitations: ["The Phase 51-55 runtime and a new separated holdout must be frozen before a new generalization claim."],
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
