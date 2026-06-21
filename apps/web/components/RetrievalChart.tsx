import { Badge } from "@/components/Badge";
import { Card } from "@/components/Card";
import { SectionHeading } from "@/components/SectionHeading";
import { EvalRun, formatTableMetric } from "@/lib/dashboard";

const chartRuns = [
  {
    runId: "phase6-vector-section",
    label: "vector-section",
    badge: "Legacy best",
    color: "bg-moss",
  },
  {
    runId: "phase6-keyword-section",
    label: "keyword-section",
    badge: null,
    color: "bg-steel",
  },
  {
    runId: "phase6-hybrid-section-0.5",
    label: "hybrid-section-0.5",
    badge: null,
    color: "bg-rust",
  },
  {
    runId: "phase33-vector-lexical-rerank-top3",
    label: "vector + lexical rerank",
    badge: "Current best precision",
    color: "bg-ink",
  },
];

export function RetrievalChart({ runs }: { runs: EvalRun[] }) {
  const selected = chartRuns
    .map((item) => {
      const run = runs.find((candidate) => candidate.run_id === item.runId);
      return run ? { ...item, run } : null;
    })
    .filter((item): item is (typeof chartRuns)[number] & { run: EvalRun } => item !== null);

  return (
    <Card>
      <SectionHeading
        title="Retrieval Precision Comparison"
        description="Legacy Phase 6 retrieval profiles compared with the Phase 33 reranked candidate."
      />
      <div className="space-y-4">
        {selected.map((item) => {
          const value = typeof item.run.metrics.precision_at_k === "number" ? item.run.metrics.precision_at_k : 0;
          return (
            <div key={item.run.run_id}>
              <div className="mb-1 flex items-center justify-between gap-4 text-sm">
                <div className="flex flex-wrap items-center gap-2">
                  <span className="font-medium text-ink">{item.label}</span>
                  {item.badge ? <Badge tone="solid">{item.badge}</Badge> : null}
                  <span className="text-xs text-stone-500">
                    {item.run.phase} | n={item.run.sample_size ?? item.run.total_questions ?? "n/a"} | benchmark{" "}
                    {item.run.benchmark_version ?? "n/a"}
                  </span>
                </div>
                <span className="font-medium text-stone-700">{formatTableMetric(item.run.metrics.precision_at_k)}</span>
              </div>
              <div className="h-3 rounded bg-stone-200">
                <div className={`h-3 rounded ${item.color}`} style={{ width: `${Math.max(value * 100, 2)}%` }} />
              </div>
            </div>
          );
        })}
      </div>
    </Card>
  );
}
