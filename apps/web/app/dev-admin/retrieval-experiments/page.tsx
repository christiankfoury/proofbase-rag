import { Badge } from "@/components/Badge";
import { Card } from "@/components/Card";
import { MetricCard } from "@/components/MetricCard";
import { PageHeader } from "@/components/PageHeader";
import { RetrievalChart } from "@/components/RetrievalChart";
import { SectionHeading } from "@/components/SectionHeading";
import { Shell } from "@/components/Shell";
import { EvalRun, formatIntegerMetric, formatLabel, formatMetric, formatTableMetric, getDashboardData } from "@/lib/dashboard";
import { serverDemoAuthHeaders } from "@/lib/serverDemoAuth";

function RetrievalExperimentTable({ runs }: { runs: EvalRun[] }) {
  const sortedRuns = [...runs].sort((a, b) => {
    const aPrecision = typeof a.metrics.precision_at_k === "number" ? a.metrics.precision_at_k : -1;
    const bPrecision = typeof b.metrics.precision_at_k === "number" ? b.metrics.precision_at_k : -1;
    return bPrecision - aPrecision;
  });

  return (
    <div className="overflow-x-auto rounded-md border border-stone-300 bg-white shadow-card">
      <table className="data-table min-w-[980px]">
        <thead>
          <tr>
            <th>Run</th>
            <th>Retrieval</th>
            <th>Chunking</th>
            <th className="text-right">All Sources</th>
            <th className="text-right">Source Recall</th>
            <th className="text-right">Precision@k</th>
            <th className="text-right">MRR</th>
            <th className="text-right">Latency</th>
            <th>Failed</th>
          </tr>
        </thead>
        <tbody>
          {sortedRuns.map((run) => (
            <tr key={run.run_id}>
              <td className="whitespace-nowrap font-medium text-ink">
                <div className="flex flex-wrap items-center gap-2">
                  <span>{run.run_name}</span>
                  {run.run_id === "phase33-vector-lexical-rerank-top3" ? <Badge tone="solid">Best precision</Badge> : null}
                </div>
              </td>
              <td className="whitespace-nowrap">{formatLabel(run.retrieval_mode)}</td>
              <td className="whitespace-nowrap">{formatLabel(run.chunking_strategy)}</td>
              <td className="text-right">{formatTableMetric(run.metrics.all_sources_hit)}</td>
              <td className="text-right">{formatTableMetric(run.metrics.expected_source_recall)}</td>
              <td className="text-right">{formatTableMetric(run.metrics.precision_at_k)}</td>
              <td className="text-right">{formatTableMetric(run.metrics.mrr)}</td>
              <td className="text-right">{formatTableMetric(run.metrics.average_latency_ms)} ms</td>
              <td>{run.failed_questions?.length ? run.failed_questions.join(", ") : run.metrics.failed_question_count ? formatIntegerMetric(run.metrics.failed_question_count) : "None"}</td>
            </tr>
          ))}
        </tbody>
      </table>
    </div>
  );
}

