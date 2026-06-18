import { MetricCard } from "@/components/MetricCard";
import { PageHeader } from "@/components/PageHeader";
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
    { label: "Total failures", value: failures.length, detail: "Open improvement backlog.", tone: "neutral" as const },
    { label: "Multi-doc failures", value: countFailures(failures, "multi_document_failure"), detail: "Requires better multi-source retrieval and synthesis.", tone: "warn" as const },
    { label: "Citation issues", value: countFailures(failures, "wrong_citation"), detail: "Citation does not match expected source.", tone: "warn" as const },
    { label: "Unsupported answers", value: countFailures(failures, "unsupported_answer"), detail: "Answer support or confidence is weak.", tone: "warn" as const },
    { label: "Answer downgrades", value: countFailures(failures, "answer_not_generated"), detail: "Answerable question returned not found.", tone: "warn" as const },
  ];

  return (
    <Shell>
      <PageHeader
        title="Failed Questions"
        description="Expand each benchmark failure to inspect expected answers, actual answers, citations, retrieved documents, and recommended fixes."
      />
      <section className="grid gap-4 md:grid-cols-2 xl:grid-cols-5">
        {summary.map((item) => (
          <MetricCard key={item.label} label={item.label} value={item.value} detail={item.detail} tone={item.tone} />
        ))}
      </section>
      <div className="mt-8">
        <FailedQuestionsClient failures={failures} />
      </div>
    </Shell>
  );
}
