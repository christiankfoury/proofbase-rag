import { Citation, QueryResponse, RetrievedChunk } from "@/lib/api";
import { formatLabel, formatMetric } from "@/lib/dashboard";

function MetricCard({ label, value }: { label: string; value: string | number | null | undefined }) {
  return (
    <div className="rounded-md border border-stone-300 bg-white p-4">
      <p className="text-xs font-semibold uppercase tracking-wide text-stone-500">{label}</p>
      <p className="mt-2 text-xl font-semibold">{formatMetric(value)}</p>
    </div>
  );
}

function formatLatency(value: number | null | undefined): string {
  if (value === null || value === undefined) return "pending";
  if (value >= 1000) return `${(value / 1000).toFixed(1)}s`;
  return `${Math.round(value)} ms`;
}

export function CitationTable({ citations }: { citations: Citation[] }) {
  if (!citations.length) {
    return <p className="text-sm text-stone-600">No citations returned.</p>;
  }
  return (
    <div className="overflow-x-auto rounded-md border border-stone-300">
      <table className="w-full min-w-[820px] text-left text-sm">
        <thead className="bg-stone-100 text-stone-700">
          <tr>
            <th className="p-3">Document</th>
            <th className="p-3">Section</th>
            <th className="p-3">Chunk</th>
            <th className="p-3 text-right">Confidence</th>
          </tr>
        </thead>
        <tbody>
          {citations.map((citation, index) => (
            <tr key={`${citation.chunk_id ?? citation.document_id}-${index}`} className="border-t border-stone-200">
              <td className="p-3">
                <p className="font-medium">{citation.document_title ?? "Untitled"}</p>
                <p className="text-xs text-stone-500">{citation.document_id ?? "n/a"}</p>
              </td>
              <td className="p-3">{citation.section_heading ?? "n/a"}</td>
              <td className="p-3 font-mono text-xs">{citation.chunk_id ?? "n/a"}</td>
              <td className="p-3 text-right">{formatMetric(citation.confidence)}</td>
            </tr>
          ))}
        </tbody>
      </table>
    </div>
  );
}

export function RetrievedContext({ chunks }: { chunks: RetrievedChunk[] }) {
  if (!chunks.length) {
    return <p className="text-sm text-stone-600">No retrieved chunks returned.</p>;
  }
  return (
    <div className="space-y-3">
      {chunks.map((chunk, index) => (
        <article key={`${chunk.chunk_id}-${index}`} className="rounded-md border border-stone-300 bg-white p-4">
          <div className="flex flex-wrap items-start justify-between gap-3">
            <div>
              <p className="text-sm font-semibold">
                #{chunk.rank ?? index + 1} {chunk.document_title}
              </p>
              <p className="text-xs text-stone-500">
                {chunk.document_id} / {chunk.section_heading} / {chunk.chunk_id}
              </p>
            </div>
            <div className="text-right text-xs text-stone-600">
              <p>Score: {formatMetric(chunk.score)}</p>
              <p>Source: {chunk.retrieval_source ?? "retrieval"}</p>
            </div>
          </div>
          <div className="mt-3 grid gap-2 text-xs text-stone-600 md:grid-cols-4">
            <span>Vector: {formatMetric(chunk.vector_score)}</span>
            <span>Keyword: {formatMetric(chunk.keyword_score)}</span>
            <span>Hybrid: {formatMetric(chunk.hybrid_score)}</span>
            <span>Sensitivity: {chunk.sensitivity ?? "n/a"}</span>
          </div>
          <p className="mt-2 text-xs text-stone-600">Roles: {(chunk.access_roles ?? []).join(", ") || "n/a"}</p>
          <p className="mt-3 text-sm leading-6 text-stone-800">{chunk.content_preview ?? "No preview available."}</p>
        </article>
      ))}
    </div>
  );
}

