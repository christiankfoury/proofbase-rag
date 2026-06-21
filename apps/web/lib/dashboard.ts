export type Metrics = Record<string, number | string | null | undefined>;

export type EvalRun = {
  run_id: string;
  run_name: string;
  phase: string;
  run_type: string;
  timestamp: string;
  run_timestamp?: string | null;
  retrieval_mode?: string | null;
  chunking_strategy?: string | null;
  top_k?: number | null;
  prompt_name?: string | null;
  prompt_version?: string | null;
  prompt_status?: string | null;
  prompt_change_notes?: string | null;
  model?: string | null;
  temperature?: number | null;
  total_questions?: number | null;
  sample_size?: number | null;
  passed_count?: number | null;
  failed_count?: number | null;
  benchmark_version?: string | null;
  category_breakdown?: Record<string, number | null> | null;
  question_filter?: string | null;
  source_question_count?: number | null;
  metrics: Metrics;
  failed_questions?: string[];
  notes?: string;
};

export type PromptComparison = {
  best?: {
    best_overall?: string;
    lowest_hallucination?: string;
    best_citations?: string;
  };
  comparisons?: Array<{
    baseline_version: string;
    candidate_version: string;
    fixed_questions: string[];
    broken_questions: string[];
    still_failing: string[];
  }>;
  prompt_versions?: Array<Record<string, unknown>>;
};

export type FailedQuestion = {
  phase: string;
  question_id: string;
  failure_type: string;
  recommended_fix: string;
  expected_behavior?: string;
  actual_response_type?: string;
  citation_confidence?: number | null;
  answer_confidence?: number | null;
};

export type MultiDocComparison = {
  baseline?: {
    multi_doc_question_count?: number;
    answer_accuracy?: number | null;
    citation_accuracy?: number | null;
    all_sources_hit?: number | null;
    source_coverage_score?: number | null;
    hallucination_rate?: number | null;
    response_type_accuracy?: number | null;
    all_required_sources_cited_rate?: number | null;
    failed_question_count?: number;
  };
  multi_doc?: {
    multi_doc_question_count?: number;
    answer_accuracy?: number | null;
    citation_accuracy?: number | null;
    all_sources_hit?: number | null;
    source_coverage_score?: number | null;
    hallucination_rate?: number | null;
    response_type_accuracy?: number | null;
    all_required_sources_cited_rate?: number | null;
    failed_question_count?: number;
  };
  fixed_questions?: string[];
  broken_questions?: string[];
  still_failing?: string[];
  hallucination_regression?: boolean;
};

export type Phase33PrecisionReadiness = {
  status?: string;
  phase?: string;
  generated_at?: string | null;
  benchmark_version?: string | null;
  diagnostic_source?: string | null;
  input_run_id?: string | null;
  candidate_mode?: string | null;
  candidate_run_id?: string | null;
  live_run_required?: boolean;
  publishable_improvement?: boolean;
  gates?: {
    precision_at_k_target?: number | null;
    expected_source_recall_minimum?: number | null;
    mrr_minimum?: number | null;
    permission_leakage_rate?: number | null;
    blocked_answer_accuracy_target?: number | null;
  };
  live_candidate?: Phase33LiveCandidate | null;
  permission_candidate?: Phase33PermissionCandidate | null;
  best_top_k_replay?: Phase33ReplaySummary | null;
  best_saved_top5_lexical_rerank_replay?: Phase33ReplaySummary | null;
  top_k_replay?: Phase33ReplaySummary[];
  saved_top5_lexical_rerank_replay?: Phase33ReplaySummary[];
  required_live_commands?: string[];
  notes?: string[];
};

export type Phase33LiveCandidate = Phase33ReplaySummary & {
  run_uuid?: string | null;
  run_name?: string | null;
  generated_at?: string | null;
  question_count?: number | null;
  retrieval_mode?: string | null;
  average_latency_ms?: number | null;
  failed_question_ids?: string[];
};

export type Phase33PermissionCandidate = {
  restricted_question_count?: number | null;
  authorized_test_count?: number | null;
  permission_leakage_rate?: number | null;
  blocked_answer_accuracy?: number | null;
  unauthorized_chunk_exposure_rate?: number | null;
  restricted_citation_leakage_rate?: number | null;
  unauthorized_chunks_reached_generation_rate?: number | null;
  authorized_retrieval_accuracy?: number | null;
  authorized_answer_accuracy?: number | null;
};

export type Phase33ReplaySummary = {
  top_k?: number | null;
  precision_at_k?: number | null;
  expected_source_recall?: number | null;
  all_sources_hit?: number | null;
  mrr?: number | null;
  failed_question_count?: number | null;
  meets_precision_target?: boolean | null;
  meets_recall_gate?: boolean | null;
  meets_mrr_gate?: boolean | null;
};

export type MetricContext = {
  run_id?: string | null;
  run_name?: string | null;
  metric_key?: string | null;
  sample_size?: number | null;
  passed_count?: number | null;
  failed_count?: number | null;
  benchmark_version?: string | null;
  run_timestamp?: string | null;
  category_breakdown?: Record<string, number | null> | null;
};

export type BenchmarkContext = {
  benchmark_version?: string | null;
  source_corpus?: string | null;
  corpus_question_count?: number | null;
  category_breakdown?: Record<string, number | null> | null;
  current_dashboard_suites?: Record<string, number | null> | null;
};

export type RegressionScorecardMetric = {
  metric_key: string;
  label: string;
  direction: "higher" | "lower";
  target?: number | null;
  target_label?: string | null;
  baseline: MetricContext & { value?: number | string | null };
  current: MetricContext & { value?: number | string | null };
  delta?: number | null;
  target_passed?: boolean | null;
  notes?: string | null;
};

