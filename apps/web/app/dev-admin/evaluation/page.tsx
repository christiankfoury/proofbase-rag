import Link from "next/link";
import { Card } from "@/components/Card";
import { PageHeader } from "@/components/PageHeader";
import { SectionHeading } from "@/components/SectionHeading";
import { Shell } from "@/components/Shell";
import evidence from "../../../../../data/evaluation/public-evidence.json";
import fresh from "../../../../../data/evaluation/fresh-current/public-report.json";

import reanalysis from "../../../../../data/evaluation/dimension-reanalysis-v1/public-summary.json";
import current from "../../../../../data/evaluation/current-runtime-v3/public-report.json";

const repo = "https://github.com/christiankfoury/proofbase-rag/blob/main/";
const reading = [
  ["Dataset and authorship", "docs/evaluation/dataset-card.md"],
  ["Scoring rules and limitations", "docs/evaluation/methodology.md"],
  ["Failure taxonomy and examples", "docs/evaluation/failure-taxonomy.md"],
  ["Reproduce the results", "docs/evaluation/reproducing-results.md"],
  ["Benchmark questions and expected answers", "data/evaluation/benchmark-questions.json"],
  ["Saved results and provenance", "data/evaluation/public-evidence.json"],
];

export default function EvaluationMethodologyPage() {
  const holdout = evidence.historical_holdout;
  const regression = evidence.historical_regressions[1];
  return (
    <Shell>
      <PageHeader title="How Evaluation Is Scored" description="Public evidence, exact denominators, and known limits of the automated rubric." />
      <Card className="mb-6">
        <SectionHeading title="Latest frozen-runtime evaluation" description="New questions authored after the runtime freeze. Each quality dimension is reported separately." />
        <p className="text-sm leading-6 text-stone-700">
          {current.completed_cases}/{current.expected_cases} cases completed. Run status: {current.status}.
          Runtime {current.runtime_commit.slice(0, 7)}; evaluator {current.version}.
        </p>
        <div className="mt-4 overflow-x-auto">
          <table className="w-full text-left text-sm">
            <thead><tr><th className="p-2">Dimension</th><th className="p-2">Model pass</th><th className="p-2">Model fail</th><th className="p-2">Unresolved</th><th className="p-2">Not applicable</th></tr></thead>
            <tbody>{Object.entries(current.dimensions).map(([name, values]) => (
              <tr key={name} className="border-t border-stone-200">
                <td className="p-2 capitalize">{name.replaceAll("_", " ")}</td>
                <td className="p-2">{values.pass}</td><td className="p-2">{values.fail}</td>
                <td className="p-2">{values.unresolved}</td><td className="p-2">{values.not_applicable}</td>
              </tr>
            ))}</tbody>
          </table>
        </div>
        <p className="mt-3 text-sm leading-6 text-stone-700">{current.limitation}</p>
        <p className="mt-3 rounded border border-amber-300 bg-amber-50 p-3 text-sm text-stone-800">{current.audit_warning}</p>
        <p className="mt-3 text-sm text-stone-700">
          Schema/reference-invalid grades: {current.invalid_grades}. Semantic disagreements are listed in the source inspection.
          Cases with recorded safety or HTTP flags: {current.safety_flag_cases.length}.
          Passing 18 visible calibration examples does not establish independent grader accuracy.
        </p>
        <div className="mt-4 flex flex-wrap gap-4 text-sm">
          <a className="underline" href={`${repo}docs/phase-68/case-review.md`}>Inspect each answer and its evidence</a>
          <a className="underline" href={`${repo}docs/phase-68/results.md`}>Results and methodology</a>
          <a className="underline" href={`${repo}docs/phase-68/agent-review.md`}>Source inspection and grader disagreements</a>
        </div>
      </Card>
      <Card className="mb-6">
        <SectionHeading title="Earlier saved-response reanalysis" description="Separate model judgments on the same saved responses. No new application run and no combined accuracy score." />
        <p className="text-sm leading-6 text-stone-700">
          {reanalysis.cases_processed}/{reanalysis.cases_expected} saved answers reanalyzed.
          Unresolved means the evaluator could not establish a judgment; it does not mean factually wrong.
          Non-answers can have no factual claims to assess. Human adjudication is not completed.
        </p>
        <p className="mt-3 rounded border border-amber-300 bg-amber-50 p-3 text-sm text-stone-800">{reanalysis.audit_warning} This evaluator is not approved for release gating. Four input-encoding mismatches are preserved as unresolved.</p>
        <div className="mt-4 overflow-x-auto">
          <table className="w-full text-left text-sm">
            <thead><tr><th className="p-2">Dimension</th><th className="p-2">Model pass</th><th className="p-2">Model fail</th><th className="p-2">Unresolved</th><th className="p-2">Not applicable</th></tr></thead>
            <tbody>{Object.entries(reanalysis.dimensions).map(([name, values]) => (
              <tr key={name} className="border-t border-stone-200">
                <td className="p-2 capitalize">{name.replaceAll("_", " ")}</td>
                <td className="p-2">{values.pass}</td><td className="p-2">{values.fail}</td>
                <td className="p-2">{values.unresolved}</td><td className="p-2">{values.not_applicable}</td>
              </tr>
            ))}</tbody>
          </table>
        </div>
        <p className="mt-3 text-sm leading-6 text-stone-700">
          Citation support uses the full cited chunk; quotation fidelity checks the excerpt separately.
          This changed rubric does not replace the original 55% protocol result or show runtime improvement.
          Passing 12 visible calibration examples does not establish human-level grader accuracy.
        </p>
        <div className="mt-4 flex flex-wrap gap-4 text-sm">
          <a className="underline" href={`${repo}docs/phase-66/case-review.md`}>Read each question, expected facts and actual answer</a>
          <a className="underline" href={`${repo}docs/phase-66/results.md`}>Dimension results and limitations</a>
        </div>
      </Card>
      <Card className="mb-6">
        <SectionHeading title="Original frozen-run protocol result" description="Separately authored after the runtime and evaluator freeze. Human review is pending." />
        <p className="text-3xl font-semibold text-ink">
          {fresh.full_response.rate === null
            ? `${fresh.completed_cases}/${fresh.expected_cases} cases completed — no full-suite score`
            : `${fresh.full_response.passed}/${fresh.full_response.total} (${(fresh.full_response.rate * 100).toFixed(1)}%) automated passes`}
        </p>
        <p className="mt-3 text-sm leading-6 text-stone-700">
          The new rubric requires every expected fact and exact citation support for every factual claim.
          Its model grader passed 24 visible development fixtures after two failed calibration versions.
          This is model-assisted scoring on synthetic cases; it is not an independent human accuracy assessment.
        </p>
        <p className="mt-3 text-sm text-stone-700">
          Answer-expected cases: {fresh.answer_expected.passed}/{fresh.answer_expected.total} completed passes.
          Non-answer cases: {fresh.non_answer_expected.passed}/{fresh.non_answer_expected.total} completed passes.
          An incomplete run has no full-suite rate. The historical 73.3% uses a different runtime, suite and evaluator and cannot establish a before/after improvement.
        </p>
        <p className="mt-3 text-sm text-stone-700">
          Predeclared quality target: {(fresh.target * 100).toFixed(0)}% — {fresh.target_met ? "met" : "not met"}.
          Overall gate: {fresh.combined_gate_met ? "passed" : "not passed"}.
          Failures include strict response-type and citation-quote checks, plus invalid model-grader outputs;
          this percentage is not a human-verified answer accuracy rate.
        </p>
        <p className="mt-3 break-all text-xs text-stone-500">Run: {fresh.run_id}; suite: {fresh.suite_version}; runtime: {fresh.runtime_commit}</p>
        <div className="mt-4 flex flex-wrap gap-4 text-sm">
          <a className="underline" href={`${repo}docs/phase-65/results.md`}>Results and limitations</a>
          <a className="underline" href={`${repo.replace("/blob/", "/tree/")}data/evaluation/fresh-current/`}>Dataset, freeze and saved evidence</a>
          <a className="underline" href={`${repo}docs/phase-65/human-review-packet.md`}>Human-review packet</a>
        </div>
        <pre className="mt-4 overflow-x-auto rounded border border-stone-300 bg-stone-50 p-4 text-sm">python scripts/report_fresh_eval.py --check</pre>
      </Card>
      <Card className="mb-6">
        <SectionHeading title="A regression score is a bounded result" />
        <p className="text-sm leading-6 text-stone-700">
          The project author created and checked the synthetic benchmark with AI assistance. These questions influenced development.
          Answer scores measure expected-word overlap; citation scores measure expected-document presence.
          A perfect score does not establish that every claim is correct or supported.
        </p>
      </Card>
      <section className="grid gap-6 lg:grid-cols-2">
        <Card>
          <SectionHeading title="Separate historical holdout" />
          <p className="text-3xl font-semibold text-ink">{holdout.automated_passes}/{holdout.sample_size} ({(holdout.automated_pass_rate * 100).toFixed(1)}%)</p>
          <p className="mt-3 text-sm leading-6 text-stone-700">
            Automated passes in {holdout.run_id}. The 27/30 target was missed. Eight failures include product defects and evaluator mistakes.
            Separate authoring and a frozen runtime do not establish independent human assessment.
          </p>
          <p className="mt-3 break-all text-xs text-stone-500">Frozen runtime: {holdout.provenance.runtime_commit}</p>
          <p className="mt-2 text-sm text-stone-700">This historical run does not measure the current runtime. The separate fresh evaluation above uses a different rubric.</p>
        </Card>
        <Card>
          <SectionHeading title="Known benchmark regression" />
          <p className="text-3xl font-semibold text-ink">{regression.recorded_failed_cases}/{regression.sample_size} recorded failures</p>
          <p className="mt-3 text-sm leading-6 text-stone-700">
            {regression.run_id}: answer and citation scores each cover {regression.metrics.answer_accuracy.scored_cases} answerable cases,
            excluding {regression.metrics.answer_accuracy.excluded_cases} refusal, not-found, and clarification cases.
            The run still records {regression.diagnostic_notes} diagnostic notes.
          </p>
          <p className="mt-3 text-sm leading-6 text-stone-700">
            The focused permission run records zero observed leaks in {evidence.focused_permission.unauthorized_cases} unauthorized tests,
            with {evidence.focused_permission.authorized_controls} authorized retrieval controls. That is finite test coverage, not a security guarantee.
          </p>
        </Card>
      </section>
      <Card className="mt-6">
        <SectionHeading title="Historical holdout category results" description="Phase 49 counts from the committed offline report. These small, designed samples are not population estimates." />
        <div className="overflow-x-auto">
          <table className="data-table">
            <thead><tr><th>Category</th><th>Automated passes</th><th>Cases</th></tr></thead>
            <tbody>{Object.entries(holdout.categories).map(([category, result]) => (
              <tr key={category}><td>{category.replaceAll("_", " ")}</td><td>{result.passed}</td><td>{result.sample_size}</td></tr>
            ))}</tbody>
          </table>
        </div>
      </Card>
      <Card className="mt-6">
        <SectionHeading title="Verify without an API key" description="Saved-score aggregation is deterministic. Fresh external model responses are not guaranteed to repeat, even at temperature zero." />
        <pre className="overflow-x-auto rounded border border-stone-300 bg-stone-50 p-4 text-sm">python scripts/build_evaluation_evidence.py --check</pre>
        <p className="mt-3 text-sm leading-6 text-stone-700">Checks metric denominators, saved answer/citation scores, and all 30 durable holdout records and their journal. It makes no external calls and does not judge semantic correctness.</p>
        <ul className="mt-4 grid gap-3 text-sm md:grid-cols-2">
          {reading.map(([label, path]) => <li key={path}><a className="underline underline-offset-4" href={`${repo}${path}`}>{label}</a></li>)}
        </ul>
        <Link className="btn-secondary mt-6" href="/dev-admin">Back to measured results</Link>
      </Card>
    </Shell>
  );
}
