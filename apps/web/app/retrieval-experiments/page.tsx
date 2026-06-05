import { MetricCard } from "@/components/MetricCard";
import { RetrievalChart } from "@/components/RetrievalChart";
import { Shell } from "@/components/Shell";
import { EvalRun, formatLabel, formatMetric, formatTableMetric, getDashboardData } from "@/lib/dashboard";

function RetrievalExperimentTable({ runs }: { runs: EvalRun[] }) {
  return (
    <div className="overflow-x-auto rounded-md border border-stone-300 bg-white">
      <table className="w-full min-w-[980px] border-collapse text-left text-sm">
        <thead className="bg-stone-100 text-stone-700">
          <tr>
            <th className="p-3">Run</th>
            <th className="p-3">Retrieval</th>
            <th className="p-3">Chunking</th>
            <th className="p-3 text-right">All Sources</th>
            <th className="p-3 text-right">Source Recall</th>
            <th className="p-3 text-right">Precision@k</th>
            <th className="p-3 text-right">MRR</th>
            <th className="p-3 text-right">Latency</th>
            <th className="p-3">Failed</th>
          </tr>
        </thead>
        <tbody>
          {runs.map((run) => (
            <tr key={run.run_id} className="border-t border-stone-200">
              <td className="whitespace-nowrap p-3 font-medium">
                <div className="flex flex-wrap items-center gap-2">
                  <span>{run.run_name}</span>
                  {run.run_name === "vector-section" ? (
                    <span className="rounded bg-moss px-2 py-1 text-xs font-semibold text-white">Current default</span>
                  ) : null}
                </div>
              </td>
              <td className="whitespace-nowrap p-3">{formatLabel(run.retrieval_mode)}</td>
              <td className="whitespace-nowrap p-3">{formatLabel(run.chunking_strategy)}</td>
              <td className="p-3 text-right">{formatTableMetric(run.metrics.all_sources_hit)}</td>
              <td className="p-3 text-right">{formatTableMetric(run.metrics.expected_source_recall)}</td>
              <td className="p-3 text-right">{formatTableMetric(run.metrics.precision_at_k)}</td>
              <td className="p-3 text-right">{formatTableMetric(run.metrics.mrr)}</td>
              <td className="p-3 text-right">{formatTableMetric(run.metrics.average_latency_ms)} ms</td>
              <td className="p-3">{run.failed_questions?.length ? run.failed_questions.join(", ") : "None"}</td>
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
      <h2 className="text-3xl font-semibold">Retrieval Experiments</h2>
      <p className="mt-3 max-w-3xl text-stone-700">
        Phase 6 compared vector, keyword, and hybrid retrieval across section-based and fixed-size chunking.
      </p>
      <section className="mt-6 grid gap-4 md:grid-cols-3">
        <MetricCard label="Best Run" value={best?.run_name} detail="Selected by overall retrieval profile." />
        <MetricCard label="Best Precision@k" value={best?.metrics.precision_at_k} />
        <MetricCard label="Best MRR" value={best?.metrics.mrr} />
        <MetricCard label="Vector Latency" value={`${formatMetric(vector?.metrics.average_latency_ms)} ms`} detail="Average retrieval latency." />
        <MetricCard label="Keyword Latency" value={`${formatMetric(keyword?.metrics.average_latency_ms)} ms`} detail="Fastest but lower precision." />
        <MetricCard label="Hybrid Latency" value={`${formatMetric(hybrid?.metrics.average_latency_ms)} ms`} detail="Comparable hit rate, higher latency." />
      </section>
      <section className="mt-8 grid gap-4 lg:grid-cols-3">
        <section className="rounded-md border border-stone-300 bg-white p-5">
          <h3 className="text-xl font-semibold">Experiment Setup</h3>
          <ul className="mt-3 space-y-2 text-sm text-stone-700">
            <li>Benchmark: 60 enterprise questions.</li>
            <li>Compared retrieval-only metrics to avoid extra generation cost.</li>
            <li>Top K: 5 chunks per question.</li>
            <li>Permission and missing-info questions are excluded from retrieval averages.</li>
          </ul>
        </section>
        <section className="rounded-md border border-stone-300 bg-white p-5">
          <h3 className="text-xl font-semibold">Metrics Used</h3>
          <ul className="mt-3 space-y-2 text-sm text-stone-700">
            <li>All-sources hit checks complete expected-document coverage.</li>
            <li>Precision@k measures retrieval noise.</li>
            <li>MRR measures how early the first expected source appears.</li>
            <li>Latency shows speed tradeoffs between modes.</li>
          </ul>
        </section>
        <section className="rounded-md border border-stone-300 bg-white p-5">
          <h3 className="text-xl font-semibold">Main Failure</h3>
          <p className="mt-3 text-sm text-stone-700">
            `MULTI-005` remains the key unresolved case for the best run. That points toward query decomposition or stronger
            multi-document retrieval logic rather than simple score blending.
          </p>
        </section>
      </section>
      <section className="mt-8 grid gap-4 lg:grid-cols-2">
        <RetrievalChart runs={retrievalRuns} />
        <section className="rounded-md border border-stone-300 bg-white p-5">
          <h3 className="text-xl font-semibold">Experiment Comparisons</h3>
          <div className="mt-4 space-y-4 text-sm text-stone-700">
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
        </section>
      </section>
      <section className="mt-8 rounded-md border border-stone-300 bg-white p-5">
        <h3 className="text-xl font-semibold">Honest Conclusion</h3>
        <p className="mt-2 text-stone-700">{data.overview.retrieval_conclusion}</p>
      </section>
      <section className="mt-8 rounded-md border border-moss bg-white p-5">
        <h3 className="text-xl font-semibold">Decision</h3>
        <p className="mt-2 text-stone-700">
          Use <span className="font-semibold">vector-section</span> as the current default retrieval configuration. Keep hybrid as an
          experiment, not the default, until it improves Precision@k or multi-document recall.
        </p>
      </section>
      <section className="mt-8">
        <h3 className="mb-3 text-xl font-semibold">Retrieval-Only Results</h3>
        <RetrievalExperimentTable runs={retrievalRuns} />
      </section>
    </Shell>
  );
}
