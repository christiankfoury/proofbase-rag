import { EvalRun, formatMetric } from "@/lib/dashboard";

export function RunTable({ runs }: { runs: EvalRun[] }) {
  return (
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
              <td className="p-3 font-medium">{run.run_name}</td>
              <td className="p-3">{run.phase}</td>
              <td className="p-3">{run.retrieval_mode ?? "n/a"}</td>
              <td className="p-3">{run.chunking_strategy ?? "n/a"}</td>
              <td className="p-3 text-right">{formatMetric(run.metrics.precision_at_k)}</td>
              <td className="p-3 text-right">{formatMetric(run.metrics.mrr)}</td>
              <td className="p-3 text-right">{formatMetric(run.metrics.answer_accuracy)}</td>
              <td className="p-3 text-right">{formatMetric(run.metrics.citation_accuracy)}</td>
              <td className="p-3 text-right">{formatMetric(run.metrics.permission_leakage_rate)}</td>
              <td className="p-3 text-right">{formatMetric(run.metrics.memory_answer_accuracy)}</td>
            </tr>
          ))}
        </tbody>
      </table>
    </div>
  );
}
