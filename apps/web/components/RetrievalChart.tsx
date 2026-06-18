import { Badge } from "@/components/Badge";
import { Card } from "@/components/Card";
import { SectionHeading } from "@/components/SectionHeading";
import { EvalRun, formatTableMetric } from "@/lib/dashboard";

const colors = ["bg-moss", "bg-steel", "bg-rust"];

export function RetrievalChart({ runs }: { runs: EvalRun[] }) {
  const selected = runs.filter((run) =>
    ["vector-section", "keyword-section", "hybrid-section-0.5"].includes(run.run_name)
  );

  return (
    <Card>
      <SectionHeading
        title="Retrieval Precision Comparison"
        description="Vector vs keyword vs hybrid from the Phase 6 retrieval experiment."
      />
      <div className="space-y-4">
        {selected.map((run, index) => {
          const value = typeof run.metrics.precision_at_k === "number" ? run.metrics.precision_at_k : 0;
          return (
            <div key={run.run_id}>
              <div className="mb-1 flex items-center justify-between gap-4 text-sm">
                <div className="flex flex-wrap items-center gap-2">
                  <span className="font-medium text-ink">{run.run_name}</span>
                  {run.run_name === "vector-section" ? <Badge tone="solid">Best overall</Badge> : null}
                </div>
                <span className="font-medium text-stone-700">{formatTableMetric(run.metrics.precision_at_k)}</span>
              </div>
              <div className="h-3 rounded bg-stone-200">
                <div className={`h-3 rounded ${colors[index]}`} style={{ width: `${Math.max(value * 100, 2)}%` }} />
              </div>
            </div>
          );
        })}
      </div>
    </Card>
  );
}
