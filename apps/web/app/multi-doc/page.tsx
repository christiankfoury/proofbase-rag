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
        <h2 className="text-3xl font-semibold">Multi-Document Reasoning</h2>
        <section className="mt-8 rounded-md border border-stone-300 bg-white p-5">
          <p className="text-stone-700">
            No multi-document evaluation results found. Run{" "}
            <code className="rounded bg-stone-100 px-1 py-0.5 text-sm">python scripts/run_multi_doc_eval.py</code>
            {" "}then{" "}
            <code className="rounded bg-stone-100 px-1 py-0.5 text-sm">python scripts/export_dashboard_data.py</code>.
          </p>
        </section>
      </Shell>
    );
  }

  const { baseline, multi_doc, fixed_questions = [], broken_questions = [], still_failing = [], hallucination_regression } = comparison;

  return (
    <Shell>
      <h2 className="text-3xl font-semibold">Multi-Document Reasoning</h2>
      <p className="mt-3 max-w-3xl text-stone-700">
        Phase 13 adds query decomposition, multi-source retrieval, and grouped evidence context to fix questions that require synthesizing answers from two or more source documents.
        Evaluated on 10 MULTI benchmark questions against a single-query baseline.
      </p>

      <section className="mt-8">
        <h3 className="mb-3 text-xl font-semibold">Baseline vs Multi-Document</h3>
        <div className="overflow-x-auto rounded-md border border-stone-300 bg-white">
          <table className="w-full text-left text-sm">
            <thead className="bg-stone-100">
              <tr>
                <th className="px-4 py-3">Metric</th>
                <th className="px-4 py-3 text-right">Baseline</th>
                <th className="px-4 py-3 text-right">Multi-Doc</th>
                <th className="px-4 py-3 text-right">Change</th>
              </tr>
            </thead>
            <tbody>
              {METRICS.map(({ key, label, higherIsBetter }) => {
                const b = baseline[key] as number | null | undefined;
                const m = multi_doc[key] as number | null | undefined;
                const d = delta(b, m, higherIsBetter);
                return (
                  <tr key={key} className="border-t border-stone-200">
                    <td className="px-4 py-3">{label}</td>
                    <td className="px-4 py-3 text-right">{formatTableMetric(b)}</td>
                    <td className="px-4 py-3 text-right font-medium">{formatTableMetric(m)}</td>
                    <td className={`px-4 py-3 text-right font-medium ${
                      d?.better ? "text-moss" : d?.worse ? "text-rust" : "text-stone-500"
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
          <p className="mt-3 rounded-md border border-rust bg-orange-50 px-4 py-3 text-sm text-rust">
            Hallucination rate increased with multi-document mode. Synthesizing across documents produces inferences that the citation validator cannot fully match back to individual chunks. This is a known tradeoff — documented, not hidden.
          </p>
        )}
      </section>

      <section className="mt-8 grid gap-4 lg:grid-cols-3">
        <article className="rounded-md border border-moss bg-white p-5">
          <h3 className="font-semibold text-moss">Fixed by Multi-Doc</h3>
          <p className="mt-3 text-sm text-stone-700">
            {fixed_questions.length > 0 ? fixed_questions.join(", ") : "None"}
          </p>
        </article>
        <article className="rounded-md border border-rust bg-white p-5">
          <h3 className="font-semibold text-rust">Broken by Multi-Doc</h3>
          <p className="mt-3 text-sm text-stone-700">
            {broken_questions.length > 0 ? broken_questions.join(", ") : "None"}
          </p>
        </article>
        <article className="rounded-md border border-stone-300 bg-white p-5">
          <h3 className="font-semibold text-steel">Still Failing</h3>
          <p className="mt-3 text-sm text-stone-700">
            {still_failing.length > 0 ? still_failing.join(", ") : "None"}
          </p>
        </article>
      </section>

      <section className="mt-8 rounded-md border border-stone-300 bg-white p-5">
        <h3 className="mb-2 font-semibold">How It Works</h3>
        <ul className="space-y-1 text-sm text-stone-700">
          <li><span className="font-medium">Detection</span> — heuristic cross-domain keyword pairs identify questions needing multiple documents</li>
          <li><span className="font-medium">Decomposition</span> — one GPT-4.1-mini call generates 2-3 subqueries, one per required document domain</li>
          <li><span className="font-medium">Multi-source retrieval</span> — each subquery runs independently through permission-filtered vector retrieval; results merged and deduplicated</li>
          <li><span className="font-medium">Grouped context</span> — chunks presented to the model grouped by document, making source boundaries clear</li>
          <li><span className="font-medium">v4 prompt</span> — instructs the model to synthesize across documents and cite every contributing source</li>
        </ul>
      </section>
    </Shell>
  );
}
