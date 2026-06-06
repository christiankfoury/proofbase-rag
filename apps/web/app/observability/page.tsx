import { Shell } from "@/components/Shell";
import { MetricCard } from "@/components/MetricCard";
import { ObservabilityRefresh } from "@/components/ObservabilityRefresh";
import { getObservabilitySummary } from "@/lib/feedback";

export default async function ObservabilityPage() {
  const data = await getObservabilitySummary();
  const recent = data.recent_requests ?? [];

  if (data.status === "not_generated" || data.status === "unavailable") {
    return (
      <Shell>
        <h2 className="text-3xl font-semibold">Observability</h2>
        <section className="mt-8 rounded-md border border-stone-300 bg-white p-5">
          <p className="text-stone-700">
            {data.status === "not_generated" ? (
              <>
                Run{" "}
                <code className="rounded bg-stone-100 px-1 py-0.5 text-sm">python scripts/generate_observability_summary.py</code>
                {" "}to generate the summary, then refresh.
              </>
            ) : (
              "API is unavailable. Make sure the server is running."
            )}
          </p>
        </section>
      </Shell>
    );
  }

  const fmt = (v: number | null | undefined, suffix = "") =>
    v != null ? `${v}${suffix}` : "pending";
  const fmtUsd = (v: number | null | undefined) =>
    v != null ? `$${v.toFixed(6)}` : "pending";

  return (
    <Shell>
      <h2 className="text-3xl font-semibold">Observability</h2>
      <div className="mt-3 flex flex-wrap items-start justify-between gap-3">
        <p className="max-w-2xl text-stone-700">
          Live latency, token usage, and confidence from RAG request logs. Auto-refreshes every 15 seconds.
        </p>
        <ObservabilityRefresh />
      </div>

      <section className="mt-6 grid gap-4 sm:grid-cols-2 xl:grid-cols-4">
        <MetricCard label="Avg Total Latency" value={fmt(data.avg_total_latency_ms, " ms")} />
        <MetricCard label="Avg Retrieval Latency" value={fmt(data.avg_retrieval_latency_ms, " ms")} />
        <MetricCard label="Avg Generation Latency" value={fmt(data.avg_generation_latency_ms, " ms")} />
        <MetricCard label="Avg Confidence" value={data.avg_final_confidence} />
        <MetricCard label="Avg Input Tokens" value={fmt(data.avg_input_tokens != null ? Math.round(data.avg_input_tokens) : null)} />
        <MetricCard label="Avg Output Tokens" value={fmt(data.avg_output_tokens != null ? Math.round(data.avg_output_tokens) : null)} />
        <MetricCard label="Total Requests" value={fmt(data.total_requests)} />
        <MetricCard label="Total Estimated Cost" value={fmtUsd(data.total_estimated_cost_usd ?? data.estimated_cost)} detail="Chat token cost only." />
        <MetricCard label="Avg Cost / Request" value={fmtUsd(data.avg_estimated_cost_usd)} detail="Configured model pricing." />
      </section>

      {recent.length > 0 && (
        <section className="mt-8">
          <h3 className="mb-3 text-xl font-semibold">Recent Requests</h3>
          <div className="overflow-x-auto rounded-md border border-stone-300 bg-white">
            <table className="w-full min-w-[960px] text-left text-sm">
              <thead className="bg-stone-100">
                <tr>
                  <th className="px-4 py-3">Time</th>
                  <th className="px-4 py-3">Role</th>
                  <th className="px-4 py-3">Question</th>
                  <th className="px-4 py-3">Response Type</th>
                  <th className="px-4 py-3 text-right">Confidence</th>
                  <th className="px-4 py-3 text-right">Total ms</th>
                  <th className="px-4 py-3 text-right">Ret ms</th>
                  <th className="px-4 py-3 text-right">Gen ms</th>
                  <th className="px-4 py-3">Prompt</th>
                  <th className="px-4 py-3 text-right">In Tok</th>
                  <th className="px-4 py-3 text-right">Out Tok</th>
                  <th className="px-4 py-3 text-right">Cost</th>
                  <th className="px-4 py-3">Pricing</th>
                  <th className="px-4 py-3">Error</th>
                </tr>
              </thead>
              <tbody>
                {[...recent].reverse().map((entry) => (
                  <tr key={entry.request_id} className="border-t border-stone-200">
                    <td className="whitespace-nowrap px-4 py-3 text-stone-500">
                      {new Date(entry.timestamp).toLocaleTimeString()}
                    </td>
                    <td className="whitespace-nowrap px-4 py-3">{entry.user_role}</td>
                    <td className="max-w-xs px-4 py-3 text-stone-700">
                      {entry.question.slice(0, 60)}{entry.question.length > 60 ? "…" : ""}
                    </td>
                    <td className="whitespace-nowrap px-4 py-3">{entry.response_type ?? "-"}</td>
                    <td className="px-4 py-3 text-right">{entry.final_confidence?.toFixed(3) ?? "-"}</td>
                    <td className="px-4 py-3 text-right">{entry.total_latency_ms ?? "-"}</td>
                    <td className="px-4 py-3 text-right">{entry.retrieval_latency_ms ?? "-"}</td>
                    <td className="px-4 py-3 text-right">{entry.generation_latency_ms ?? "-"}</td>
                    <td className="whitespace-nowrap px-4 py-3">{entry.prompt_version ?? "-"}</td>
                    <td className="px-4 py-3 text-right">{entry.input_tokens ?? "-"}</td>
                    <td className="px-4 py-3 text-right">{entry.output_tokens ?? "-"}</td>
                    <td className="px-4 py-3 text-right">{fmtUsd(entry.estimated_cost_usd)}</td>
                    <td className="whitespace-nowrap px-4 py-3">{entry.pricing_status ?? "-"}</td>
                    <td className="px-4 py-3 text-rust">{entry.error ?? ""}</td>
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
