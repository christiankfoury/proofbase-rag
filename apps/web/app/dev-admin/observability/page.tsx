import { EmptyState } from "@/components/EmptyState";
import { MetricCard } from "@/components/MetricCard";
import { ObservabilityRefresh } from "@/components/ObservabilityRefresh";
import { PageHeader } from "@/components/PageHeader";
import { SectionHeading } from "@/components/SectionHeading";
import { Shell } from "@/components/Shell";
import { goodRateClass } from "@/lib/dashboard";
import { getObservabilitySummary } from "@/lib/feedback";
import { serverDemoAuthHeaders } from "@/lib/serverDemoAuth";

export default async function ObservabilityPage() {
  const authHeaders = await serverDemoAuthHeaders();
  const data = await getObservabilitySummary(authHeaders);
  const recent = data.recent_requests ?? [];

  if (data.status === "not_generated" || data.status === "unavailable") {
    return (
      <Shell>
        <PageHeader title="Observability" />
        <EmptyState>
          {data.status === "not_generated" ? (
            <>
              Run{" "}
              <code className="rounded bg-stone-100 px-1 py-0.5 text-sm">python scripts/generate_observability_summary.py</code>
              {" "}to generate the summary, then refresh.
            </>
          ) : (
            "API is unavailable. Make sure the server is running."
          )}
        </EmptyState>
      </Shell>
    );
  }

  const fmt = (v: number | null | undefined, suffix = "") =>
    v != null ? `${v}${suffix}` : "pending";
  const fmtUsd = (v: number | null | undefined) =>
    v != null ? `$${v.toFixed(6)}` : "pending";

  return (
    <Shell>
      <PageHeader
        title="Observability"
        description="Live latency, token usage, confidence, and privacy-safe prompt fingerprints from RAG request logs. Auto-refreshes every 15 seconds."
        actions={<ObservabilityRefresh />}
      />

      <section className="grid gap-4 sm:grid-cols-2 xl:grid-cols-4">
        <MetricCard label="Avg Total Latency" value={fmt(data.avg_total_latency_ms, " ms")} />
        <MetricCard label="Avg Retrieval Latency" value={fmt(data.avg_retrieval_latency_ms, " ms")} />
        <MetricCard label="Avg Generation Latency" value={fmt(data.avg_generation_latency_ms, " ms")} />
        <MetricCard label="Avg Confidence" value={data.avg_final_confidence} tone={typeof data.avg_final_confidence === "number" && data.avg_final_confidence < 0.6 ? "warn" : "neutral"} />
        <MetricCard label="Avg Input Tokens" value={fmt(data.avg_input_tokens != null ? Math.round(data.avg_input_tokens) : null)} />
        <MetricCard label="Avg Output Tokens" value={fmt(data.avg_output_tokens != null ? Math.round(data.avg_output_tokens) : null)} />
        <MetricCard label="Total Requests" value={fmt(data.total_requests)} />
        <MetricCard label="Total Estimated Cost" value={fmtUsd(data.total_estimated_cost_usd ?? data.estimated_cost)} detail="Chat token cost only." />
        <MetricCard label="Avg Cost / Request" value={fmtUsd(data.avg_estimated_cost_usd)} detail="Configured model pricing." />
      </section>

      {recent.length > 0 && (
        <section className="mt-8">
          <SectionHeading title="Recent Requests" />
          <div className="overflow-x-auto rounded-md border border-stone-300 bg-white shadow-card">
            <table className="data-table min-w-[960px]">
              <thead>
                <tr>
                  <th>Time</th>
                  <th>Role</th>
                  <th>Question fingerprint</th>
                  <th>Response Type</th>
                  <th className="text-right">Confidence</th>
                  <th className="text-right">Total ms</th>
                  <th className="text-right">Ret ms</th>
                  <th className="text-right">Gen ms</th>
                  <th>Prompt</th>
                  <th className="text-right">In Tok</th>
                  <th className="text-right">Out Tok</th>
                  <th className="text-right">Cost</th>
                  <th>Pricing</th>
                  <th>Error</th>
                </tr>
              </thead>
              <tbody>
                {[...recent].reverse().map((entry) => (
                  <tr key={entry.request_id}>
                    <td className="whitespace-nowrap text-stone-500">
                      {new Date(entry.timestamp).toLocaleTimeString()}
                    </td>
                    <td className="whitespace-nowrap">{entry.user_role}</td>
                    <td className="max-w-xs text-stone-700">
                      <code className="text-xs">{entry.question_hash?.slice(0, 16) ?? "not recorded"}</code>
                    </td>
                    <td className="whitespace-nowrap">{entry.response_type ?? "-"}</td>
                    <td className={`text-right ${goodRateClass(entry.final_confidence)}`}>{entry.final_confidence?.toFixed(3) ?? "-"}</td>
                    <td className="text-right">{entry.total_latency_ms ?? "-"}</td>
                    <td className="text-right">{entry.retrieval_latency_ms ?? "-"}</td>
                    <td className="text-right">{entry.generation_latency_ms ?? "-"}</td>
                    <td className="whitespace-nowrap">{entry.prompt_version ?? "-"}</td>
                    <td className="text-right">{entry.input_tokens ?? "-"}</td>
                    <td className="text-right">{entry.output_tokens ?? "-"}</td>
                    <td className="text-right">{fmtUsd(entry.estimated_cost_usd)}</td>
                    <td className="whitespace-nowrap">{entry.pricing_status ?? "-"}</td>
                    <td className="font-medium text-rust-dark">{entry.error ?? ""}</td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
        </section>
      )}
    </Shell>
  );
}
