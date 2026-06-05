import { MetricCard } from "@/components/MetricCard";
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
        <MetricCard label="Retrieval Hit Rate" value={metrics.retrieval_hit_rate} detail="All expected sources retrieved." />
        <MetricCard label="Precision@k" value={metrics.precision_at_k} detail="Expected-source chunks in top-k." />
        <MetricCard label="MRR" value={metrics.mrr} detail="Rank quality for first expected source." />
        <MetricCard label="Answer Accuracy" value={metrics.answer_accuracy} detail="Deterministic answer scoring." />
        <MetricCard label="Citation Accuracy" value={metrics.citation_accuracy} detail="Citations match expected documents." />
        <MetricCard label="Hallucination Rate" value={metrics.hallucination_rate} detail="Unsupported-answer signal." />
        <MetricCard label="Permission Leakage" value={metrics.permission_leakage_rate} detail="Restricted-source leakage." />
        <MetricCard label="Memory Accuracy" value={metrics.memory_accuracy} detail="Follow-up benchmark answers." />
      </section>
      <section className="mt-8 rounded-md border border-stone-300 bg-white p-5">
        <h3 className="text-xl font-semibold">Current Learning</h3>
        <p className="mt-2 text-stone-700">{data.overview.retrieval_conclusion}</p>
      </section>
      <section className="mt-8">
        <h3 className="mb-3 text-xl font-semibold">Recent Runs</h3>
        <RunTable runs={data.runs} />
      </section>
    </Shell>
  );
}
