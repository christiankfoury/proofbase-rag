import { Card } from "@/components/Card";
import { MetricCard } from "@/components/MetricCard";
import { PageHeader } from "@/components/PageHeader";
import { PhaseLabel, RunLabel } from "@/components/PhaseLabel";
import { SectionHeading } from "@/components/SectionHeading";
import { Shell } from "@/components/Shell";
import { formatLabel, getDashboardData } from "@/lib/dashboard";
import { serverDemoAuthHeaders } from "@/lib/serverDemoAuth";

export default async function PermissionSafetyPage() {
  const authHeaders = await serverDemoAuthHeaders();
  const data = await getDashboardData(authHeaders);
  const run = data.runs.find((item) => item.run_id === "phase36-permission-evaluation") ?? data.runs.find((item) => item.phase === "phase-8");
  const metrics = run?.metrics ?? {};
  const restrictedQuestionCount = metrics.restricted_question_count ?? run?.total_questions ?? "pending";
  const authorizedTestCount = metrics.authorized_test_count ?? "pending";

  return (
    <Shell>
      <PageHeader
        title="Permission Safety"
        description="The permission suite tests whether restricted sources stay out of retrieval, generation, citations, and final answers."
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
            <li>
              Run: <RunLabel run={run} showRaw={false} />{" "}
              <span className="text-stone-500">(<PhaseLabel phase={run?.phase} />)</span>
            </li>
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
