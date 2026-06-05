import { MetricCard } from "@/components/MetricCard";
import { Shell } from "@/components/Shell";
import { getDashboardData } from "@/lib/dashboard";

export default async function PermissionSafetyPage() {
  const data = await getDashboardData();
  const run = data.runs.find((item) => item.phase === "phase-8");
  const metrics = run?.metrics ?? {};

  return (
    <Shell>
      <h2 className="text-3xl font-semibold">Permission Safety</h2>
      <p className="mt-3 max-w-3xl text-stone-700">
        Phase 8 tests whether restricted sources stay out of retrieval, generation, citations, and final answers.
      </p>
      <section className="mt-6 grid gap-4 md:grid-cols-3">
        <MetricCard label="Permission Leakage" value={metrics.permission_leakage_rate} />
        <MetricCard label="Unauthorized Chunk Exposure" value={metrics.unauthorized_chunk_exposure_rate} />
        <MetricCard label="Restricted Citation Leakage" value={metrics.restricted_citation_leakage_rate} />
        <MetricCard label="Blocked Answer Accuracy" value={metrics.blocked_answer_accuracy} />
        <MetricCard label="Authorized Retrieval Accuracy" value={metrics.authorized_retrieval_accuracy} />
        <MetricCard label="Authorized Answer Response" value={metrics.authorized_answer_accuracy} />
      </section>
      <section className="mt-8 rounded-md border border-stone-300 bg-white p-5">
        <h3 className="text-xl font-semibold">Safety Rule</h3>
        <p className="mt-2 text-stone-700">
          Current-role permission filters run before generation, and unauthorized chunks are not passed to the model.
        </p>
      </section>
    </Shell>
  );
}
