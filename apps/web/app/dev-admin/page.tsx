import { MetricCard } from "@/components/MetricCard";
import { RetrievalChart } from "@/components/RetrievalChart";
import { RunTable } from "@/components/RunTable";
import { Shell } from "@/components/Shell";
import { PageHeader } from "@/components/PageHeader";
import { Card } from "@/components/Card";
import { PhaseLabel, RunLabel } from "@/components/PhaseLabel";
import { SectionHeading } from "@/components/SectionHeading";
import { formatDateTime, formatIntegerMetric, formatLabel, formatMetric, getDashboardData, MetricContext } from "@/lib/dashboard";
import { formatRunLabel } from "@/lib/phases";
import { serverDemoAuthHeaders } from "@/lib/serverDemoAuth";
import Link from "next/link";

const proofPath = [
  {
    title: "Algorithm comparison",
    detail: "Named profiles show historical metrics, live source coverage, citations, latency, cost signals, and review notes.",
    href: "/dev-admin/retrieval-playground",
  },
  {
    title: "Failure inspection",
    detail: "Failed benchmark questions keep expected answers, actual answers, citations, root causes, fixes, and human review labels together.",
    href: "/dev-admin/failed-questions",
  },
  {
    title: "Permission safety",
    detail: "Role-restricted questions demonstrate that unauthorized chunks do not reach generation.",
    href: "/dev-admin/permission-safety",
  },
];

const metricLabels: Record<string, string> = {
  retrieval_hit_rate: "Source Recall",
  precision_at_k: "Precision@k",
  mrr: "MRR / First Source Rank",
  answer_accuracy: "Answer Accuracy",
  citation_accuracy: "Citation Accuracy",
  hallucination_rate: "Hallucination Rate",
  permission_leakage_rate: "Permission Leakage Rate",
  memory_accuracy: "Memory Answer Accuracy",
};

function contextLine(context?: MetricContext): string {
  const sample = context?.sample_size ?? "not measured";
  const failed = context?.failed_count ?? "not available";
  const version = context?.benchmark_version ?? "not available";
  return `Run: ${formatRunLabel(context)} | n=${sample} | failed=${failed} | benchmark ${version}`;
}

function sortedBreakdown(breakdown?: Record<string, number | null> | null): Array<[string, number | null]> {
  return Object.entries(breakdown ?? {}).sort(([a], [b]) => a.localeCompare(b));
}

function gateLabel(value: boolean | null | undefined): string {
  if (value === true) return "pass";
  if (value === false) return "fail";
  return "pending";
}

function deltaText(value: number | null | undefined, direction?: "higher" | "lower"): string {
  if (value === null || value === undefined) return "pending";
  const signed = value > 0 ? `+${value.toFixed(3)}` : value.toFixed(3);
  if (direction === "lower") return value <= 0 ? `${signed} better` : `${signed} worse`;
  return value >= 0 ? `${signed} better` : `${signed} worse`;
}

function targetTone(passed: boolean | null | undefined): string {
  if (passed === true) return "text-moss-dark";
  if (passed === false) return "text-rust-dark";
  return "text-stone-600";
}

function HelpMarker({ label }: { label: string }) {
  return (
    <span
      aria-label={label}
      title={label}
      className="ml-1 inline-flex h-4 w-4 cursor-help items-center justify-center rounded-full border border-stone-300 text-[10px] font-semibold text-stone-500"
    >
      ?
    </span>
  );
}

