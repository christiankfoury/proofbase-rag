"use client";

import { useState, useRef } from "react";
import { createPortal } from "react-dom";
import Link from "next/link";
import { Badge } from "@/components/Badge";
import { PhaseLabel, RunLabel } from "@/components/PhaseLabel";
import { EvalRun, formatDateTime, formatLabel, formatTableMetric, riskRateClass } from "@/lib/dashboard";

function formatCost(value: number | string | null | undefined): string {
  if (value === null || value === undefined || value === "") return "-";
  if (typeof value === "number") return `$${value.toFixed(6)}`;
  if (value.toLowerCase() === "pending") return "-";
  return value;
}

function MetricTh({ label, tip }: { label: string; tip: string }) {
  const [visible, setVisible] = useState(false);
  const [pos, setPos] = useState({ top: 0, left: 0 });
  const ref = useRef<HTMLSpanElement>(null);

  const handleMouseEnter = () => {
    if (ref.current) {
      const r = ref.current.getBoundingClientRect();
      setPos({ top: r.bottom + 6, left: r.left + r.width / 2 });
    }
    setVisible(true);
  };

  return (
    <th className="text-right">
      <span
        ref={ref}
        onMouseEnter={handleMouseEnter}
        onMouseLeave={() => setVisible(false)}
        className="inline-flex cursor-default items-center gap-1"
      >
        {label}
        <span className="text-[10px] text-stone-400">(?)</span>
      </span>
      {visible &&
        createPortal(
          <span
            style={{ position: "fixed", top: pos.top, left: pos.left, transform: "translateX(-50%)", zIndex: 9999 }}
            className="pointer-events-none w-56 rounded bg-stone-800 px-2 py-1.5 text-left text-xs font-normal text-white shadow-lg"
          >
            {tip}
          </span>,
          document.body
        )}
    </th>
  );
}

export function RunTable({ runs, bestRunName }: { runs: EvalRun[]; bestRunName?: string }) {
  return (
    <div>
      <p className="mb-3 text-sm text-stone-600">A dash means the metric was not measured for that run type.</p>
      <div className="overflow-x-auto rounded-md border border-stone-300 bg-white shadow-card">
        <table className="data-table min-w-[1320px]">
          <thead>
            <tr>
              <th>Run</th>
              <th>Run ID</th>
              <th>Phase</th>
              <th>Timestamp</th>
              <th className="text-right">Sample</th>
              <th className="text-right">Passed</th>
              <th className="text-right">Failed</th>
              <th>Mode</th>
              <th>Chunking</th>
              <MetricTh
                label="Precision@k"
                tip="Chunk-level: what fraction of the 5 retrieved chunks belong to an expected source document. Questions with multiple expected documents naturally score higher."
              />
              <MetricTh
                label="MRR"
                tip="Mean Reciprocal Rank: 1 / rank of the first retrieved chunk from an expected document. Close to 1.0 means the relevant chunk is almost always ranked #1."
              />
              <MetricTh
                label="Answer"
                tip="Term-overlap accuracy: the generated answer contains at least 65% of the key terms from the expected answer. Deterministic signal, not an LLM judge."
              />
              <MetricTh
                label="Citation"
                tip="Fraction of expected source documents that appear in generated citations."
              />
              <MetricTh
                label="Permission Leak"
                tip="Rate at which restricted documents appear in responses for unauthorized roles. 0.000 = pre-retrieval hard filter blocked all unauthorized requests and zero restricted chunks reached generation."
              />
              <MetricTh
                label="Memory"
                tip="Query-rewrite accuracy on conversation follow-up questions. The rewriter must detect the follow-up and expand it using prior context before retrieval."
              />
              <MetricTh
                label="Est. Cost"
                tip="Estimated chat-generation cost from configured model pricing (input + output tokens). Excludes embedding, ingestion, and infrastructure costs."
              />
            </tr>
          </thead>
          <tbody>
            {runs.map((run) => (
              <tr key={run.run_id}>
                <td className="font-medium text-ink">
                  <div className="flex flex-wrap items-center gap-2">
                    <Link
                      href={`/dev-admin/evaluation/runs/${encodeURIComponent(run.run_id)}`}
                      className="rounded underline decoration-stone-400 underline-offset-4 hover:text-moss-dark focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-moss"
                    >
                      <RunLabel run={run} showRaw={false} />
                    </Link>
                    {run.run_name === bestRunName ? <Badge tone="solid">Best config</Badge> : null}
                    {run.question_filter && run.question_filter !== "all" ? (
                      <Badge
                        tone="warn"
                        title={`Evaluated on ${run.total_questions ?? "?"}/${run.source_question_count ?? "?"} questions (${run.question_filter} filter). Metrics are not directly comparable to full-benchmark runs.`}
                      >
                        Subset
                      </Badge>
                    ) : null}
                  </div>
                </td>
                <td className="text-xs text-stone-600">{run.run_id}</td>
                <td><PhaseLabel phase={run.phase} /></td>
                <td>{formatDateTime(run.run_timestamp ?? run.timestamp)}</td>
                <td className="text-right">{run.sample_size ?? run.total_questions ?? "not measured"}</td>
                <td className="text-right">{run.passed_count ?? "not available"}</td>
                <td className="text-right">{run.failed_count ?? "not available"}</td>
                <td>{formatLabel(run.retrieval_mode)}</td>
                <td>{formatLabel(run.chunking_strategy)}</td>
                <td className="text-right">{formatTableMetric(run.metrics.precision_at_k)}</td>
                <td className="text-right">{formatTableMetric(run.metrics.mrr)}</td>
                <td className="text-right">{formatTableMetric(run.metrics.answer_accuracy)}</td>
                <td className="text-right">{formatTableMetric(run.metrics.citation_accuracy)}</td>
                <td className={`text-right ${riskRateClass(run.metrics.permission_leakage_rate)}`}>
                  {formatTableMetric(run.metrics.permission_leakage_rate)}
                </td>
                <td className="text-right">{formatTableMetric(run.metrics.memory_answer_accuracy)}</td>
                <td className="text-right">{formatCost(run.metrics.estimated_cost)}</td>
              </tr>
            ))}
          </tbody>
        </table>
      </div>
    </div>
  );
}
