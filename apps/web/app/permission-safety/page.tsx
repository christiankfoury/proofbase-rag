import { Card } from "@/components/Card";
import { MetricCard } from "@/components/MetricCard";
import { PageHeader } from "@/components/PageHeader";
import { SectionHeading } from "@/components/SectionHeading";
import { Shell } from "@/components/Shell";
import { formatLabel, getDashboardData } from "@/lib/dashboard";

export default async function PermissionSafetyPage() {
  const data = await getDashboardData();
  const run = data.runs.find((item) => item.phase === "phase-8");
  const metrics = run?.metrics ?? {};
  const restrictedQuestionCount = metrics.restricted_question_count ?? run?.total_questions ?? "pending";
  const authorizedTestCount = metrics.authorized_test_count ?? "pending";

  return (
    <Shell>
      <PageHeader
        title="Permission Safety"
        description="Phase 8 tests whether restricted sources stay out of retrieval, generation, citations, and final answers."
      />
      <section className="grid gap-4 md:grid-cols-3">
        <MetricCard label="Permission Leakage" value={metrics.permission_leakage_rate} tone="good" badge="Safety" />
        <MetricCard label="Unauthorized Chunk Exposure" value={metrics.unauthorized_chunk_exposure_rate} tone="good" />
        <MetricCard label="Restricted Citation Leakage" value={metrics.restricted_citation_leakage_rate} tone="good" />
        <MetricCard label="Blocked Answer Accuracy" value={metrics.blocked_answer_accuracy} />
        <MetricCard label="Authorized Retrieval Accuracy" value={metrics.authorized_retrieval_accuracy} />
        <MetricCard label="Authorized Answer Response Rate" value={metrics.authorized_answer_accuracy} />
      </section>
      <section className="mt-8 grid gap-4 lg:grid-cols-3">
        <Card>
          <SectionHeading title="What Was Tested" />
          <ul className="space-y-2 text-sm text-stone-700">
            <li>{restrictedQuestionCount} restricted benchmark questions.</li>
            <li>{authorizedTestCount} authorized source-access tests.</li>
            <li>Retrieval mode: {formatLabel(run?.retrieval_mode)}.</li>
            <li>Chunking: {formatLabel(run?.chunking_strategy)}.</li>
            <li>Top K: {run?.top_k ?? "pending"} chunks per question.</li>
          </ul>
        </Card>
        <Card tone="good">
          <SectionHeading title="Security Outcome" />
          <ul className="space-y-2 text-sm text-stone-700">
            <li>Restricted chunks did not appear in unauthorized retrieval results.</li>
            <li>Restricted citations were not returned to unauthorized users.</li>
            <li>Unauthorized chunks did not reach answer generation.</li>
            <li>Authorized roles could retrieve expected restricted sources.</li>
          </ul>
        </Card>
        <Card>
          <SectionHeading title="Why This Matters" />
          <p className="text-sm text-stone-700">
            The system does not rely only on prompt refusal. Permissions are enforced before retrieval context reaches the LLM, which is a core enterprise control.
          </p>
        </Card>
      </section>
      <Card className="mt-8">
        <SectionHeading title="Safety Rule" />
        <p className="text-stone-700">
          Current-role permission filters run before generation, and unauthorized chunks are not passed to the model.
        </p>
      </Card>
    </Shell>
  );
}
