import { EvalRun, formatTableMetric } from "@/lib/dashboard";

const colors = ["bg-moss", "bg-steel", "bg-rust"];

export function RetrievalChart({ runs }: { runs: EvalRun[] }) {
  const selected = runs.filter((run) =>
    ["vector-section", "keyword-section", "hybrid-section-0.5"].includes(run.run_name)
  );

  return (
    <section className="rounded-md border border-stone-300 bg-white p-5">
      <div className="mb-5">
        <h3 className="text-xl font-semibold">Vector vs Keyword vs Hybrid</h3>
        <p className="mt-2 text-sm text-stone-600">Precision@k comparison from the Phase 6 retrieval experiment.</p>
      </div>
      <div className="space-y-4">
        {selected.map((run, index) => {
          const value = typeof run.metrics.precision_at_k === "number" ? run.metrics.precision_at_k : 0;
          return (
            <div key={run.run_id}>
              <div className="mb-1 flex items-center justify-between gap-4 text-sm">
                <span className="font-medium">{run.run_name}</span>
                <span>{formatTableMetric(run.metrics.precision_at_k)}</span>
              </div>
              <div className="h-3 rounded bg-stone-200">
                <div className={`h-3 rounded ${colors[index]}`} style={{ width: `${Math.max(value * 100, 2)}%` }} />
              </div>
            </div>
          );
        })}
      </div>
    </section>
  );
}
