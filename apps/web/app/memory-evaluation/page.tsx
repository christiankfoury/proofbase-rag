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
        <MetricCard label="Follow-up Detection" value={metrics.followup_detection_accuracy} tone="good" />
        <MetricCard label="Query Rewrite Quality" value={metrics.query_rewrite_quality} tone="good" />
        <MetricCard label="Memory Answer Accuracy" value={metrics.memory_answer_accuracy} tone="good" />
        <MetricCard label="Memory Citation Accuracy" value={metrics.memory_citation_accuracy} tone="good" />
        <MetricCard label="Memory Permission Leakage" value={metrics.memory_permission_leakage} tone="good" />
        <MetricCard label="Follow-up Hallucination Rate" value={metrics.hallucination_rate} tone="good" />
      </section>
      <section className="mt-8 grid gap-4 lg:grid-cols-3">
        <section className="rounded-md border border-stone-300 bg-white p-5">
          <h3 className="text-xl font-semibold">What Was Tested</h3>
          <ul className="mt-3 space-y-2 text-sm text-stone-700">
            <li>5 conversation-memory benchmark questions.</li>
            <li>Previous benchmark turns were included as session context.</li>
            <li>Retrieval mode: vector only.</li>
            <li>Chunking: section based.</li>
            <li>Top K: 5 chunks per follow-up.</li>
          </ul>
        </section>
        <section className="rounded-md border border-stone-300 bg-white p-5">
          <h3 className="text-xl font-semibold">How Memory Works</h3>
          <ul className="mt-3 space-y-2 text-sm text-stone-700">
            <li>Detects whether the current question depends on prior context.</li>
            <li>Rewrites follow-ups into standalone retrieval queries.</li>
            <li>Uses prior turns only to clarify the current question.</li>
            <li>Runs retrieval again against permission-filtered documents.</li>
          </ul>
        </section>
        <section className="rounded-md border border-stone-300 bg-white p-5">
          <h3 className="text-xl font-semibold">Safety Boundary</h3>
          <ul className="mt-3 space-y-2 text-sm text-stone-700">
            <li>Prior assistant answers are not source evidence.</li>
            <li>Memory does not cross sessions.</li>
            <li>Memory does not bypass role permissions.</li>
            <li>Citations must come from currently allowed documents.</li>
          </ul>
        </section>
      </section>
      <section className="mt-8 rounded-md border border-stone-300 bg-white p-5">
        <h3 className="text-xl font-semibold">Follow-up Example</h3>
        <div className="mt-3 grid gap-4 text-sm text-stone-700 md:grid-cols-2">
          <div className="rounded border border-stone-200 bg-stone-50 p-4">
            <p className="font-semibold text-ink">Conversation</p>
            <p className="mt-2">User: What is the parental leave policy?</p>
            <p className="mt-1">Follow-up: Does that apply to adoptive parents too?</p>
          </div>
          <div className="rounded border border-stone-200 bg-stone-50 p-4">
            <p className="font-semibold text-ink">Memory-safe handling</p>
            <p className="mt-2">Rewritten query: Does the parental leave policy apply to adoptive parents?</p>
            <p className="mt-1">Expected behavior: answer only if current allowed documents support it; otherwise say not found.</p>
          </div>
        </div>
      </section>
    </Shell>
  );
}
