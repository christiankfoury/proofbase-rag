import Link from "next/link";
import { Card } from "@/components/Card";
import { PageHeader } from "@/components/PageHeader";
import { SectionHeading } from "@/components/SectionHeading";
import { Shell } from "@/components/Shell";
import evidence from "../../../../../data/evaluation/public-evidence.json";
import fresh from "../../../../../data/evaluation/fresh-current/public-report.json";

import reanalysis from "../../../../../data/evaluation/dimension-reanalysis-v1/public-summary.json";
import current from "../../../../../data/evaluation/current-runtime-v3/public-report.json";
import latest from "../../../../../data/evaluation/current-runtime-v4/public-report.json";
import successor from "../../../../../data/evaluation/current-runtime-v5/public-report.json";
import captures from "../../../../../data/evaluation/current-runtime-v5/capture-publication.json";

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
        <SectionHeading title="Latest frozen-runtime evaluation" description="Phase 73 successor: a fresh sealed suite with the separately qualified v21 evaluator." />
        <p className="text-3xl font-semibold text-ink">
          {successor.validated_passes === null ? "No validated full-suite score" : `${successor.validated_passes}/${successor.expected_cases} automated protocol passes`}
        </p>
        <p className="mt-3 text-sm leading-6 text-stone-700">
          {successor.completed_cases}/{successor.expected_cases} cases graded. Run status: {successor.status}.{" "}
          {successor.budget_exhausted ? "The spending guard stopped execution before another request could be reserved. " : ""}
          Predeclared target: {successor.target}/{successor.expected_cases}; {successor.target_met ? "met under the declared protocol" : "not established"}.
          {" "}Model candidate passes among completed cases: {successor.candidate_passes}/{successor.completed_cases}.
          {" "}A partial prefix is not a full-suite accuracy estimate.
          {" "}{captures.captured_cases} application responses are saved; {captures.ungraded_captured_cases.length} lacks a completed evaluation row and {captures.unexecuted_cases.length} cases were not executed.
        </p>
        <p className="mt-3 text-sm leading-6 text-stone-700">
          Source inspection: {successor.source_inspection_passed ? "approved" : "not approved"}.
          {" "}Invalid grades: {successor.invalid_grades}. Cases with model-review disagreements: {successor.disputed_cases.length}.
          {" "}Recorded safety-flag cases among graded rows: {successor.safety_flag_cases.length}.
          {" "}Unfinished coverage cannot establish the full safety gate. Unresolved judgments receive no target credit; quotation fidelity is separate.
        </p>
        <div className="mt-4 overflow-x-auto">
          <table className="w-full text-left text-sm">
            <thead><tr><th className="p-2">Dimension</th><th className="p-2">Model pass</th><th className="p-2">Model fail</th><th className="p-2">Unresolved</th><th className="p-2">Not applicable</th></tr></thead>
            <tbody>{Object.entries(successor.dimensions).map(([name, values]) => {
              const counts = values as Record<string, number>;
              return <tr key={name} className="border-t border-stone-200"><td className="p-2 capitalize">{name.replaceAll("_", " ")}</td><td className="p-2">{counts.pass ?? 0}</td><td className="p-2">{counts.fail ?? 0}</td><td className="p-2">{counts.unresolved ?? 0}</td><td className="p-2">{counts.not_applicable ?? 0}</td></tr>;
            })}</tbody>
          </table>
        </div>
        <p className="mt-3 text-sm leading-6 text-stone-700">
          This attempt: {successor.calls} API calls; estimated usage USD {Number(successor.holdout_cost_usd).toFixed(4)}.
          {" "}Shared additional accounting: USD {Number(successor.additional_spend_usd).toFixed(4)} of {Number(successor.additional_ceiling_usd).toFixed(2)}, including retained historical reservations.
          {" "}Median application latency across {captures.latency_ms.count} saved responses: {captures.latency_ms.median === null ? "unavailable" : `${(captures.latency_ms.median / 1000).toFixed(1)} seconds`}.
          {" "}P95: {captures.latency_ms.p95 === null ? "unavailable" : `${(captures.latency_ms.p95 / 1000).toFixed(1)} seconds`}. Grading and fixture indexing are excluded. Costs are estimates, not invoices.
        </p>
        <p className="mt-3 text-sm leading-6 text-stone-700">{successor.limitation}</p>
        <p className="mt-3 break-all text-xs text-stone-500">Suite: {successor.suite_version}; runtime: {successor.runtime_commit}; evaluator: {successor.version}; model: {successor.model}.</p>
        <div className="mt-4 flex flex-wrap gap-4 text-sm">
          <a className="underline" href={`${repo}docs/phase-73/v5-case-review.md`}>Inspect every question and answer</a>
          <a className="underline" href={`${repo}docs/phase-73/v5-results.md`}>Results, costs and limitations</a>
          <a className="underline" href={`${repo}docs/phase-73/v5-source-review.md`}>Source inspection and findings</a>
        </div>
        <pre className="mt-4 overflow-x-auto rounded border border-stone-300 bg-stone-50 p-4 text-sm">python scripts/report_phase73_v5.py --check</pre>
      </Card>
      <Card className="mb-6">
        <SectionHeading title="Original Phase 73 attempt — interrupted" description="Phase 73: a planned 60-case run stopped after an API timeout. No full-suite score." />
        <p className="text-3xl font-semibold text-ink">
          {latest.validated_passes === null
            ? "No validated full-suite score"
            : `${latest.validated_passes}/${latest.expected_cases} automated protocol passes`}
        </p>
        <p className="mt-3 text-sm leading-6 text-stone-700">
          {latest.completed_cases}/{latest.expected_cases} cases completed. Run status: {latest.status}.{" "}
          {latest.captured_cases} application responses saved; {latest.ungraded_captured_cases} remains ungraded and {latest.unexecuted_cases} cases were not executed.
          Predeclared target: {latest.target}/{latest.expected_cases} — not established by this incomplete run.
          Unresolved judgments receive no target credit; quotation fidelity is reported separately.
        </p>
        <p className="mt-3 text-sm leading-6 text-stone-700">
          Model candidate passes among completed cases: {latest.candidate_passes}/{latest.completed_cases}. Source inspection: {latest.source_inspection_passed ? "passed" : "not approved"}.
          Invalid grades: {latest.invalid_grades}. Cases with model-review disagreements: {latest.disputed_cases.length}.
          Cases with recorded safety flags: {latest.safety_flag_cases.length}. The dedicated safety groups were not executed.
        </p>
        <div className="mt-4 overflow-x-auto">
          <table className="w-full text-left text-sm">
            <thead><tr><th className="p-2">Dimension</th><th className="p-2">Model pass</th><th className="p-2">Model fail</th><th className="p-2">Unresolved</th><th className="p-2">Not applicable</th></tr></thead>
            <tbody>{Object.entries(latest.dimensions).map(([name, values]) => {
              const counts = values as Record<string, number>;
              return (
                <tr key={name} className="border-t border-stone-200">
                  <td className="p-2 capitalize">{name.replaceAll("_", " ")}</td>
                  <td className="p-2">{counts.pass ?? 0}</td><td className="p-2">{counts.fail ?? 0}</td>
                  <td className="p-2">{counts.unresolved ?? 0}</td><td className="p-2">{counts.not_applicable ?? 0}</td>
                </tr>
              );
            })}</tbody>
          </table>
        </div>
        <p className="mt-3 text-sm leading-6 text-stone-700">
          This run attempted {latest.calls} API calls, including application and grading calls: {latest.settled_calls} settled and {latest.unknown_calls} with an unknown outcome.
          Settled usage estimate: USD {Number(latest.settled_usage_cost_usd).toFixed(4)}; retained unknown-call reservation: USD {Number(latest.unknown_reserved_usd).toFixed(4)}.
          Median application latency: {latest.latency_ms.median === null ? "unavailable" : `${(latest.latency_ms.median / 1000).toFixed(1)} seconds`}.
          P95: {latest.latency_ms.p95 === null ? "unavailable" : `${(latest.latency_ms.p95 / 1000).toFixed(1)} seconds`}.
          Latency covers all {latest.latency_ms.count} saved application responses and excludes grading and fixture indexing. Costs are not invoices.
        </p>
        <p className="mt-3 text-sm leading-6 text-stone-700">{latest.limitation}</p>
        <p className="mt-3 text-sm leading-6 text-stone-700">
          The evaluator qualified on 24/24 development cases, 3/3 reviewer probes and 16/16 fresh confirmation cases with source inspection.
          That bounded qualification does not establish infallibility. Role and project tests do not establish department-only or production security coverage.
        </p>
        <p className="mt-3 break-all text-xs text-stone-500">Suite: {latest.suite_version}; runtime: {latest.runtime_commit}; evaluator: {latest.version}; model: {latest.model}.</p>
        <div className="mt-4 flex flex-wrap gap-4 text-sm">
          <a className="underline" href={`${repo}docs/phase-73/case-review.md`}>Inspect every question and answer</a>
          <a className="underline" href={`${repo}docs/phase-73/results.md`}>Results, costs and limitations</a>
          <a className="underline" href={`${repo}docs/phase-73/source-review.md`}>Source inspection and findings</a>
        </div>
        <pre className="mt-4 overflow-x-auto rounded border border-stone-300 bg-stone-50 p-4 text-sm">python scripts/report_phase73_interruption.py --check</pre>
      </Card>
      <Card className="mb-6">
        <SectionHeading title="Previous frozen-runtime evaluation" description="Phase 68 historical evidence. Its separate dimensions are preserved with the original audit limitations." />
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
