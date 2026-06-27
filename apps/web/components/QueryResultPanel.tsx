import { Badge } from "@/components/Badge";
import { Card } from "@/components/Card";
import { Citation, QueryResponse, RetrievedChunk } from "@/lib/api";
import { formatLabel, formatMetric, goodRateClass } from "@/lib/dashboard";

function CompactMetric({ label, value }: { label: string; value: string | number | null | undefined }) {
  return (
    <Card padding="compact">
      <p className="text-2xs font-semibold uppercase tracking-wide text-stone-500">{label}</p>
      <p className="mt-2 text-xl font-semibold text-ink">{formatMetric(value)}</p>
    </Card>
  );
}

function confidenceLabel(result: QueryResponse): string {
  return result.confidence_interpretation === "response_behavior" ? "Behavior confidence" : "Final support confidence";
}

function formatLatency(value: number | null | undefined): string {
  if (value === null || value === undefined) return "pending";
  if (value >= 1000) return `${(value / 1000).toFixed(1)}s`;
  return `${Math.round(value)} ms`;
}

function formatUsd(value: number | null | undefined): string {
  if (value === null || value === undefined) return "pending";
  return `$${value.toFixed(6)}`;
}

function shortId(value: string | null | undefined, fallback = "global"): string {
  return value ? value.slice(0, 8) : fallback;
}

export function CitationTable({ citations }: { citations: Citation[] }) {
  if (!citations.length) {
    return <p className="text-sm text-stone-600">No citations returned.</p>;
  }
  return (
    <div className="overflow-x-auto rounded-md border border-stone-300">
      <table className="data-table min-w-[820px]">
        <thead>
          <tr>
            <th>Document</th>
            <th>Section</th>
            <th>Chunk</th>
            <th className="text-right">Confidence</th>
          </tr>
        </thead>
        <tbody>
          {citations.map((citation, index) => (
            <tr key={`${citation.chunk_id ?? citation.document_id}-${index}`}>
              <td>
                <p className="font-medium text-ink">{citation.document_title ?? "Untitled"}</p>
                <p className="text-xs text-stone-500">{citation.document_id ?? "n/a"}</p>
              </td>
              <td>{citation.section_heading ?? "n/a"}</td>
              <td className="font-mono text-xs">{citation.chunk_id ?? "n/a"}</td>
              <td className={`text-right font-medium ${goodRateClass(citation.confidence)}`}>{formatMetric(citation.confidence)}</td>
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
              <p className="text-sm font-semibold text-ink">
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
          <p className="mt-2 text-xs text-stone-600">
            Scope: project {shortId(chunk.project_id)} / department {shortId(chunk.department_id, "all")}
          </p>
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
      <Card tone={result.permission_check.unauthorized_chunks_reached_generation ? "risk" : "neutral"}>
        <div className="flex flex-wrap items-start justify-between gap-3">
          <div>
            <p className="text-sm font-semibold uppercase tracking-wide text-steel">{formatLabel(result.response_type)}</p>
            <h3 className="mt-2 text-xl font-semibold text-ink">Generated Response</h3>
          </div>
          <Badge tone="neutral">{result.multi_doc_used ? "Multi-doc used" : "Single-query retrieval"}</Badge>
        </div>
        <p className="mt-4 whitespace-pre-wrap leading-7 text-stone-800">{result.answer}</p>
      </Card>

      <section className="grid gap-3 md:grid-cols-4">
        <CompactMetric label={confidenceLabel(result)} value={result.final_confidence} />
        <CompactMetric label="Retrieval confidence" value={result.retrieval_confidence} />
        <CompactMetric label="Citation confidence" value={result.citation_confidence} />
        <CompactMetric label="Answer confidence" value={result.answer_confidence} />
      </section>

      <section className="grid gap-3 md:grid-cols-4">
        <CompactMetric label="Retrieval latency" value={formatLatency(result.retrieval_latency_ms)} />
        <CompactMetric label="Generation latency" value={formatLatency(result.generation_latency_ms)} />
        <CompactMetric label="Total latency" value={formatLatency(result.total_latency_ms)} />
        <CompactMetric label="Estimated cost" value={formatUsd(result.estimated_cost_usd)} />
      </section>

      <Card>
        <h3 className="text-lg font-semibold text-ink">Permission Check</h3>
        <div className="mt-3 grid items-center gap-3 text-sm text-stone-700 md:grid-cols-4">
          <p>Role: {result.permission_check.user_role}</p>
          <p>Returned chunks: {result.permission_check.retrieved_chunks_count}</p>
          <p>Scope: {result.scope?.project_id ? `project ${shortId(result.scope.project_id)}` : "global"}</p>
          <Badge tone={result.permission_check.unauthorized_chunks_reached_generation ? "warn" : "good"}>
            {result.permission_check.unauthorized_chunks_reached_generation ? "Leakage detected" : "No leakage"}
          </Badge>
        </div>
        {result.scope?.department_id ? (
          <p className="mt-2 text-sm text-stone-600">Department narrowed to {shortId(result.scope.department_id)} before role filtering.</p>
        ) : null}
      </Card>

      <Card>
        <h3 className="text-lg font-semibold text-ink">Citations</h3>
        <div className="mt-3">
          <CitationTable citations={result.citations} />
        </div>
      </Card>

      <section className="grid gap-4 lg:grid-cols-2">
        <Card>
          <h3 className="text-lg font-semibold text-ink">Supported Claims</h3>
          <ul className="mt-3 list-disc space-y-2 pl-5 text-sm text-stone-700">
            {result.supported_claims.length ? result.supported_claims.map((claim) => <li key={claim}>{claim}</li>) : <li>No supported claims returned.</li>}
          </ul>
        </Card>
        <Card tone={result.unsupported_claims.length ? "warn" : "neutral"}>
          <h3 className="text-lg font-semibold text-ink">Unsupported Claims</h3>
          <ul className="mt-3 list-disc space-y-2 pl-5 text-sm text-stone-700">
            {result.unsupported_claims.length ? result.unsupported_claims.map((claim) => <li key={claim}>{claim}</li>) : <li>No unsupported claims returned.</li>}
          </ul>
        </Card>
      </section>

      <Card>
        <h3 className="text-lg font-semibold text-ink">Validation Notes</h3>
        <p className="mt-2 text-sm text-stone-700">{result.validation_notes || "No validation notes returned."}</p>
      </Card>

      <details className="card group">
        <summary className="cursor-pointer text-lg font-semibold text-ink focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-moss">
          Retrieved Context
        </summary>
        <div className="mt-4">
          <RetrievedContext chunks={result.retrieved_chunks} />
        </div>
      </details>
    </div>
  );
}