export function QueryResultPanel({ result }: { result: QueryResponse }) {
  return (
    <div className="space-y-5">
      <section className="rounded-md border border-stone-300 bg-white p-5">
        <div className="flex flex-wrap items-start justify-between gap-3">
          <div>
            <p className="text-sm font-semibold uppercase tracking-wide text-steel">{formatLabel(result.response_type)}</p>
            <h3 className="mt-2 text-xl font-semibold">Generated Response</h3>
          </div>
          <div className="rounded border border-stone-300 px-3 py-2 text-sm">
            {result.multi_doc_used ? "Multi-doc used" : "Single-query retrieval"}
          </div>
        </div>
        <p className="mt-4 whitespace-pre-wrap leading-7 text-stone-800">{result.answer}</p>
      </section>

      <section className="grid gap-3 md:grid-cols-4">
        <MetricCard label="Final confidence" value={result.final_confidence} />
        <MetricCard label="Retrieval confidence" value={result.retrieval_confidence} />
        <MetricCard label="Citation confidence" value={result.citation_confidence} />
        <MetricCard label="Answer confidence" value={result.answer_confidence} />
      </section>

      <section className="grid gap-3 md:grid-cols-3">
        <MetricCard label="Retrieval latency" value={formatLatency(result.retrieval_latency_ms)} />
        <MetricCard label="Generation latency" value={formatLatency(result.generation_latency_ms)} />
        <MetricCard label="Total latency" value={formatLatency(result.total_latency_ms)} />
      </section>

      <section className="rounded-md border border-stone-300 bg-white p-5">
        <h3 className="text-lg font-semibold">Permission Check</h3>
        <div className="mt-3 grid gap-3 text-sm md:grid-cols-3">
          <p>Role: {result.permission_check.user_role}</p>
          <p>Returned chunks: {result.permission_check.retrieved_chunks_count}</p>
          <p>
            <span className={`inline-flex rounded border px-2 py-1 text-xs font-semibold ${
              result.permission_check.unauthorized_chunks_reached_generation
                ? "border-rust bg-orange-50 text-rust"
                : "border-moss bg-green-50 text-moss"
            }`}>
              {result.permission_check.unauthorized_chunks_reached_generation ? "Leakage detected" : "No leakage"}
            </span>
          </p>
        </div>
      </section>

      <section className="rounded-md border border-stone-300 bg-white p-5">
        <h3 className="text-lg font-semibold">Citations</h3>
        <div className="mt-3">
          <CitationTable citations={result.citations} />
        </div>
      </section>

      <section className="grid gap-4 lg:grid-cols-2">
        <div className="rounded-md border border-stone-300 bg-white p-5">
          <h3 className="text-lg font-semibold">Supported Claims</h3>
          <ul className="mt-3 list-disc space-y-2 pl-5 text-sm text-stone-700">
            {result.supported_claims.length ? result.supported_claims.map((claim) => <li key={claim}>{claim}</li>) : <li>No supported claims returned.</li>}
          </ul>
        </div>
        <div className="rounded-md border border-stone-300 bg-white p-5">
          <h3 className="text-lg font-semibold">Unsupported Claims</h3>
          <ul className="mt-3 list-disc space-y-2 pl-5 text-sm text-stone-700">
            {result.unsupported_claims.length ? result.unsupported_claims.map((claim) => <li key={claim}>{claim}</li>) : <li>No unsupported claims returned.</li>}
          </ul>
        </div>
      </section>

      <section className="rounded-md border border-stone-300 bg-white p-5">
        <h3 className="text-lg font-semibold">Validation Notes</h3>
        <p className="mt-2 text-sm text-stone-700">{result.validation_notes || "No validation notes returned."}</p>
      </section>

      <details className="rounded-md border border-stone-300 bg-white p-5">
        <summary className="cursor-pointer text-lg font-semibold">Retrieved Context</summary>
        <div className="mt-4">
          <RetrievedContext chunks={result.retrieved_chunks} />
        </div>
      </details>
    </div>
  );
}