export default async function OverviewPage() {
  const authHeaders = await serverDemoAuthHeaders();
  const data = await getDashboardData(authHeaders);
  const metrics = data.overview.headline_metrics;
  const metricContext = data.overview.metric_context ?? {};
  const benchmarkContext = data.benchmark_context ?? {};
  const currentAnswerRun = data.runs.find((run) => run.run_id === data.overview.current_answer_run_id);
  const currentRunCategoryBreakdown = sortedBreakdown(currentAnswerRun?.category_breakdown);
  const benchmarkCategoryBreakdown = sortedBreakdown(benchmarkContext.category_breakdown);
  const suiteSizes = Object.entries(benchmarkContext.current_dashboard_suites ?? {});
  const scorecard = data.regression_scorecard;
  const scorecardMetrics = scorecard?.metrics ?? [];
  const scorecardFailures = Object.entries(scorecard?.failed_question_summary?.failure_reason_counts ?? {}).sort(([a], [b]) =>
    a.localeCompare(b)
  );
  const phase33 = data.phase33_precision_readiness;
  const phase33Live = phase33?.live_candidate;
  const phase33Permission = phase33?.permission_candidate;
  const phase33Replay = phase33?.best_saved_top5_lexical_rerank_replay;
  const phase33Primary = phase33Live ?? phase33Replay;
  const phase33Commands = phase33?.required_live_commands ?? [];
  const progressSummary = data.overview.progress_summary ?? {
    improved: [
      "Permission tests reached zero leakage.",
      "Memory follow-up tests reached full accuracy.",
      "Chat-generation cost tracking is implemented.",
    ],
    still_needs_work: [
      "Hybrid retrieval still did not beat vector-only overall.",
      `${data.overview.current_failed_question_count ?? data.failed_questions.length} failed-question cases remain in the current improvement backlog.`,
      "Embedding, infrastructure, cached-input, and batch cost modeling remain pending.",
    ],
  };

  return (
    <Shell>
      <PageHeader
        title="Measured Enterprise RAG Progress"
        description={
          <>
            <p className="text-lg text-stone-800">
              A permission-aware enterprise RAG assistant with citations, confidence scoring, benchmark evaluation, and interactive demos.
            </p>
            <p className="mt-3 text-stone-700">
              This dashboard compares real evaluation runs across retrieval, answer quality, citations, permission safety, and memory.
            </p>
          </>
        }
        actions={
          <>
            <Link href="/chat" className="btn-primary">
              Try Chat Demo
            </Link>
            <Link href="/dev-admin/permission-demo" className="btn-secondary">
              Run Permission Demo
            </Link>
            <Link href="/dev-admin/retrieval-playground" className="btn-secondary">
              Open Algorithm Lab
            </Link>
          </>
        }
      />
      <section className="mb-8 grid gap-4 lg:grid-cols-2">
        <Card>
          <SectionHeading
            title="Proof Without Hiding Failures"
            description="Dev & Admin is the evidence layer behind the App demo: benchmark outputs, known misses, review decisions, and audit trails stay visible."
          />
          <p className="text-sm leading-6 text-stone-700">
            The App side shows a usable project workspace. This surface shows whether the assistant is safe enough to trust, where it still fails, and what evidence supports any retrieval or prompt change.
          </p>
        </Card>
        <div className="grid gap-4 md:grid-cols-3">
          {proofPath.map((item) => (
            <Card key={item.title} padding="compact" className="flex h-full flex-col justify-between">
              <div>
                <p className="font-semibold text-ink">{item.title}</p>
                <p className="mt-2 text-sm leading-6 text-stone-700">{item.detail}</p>
              </div>
              <Link href={item.href} className="btn-secondary btn-sm mt-4 self-start">
                Open
              </Link>
            </Card>
          ))}
        </div>
      </section>
      <section className="grid gap-4 md:grid-cols-2 xl:grid-cols-4">
        <MetricCard
          label="Source Recall"
          value={metrics.retrieval_hit_rate}
          detail="Expected-source coverage."
          context={contextLine(metricContext.retrieval_hit_rate)}
          badge="Best"
          tone="good"
        />
        <MetricCard
          label="Precision@k"
          value={metrics.precision_at_k}
          detail="Expected-source chunks in top-k."
          context={contextLine(metricContext.precision_at_k)}
        />
        <MetricCard
          label="MRR / First Source Rank"
          value={metrics.mrr}
          detail="Rank quality for first expected source."
          context={contextLine(metricContext.mrr)}
        />
        <MetricCard
          label="Answer Accuracy"
          value={metrics.answer_accuracy}
          detail="Deterministic answer scoring."
          context={contextLine(metricContext.answer_accuracy)}
        />
        <MetricCard
          label="Citation Accuracy"
          value={metrics.citation_accuracy}
          detail="Citations match expected documents."
          context={contextLine(metricContext.citation_accuracy)}
        />
        <MetricCard
          label="Hallucination Rate"
          value={metrics.hallucination_rate}
          detail="Unsupported-answer signal."
          context={contextLine(metricContext.hallucination_rate)}
          badge="Risk"
          tone="warn"
        />
        <MetricCard
          label="Permission Leakage Rate"
          value={metrics.permission_leakage_rate}
          detail="Restricted-source leakage."
          context={contextLine(metricContext.permission_leakage_rate)}
          badge="Safety"
          tone="good"
        />
        <MetricCard
          label="Memory Answer Accuracy"
          value={metrics.memory_accuracy}
          detail="Follow-up benchmark answers."
          context={contextLine(metricContext.memory_accuracy)}
          tone="good"
        />
      </section>
      {scorecardMetrics.length > 0 ? (
        <section className="mt-8">
          <Card>
            <div>
              <div>
                <SectionHeading
                  title="Regression Scorecard"
                  description="Baseline-vs-current metrics use measured run IDs, exact sample sizes, benchmark versions, and visible failures."
                />
                <div className="overflow-x-auto">
                  <table className="data-table min-w-[920px]">
                    <thead>
                      <tr>
                        <th>Metric</th>
                        <th>
                          Pre-Optimization Baseline
                          <HelpMarker label="Baseline runs were captured before retrieval reranking, answer grounding, citation alignment, and expanded permission/memory evaluations." />
                        </th>
                        <th>Current</th>
                        <th className="text-right">Delta</th>
                        <th>Target</th>
                        <th>Status</th>
                      </tr>
                    </thead>
                    <tbody>
                      {scorecardMetrics.map((item) => (
                        <tr key={item.metric_key}>
                          <td>
                            <p className="font-medium text-ink">{item.label}</p>
                            <p className="mt-1 text-xs text-stone-500">{item.notes}</p>
                          </td>
                          <td>
                            <p className="font-medium text-ink">{formatMetric(item.baseline.value)}</p>
                            <p className="mt-1 text-xs text-stone-500">
                              {formatRunLabel(item.baseline)} | n={item.baseline.sample_size ?? "n/a"} | benchmark{" "}
                              {item.baseline.benchmark_version ?? "n/a"}
                            </p>
                            {item.baseline.run_id ? <p className="mt-1 text-xs text-stone-400">{item.baseline.run_id}</p> : null}
                          </td>
                          <td>
                            <p className="font-medium text-ink">{formatMetric(item.current.value)}</p>
                            <p className="mt-1 text-xs text-stone-500">
                              {formatRunLabel(item.current)} | n={item.current.sample_size ?? "n/a"} | benchmark{" "}
                              {item.current.benchmark_version ?? "n/a"}
                            </p>
                            {item.current.run_id ? <p className="mt-1 text-xs text-stone-400">{item.current.run_id}</p> : null}
                          </td>
                          <td className="text-right font-medium text-ink">{deltaText(item.delta, item.direction)}</td>
                          <td>{item.target_label ?? formatMetric(item.target)}</td>
                          <td className={targetTone(item.target_passed)}>{gateLabel(item.target_passed)}</td>
                        </tr>
                      ))}
                    </tbody>
                  </table>
                </div>
              </div>
              <div className="mt-6">
                <aside className="rounded-md border border-stone-300 bg-stone-50">
                  <div className="border-b border-stone-200 p-4">
                    <p className="font-semibold text-ink">Proof Summary</p>
                    <p className="mt-1 text-sm leading-5 text-stone-600">
                      Claims, failures, and known limits stay visible next to the measured scorecard.
                    </p>
                  </div>
                  <div className="grid gap-5 bg-white p-4 text-sm leading-6 text-stone-700 lg:grid-cols-3">
                    <section className="border-l-4 border-moss pl-3">
                      <p className="font-semibold text-moss-dark">Supported Claims</p>
                      <p className="mt-1 text-xs font-medium uppercase tracking-wide text-stone-500">
                        Backed by measured runs and benchmark evidence
                      </p>
                      <ul className="mt-2 list-disc space-y-2 pl-4">
                        {(scorecard?.portfolio_claims ?? []).map((claim) => (
                          <li key={claim}>{claim}</li>
                        ))}
                      </ul>
                    </section>
                    <section className="border-l-4 border-stone-300 pl-3">
                      <p className="font-semibold text-ink">Current Failures</p>
                      <p className="mt-1 text-stone-700">
                        {scorecard?.failed_question_summary?.failed_question_count ?? "not available"} failed questions in{" "}
                        {formatRunLabel(scorecard?.failed_question_summary?.current_answer_run_id ?? null)}.
                      </p>
                      {scorecardFailures.length ? (
                        <ul className="mt-3 space-y-2">
                          {scorecardFailures.map(([reason, count]) => (
                            <li key={reason} className="flex justify-between gap-3 border-b border-stone-200 pb-1 last:border-b-0 last:pb-0">
                              <span>{formatLabel(reason)}</span>
                              <span className="font-medium text-ink">{count}</span>
                            </li>
                          ))}
                        </ul>
                      ) : (
                        <p className="mt-2 text-stone-600">No failure reasons are reported for the current scorecard run.</p>
                      )}
                    </section>
                    <section className="border-l-4 border-rust pl-3">
                      <p className="font-semibold text-rust-dark">Limitations</p>
                      <p className="mt-1 text-xs font-medium uppercase tracking-wide text-stone-500">Known boundaries</p>
                      <ul className="mt-2 list-disc space-y-2 pl-4">
                        {(scorecard?.limitations ?? []).map((item) => (
                          <li key={item}>{item}</li>
                        ))}
                      </ul>
                    </section>
                  </div>
                </aside>
              </div>
            </div>
          </Card>
        </section>
      ) : null}
      <section className="mt-8 grid gap-4 lg:grid-cols-2">
        <Card>
          <SectionHeading
            title="Metric Context"
            description="Headline metrics keep their source run, sample size, benchmark version, and timestamp visible."
          />
          <div className="overflow-x-auto">
            <table className="data-table min-w-[760px]">
              <thead>
                <tr>
                  <th>Metric</th>
                  <th>Run</th>
                  <th className="text-right">Sample</th>
                  <th className="text-right">Passed</th>
                  <th className="text-right">Failed</th>
                  <th>Benchmark</th>
                  <th>Run Timestamp</th>
                </tr>
              </thead>
              <tbody>
                {Object.entries(metricLabels).map(([key, label]) => {
                  const context = metricContext[key];
                  return (
                    <tr key={key}>
                      <td className="font-medium text-ink">{label}</td>
                      <td>
                        <RunLabel run={context} />
                      </td>
                      <td className="text-right">{context?.sample_size ?? "not measured"}</td>
                      <td className="text-right">{context?.passed_count ?? "not available"}</td>
                      <td className="text-right">{context?.failed_count ?? "not available"}</td>
                      <td>{context?.benchmark_version ?? "not available"}</td>
                      <td>{formatDateTime(context?.run_timestamp)}</td>
                    </tr>
                  );
                })}
              </tbody>
            </table>
          </div>
        </Card>
        <Card>
          <SectionHeading title="Benchmark And Suites" description="Dashboard runs are subsets of the current source corpus." />
          <dl className="grid gap-3 text-sm">
            <div className="flex items-center justify-between gap-4">
              <dt className="text-stone-600">Benchmark version</dt>
              <dd className="font-semibold text-ink">{benchmarkContext.benchmark_version ?? "not available"}</dd>
            </div>
            <div className="flex items-center justify-between gap-4">
              <dt className="text-stone-600">Source corpus questions</dt>
              <dd className="font-semibold text-ink">{benchmarkContext.corpus_question_count ?? "not available"}</dd>
            </div>
            {suiteSizes.map(([key, value]) => (
              <div key={key} className="flex items-center justify-between gap-4">
                <dt className="text-stone-600">{formatLabel(key)}</dt>
                <dd className="font-semibold text-ink">{value ?? "not measured"}</dd>
              </div>
            ))}
          </dl>
          <div className="mt-5">
            <p className="font-semibold text-ink">Corpus categories</p>
            <div className="mt-2 grid grid-cols-2 gap-2 text-sm text-stone-700">
              {benchmarkCategoryBreakdown.map(([category, count]) => (
                <div key={category} className="flex justify-between gap-3 border-b border-stone-200 pb-1">
                  <span>{formatLabel(category)}</span>
                  <span className="font-medium text-ink">{count ?? "n/a"}</span>
                </div>
              ))}
            </div>
          </div>
          <div className="mt-5">
            <p className="font-semibold text-ink">Current answer run categories</p>
            <p className="mt-1 text-xs text-stone-500">
              {formatRunLabel(currentAnswerRun)}
              {currentAnswerRun?.run_id ? <span className="block text-stone-400">{currentAnswerRun.run_id}</span> : null}
            </p>
            <div className="mt-2 grid grid-cols-2 gap-2 text-sm text-stone-700">
              {currentRunCategoryBreakdown.length > 0 ? (
                currentRunCategoryBreakdown.map(([category, count]) => (
                  <div key={category} className="flex justify-between gap-3 border-b border-stone-200 pb-1">
                    <span>{formatLabel(category)}</span>
                    <span className="font-medium text-ink">{count ?? "n/a"}</span>
                  </div>
                ))
              ) : (
                <p className="col-span-2 text-stone-600">not available</p>
              )}
            </div>
          </div>
        </Card>
      </section>
      {phase33 && Object.keys(phase33).length > 0 ? (
        <section className="mt-8 grid gap-4 lg:grid-cols-2">
          <Card tone={phase33.publishable_improvement ? "good" : "warn"}>
            <SectionHeading
              title={<PhaseLabel phase="phase-33" />}
              description="Live retrieval and permission gates are shown first; saved replay remains as candidate-selection evidence."
            />
            <dl className="grid gap-3 text-sm">
              <div className="flex items-center justify-between gap-4">
                <dt className="text-stone-600">Status</dt>
                <dd className="font-semibold text-rust-dark">{formatLabel(phase33.status)}</dd>
              </div>
              <div className="flex items-center justify-between gap-4">
                <dt className="text-stone-600">Candidate mode</dt>
                <dd className="font-semibold text-ink">{phase33.candidate_mode ?? "not available"}</dd>
              </div>
              <div className="flex items-center justify-between gap-4">
                <dt className="text-stone-600">Live run required</dt>
                <dd className="font-semibold text-ink">{phase33.live_run_required ? "yes" : "no"}</dd>
              </div>
              <div className="flex items-center justify-between gap-4">
                <dt className="text-stone-600">Publishable improvement</dt>
                <dd className="font-semibold text-ink">{phase33.publishable_improvement ? "yes" : "no"}</dd>
              </div>
              <div className="flex items-center justify-between gap-4">
                <dt className="text-stone-600">Benchmark</dt>
                <dd className="font-semibold text-ink">{phase33.benchmark_version ?? "not available"}</dd>
              </div>
              <div className="flex items-center justify-between gap-4">
                <dt className="text-stone-600">Live run</dt>
                <dd className="font-semibold text-ink">{formatRunLabel(phase33Live?.run_name ?? phase33.candidate_run_id ?? null)}</dd>
              </div>
            </dl>
            <p className="mt-4 text-xs leading-5 text-stone-600">
              Source: {phase33.diagnostic_source ?? "not available"} from {formatRunLabel(phase33.input_run_id ?? null)}
              {phase33.input_run_id ? <span className="block text-stone-400">{phase33.input_run_id}</span> : null}
            </p>
          </Card>
          <Card>
            <SectionHeading
              title={phase33Live ? "Live Candidate Gates" : "Best Saved Rerank Replay"}
              description={
                phase33Live
                  ? "These metrics come from the live vector/lexical rerank run and matching permission safety report."
                  : (
                    <>
                      These numbers reorder only the saved <PhaseLabel phase="phase-32" /> top-5 chunks; live retrieval and permission safety
                      are still pending.
                    </>
                  )
              }
            />
            <div className="grid gap-3 sm:grid-cols-4">
              {[
                {
                  label: "Precision@k",
                  value: phase33Primary?.precision_at_k,
                  detail: `Target ${formatMetric(phase33.gates?.precision_at_k_target)}`,
                  passed: phase33Primary?.meets_precision_target,
                },
                {
                  label: "Source Recall",
                  value: phase33Primary?.expected_source_recall,
                  detail: `Gate ${formatMetric(phase33.gates?.expected_source_recall_minimum)}`,
                  passed: phase33Primary?.meets_recall_gate,
                },
                {
                  label: "MRR",
                  value: phase33Primary?.mrr,
                  detail: `Gate ${formatMetric(phase33.gates?.mrr_minimum)}`,
                  passed: phase33Primary?.meets_mrr_gate,
                },
                {
                  label: "Failed Source Questions",
                  value: phase33Primary?.failed_question_count,
                  detail: `Top-k ${phase33Primary?.top_k ?? "pending"}`,
                  passed: undefined,
                  integer: true,
                },
              ].map((item) => (
                <div key={item.label} className="rounded-md border border-stone-200 bg-stone-50 p-3">
                  <p className="text-xs font-medium text-steel">{item.label}</p>
                  <p className={item.passed === false ? "mt-1 text-2xl font-semibold text-rust-dark" : "mt-1 text-2xl font-semibold text-ink"}>
                    {item.integer ? formatIntegerMetric(item.value) : formatMetric(item.value)}
                  </p>
                  <p className="mt-1 text-xs text-stone-600">{item.detail}</p>
                </div>
              ))}
            </div>
            <div className="mt-5 overflow-x-auto">
              <table className="data-table min-w-[620px]">
                <thead>
                  <tr>
                    <th>Gate</th>
                    <th className="text-right">Value</th>
                    <th className="text-right">Required</th>
                    <th>Status</th>
                  </tr>
                </thead>
                <tbody>
                  <tr>
                    <td>Precision@k</td>
                    <td className="text-right">{formatMetric(phase33Primary?.precision_at_k)}</td>
                    <td className="text-right">{formatMetric(phase33.gates?.precision_at_k_target)}</td>
                    <td>{gateLabel(phase33Primary?.meets_precision_target)}</td>
                  </tr>
                  <tr>
                    <td>Source recall</td>
                    <td className="text-right">{formatMetric(phase33Primary?.expected_source_recall)}</td>
                    <td className="text-right">{formatMetric(phase33.gates?.expected_source_recall_minimum)}</td>
                    <td>{gateLabel(phase33Primary?.meets_recall_gate)}</td>
                  </tr>
                  <tr>
                    <td>MRR</td>
                    <td className="text-right">{formatMetric(phase33Primary?.mrr)}</td>
                    <td className="text-right">{formatMetric(phase33.gates?.mrr_minimum)}</td>
                    <td>{gateLabel(phase33Primary?.meets_mrr_gate)}</td>
                  </tr>
                  <tr>
                    <td>Permission leakage</td>
                    <td className="text-right">{formatMetric(phase33Permission?.permission_leakage_rate)}</td>
                    <td className="text-right">{formatMetric(phase33.gates?.permission_leakage_rate)}</td>
                    <td>{gateLabel(phase33Permission?.permission_leakage_rate === 0)}</td>
                  </tr>
                  <tr>
                    <td>Blocked-answer accuracy</td>
                    <td className="text-right">{formatMetric(phase33Permission?.blocked_answer_accuracy)}</td>
                    <td className="text-right">{formatMetric(phase33.gates?.blocked_answer_accuracy_target)}</td>
                    <td>{gateLabel(phase33Permission?.blocked_answer_accuracy === 1)}</td>
                  </tr>
                </tbody>
              </table>
            </div>
            {phase33Commands.length > 0 ? (
              <div className="mt-5">
                <p className="font-semibold text-ink">{phase33.live_run_required ? "Required live checks" : "Completed live checks"}</p>
                <ul className="mt-2 space-y-2 text-sm text-stone-700">
                  {phase33Commands.map((command) => (
                    <li key={command}>
                      <code className="rounded bg-stone-100 px-1 py-0.5">{command}</code>
                    </li>
                  ))}
                </ul>
              </div>
            ) : null}
          </Card>
        </section>
      ) : null}
      <section className="mt-8 grid gap-4 lg:grid-cols-2">
        <RetrievalChart runs={data.runs} />
        <Card>
          <SectionHeading title="What Improved / Still Needs Work" />
          <div className="grid gap-4 md:grid-cols-2">
            <div>
              <p className="font-semibold text-moss-dark">Improved</p>
              <ul className="mt-2 space-y-2 text-sm text-stone-700">
                {progressSummary.improved.map((item) => (
                  <li key={item}>{item}</li>
                ))}
              </ul>
            </div>
            <div>
              <p className="font-semibold text-rust-dark">Still Needs Work</p>
              <ul className="mt-2 space-y-2 text-sm text-stone-700">
                {progressSummary.still_needs_work.map((item) => (
                  <li key={item}>{item}</li>
                ))}
              </ul>
            </div>
          </div>
        </Card>
      </section>
      <section className="mt-8">
        <SectionHeading title="Evaluation Runs" />
        <RunTable runs={data.runs} bestRunName={data.overview.best_retrieval_run} />
      </section>
    </Shell>
  );
}
