export type PhaseCategory =
  | "product"
  | "retrieval"
  | "answer_quality"
  | "safety"
  | "memory"
  | "observability"
  | "deployment"
  | "evaluation"
  | "documents";

export type PhaseMeta = {
  id: string;
  number: number;
  label: string;
  shortDescription: string;
  category: PhaseCategory;
  docHref?: string;
};

export type RunLike = {
  run_id?: string | null;
  run_name?: string | null;
  phase?: string | null;
  sample_size?: number | null;
  total_questions?: number | null;
  benchmark_version?: string | null;
};

const PHASES: PhaseMeta[] = [
  {
    id: "phase-6",
    number: 6,
    label: "Retrieval Baseline",
    shortDescription: "Compares vector, keyword, hybrid, and chunking retrieval profiles.",
    category: "retrieval",
    docHref: "/docs/phase-6/evaluation-results.md",
  },
  {
    id: "phase-7",
    number: 7,
    label: "Answer Generation Baseline",
    shortDescription: "Adds generated answers, citation output, and confidence scoring.",
    category: "answer_quality",
    docHref: "/docs/phase-7/evaluation-results.md",
  },
  {
    id: "phase-8",
    number: 8,
    label: "Permission Safety Baseline",
    shortDescription: "Measures restricted-source handling and permission leakage.",
    category: "safety",
    docHref: "/docs/phase-8/permission-evaluation-results.md",
  },
  {
    id: "phase-9",
    number: 9,
    label: "Conversation Memory Baseline",
    shortDescription: "Evaluates follow-up detection and memory-safe query rewriting.",
    category: "memory",
    docHref: "/docs/phase-9/memory-evaluation-results.md",
  },
  {
    id: "phase-10",
    number: 10,
    label: "Evaluation Dashboard",
    shortDescription: "Introduces the dashboard for comparing measured evaluation runs.",
    category: "evaluation",
    docHref: "/docs/phase-10/evaluation-dashboard-design.md",
  },
  {
    id: "phase-11",
    number: 11,
    label: "Prompt Experiments",
    shortDescription: "Compares answer-generation prompt versions against the benchmark.",
    category: "answer_quality",
    docHref: "/docs/phase-11/prompt-experiment-results.md",
  },
  {
    id: "phase-12",
    number: 12,
    label: "Observability And Audit",
    shortDescription: "Adds feedback, observability, and audit evidence surfaces.",
    category: "observability",
    docHref: "/docs/phase-12/observability-design.md",
  },
  {
    id: "phase-13",
    number: 13,
    label: "Multi-Document Reasoning",
    shortDescription: "Adds query decomposition and grouped multi-source evidence.",
    category: "answer_quality",
    docHref: "/docs/phase-13/multi-document-reasoning-design.md",
  },
  {
    id: "phase-14",
    number: 14,
    label: "Docker And Azure Readiness",
    shortDescription: "Packages the local stack and documents Azure deployment readiness.",
    category: "deployment",
    docHref: "/docs/phase-14/docker-local-setup.md",
  },
  {
    id: "phase-15",
    number: 15,
    label: "Interactive Demo UX",
    shortDescription: "Adds the recruiter-facing interactive demo experience.",
    category: "product",
    docHref: "/docs/phase-15/interactive-demo-ux.md",
  },
  {
    id: "phase-16",
    number: 16,
    label: "Cost Tracking",
    shortDescription: "Tracks chat-generation model cost estimates.",
    category: "observability",
    docHref: "/docs/phase-16/cost-tracking.md",
  },
  {
    id: "phase-24",
    number: 24,
    label: "Algorithm Quality Lab",
    shortDescription: "Adds named retrieval profiles and algorithm-review workflow.",
    category: "retrieval",
    docHref: "/docs/phase-24/algorithm-quality-lab-design.md",
  },
  {
    id: "phase-25",
    number: 25,
    label: "Human Review Workflow",
    shortDescription: "Adds human review labels for failed questions and feedback candidates.",
    category: "evaluation",
    docHref: "/docs/phase-25/result-verification-review-design.md",
  },
  {
    id: "phase-27",
    number: 27,
    label: "Local Demo Auth",
    shortDescription: "Adds local demo roles, project memberships, and Dev/Admin gating.",
    category: "safety",
    docHref: "/docs/phase-27/local-demo-auth-design.md",
  },
  {
    id: "phase-28",
    number: 28,
    label: "Dashboard Transparency",
    shortDescription: "Makes dashboard metric context and limitations clearer.",
    category: "evaluation",
  },
  {
    id: "phase-29",
    number: 29,
    label: "Benchmark Schema Validation",
    shortDescription: "Cleans up and validates the benchmark schema.",
    category: "evaluation",
  },
  {
    id: "phase-30",
    number: 30,
    label: "Enterprise Document Expansion",
    shortDescription: "Expands the synthetic enterprise source corpus.",
    category: "documents",
  },
  {
    id: "phase-31",
    number: 31,
    label: "Benchmark Expansion",
    shortDescription: "Expands benchmark coverage for the larger corpus.",
    category: "evaluation",
  },
  {
    id: "phase-32",
    number: 32,
    label: "Expanded Baseline Run",
    shortDescription: "Captures the expanded benchmark baseline.",
    category: "evaluation",
  },
  {
    id: "phase-33",
    number: 33,
    label: "Lexical Rerank Candidate",
    shortDescription: "Adds vector plus lexical reranking candidate evidence.",
    category: "retrieval",
  },
  {
    id: "phase-34",
    number: 34,
    label: "Grounded Abstention",
    shortDescription: "Improves abstention and hallucination control.",
    category: "answer_quality",
  },
  {
    id: "phase-35",
    number: 35,
    label: "Citation Alignment",
    shortDescription: "Improves citation accuracy and citation validation alignment.",
    category: "answer_quality",
  },
  {
    id: "phase-36",
    number: 36,
    label: "Permission And Memory Expansion",
    shortDescription: "Expands permission and memory evaluation coverage.",
    category: "safety",
  },
  {
    id: "phase-37",
    number: 37,
    label: "Regression Scorecard",
    shortDescription: "Adds before/after regression scorecard evidence.",
    category: "evaluation",
  },
  {
    id: "phase-38",
    number: 38,
    label: "Answer Quality Remediation",
    shortDescription: "Reduces answer-quality failures without weakening safety gates.",
    category: "answer_quality",
  },
  {
    id: "phase-39",
    number: 39,
    label: "Multi-Document Orchestration",
    shortDescription: "Plans stricter ambiguity and multi-document orchestration behavior.",
    category: "answer_quality",
  },
  {
    id: "phase-40",
    number: 40,
    label: "Uploaded Document Workflow",
    shortDescription: "Plans upload, review, approve, index, and ask workflow.",
    category: "documents",
  },
];

