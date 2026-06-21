import { MetricCard } from "@/components/MetricCard";
import { PageHeader } from "@/components/PageHeader";
import { Shell } from "@/components/Shell";
import { getEnrichedFailures } from "@/lib/api";
import { serverDemoAuthHeaders } from "@/lib/serverDemoAuth";
import { FailedQuestionsClient } from "./FailedQuestionsClient";

function countFailures(items: { failure_type: string }[], type: string): number {
  return items.filter((item) => item.failure_type === type).length;
}

function countCitationCategoryRows(items: { citation_failure_categories?: string[] }[]): number {
  return items.filter((item) => (item.citation_failure_categories ?? []).length > 0).length;
}

export default async function FailedQuestionsPage() {
  const authHeaders = await serverDemoAuthHeaders();
  const data = await getEnrichedFailures(authHeaders);
  const failures = data.failed_questions;
  const summary = [
    { label: "Total failures", value: failures.length, detail: "Open improvement backlog.", tone: "neutral" as const },
    { label: "Multi-doc failures", value: countFailures(failures, "multi_document_failure"), detail: "Requires better multi-source retrieval and synthesis.", tone: "warn" as const },
    { label: "Citation issues", value: countCitationCategoryRows(failures) || countFailures(failures, "wrong_citation"), detail: "Rows with a Phase 35 citation category.", tone: "warn" as const },
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
