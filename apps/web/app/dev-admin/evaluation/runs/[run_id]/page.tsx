import { Card } from "@/components/Card";
import { PageHeader } from "@/components/PageHeader";
import { PhaseLabel, RunLabel } from "@/components/PhaseLabel";
import { Shell } from "@/components/Shell";
import { getRunQuestions } from "@/lib/api";
import { formatLabel } from "@/lib/dashboard";
import { formatRunLabel } from "@/lib/phases";
import { serverDemoAuthHeaders } from "@/lib/serverDemoAuth";
import { RunQuestionExplorer } from "./RunQuestionExplorer";

export default async function EvaluationRunDetailPage({ params }: { params: Promise<{ run_id: string }> }) {
  const resolvedParams = await params;
  const runId = decodeURIComponent(resolvedParams.run_id);
  const authHeaders = await serverDemoAuthHeaders();
  const data = await getRunQuestions(runId, authHeaders);
  const runName = typeof data.run?.run_name === "string" ? data.run.run_name : runId;
  const runLabel = formatRunLabel({
    run_id: runId,
    run_name: typeof data.run?.run_name === "string" ? data.run.run_name : null,
  });

  return (
    <Shell>
      <PageHeader
        title="Evaluation Run Detail"
        description={`Inspect available per-question benchmark rows for ${runLabel}. Some historical runs only have summary metrics.`}
      />
      <section className="grid gap-4 md:grid-cols-4">
        <Card padding="compact">
          <p className="text-sm font-medium text-steel">Run</p>
          <p className="mt-2 font-semibold text-ink">
            <RunLabel run={{ run_id: runId, run_name: runName }} />
          </p>
        </Card>
        <Card padding="compact">
          <p className="text-sm font-medium text-steel">Phase</p>
          <p className="mt-2 font-semibold text-ink">
            <PhaseLabel phase={typeof data.run?.phase === "string" ? data.run.phase : null} />
          </p>
        </Card>
        <Card padding="compact">
          <p className="text-sm font-medium text-steel">Detail Source</p>
          <p className="mt-2 font-semibold text-ink">{formatLabel(data.detail_source)}</p>
        </Card>
        <Card padding="compact">
          <p className="text-sm font-medium text-steel">Rows</p>
          <p className="mt-2 font-semibold text-ink">{data.row_count}</p>
        </Card>
      </section>
      <div className="mt-6">
        <RunQuestionExplorer data={data} />
      </div>
    </Shell>
  );
}