export default async function RetrievalExperimentsPage() {
  const authHeaders = await serverDemoAuthHeaders();
  const data = await getDashboardData(authHeaders);
  const retrievalRuns = data.runs.filter((run) => run.phase === "phase-6");
  const precisionCandidate = data.runs.find((run) => run.run_id === "phase33-vector-lexical-rerank-top3");
  const chartRuns = precisionCandidate ? [...retrievalRuns, precisionCandidate] : retrievalRuns;
  const vector = retrievalRuns.find((run) => run.run_name === "vector-section");
  const keyword = retrievalRuns.find((run) => run.run_name === "keyword-section");
  const hybrid = retrievalRuns.find((run) => run.run_name === "hybrid-section-0.5");
  const fixed = retrievalRuns.find((run) => run.run_name === "vector-fixed-size");
  const bestPrecisionRun = [...chartRuns].sort((a, b) => {
    const aPrecision = typeof a.metrics.precision_at_k === "number" ? a.metrics.precision_at_k : -1;
    const bPrecision = typeof b.metrics.precision_at_k === "number" ? b.metrics.precision_at_k : -1;
    return bPrecision - aPrecision;
  })[0];
  const currentBenchmarkCount =
    data.benchmark_context?.corpus_question_count ?? precisionCandidate?.source_question_count ?? precisionCandidate?.total_questions;
  const currentBenchmarkVersion = data.benchmark_context?.benchmark_version ?? precisionCandidate?.benchmark_version;

  return (
    <Shell>
      <PageHeader
        title="Retrieval Experiments"
        description="Compare retrieval profiles across legacy Phase 6 experiments and the current expanded benchmark candidate."
      />
      <section className="grid gap-4 md:grid-cols-3">
        <MetricCard label="Best Precision Run" value={bestPrecisionRun?.run_name} detail={`Benchmark ${bestPrecisionRun?.benchmark_version ?? "n/a"} / n=${bestPrecisionRun?.sample_size ?? bestPrecisionRun?.total_questions ?? "n/a"}.`} badge="Best" tone="good" />
        <MetricCard label="Precision@k" value={bestPrecisionRun?.metrics.precision_at_k} detail="Highest score in this comparison." />
        <MetricCard label="MRR" value={bestPrecisionRun?.metrics.mrr} detail="Same current best-precision run." />
        <MetricCard label="Source Recall" value={bestPrecisionRun?.metrics.expected_source_recall} detail="Expected-source recall for the current reference run." />
        <MetricCard label="Avg Latency" value={`${formatMetric(bestPrecisionRun?.metrics.average_latency_ms)} ms`} detail="Average retrieval latency for the current reference run." />
        <MetricCard label="Source Failures" value={bestPrecisionRun?.metrics.failed_question_count ?? bestPrecisionRun?.failed_questions?.length} detail="Source-coverage misses in the current reference run." tone="warn" format="integer" />
      </section>
      <section className="mt-8 grid gap-4 lg:grid-cols-3">
        <Card>
          <SectionHeading title="Experiment Setup" />
          <ul className="space-y-2 text-sm text-stone-700">
            <li>
              Legacy Phase 6 comparison: {vector?.total_questions ?? "pending"} benchmark {vector?.benchmark_version ?? "n/a"} retrieval questions.
            </li>
            <li>
              Current expanded benchmark: {currentBenchmarkCount ?? "pending"} benchmark {currentBenchmarkVersion ?? "n/a"} questions.
            </li>
            <li>Compared retrieval-only metrics to avoid extra generation cost.</li>
            <li>
              Top K: legacy profiles use {vector?.top_k ?? "pending"} chunks; the Phase 33 reranked candidate uses{" "}
              {precisionCandidate?.top_k ?? "pending"}.
            </li>
            <li>Permission and missing-info questions are excluded from retrieval averages.</li>
          </ul>
        </Card>
        <Card>
          <SectionHeading title="Metrics Used" />
          <ul className="space-y-2 text-sm text-stone-700">
            <li>All-sources hit checks complete expected-document coverage.</li>
            <li>Precision@k measures retrieval noise.</li>
            <li>MRR measures how early the first expected source appears.</li>
            <li>Latency shows speed tradeoffs between modes.</li>
          </ul>
        </Card>
        <Card tone="warn">
          <SectionHeading title="Remaining Gaps" />
          <p className="text-sm text-stone-700">
            The current best-precision run still has {formatIntegerMetric(bestPrecisionRun?.metrics.failed_question_count ?? bestPrecisionRun?.failed_questions?.length)} source-coverage misses, mostly in multi-document,
            memory, and ambiguity cases. That points toward orchestration improvements rather than another simple score blend.
          </p>
        </Card>
      </section>
      <section className="mt-8 grid gap-4 lg:grid-cols-2">
        <RetrievalChart runs={chartRuns} />
        <Card>
          <SectionHeading title="Experiment Comparisons" />
          <div className="space-y-4 text-sm text-stone-700">
            <div>
              <p className="font-semibold text-ink">Reranked Candidate</p>
              <p>
                Phase 33 added vector + lexical reranking and lifted Precision@k to{" "}
                {formatMetric(precisionCandidate?.metrics.precision_at_k)} on benchmark {precisionCandidate?.benchmark_version ?? "n/a"} with{" "}
                n={precisionCandidate?.sample_size ?? precisionCandidate?.total_questions ?? "n/a"}.
              </p>
            </div>
            <div>
              <p className="font-semibold text-ink">Legacy Vector vs Hybrid</p>
              <p>
                Hybrid matched the vector hit rate but lowered Precision@k from {formatMetric(vector?.metrics.precision_at_k)} to{" "}
                {formatMetric(hybrid?.metrics.precision_at_k)} on the older benchmark {vector?.benchmark_version ?? "n/a"} comparison.
              </p>
            </div>
            <div>
              <p className="font-semibold text-ink">Keyword-only</p>
              <p>
                Keyword-only was much faster at {formatMetric(keyword?.metrics.average_latency_ms)} ms average latency, but weaker on
                Precision@k at {formatMetric(keyword?.metrics.precision_at_k)} in the legacy Phase 6 run.
              </p>
            </div>
            <div>
              <p className="font-semibold text-ink">Fixed-size Chunking</p>
              <p>
                Fixed-size chunking reached Precision@k {formatMetric(fixed?.metrics.precision_at_k)}, so it did not outperform
                section-based chunking.
              </p>
            </div>
          </div>
        </Card>
      </section>
      <Card className="mt-8">
        <SectionHeading title="Current Takeaway" />
        <p className="text-stone-700">
          The Phase 33 vector + lexical reranked candidate is the current retrieval-quality reference for the expanded benchmark.
          The Phase 6 profiles remain useful historical comparisons, but they should not override the v1.1 result.
        </p>
      </Card>
      <section className="mt-8">
        <SectionHeading title="Retrieval-Only Results" description="Sorted by Precision@k. Phase 6 rows are benchmark v1.0; the reranked candidate is benchmark v1.1." />
        <RetrievalExperimentTable runs={chartRuns} />
      </section>
    </Shell>
  );
}