const PHASE_BY_ID = new Map(PHASES.map((phase) => [phase.id, phase]));
const PHASE_BY_NUMBER = new Map(PHASES.map((phase) => [phase.number, phase]));

const RUN_LABEL_OVERRIDES: Record<string, string> = {
  "phase6-vector-section": "Vector Section Retrieval",
  "phase6-keyword-section": "Keyword Section Retrieval",
  "phase6-hybrid-section-0.5": "Hybrid Section Retrieval 50/50",
  "phase6-vector-fixed-size": "Vector Fixed-Size Retrieval",
  "phase6-hybrid-fixed-size-0.5": "Hybrid Fixed-Size Retrieval 50/50",
  "phase7-answer-quality": "Answer Quality Baseline",
  "phase8-permission-safety": "Permission Safety Baseline",
  "phase9-memory": "Conversation Memory Baseline",
  "phase11-answer-generation-v1": "Answer Generation v1",
  "phase11-answer-generation-v2": "Answer Generation v2",
  "phase11-answer-generation-v3": "Answer Generation v3",
  "phase11-answer-generation-v5": "Answer Generation v5",
  "phase11-answer-generation-v5-failed-subset": "Answer Generation v5 Failed Subset",
  "phase32-expanded-retrieval": "Expanded Retrieval Baseline",
  "phase32-expanded-answer-generation-v5": "Expanded Answer Generation v5",
  "phase33-vector-lexical-rerank-top3": "Lexical Rerank Candidate top-3",
  "phase34-answer-grounding-v6": "Grounded Abstention v6",
  "phase35-citation-alignment-v7": "Citation Alignment v7",
  "phase36-permission-evaluation": "Expanded Permission Evaluation",
  "phase36-memory-evaluation": "Expanded Memory Evaluation",
  "phase36-memory-permission-boundary": "Memory Permission Boundary",
  "phase38-answer-quality-remediation-v8": "Answer Quality Remediation v8",
  "phase38-permission-evaluation": "Permission Safety Remediation",
};

