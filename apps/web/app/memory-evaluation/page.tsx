import { MetricCard } from "@/components/MetricCard";
import { Shell } from "@/components/Shell";
import { getDashboardData } from "@/lib/dashboard";

export default async function MemoryEvaluationPage() {
  const data = await getDashboardData();
  const run = data.runs.find((item) => item.phase === "phase-9");
  const metrics = run?.metrics ?? {};

  return (
    <Shell>
      <h2 className="text-3xl font-semibold">Memory Evaluation</h2>
      <p className="mt-3 max-w-3xl text-stone-700">
        Phase 9 evaluates session-level follow-up detection and query rewriting while keeping source evidence permission-filtered.
      </p>
      <section className="mt-6 grid gap-4 md:grid-cols-3">
        <MetricCard label="Follow-up Detection" value={metrics.followup_detection_accuracy} />
        <MetricCard label="Query Rewrite Quality" value={metrics.query_rewrite_quality} />
        <MetricCard label="Memory Answer Accuracy" value={metrics.memory_answer_accuracy} />
        <MetricCard label="Memory Citation Accuracy" value={metrics.memory_citation_accuracy} />
        <MetricCard label="Memory Permission Leakage" value={metrics.memory_permission_leakage} />
        <MetricCard label="Follow-up Hallucination Rate" value={metrics.hallucination_rate} />
      </section>
      <section className="mt-8 rounded-md border border-stone-300 bg-white p-5">
        <h3 className="text-xl font-semibold">Memory Boundary</h3>
        <p className="mt-2 text-stone-700">
          Prior turns clarify the query only. Prior assistant text is not treated as source evidence, and retrieval still cites current allowed documents.
        </p>
      </section>
    </Shell>
  );
}