export type RegressionScorecard = {
  phase?: string;
  generated_at?: string | null;
  benchmark_version?: string | null;
  benchmark_question_count?: number | null;
  category_breakdown?: Record<string, number | null> | null;
  baseline_run_ids?: string[];
  current_run_ids?: string[];
  metrics?: RegressionScorecardMetric[];
  failed_question_summary?: {
    current_answer_run_id?: string | null;
    failed_question_count?: number | null;
    failure_reason_counts?: Record<string, number>;
    failed_question_ids?: string[];
  };
  safety_summary?: Record<string, number | string | null | undefined>;
  portfolio_claims?: string[];
  limitations?: string[];
};

export type DashboardData = {
  generated_at: string;
  benchmark_context?: BenchmarkContext;
  overview: {
    best_retrieval_run: string;
    retrieval_conclusion: string;
    current_answer_run_id?: string | null;
    current_failed_question_count?: number | null;
    progress_summary?: {
      improved: string[];
      still_needs_work: string[];
    };
    headline_metrics: Metrics;
    metric_context?: Record<string, MetricContext>;
  };
  comparisons: Record<string, { summary: string; runs?: string[]; baseline?: string; current?: string }>;
  regression_scorecard?: RegressionScorecard;
  prompt_comparison?: PromptComparison;
  multi_doc_comparison?: MultiDocComparison;
  phase33_precision_readiness?: Phase33PrecisionReadiness;
  runs: EvalRun[];
  failed_questions: FailedQuestion[];
  notes: string[];
};

const API_BASE = process.env.NEXT_PUBLIC_API_BASE_URL ?? "http://127.0.0.1:8000";

function emptyDashboardData(): DashboardData {
  return {
    generated_at: "",
    overview: {
      best_retrieval_run: "",
      retrieval_conclusion: "",
      headline_metrics: {},
      metric_context: {},
    },
    benchmark_context: {},
    comparisons: {},
    regression_scorecard: {},
    phase33_precision_readiness: {},
    runs: [],
    failed_questions: [],
    notes: [],
  };
}

export async function getDashboardData(headers: HeadersInit = {}): Promise<DashboardData> {
  const response = await fetch(`${API_BASE}/evaluation/compare`, { cache: "no-store", headers });
  if (!response.ok) {
    return emptyDashboardData();
  }
  const compare = await response.json();
  const failedResponse = await fetch(`${API_BASE}/evaluation/failed-questions`, { cache: "no-store", headers });
  const summaryResponse = await fetch(`${API_BASE}/evaluation/summary`, { cache: "no-store", headers });
  const failed = failedResponse.ok ? await failedResponse.json() : { failed_questions: [] };
  const summary = summaryResponse.ok ? await summaryResponse.json() : { generated_at: "", notes: [] };
  return {
    generated_at: summary.generated_at,
    overview: compare.overview,
    benchmark_context: compare.benchmark_context ?? summary.benchmark_context ?? {},
    comparisons: compare.comparisons,
    regression_scorecard: compare.regression_scorecard ?? summary.regression_scorecard,
    prompt_comparison: compare.prompt_comparison,
    multi_doc_comparison: compare.multi_doc_comparison,
    phase33_precision_readiness: compare.phase33_precision_readiness ?? summary.phase33_precision_readiness,
    runs: compare.runs,
    failed_questions: failed.failed_questions,
    notes: summary.notes ?? [],
  };
}

export function formatMetric(value: number | string | null | undefined): string {
  if (value === null || value === undefined || value === "") return "pending";
  if (typeof value === "number") return value.toFixed(3);
  return value;
}

export function formatTableMetric(value: number | string | null | undefined): string {
  if (value === null || value === undefined || value === "") return "-";
  if (typeof value === "string" && value.toLowerCase() === "pending") return "-";
  if (typeof value === "number") return value.toFixed(3);
  return value;
}

export function formatLabel(value: string | null | undefined): string {
  if (!value) return "n/a";
  return value
    .replaceAll("_", " ")
    .replaceAll("-", " ")
    .replace(/\b\w/g, (letter) => letter.toUpperCase());
}

export function formatDateTime(value: string | null | undefined): string {
  if (!value) return "not available";
  const parsed = new Date(value);
  if (Number.isNaN(parsed.getTime())) return value;
  return new Intl.DateTimeFormat("en-US", {
    month: "short",
    day: "numeric",
    year: "numeric",
    hour: "2-digit",
    minute: "2-digit",
    hour12: false,
    timeZone: "UTC",
    timeZoneName: "short",
  }).format(parsed);
}

/**
 * Returns a text color/weight class for rate-style metrics where lower is
 * better (hallucination rate, permission leakage rate, error rate). Used to
 * give risk signals visual emphasis instead of rendering as plain numbers.
 */
export function riskRateClass(
  value: number | string | null | undefined,
  { warnAt = 0.05, riskAt = 0.15 }: { warnAt?: number; riskAt?: number } = {}
): string {
  if (typeof value !== "number") return "text-stone-700";
  if (value >= riskAt) return "font-semibold text-red-600";
  if (value >= warnAt) return "font-semibold text-rust";
  return "text-moss-dark";
}

/**
 * Returns a text color/weight class for rate-style metrics where higher is
 * better (accuracy, recall, precision). Used to flag weak scores.
 */
export function goodRateClass(
  value: number | string | null | undefined,
  { warnBelow = 0.8, riskBelow = 0.6 }: { warnBelow?: number; riskBelow?: number } = {}
): string {
  if (typeof value !== "number") return "text-stone-700";
  if (value < riskBelow) return "font-semibold text-red-600";
  if (value < warnBelow) return "font-semibold text-rust";
  return "text-stone-700";
}
