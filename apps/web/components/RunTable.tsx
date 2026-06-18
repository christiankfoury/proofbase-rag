import Link from "next/link";
import { Badge } from "@/components/Badge";
import { EvalRun, formatLabel, formatTableMetric, riskRateClass } from "@/lib/dashboard";

function formatCost(value: number | string | null | undefined): string {
  if (value === null || value === undefined || value === "") return "-";
  if (typeof value === "number") return `$${value.toFixed(6)}`;
  if (value.toLowerCase() === "pending") return "-";
  return value;
}

export function RunTable({ runs, bestRunName }: { runs: EvalRun[]; bestRunName?: string }) {
  return (
    <div>
      <p className="mb-3 text-sm text-stone-600">A dash means the metric was not measured for that run type.</p>
      <div className="overflow-x-auto rounded-md border border-stone-300 bg-white shadow-card">
        <table className="data-table min-w-[1040px]">
          <thead>
            <tr>
              <th>Run</th>
              <th>Phase</th>
              <th>Mode</th>
              <th>Chunking</th>
              <th className="text-right">Precision@k</th>
              <th className="text-right">MRR</th>
              <th className="text-right">Answer</th>
              <th className="text-right">Citation</th>
              <th className="text-right">Permission Leak</th>
              <th className="text-right">Memory</th>
              <th className="text-right">Est. Cost</th>
            </tr>
          </thead>
          <tbody>
            {runs.map((run) => (
              <tr key={run.run_id}>
                <td className="font-medium text-ink">
                  <div className="flex flex-wrap items-center gap-2">
                    <Link
                      href={`/evaluation/runs/${encodeURIComponent(run.run_id)}`}
                      className="rounded underline decoration-stone-400 underline-offset-4 hover:text-moss-dark focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-moss"
                    >
                      {run.run_name}
                    </Link>
                    {run.run_name === bestRunName ? <Badge tone="solid">Best config</Badge> : null}
                  </div>
                </td>
                <td>{run.phase}</td>
                <td>{formatLabel(run.retrieval_mode)}</td>
                <td>{formatLabel(run.chunking_strategy)}</td>
                <td className="text-right">{formatTableMetric(run.metrics.precision_at_k)}</td>
                <td className="text-right">{formatTableMetric(run.metrics.mrr)}</td>
                <td className="text-right">{formatTableMetric(run.metrics.answer_accuracy)}</td>
                <td className="text-right">{formatTableMetric(run.metrics.citation_accuracy)}</td>
                <td className={`text-right ${riskRateClass(run.metrics.permission_leakage_rate)}`}>
                  {formatTableMetric(run.metrics.permission_leakage_rate)}
                </td>
                <td className="text-right">{formatTableMetric(run.metrics.memory_answer_accuracy)}</td>
                <td className="text-right">{formatCost(run.metrics.estimated_cost)}</td>
              </tr>
            ))}
          </tbody>
        </table>
      </div>
    </div>
  );
}
