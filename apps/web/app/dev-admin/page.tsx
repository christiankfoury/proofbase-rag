import { MetricCard } from "@/components/MetricCard";
import { RetrievalChart } from "@/components/RetrievalChart";
import { RunTable } from "@/components/RunTable";
import { Shell } from "@/components/Shell";
import { PageHeader } from "@/components/PageHeader";
import { Card } from "@/components/Card";
import { SectionHeading } from "@/components/SectionHeading";
import { formatDateTime, formatLabel, getDashboardData, MetricContext } from "@/lib/dashboard";
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
  return `Run ${context?.run_id ?? "not available"} | n=${sample} | failed=${failed} | benchmark ${version}`;
}

function sortedBreakdown(breakdown?: Record<string, number | null> | null): Array<[string, number | null]> {
  return Object.entries(breakdown ?? {}).sort(([a], [b]) => a.localeCompare(b));
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
      <section className="mb-8 grid gap-4 lg:grid-cols-[0.9fr_1.1fr]">
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
          detail="All expected sources retrieved."
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
      <section className="mt-8 grid gap-4 lg:grid-cols-[1.2fr_0.8fr]">
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
                  <th>Run ID</th>
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
                      <td>{context?.run_id ?? "not available"}</td>
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
              {currentAnswerRun?.run_id ?? "not available"}
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
      <Card tone="good" className="mt-8">
        <SectionHeading title="Experiment Conclusion" />
        <p className="text-stone-700">
          Vector retrieval with section-based chunks remains the best overall configuration; hybrid did not outperform it on this corpus.
        </p>
      </Card>
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
