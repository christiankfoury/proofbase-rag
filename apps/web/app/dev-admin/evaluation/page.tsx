import Link from "next/link";
import { Card } from "@/components/Card";
import { PageHeader } from "@/components/PageHeader";
import { SectionHeading } from "@/components/SectionHeading";
import { Shell } from "@/components/Shell";
import evidence from "../../../../../data/evaluation/public-evidence.json";

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
          <p className="mt-2 text-sm text-stone-700">This historical run does not measure the current runtime. No new holdout was executed for this report.</p>
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
        <SectionHeading title="Where the holdout failed" description="Category counts come from the committed offline report. These small, designed samples are not population estimates." />
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
