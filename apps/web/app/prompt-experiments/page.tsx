import { Shell } from "@/components/Shell";
import { EvalRun, formatLabel, formatTableMetric, getDashboardData } from "@/lib/dashboard";

function PromptExperimentTable({ runs }: { runs: EvalRun[] }) {
  return (
    <section className="rounded-md border border-stone-300 bg-white">
      <table className="w-full border-collapse text-sm">
        <thead className="bg-stone-100 text-left">
          <tr>
            <th className="px-4 py-3">Prompt</th>
            <th className="px-4 py-3">Status</th>
            <th className="px-4 py-3">Change Notes</th>
            <th className="px-4 py-3">Model</th>
            <th className="px-4 py-3 text-right">Temp</th>
            <th className="px-4 py-3 text-right">Answer</th>
            <th className="px-4 py-3 text-right">Citation</th>
            <th className="px-4 py-3 text-right">Hallucination</th>
            <th className="px-4 py-3 text-right">Response Type</th>
            <th className="px-4 py-3 text-right">Confidence</th>
            <th className="px-4 py-3 text-right">Failed</th>
          </tr>
        </thead>
        <tbody>
          {runs.map((run) => (
            <tr key={run.run_id} className="border-t border-stone-200">
              <td className="px-4 py-3 font-semibold">{run.prompt_version}</td>
              <td className="px-4 py-3">{formatLabel(run.prompt_status)}</td>
              <td className="px-4 py-3 max-w-xs text-stone-600">{run.prompt_change_notes ?? "-"}</td>
              <td className="px-4 py-3">{run.model}</td>
              <td className="px-4 py-3 text-right">{formatTableMetric(run.temperature)}</td>
              <td className="px-4 py-3 text-right">{formatTableMetric(run.metrics.answer_accuracy)}</td>
              <td className="px-4 py-3 text-right">{formatTableMetric(run.metrics.citation_accuracy)}</td>
              <td className="px-4 py-3 text-right">{formatTableMetric(run.metrics.hallucination_rate)}</td>
              <td className="px-4 py-3 text-right">{formatTableMetric(run.metrics.response_type_accuracy)}</td>
              <td className="px-4 py-3 text-right">{formatTableMetric(run.metrics.final_confidence)}</td>
              <td className="px-4 py-3 text-right">{formatTableMetric(run.metrics.failed_question_count)}</td>
            </tr>
          ))}
        </tbody>
      </table>
    </section>
  );
}

export default async function PromptExperimentsPage() {
  const data = await getDashboardData();
  const runs = data.runs.filter((run) => run.run_type === "prompt_experiment");
  const best = data.prompt_comparison?.best ?? {};
  const comparisons = data.prompt_comparison?.comparisons ?? [];

  return (
    <Shell>
      <h2 className="text-3xl font-semibold">Prompt Experiments</h2>
      <p className="mt-3 max-w-3xl text-stone-700">
        Phase 11 compares answer-generation prompt versions against the same 60-question benchmark so prompt changes are measured instead of changed blindly.
      </p>

      <section className="mt-8 grid gap-4 md:grid-cols-3">
        <article className="rounded-md border border-moss bg-white p-5">
          <p className="text-sm font-semibold text-steel">Best Overall</p>
          <p className="mt-3 text-3xl font-semibold">{best.best_overall ?? "-"}</p>
          <p className="mt-2 text-sm text-stone-700">Selected by answer accuracy, citation accuracy, hallucination rate, and failed-question count.</p>
        </article>
        <article className="rounded-md border border-stone-300 bg-white p-5">
          <p className="text-sm font-semibold text-steel">Best Citations</p>
          <p className="mt-3 text-3xl font-semibold">{best.best_citations ?? "-"}</p>
          <p className="mt-2 text-sm text-stone-700">Highest citation match against expected documents.</p>
        </article>
        <article className="rounded-md border border-stone-300 bg-white p-5">
          <p className="text-sm font-semibold text-steel">Lowest Hallucination</p>
          <p className="mt-3 text-3xl font-semibold">{best.lowest_hallucination ?? "-"}</p>
          <p className="mt-2 text-sm text-stone-700">Lowest unsupported-answer signal in the prompt run.</p>
        </article>
      </section>

      <section className="mt-8 rounded-md border border-stone-300 bg-white p-5">
        <h3 className="text-xl font-semibold">Experiment Boundary</h3>
        <p className="mt-2 text-stone-700">
          These runs keep retrieval fixed at vector-only section-based retrieval and vary only the answer-generation prompt, model, and temperature metadata.
        </p>
      </section>

      <section className="mt-8">
        <h3 className="mb-3 text-xl font-semibold">Prompt Version Metrics</h3>
        {runs.length > 0 ? (
          <PromptExperimentTable runs={runs} />
        ) : (
          <p className="rounded-md border border-stone-300 bg-white p-5 text-stone-700">
            No prompt experiment runs have been exported yet. Run `python scripts/run_prompt_experiment.py` and `python scripts/export_dashboard_data.py`.
          </p>
        )}
      </section>

      <section className="mt-8 grid gap-4 lg:grid-cols-2">
        {comparisons.map((comparison) => (
          <article key={comparison.candidate_version} className="rounded-md border border-stone-300 bg-white p-5">
            <h3 className="text-lg font-semibold">
              {comparison.candidate_version} vs {comparison.baseline_version}
            </h3>
            <div className="mt-4 grid gap-4 md:grid-cols-3">
              <div>
                <p className="font-medium text-moss">Fixed</p>
                <p className="mt-2 text-sm text-stone-700">{comparison.fixed_questions.length ? comparison.fixed_questions.join(", ") : "None"}</p>
              </div>
              <div>
                <p className="font-medium text-rust">Broken</p>
                <p className="mt-2 text-sm text-stone-700">{comparison.broken_questions.length ? comparison.broken_questions.join(", ") : "None"}</p>
              </div>
              <div>
                <p className="font-medium text-steel">Still Failing</p>
                <p className="mt-2 text-sm text-stone-700">{comparison.still_failing.length ? comparison.still_failing.join(", ") : "None"}</p>
              </div>
            </div>
          </article>
        ))}
      </section>
    </Shell>
  );
}
