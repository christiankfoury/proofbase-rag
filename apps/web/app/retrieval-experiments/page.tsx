import { Badge } from "@/components/Badge";
import { Card } from "@/components/Card";
import { MetricCard } from "@/components/MetricCard";
import { PageHeader } from "@/components/PageHeader";
import { RetrievalChart } from "@/components/RetrievalChart";
import { SectionHeading } from "@/components/SectionHeading";
import { Shell } from "@/components/Shell";
import { EvalRun, formatLabel, formatMetric, formatTableMetric, getDashboardData } from "@/lib/dashboard";

function RetrievalExperimentTable({ runs }: { runs: EvalRun[] }) {
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
          {runs.map((run) => (
            <tr key={run.run_id}>
              <td className="whitespace-nowrap font-medium text-ink">
                <div className="flex flex-wrap items-center gap-2">
                  <span>{run.run_name}</span>
                  {run.run_name === "vector-section" ? <Badge tone="solid">Current default</Badge> : null}
                </div>
              </td>
              <td className="whitespace-nowrap">{formatLabel(run.retrieval_mode)}</td>
              <td className="whitespace-nowrap">{formatLabel(run.chunking_strategy)}</td>
              <td className="text-right">{formatTableMetric(run.metrics.all_sources_hit)}</td>
              <td className="text-right">{formatTableMetric(run.metrics.expected_source_recall)}</td>
              <td className="text-right">{formatTableMetric(run.metrics.precision_at_k)}</td>
              <td className="text-right">{formatTableMetric(run.metrics.mrr)}</td>
              <td className="text-right">{formatTableMetric(run.metrics.average_latency_ms)} ms</td>
              <td>{run.failed_questions?.length ? run.failed_questions.join(", ") : "None"}</td>
            </tr>
          ))}
        </tbody>
      </table>
    </div>
  );
}

export default async function RetrievalExperimentsPage() {
  const data = await getDashboardData();
  const retrievalRuns = data.runs.filter((run) => run.phase === "phase-6");
  const best = retrievalRuns.find((run) => run.run_name === data.overview.best_retrieval_run);
  const vector = retrievalRuns.find((run) => run.run_name === "vector-section");
  const keyword = retrievalRuns.find((run) => run.run_name === "keyword-section");
  const hybrid = retrievalRuns.find((run) => run.run_name === "hybrid-section-0.5");
  const fixed = retrievalRuns.find((run) => run.run_name === "vector-fixed-size");

  return (
    <Shell>
      <PageHeader
        title="Retrieval Experiments"
        description="Phase 6 compared vector, keyword, and hybrid retrieval across section-based and fixed-size chunking."
      />
      <section className="grid gap-4 md:grid-cols-3">
        <MetricCard label="Best Run" value={best?.run_name} detail="Selected by overall retrieval profile." badge="Best" tone="good" />
        <MetricCard label="Best Precision@k" value={best?.metrics.precision_at_k} />
        <MetricCard label="Best MRR" value={best?.metrics.mrr} />
        <MetricCard label="Vector Latency" value={`${formatMetric(vector?.metrics.average_latency_ms)} ms`} detail="Average retrieval latency." />
        <MetricCard label="Keyword Latency" value={`${formatMetric(keyword?.metrics.average_latency_ms)} ms`} detail="Fastest but lower precision." />
        <MetricCard label="Hybrid Latency" value={`${formatMetric(hybrid?.metrics.average_latency_ms)} ms`} detail="Comparable hit rate, higher latency." />
      </section>
      <section className="mt-8 grid gap-4 lg:grid-cols-3">
        <Card>
          <SectionHeading title="Experiment Setup" />
          <ul className="space-y-2 text-sm text-stone-700">
            <li>Benchmark: {vector?.total_questions ?? "pending"} enterprise questions.</li>
            <li>Compared retrieval-only metrics to avoid extra generation cost.</li>
            <li>Top K: {vector?.top_k ?? "pending"} chunks per question.</li>
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
          <SectionHeading title="Main Failure" />
          <p className="text-sm text-stone-700">
            `MULTI-005` remains the key unresolved case for the best run. That points toward query decomposition or stronger
            multi-document retrieval logic rather than simple score blending.
          </p>
        </Card>
      </section>
      <section className="mt-8 grid gap-4 lg:grid-cols-2">
        <RetrievalChart runs={retrievalRuns} />
        <Card>
          <SectionHeading title="Experiment Comparisons" />
          <div className="space-y-4 text-sm text-stone-700">
            <div>
              <p className="font-semibold text-ink">Vector vs Hybrid</p>
              <p>
                Hybrid matched the vector hit rate but lowered Precision@k from {formatMetric(vector?.metrics.precision_at_k)} to{" "}
                {formatMetric(hybrid?.metrics.precision_at_k)}.
              </p>
            </div>
            <div>
              <p className="font-semibold text-ink">Keyword-only</p>
              <p>
                Keyword-only was much faster at {formatMetric(keyword?.metrics.average_latency_ms)} ms average latency, but weaker on
                Precision@k at {formatMetric(keyword?.metrics.precision_at_k)}.
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
        <SectionHeading title="Honest Conclusion" />
        <p className="text-stone-700">{data.overview.retrieval_conclusion}</p>
      </Card>
      <Card tone="good" className="mt-8">
        <SectionHeading title="Decision" />
        <p className="text-stone-700">
          Use <span className="font-semibold">vector-section</span> as the current default retrieval configuration. Keep hybrid as an
          experiment, not the default, until it improves Precision@k or multi-document recall.
        </p>
      </Card>
      <section className="mt-8">
        <SectionHeading title="Retrieval-Only Results" />
        <RetrievalExperimentTable runs={retrievalRuns} />
      </section>
    </Shell>
  );
}
