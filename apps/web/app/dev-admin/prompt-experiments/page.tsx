import { Badge } from "@/components/Badge";
import { Card } from "@/components/Card";
import { MetricCard } from "@/components/MetricCard";
import { PageHeader } from "@/components/PageHeader";
import { PhaseLabel } from "@/components/PhaseLabel";
import { SectionHeading } from "@/components/SectionHeading";
import { Shell } from "@/components/Shell";
import { EvalRun, formatLabel, formatTableMetric, getDashboardData, riskRateClass } from "@/lib/dashboard";
import { serverDemoAuthHeaders } from "@/lib/serverDemoAuth";

function runQuestionCount(run: EvalRun | undefined): number | string {
  return run?.sample_size ?? run?.total_questions ?? "-";
}

function runFailedCount(run: EvalRun | undefined): number | string {
  return run?.metrics.failed_question_count ?? run?.failed_count ?? "-";
}

function runContext(run: EvalRun | undefined): string {
  if (!run) return "No current answer run exported.";
  return `${runQuestionCount(run)} questions / ${runFailedCount(run)} failed / benchmark ${run.benchmark_version ?? "-"}`;
}

function runTypeLabel(run: EvalRun): string {
  if (run.run_type === "live_query_eval") return "Live answer run";
  if (run.run_type === "prompt_experiment") return "Prompt run";
  return formatLabel(run.run_type);
}

function PromptHistoryTable({ runs }: { runs: EvalRun[] }) {
  return (
    <div className="overflow-x-auto rounded-md border border-stone-300 bg-white shadow-card">
      <table className="data-table min-w-[1120px]">
        <thead>
          <tr>
            <th>Prompt</th>
            <th>Phase</th>
            <th>Run</th>
            <th>Type</th>
            <th>Benchmark</th>
            <th>Retrieval</th>
            <th className="text-right">Questions</th>
            <th>Model</th>
            <th className="text-right">Answer</th>
            <th className="text-right">Citation</th>
            <th className="text-right">Hallucination</th>
            <th className="text-right">Failed</th>
          </tr>
        </thead>
        <tbody>
          {runs.map((run) => (
            <tr key={run.run_id}>
              <td className="whitespace-nowrap font-semibold text-ink">{run.prompt_version}</td>
              <td className="whitespace-nowrap">
                <PhaseLabel phase={run.phase} />
              </td>
              <td className="max-w-xs">
                <p className="font-medium text-ink">{run.run_name}</p>
                <p className="mt-1 text-xs text-stone-500">{run.run_id}</p>
              </td>
              <td className="whitespace-nowrap">
                <Badge tone={run.run_type === "live_query_eval" ? "solid" : "neutral"}>{runTypeLabel(run)}</Badge>
              </td>
              <td className="whitespace-nowrap">{run.benchmark_version ?? "-"}</td>
              <td className="whitespace-nowrap">{formatLabel(run.retrieval_mode)}</td>
              <td className="text-right">{formatTableMetric(runQuestionCount(run), { integer: true })}</td>
              <td className="whitespace-nowrap">{run.model ?? "-"}</td>
              <td className="text-right">{formatTableMetric(run.metrics.answer_accuracy)}</td>
              <td className="text-right">{formatTableMetric(run.metrics.citation_accuracy)}</td>
              <td className={`text-right ${riskRateClass(run.metrics.hallucination_rate)}`}>
                {formatTableMetric(run.metrics.hallucination_rate)}
              </td>
              <td className="text-right">{formatTableMetric(runFailedCount(run), { integer: true })}</td>
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
  const runs = data.runs.filter(
    (run) =>
      Boolean(run.prompt_version) &&
      (run.run_type === "prompt_experiment" || run.run_type === "live_query_eval") &&
      run.metrics.answer_accuracy !== undefined
  );
  const currentRun =
    runs.find((run) => run.run_id === data.overview.current_answer_run_id) ??
    runs.find((run) => run.run_type === "live_query_eval") ??
    runs.at(-1);
  const phase11Runs = runs.filter((run) => run.phase === "phase-11" && run.run_type === "prompt_experiment");
  const phase11QuestionCount = Math.max(...phase11Runs.map((run) => Number(runQuestionCount(run))).filter(Number.isFinite), 0);
  const currentBenchmarkCount = data.regression_scorecard?.benchmark_question_count ?? currentRun?.sample_size ?? currentRun?.total_questions;
  const comparisons = data.prompt_comparison?.comparisons ?? [];

  return (
    <Shell>
      <PageHeader
        title="Prompt History"
        description={
          <p>
            <PhaseLabel phase="phase-11" /> started controlled answer-prompt experiments. Later phases are shown here as prompt-run
            history so the scorecard has provenance without repeating its proof claims.
          </p>
        }
      />

      <section className="grid gap-4 md:grid-cols-2 xl:grid-cols-4">
        <MetricCard
          label="Current Answer Run"
          value={currentRun?.prompt_version ?? "-"}
          detail={currentRun?.run_name ?? "-"}
          context={runContext(currentRun)}
          badge="Current"
          tone="good"
        />
        <MetricCard
          label="Original Experiment"
          value="Phase 11"
          detail={`${phase11Runs.length} prompt runs compared on the original ${phase11QuestionCount || "-"}-question suite.`}
        />
        <MetricCard
          label="Current Benchmark"
          value={currentBenchmarkCount ?? "-"}
          detail={`Benchmark ${data.regression_scorecard?.benchmark_version ?? currentRun?.benchmark_version ?? "-"} is the current scorecard basis.`}
          format="integer"
        />
        <MetricCard
          label="Retrieval Boundary"
          value="Mixed"
          detail="Phase 11 keeps retrieval fixed; later rows include retrieval and benchmark changes."
          tone="warn"
        />
      </section>

      <Card className="mt-8">
        <SectionHeading title="How To Read This" />
        <p className="text-stone-700">
          Phase 11 rows are controlled prompt experiments with vector-only section retrieval. Later rows are answer-quality milestones, so
          they show how the answer prompt evolved with the broader retrieval and benchmark work rather than a same-boundary A/B test.
        </p>
      </Card>

      <section className="mt-8">
        <SectionHeading title="Answer Prompt Run History" />
        {runs.length > 0 ? (
          <PromptHistoryTable runs={runs} />
        ) : (
          <p className="rounded-md border border-stone-300 bg-white p-5 text-stone-700 shadow-card">
            No prompt experiment runs have been exported yet. Run `python scripts/run_prompt_experiment.py` and `python scripts/export_dashboard_data.py`.
          </p>
        )}
      </section>

      <section className="mt-8 grid gap-4 lg:grid-cols-2">
        <div className="lg:col-span-2">
          <SectionHeading title="Phase 11 Comparison Detail" />
        </div>
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
