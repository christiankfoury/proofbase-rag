import { MetricCard } from "@/components/MetricCard";
import { RetrievalChart } from "@/components/RetrievalChart";
import { RunTable } from "@/components/RunTable";
import { Shell } from "@/components/Shell";
import { getDashboardData } from "@/lib/dashboard";

export default async function OverviewPage() {
  const data = await getDashboardData();
  const metrics = data.overview.headline_metrics;

  return (
    <Shell>
      <div className="mb-8">
        <h2 className="text-3xl font-semibold">Measured Enterprise RAG Progress</h2>
        <p className="mt-3 max-w-3xl text-stone-700">
          This dashboard compares real evaluation runs across retrieval, answer quality, citations, permission safety, and memory.
        </p>
      </div>
      <section className="grid gap-4 md:grid-cols-2 xl:grid-cols-4">
        <MetricCard
          label="All-Source Retrieval Hit"
          value={metrics.retrieval_hit_rate}
          detail="All expected sources retrieved."
          tone="good"
        />
        <MetricCard label="Precision@k" value={metrics.precision_at_k} detail="Expected-source chunks in top-k." />
        <MetricCard label="MRR" value={metrics.mrr} detail="Rank quality for first expected source." />
        <MetricCard label="Answer Accuracy" value={metrics.answer_accuracy} detail="Deterministic answer scoring." />
        <MetricCard label="Citation Accuracy" value={metrics.citation_accuracy} detail="Citations match expected documents." />
        <MetricCard label="Hallucination Rate" value={metrics.hallucination_rate} detail="Unsupported-answer signal." tone="warn" />
        <MetricCard label="Permission Leakage" value={metrics.permission_leakage_rate} detail="Restricted-source leakage." tone="good" />
        <MetricCard label="Memory Answer Accuracy" value={metrics.memory_accuracy} detail="Follow-up benchmark answers." tone="good" />
      </section>
      <section className="mt-8 rounded-md border border-stone-300 bg-white p-5">
        <h3 className="text-xl font-semibold">Experiment Conclusion</h3>
        <p className="mt-2 text-stone-700">{data.overview.retrieval_conclusion}</p>
      </section>
      <section className="mt-8 grid gap-4 lg:grid-cols-2">
        <RetrievalChart runs={data.runs} />
        <section className="rounded-md border border-stone-300 bg-white p-5">
          <h3 className="text-xl font-semibold">What Improved / What Failed</h3>
          <div className="mt-4 grid gap-4 md:grid-cols-2">
            <div>
              <p className="font-medium text-moss">Improved</p>
              <ul className="mt-2 space-y-2 text-sm text-stone-700">
                <li>Permission tests reached zero leakage.</li>
                <li>Memory follow-up tests reached full accuracy.</li>
                <li>Evaluation data is now comparable across phases.</li>
              </ul>
            </div>
            <div>
              <p className="font-medium text-rust">Still Weak</p>
              <ul className="mt-2 space-y-2 text-sm text-stone-700">
                <li>Hybrid retrieval did not beat vector-only overall.</li>
                <li>Thirteen failed-question records remain in the backlog.</li>
                <li>Cost tracking is still pending.</li>
              </ul>
            </div>
          </div>
        </section>
      </section>
      <section className="mt-8">
        <h3 className="mb-3 text-xl font-semibold">Recent Runs</h3>
        <RunTable runs={data.runs} bestRunName={data.overview.best_retrieval_run} />
      </section>
    </Shell>
  );
}