function parsePhaseNumber(value: string | number | null | undefined): number | null {
  if (value === null || value === undefined || value === "") return null;
  if (typeof value === "number") return Number.isFinite(value) ? value : null;
  const match = value.match(/phase[-\s]?(\d+)/i);
  if (!match) return null;
  const parsed = Number.parseInt(match[1], 10);
  return Number.isFinite(parsed) ? parsed : null;
}

export function normalizePhaseId(value: string | number | null | undefined): string | null {
  const number = parsePhaseNumber(value);
  return number === null ? null : `phase-${number}`;
}

export function getPhaseMeta(value: string | number | null | undefined): PhaseMeta | null {
  const normalized = normalizePhaseId(value);
  if (normalized) return PHASE_BY_ID.get(normalized) ?? PHASE_BY_NUMBER.get(parsePhaseNumber(value) ?? -1) ?? null;
  return null;
}

export function formatPhaseLabel(value: string | number | null | undefined): string {
  const meta = getPhaseMeta(value);
  if (meta) return `${meta.label} (Phase ${meta.number})`;
  const number = parsePhaseNumber(value);
  if (number !== null) return `Phase ${number}`;
  if (value === null || value === undefined || value === "") return "n/a";
  return String(value);
}

function titleCaseWords(value: string): string {
  return value
    .replaceAll("_", " ")
    .replaceAll("-", " ")
    .replace(/\btop\s+(\d+)\b/gi, "top-$1")
    .replace(/\bv(\d+)\b/gi, "v$1")
    .replace(/\b\w/g, (letter) => letter.toUpperCase())
    .replace(/\bV(\d+)\b/g, "v$1")
    .replace(/\bTop-(\d+)\b/g, "top-$1");
}

function cleanRunName(value: string): string {
  const withoutPhasePrefix = value.replace(/^phase[-\s]?\d+[-\s]?/i, "");
  return titleCaseWords(withoutPhasePrefix || value);
}

function runIdFromInput(input: RunLike | string | null | undefined): string | null {
  if (!input) return null;
  if (typeof input === "string") return input;
  return input.run_id ?? null;
}

export function formatRunLabel(input: RunLike | string | null | undefined): string {
  const runId = runIdFromInput(input);
  if (runId && RUN_LABEL_OVERRIDES[runId]) return RUN_LABEL_OVERRIDES[runId];

  if (typeof input === "object" && input?.run_name) {
    const byName = RUN_LABEL_OVERRIDES[input.run_name];
    if (byName) return byName;
    return cleanRunName(input.run_name);
  }

  if (runId) {
    const withoutPhasePrefix = runId.replace(/^phase[-\s]?\d+[-\s]?/i, "");
    return cleanRunName(withoutPhasePrefix || runId);
  }

  return "n/a";
}

export function getRunSummary(input: RunLike | string | null | undefined): string {
  if (!input || typeof input === "string") return formatRunLabel(input);

  const parts = [formatRunLabel(input)];
  if (input.phase) parts.push(formatPhaseLabel(input.phase));
  const sample = input.sample_size ?? input.total_questions;
  if (sample !== null && sample !== undefined) parts.push(`n=${sample}`);
  if (input.benchmark_version) parts.push(`benchmark ${input.benchmark_version}`);
  return parts.join(" | ");
}
