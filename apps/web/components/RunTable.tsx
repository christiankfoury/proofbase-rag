import { EvalRun, formatTableMetric } from "@/lib/dashboard";

export function RunTable({ runs, bestRunName }: { runs: EvalRun[]; bestRunName?: string }) {
  return (
    <div>
      <p className="mb-3 text-sm text-stone-600">"-" means the metric was not measured for that run type.</p>
      <div className="overflow-x-auto rounded-md border border-stone-300 bg-white">
        <table className="w-full min-w-[960px] border-collapse text-left text-sm">
          <thead className="bg-stone-100 text-stone-700">
            <tr>
              <th className="p-3">Run</th>
              <th className="p-3">Phase</th>
              <th className="p-3">Mode</th>
              <th className="p-3">Chunking</th>
              <th className="p-3 text-right">Precision@k</th>
              <th className="p-3 text-right">MRR</th>
              <th className="p-3 text-right">Answer</th>
              <th className="p-3 text-right">Citation</th>
              <th className="p-3 text-right">Permission Leak</th>
              <th className="p-3 text-right">Memory</th>
            </tr>
          </thead>
          <tbody>
            {runs.map((run) => (
              <tr key={run.run_id} className="border-t border-stone-200">
                <td className="p-3 font-medium">
                  <div className="flex flex-wrap items-center gap-2">
                    <span>{run.run_name}</span>
                    {run.run_name === bestRunName ? (
                      <span className="rounded bg-moss px-2 py-1 text-xs font-semibold text-white">Best config</span>
                    ) : null}
                  </div>
                </td>
                <td className="p-3">{run.phase}</td>
                <td className="p-3">{run.retrieval_mode ?? "n/a"}</td>
                <td className="p-3">{run.chunking_strategy ?? "n/a"}</td>
                <td className="p-3 text-right">{formatTableMetric(run.metrics.precision_at_k)}</td>
                <td className="p-3 text-right">{formatTableMetric(run.metrics.mrr)}</td>
                <td className="p-3 text-right">{formatTableMetric(run.metrics.answer_accuracy)}</td>
                <td className="p-3 text-right">{formatTableMetric(run.metrics.citation_accuracy)}</td>
                <td className="p-3 text-right">{formatTableMetric(run.metrics.permission_leakage_rate)}</td>
                <td className="p-3 text-right">{formatTableMetric(run.metrics.memory_answer_accuracy)}</td>
              </tr>
            ))}
          </tbody>
        </table>
      </div>
    </div>
  );
}
