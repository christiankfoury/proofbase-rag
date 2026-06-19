import { Card } from "@/components/Card";
import { EmptyState } from "@/components/EmptyState";
import { PageHeader } from "@/components/PageHeader";
import { SectionHeading } from "@/components/SectionHeading";
import { Shell } from "@/components/Shell";
import { getDashboardData, formatTableMetric, type MultiDocComparison } from "@/lib/dashboard";

const METRICS: { key: keyof NonNullable<MultiDocComparison["baseline"]>; label: string; higherIsBetter: boolean }[] = [
  { key: "answer_accuracy", label: "Answer Accuracy", higherIsBetter: true },
  { key: "citation_accuracy", label: "Citation Accuracy", higherIsBetter: true },
  { key: "all_sources_hit", label: "All Sources Hit", higherIsBetter: true },
  { key: "source_coverage_score", label: "Source Coverage", higherIsBetter: true },
  { key: "all_required_sources_cited_rate", label: "All Sources Cited", higherIsBetter: true },
  { key: "response_type_accuracy", label: "Response Type Accuracy", higherIsBetter: true },
  { key: "hallucination_rate", label: "Hallucination Rate", higherIsBetter: false },
  { key: "failed_question_count", label: "Failed Questions", higherIsBetter: false },
];

function delta(baseline: number | null | undefined, improved: number | null | undefined, higherIsBetter: boolean) {
  if (baseline == null || improved == null) return null;
  const diff = improved - baseline;
  const better = higherIsBetter ? diff > 0 : diff < 0;
  const worse = higherIsBetter ? diff < 0 : diff > 0;
  return { diff, better, worse };
}

export default async function MultiDocPage() {
  const data = await getDashboardData();
  const comparison = data.multi_doc_comparison;

  if (!comparison || !comparison.baseline || !comparison.multi_doc) {
    return (
      <Shell>
        <PageHeader title="Multi-Document Reasoning" />
        <EmptyState>
          No multi-document evaluation results found. Run{" "}
          <code className="rounded bg-stone-100 px-1 py-0.5 text-sm">python scripts/run_multi_doc_eval.py</code>
          {" "}then{" "}
          <code className="rounded bg-stone-100 px-1 py-0.5 text-sm">python scripts/export_dashboard_data.py</code>.
        </EmptyState>
      </Shell>
    );
  }

  const { baseline, multi_doc, fixed_questions = [], broken_questions = [], still_failing = [], hallucination_regression } = comparison;

  return (
    <Shell>
      <PageHeader
        title="Multi-Document Reasoning"
        description="Phase 13 adds query decomposition, multi-source retrieval, and grouped evidence context to fix questions that require synthesizing answers from two or more source documents. Evaluated on 10 MULTI benchmark questions against a single-query baseline."
      />

      <section>
        <SectionHeading title="Baseline vs Multi-Document" />
        <div className="overflow-x-auto rounded-md border border-stone-300 bg-white shadow-card">
          <table className="data-table">
            <thead>
              <tr>
                <th>Metric</th>
                <th className="text-right">Baseline</th>
                <th className="text-right">Multi-Doc</th>
                <th className="text-right">Change</th>
              </tr>
            </thead>
            <tbody>
              {METRICS.map(({ key, label, higherIsBetter }) => {
                const b = baseline[key] as number | null | undefined;
                const m = multi_doc[key] as number | null | undefined;
                const d = delta(b, m, higherIsBetter);
                return (
                  <tr key={key}>
                    <td>{label}</td>
                    <td className="text-right">{formatTableMetric(b)}</td>
                    <td className="text-right font-medium text-ink">{formatTableMetric(m)}</td>
                    <td className={`text-right font-semibold ${
                      d?.better ? "text-moss-dark" : d?.worse ? "text-rust-dark" : "text-stone-500"
                    }`}>
                      {d == null ? "-" : d.diff === 0 ? "±0" : `${d.diff > 0 ? "+" : ""}${typeof m === "number" && typeof b === "number" && !Number.isInteger(b) ? d.diff.toFixed(3) : d.diff}`}
                    </td>
                  </tr>
                );
              })}
            </tbody>
          </table>
        </div>
        {hallucination_regression && (
          <p className="mt-3 rounded-md border border-rust bg-rust-soft px-4 py-3 text-sm font-medium text-rust-dark">
            Hallucination rate increased with multi-document mode. Synthesizing across documents produces inferences that the citation validator cannot fully match back to individual chunks. This is a known tradeoff — documented, not hidden.
          </p>
        )}
      </section>

      <section className="mt-8 grid gap-4 lg:grid-cols-3">
        <Card tone="good">
          <h3 className="font-semibold text-moss-dark">Fixed by Multi-Doc</h3>
          <p className="mt-3 text-sm text-stone-700">
            {fixed_questions.length > 0 ? fixed_questions.join(", ") : "None"}
          </p>
        </Card>
        <Card tone="warn">
          <h3 className="font-semibold text-rust-dark">Broken by Multi-Doc</h3>
          <p className="mt-3 text-sm text-stone-700">
            {broken_questions.length > 0 ? broken_questions.join(", ") : "None"}
          </p>
        </Card>
        <Card>
          <h3 className="font-semibold text-steel-dark">Still Failing</h3>
          <p className="mt-3 text-sm text-stone-700">
            {still_failing.length > 0 ? still_failing.join(", ") : "None"}
          </p>
        </Card>
      </section>

      <Card className="mt-8">
        <SectionHeading title="How It Works" />
        <ul className="space-y-1 text-sm text-stone-700">
          <li><span className="font-medium text-ink">Detection</span> — heuristic cross-domain keyword pairs identify questions needing multiple documents</li>
          <li><span className="font-medium text-ink">Decomposition</span> — one GPT-4.1-mini call generates 2-3 subqueries, one per required document domain</li>
          <li><span className="font-medium text-ink">Multi-source retrieval</span> — each subquery runs independently through permission-filtered vector retrieval; results merged and deduplicated</li>
          <li><span className="font-medium text-ink">Grouped context</span> — chunks presented to the model grouped by document, making source boundaries clear</li>
          <li><span className="font-medium text-ink">v4 prompt</span> — instructs the model to synthesize across documents and cite every contributing source</li>
        </ul>
      </Card>
    </Shell>
  );
}
