import { Shell } from "@/components/Shell";
import { formatMetric, getDashboardData } from "@/lib/dashboard";

const failureLabels: Record<string, string> = {
  answer_not_generated: "Answer downgraded",
  incomplete_answer: "Incomplete answer",
  multi_document_failure: "Multi-doc failure",
  unsupported_answer: "Unsupported answer",
  wrong_citation: "Wrong citation",
};

const failureTone: Record<string, string> = {
  answer_not_generated: "border-rust bg-orange-50 text-rust",
  incomplete_answer: "border-steel bg-slate-50 text-steel",
  multi_document_failure: "border-rust bg-orange-50 text-rust",
  unsupported_answer: "border-rust bg-orange-50 text-rust",
  wrong_citation: "border-steel bg-slate-50 text-steel",
};

function labelForFailure(value: string): string {
  return failureLabels[value] ?? value.replaceAll("_", " ");
}

function labelForResponse(value: string | undefined): string {
  if (!value) return "n/a";
  return value
    .replaceAll("_", " ")
    .replace(/\b\w/g, (letter) => letter.toUpperCase());
}

function countFailures(items: { failure_type: string }[], type: string): number {
  return items.filter((item) => item.failure_type === type).length;
}

export default async function FailedQuestionsPage() {
  const data = await getDashboardData();
  const failures = data.failed_questions;
  const summary = [
    { label: "Total failures", value: failures.length, detail: "Open improvement backlog." },
    { label: "Multi-doc failures", value: countFailures(failures, "multi_document_failure"), detail: "Requires better multi-source synthesis." },
    { label: "Citation issues", value: countFailures(failures, "wrong_citation"), detail: "Citation does not match expected source." },
    { label: "Unsupported answers", value: countFailures(failures, "unsupported_answer"), detail: "Answer support or confidence is weak." },
    { label: "Answer downgrades", value: countFailures(failures, "answer_not_generated"), detail: "Answerable question returned not found." },
  ];

  return (
    <Shell>
      <h2 className="text-3xl font-semibold">Failed Questions</h2>
      <p className="mt-3 max-w-3xl text-stone-700">
        These failures are the next improvement backlog. They are exported from the Phase 7 and Phase 9 failed-question reports.
      </p>
      <section className="mt-6 grid gap-4 md:grid-cols-2 xl:grid-cols-5">
        {summary.map((item) => (
          <article key={item.label} className="rounded-md border border-stone-300 bg-white p-4">
            <p className="text-sm font-medium text-steel">{item.label}</p>
            <p className="mt-2 text-3xl font-semibold">{item.value}</p>
            <p className="mt-2 text-sm text-stone-600">{item.detail}</p>
          </article>
        ))}
      </section>
      <section className="mt-6 rounded-md border border-stone-300 bg-white p-5">
        <h3 className="text-xl font-semibold">Failure Interpretation</h3>
        <p className="mt-2 text-stone-700">
          Most failures are answer-generation, citation, and multi-document synthesis issues. Permission safety is not the current failure pattern.
        </p>
        <p className="mt-2 text-stone-700">
          The next improvement target is stronger multi-document reasoning, stricter citation grounding, and better confidence thresholds for answerable questions.
        </p>
      </section>
      <div className="mt-6 overflow-x-auto rounded-md border border-stone-300 bg-white">
        <table className="w-full min-w-[960px] text-left text-sm">
          <thead className="bg-stone-100">
            <tr>
              <th className="p-3">Question</th>
              <th className="p-3">Phase</th>
              <th className="p-3">Failure</th>
              <th className="p-3">Actual</th>
              <th className="p-3 text-right">Citation Conf</th>
              <th className="p-3 text-right">Answer Conf</th>
              <th className="p-3">Recommended Fix</th>
            </tr>
          </thead>
          <tbody>
            {failures.map((item) => (
              <tr key={`${item.phase}-${item.question_id}`} className="border-t border-stone-200">
                <td className="whitespace-nowrap p-3 font-medium">{item.question_id}</td>
                <td className="whitespace-nowrap p-3">{item.phase}</td>
                <td className="p-3">
                  <span className={`inline-flex whitespace-nowrap rounded border px-2 py-1 text-xs font-semibold ${failureTone[item.failure_type] ?? "border-stone-300 bg-stone-50 text-stone-700"}`}>
                    {labelForFailure(item.failure_type)}
                  </span>
                </td>
                <td className="whitespace-nowrap p-3">{labelForResponse(item.actual_response_type)}</td>
                <td className="p-3 text-right">{formatMetric(item.citation_confidence)}</td>
                <td className="p-3 text-right">{formatMetric(item.answer_confidence)}</td>
                <td className="p-3">{item.recommended_fix}</td>
              </tr>
            ))}
          </tbody>
        </table>
      </div>
    </Shell>
  );
}
