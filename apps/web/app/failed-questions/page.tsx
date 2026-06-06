import { Shell } from "@/components/Shell";
import { getEnrichedFailures } from "@/lib/api";
import { FailedQuestionsClient } from "./FailedQuestionsClient";

function countFailures(items: { failure_type: string }[], type: string): number {
  return items.filter((item) => item.failure_type === type).length;
}

export default async function FailedQuestionsPage() {
  const data = await getEnrichedFailures();
  const failures = data.failed_questions;
  const summary = [
    { label: "Total failures", value: failures.length, detail: "Open improvement backlog." },
    { label: "Multi-doc failures", value: countFailures(failures, "multi_document_failure"), detail: "Requires better multi-source retrieval and synthesis." },
    { label: "Citation issues", value: countFailures(failures, "wrong_citation"), detail: "Citation does not match expected source." },
    { label: "Unsupported answers", value: countFailures(failures, "unsupported_answer"), detail: "Answer support or confidence is weak." },
    { label: "Answer downgrades", value: countFailures(failures, "answer_not_generated"), detail: "Answerable question returned not found." },
  ];

  return (
    <Shell>
      <h2 className="text-3xl font-semibold">Failed Questions</h2>
      <p className="mt-3 max-w-3xl text-stone-700">
        Expand each benchmark failure to inspect expected answers, actual answers, citations, retrieved documents, and recommended fixes.
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
      <div className="mt-6">
        <FailedQuestionsClient failures={failures} />
      </div>
    </Shell>
  );
}
