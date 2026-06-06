import { Shell } from "@/components/Shell";
import { getRunQuestions } from "@/lib/api";
import { formatLabel } from "@/lib/dashboard";
import { RunQuestionExplorer } from "./RunQuestionExplorer";

export default async function EvaluationRunDetailPage({ params }: { params: Promise<{ run_id: string }> }) {
  const resolvedParams = await params;
  const runId = decodeURIComponent(resolvedParams.run_id);
  const data = await getRunQuestions(runId);
  const runName = typeof data.run?.run_name === "string" ? data.run.run_name : runId;

  return (
    <Shell>
      <h2 className="text-3xl font-semibold">Evaluation Run Detail</h2>
      <p className="mt-3 max-w-3xl text-stone-700">
        Inspect available per-question benchmark rows for {runName}. Some historical runs only have summary metrics.
      </p>
      <section className="mt-6 grid gap-4 md:grid-cols-4">
        <article className="rounded-md border border-stone-300 bg-white p-4">
          <p className="text-sm font-medium text-steel">Run</p>
          <p className="mt-2 font-semibold">{runName}</p>
        </article>
        <article className="rounded-md border border-stone-300 bg-white p-4">
          <p className="text-sm font-medium text-steel">Phase</p>
          <p className="mt-2 font-semibold">{typeof data.run?.phase === "string" ? data.run.phase : "n/a"}</p>
        </article>
        <article className="rounded-md border border-stone-300 bg-white p-4">
          <p className="text-sm font-medium text-steel">Detail Source</p>
          <p className="mt-2 font-semibold">{formatLabel(data.detail_source)}</p>
        </article>
        <article className="rounded-md border border-stone-300 bg-white p-4">
          <p className="text-sm font-medium text-steel">Rows</p>
          <p className="mt-2 font-semibold">{data.row_count}</p>
        </article>
      </section>
      <div className="mt-6">
        <RunQuestionExplorer data={data} />
      </div>
    </Shell>
  );
}
