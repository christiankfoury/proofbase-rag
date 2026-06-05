import { EvalRun, formatTableMetric } from "@/lib/dashboard";

const colors = ["bg-moss", "bg-steel", "bg-rust"];

export function RetrievalChart({ runs }: { runs: EvalRun[] }) {
  const selected = runs.filter((run) =>
    ["vector-section", "keyword-section", "hybrid-section-0.5"].includes(run.run_name)
  );

  return (
    <section className="rounded-md border border-stone-300 bg-white p-5">
      <div className="mb-5">
        <h3 className="text-xl font-semibold">Retrieval Precision Comparison</h3>
        <p className="mt-2 text-sm text-stone-600">Vector vs keyword vs hybrid from the Phase 6 retrieval experiment.</p>
      </div>
      <div className="space-y-4">
        {selected.map((run, index) => {
          const value = typeof run.metrics.precision_at_k === "number" ? run.metrics.precision_at_k : 0;
          return (
            <div key={run.run_id}>
              <div className="mb-1 flex items-center justify-between gap-4 text-sm">
                <div className="flex flex-wrap items-center gap-2">
                  <span className="font-medium">{run.run_name}</span>
                  {run.run_name === "vector-section" ? (
                    <span className="rounded bg-moss px-2 py-1 text-xs font-semibold text-white">Best overall</span>
                  ) : null}
                </div>
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
