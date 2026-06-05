import { MetricCard } from "@/components/MetricCard";
import { RunTable } from "@/components/RunTable";
import { Shell } from "@/components/Shell";
import { getDashboardData } from "@/lib/dashboard";

export default async function RetrievalExperimentsPage() {
  const data = await getDashboardData();
  const retrievalRuns = data.runs.filter((run) => run.phase === "phase-6");
  const best = retrievalRuns.find((run) => run.run_name === data.overview.best_retrieval_run);

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
      </section>
      <section className="mt-8 rounded-md border border-stone-300 bg-white p-5">
        <h3 className="text-xl font-semibold">Honest Conclusion</h3>
        <p className="mt-2 text-stone-700">{data.overview.retrieval_conclusion}</p>
      </section>
      <section className="mt-8">
        <RunTable runs={retrievalRuns} />
      </section>
    </Shell>
  );
}
