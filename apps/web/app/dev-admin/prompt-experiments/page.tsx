import { Badge } from "@/components/Badge";
import { Card } from "@/components/Card";
import { MetricCard } from "@/components/MetricCard";
import { PageHeader } from "@/components/PageHeader";
import { SectionHeading } from "@/components/SectionHeading";
import { Shell } from "@/components/Shell";
import { EvalRun, formatLabel, formatTableMetric, getDashboardData, riskRateClass } from "@/lib/dashboard";
import { serverDemoAuthHeaders } from "@/lib/serverDemoAuth";

function PromptExperimentTable({ runs }: { runs: EvalRun[] }) {
  return (
    <div className="overflow-x-auto rounded-md border border-stone-300 bg-white shadow-card">
      <table className="data-table min-w-[980px]">
        <thead>
          <tr>
            <th>Prompt</th>
            <th>Status</th>
            <th>Change Notes</th>
            <th>Model</th>
            <th className="text-right">Temp</th>
            <th className="text-right">Answer</th>
            <th className="text-right">Citation</th>
            <th className="text-right">Hallucination</th>
            <th className="text-right">Response Type</th>
            <th className="text-right">Confidence</th>
            <th className="text-right">Failed</th>
          </tr>
        </thead>
        <tbody>
          {runs.map((run) => (
            <tr key={run.run_id}>
              <td className="whitespace-nowrap font-semibold text-ink">{run.prompt_version}</td>
              <td className="whitespace-nowrap">
                <Badge tone={run.prompt_status === "active" ? "solid" : "neutral"}>{formatLabel(run.prompt_status)}</Badge>
              </td>
              <td className="max-w-xs text-stone-600">{run.prompt_change_notes ?? "-"}</td>
              <td className="whitespace-nowrap">{run.model}</td>
              <td className="text-right">{formatTableMetric(run.temperature)}</td>
              <td className="text-right">{formatTableMetric(run.metrics.answer_accuracy)}</td>
              <td className="text-right">{formatTableMetric(run.metrics.citation_accuracy)}</td>
              <td className={`text-right ${riskRateClass(run.metrics.hallucination_rate)}`}>
                {formatTableMetric(run.metrics.hallucination_rate)}
              </td>
              <td className="text-right">{formatTableMetric(run.metrics.response_type_accuracy)}</td>
              <td className="text-right">{formatTableMetric(run.metrics.final_confidence)}</td>
              <td className="text-right">{formatTableMetric(run.metrics.failed_question_count)}</td>
            </tr>
          ))}
        </tbody>
      </table>
    </div>
  );
}

export default async function PromptExperimentsPage() {
  const authHeaders = await serverDemoAuthHeaders();
  const data = await getDashboardData(authHeaders);
  const runs = data.runs.filter((run) => run.run_type === "prompt_experiment");
  const best = data.prompt_comparison?.best ?? {};
  const comparisons = data.prompt_comparison?.comparisons ?? [];

  return (
    <Shell>
      <PageHeader
        title="Prompt Experiments"
        description="Phase 11 compares answer-generation prompt versions against the same 60-question benchmark so prompt changes are measured instead of changed blindly."
      />

      <section className="grid gap-4 md:grid-cols-3">
        <MetricCard
          label="Best Overall"
          value={best.best_overall ?? "-"}
          detail="Selected by answer accuracy, citation accuracy, hallucination rate, and failed-question count."
          badge="Best"
          tone="good"
        />
        <MetricCard label="Best Citations" value={best.best_citations ?? "-"} detail="Highest citation match against expected documents." />
        <MetricCard label="Lowest Hallucination" value={best.lowest_hallucination ?? "-"} detail="Lowest unsupported-answer signal in the prompt run." />
      </section>

      <Card className="mt-8">
        <SectionHeading title="Experiment Boundary" />
        <p className="text-stone-700">
          These runs keep retrieval fixed at vector-only section-based retrieval and vary only the answer-generation prompt, model, and temperature metadata.
        </p>
      </Card>

      <section className="mt-8">
        <SectionHeading title="Prompt Version Metrics" />
        {runs.length > 0 ? (
          <PromptExperimentTable runs={runs} />
        ) : (
          <p className="rounded-md border border-stone-300 bg-white p-5 text-stone-700 shadow-card">
            No prompt experiment runs have been exported yet. Run `python scripts/run_prompt_experiment.py` and `python scripts/export_dashboard_data.py`.
          </p>
        )}
      </section>

      <section className="mt-8 grid gap-4 lg:grid-cols-2">
        {comparisons.map((comparison) => (
          <Card key={comparison.candidate_version} as="article">
            <h3 className="text-lg font-semibold text-ink">
              {comparison.candidate_version} vs {comparison.baseline_version}
            </h3>
            <div className="mt-4 grid gap-4 md:grid-cols-3">
              <div>
                <p className="font-medium text-moss-dark">Fixed</p>
                <p className="mt-2 text-sm text-stone-700">{comparison.fixed_questions.length ? comparison.fixed_questions.join(", ") : "None"}</p>
              </div>
              <div>
                <p className="font-medium text-rust-dark">Broken</p>
                <p className="mt-2 text-sm text-stone-700">{comparison.broken_questions.length ? comparison.broken_questions.join(", ") : "None"}</p>
              </div>
              <div>
                <p className="font-medium text-steel-dark">Still Failing</p>
                <p className="mt-2 text-sm text-stone-700">{comparison.still_failing.length ? comparison.still_failing.join(", ") : "None"}</p>
              </div>
            </div>
          </Card>
        ))}
      </section>
    </Shell>
  );
}
