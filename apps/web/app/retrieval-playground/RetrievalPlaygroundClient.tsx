"use client";

import { useState } from "react";
import { RetrievedContext } from "@/components/QueryResultPanel";
import { Citation, QueryResponse, UserRole, queryRag } from "@/lib/api";
import { formatLabel, formatMetric } from "@/lib/dashboard";

const modes = [
  { label: "Vector only", retrieval_mode: "vector_only" as const, multi_doc_mode: "off" as const },
  { label: "Keyword only", retrieval_mode: "keyword_only" as const, multi_doc_mode: "off" as const },
  { label: "Hybrid", retrieval_mode: "hybrid" as const, multi_doc_mode: "off" as const },
  { label: "Multi-doc", retrieval_mode: "vector_only" as const, multi_doc_mode: "force" as const },
];

type ModeResult = {
  label: string;
  result?: QueryResponse;
  error?: string;
};

function formatLatency(value: number | null | undefined): string {
  if (value === null || value === undefined) return "pending";
  if (value >= 1000) return `${(value / 1000).toFixed(1)}s`;
  return `${Math.round(value)} ms`;
}

function outcomeFor(label: string, result?: QueryResponse): { text: string; tone: string } {
  if (!result) return { text: "Not run", tone: "border-stone-300 bg-stone-50 text-stone-700" };
  if (label === "Multi-doc" && result.citations.length > 1 && result.response_type !== "not_found") {
    return { text: "Best for this query", tone: "border-moss bg-green-50 text-moss" };
  }
  if (label === "Keyword only" && result.citations.length > 0) {
    return { text: "Exact terms helped", tone: "border-steel bg-slate-50 text-steel" };
  }
  if (result.response_type === "not_found") {
    return { text: "Missed supporting evidence", tone: "border-rust bg-orange-50 text-rust" };
  }
  if (result.response_type === "partial_answer") {
    return { text: "Partial support", tone: "border-rust bg-orange-50 text-rust" };
  }
  return { text: "Answered", tone: "border-moss bg-green-50 text-moss" };
}

function CompactCitations({ citations }: { citations: Citation[] }) {
  if (!citations.length) return <p className="text-sm text-stone-600">No citations returned.</p>;
  return (
    <div className="space-y-2">
      {citations.slice(0, 5).map((citation, index) => (
        <div key={`${citation.chunk_id ?? citation.document_id}-${index}`} className="rounded border border-stone-200 p-3 text-sm">
          <div className="flex flex-wrap items-start justify-between gap-2">
            <div>
              <p className="font-semibold">{citation.document_title ?? "Untitled"}</p>
              <p className="text-xs text-stone-500">{citation.document_id ?? "n/a"} / {citation.section_heading ?? "n/a"}</p>
            </div>
            <p className="text-xs text-stone-600">{formatMetric(citation.confidence)}</p>
          </div>
          <p className="mt-2 break-all font-mono text-xs text-stone-500">{citation.chunk_id ?? "no chunk id"}</p>
        </div>
      ))}
      {citations.length > 5 ? <p className="text-xs text-stone-500">Showing 5 of {citations.length} citations.</p> : null}
    </div>
  );
}

export function RetrievalPlaygroundClient() {
  const [question, setQuestion] = useState("If I work remotely, what approval and device security expectations apply?");
  const [role, setRole] = useState<UserRole>("Employee");
  const [results, setResults] = useState<ModeResult[]>(modes.map((mode) => ({ label: mode.label })));
  const [loading, setLoading] = useState(false);

  async function runComparison() {
    setLoading(true);
    const nextResults: ModeResult[] = [];
    for (const mode of modes) {
      try {
        const result = await queryRag({
          question,
          user_role: role,
          retrieval_mode: mode.retrieval_mode,
          chunking_strategy: "section_based",
          multi_doc_mode: mode.multi_doc_mode,
        });
        nextResults.push({ label: mode.label, result });
      } catch (exc) {
        nextResults.push({ label: mode.label, error: exc instanceof Error ? exc.message : "Query failed." });
      }
    }
    setResults(nextResults);
    setLoading(false);
  }

  return (
    <section className="space-y-5">
      <div className="rounded-md border border-stone-300 bg-white p-5">
        <div className="grid gap-3 lg:grid-cols-[1fr_180px_auto]">
          <input value={question} onChange={(event) => setQuestion(event.target.value)} className="rounded border border-stone-300 px-3 py-2" />
          <select value={role} onChange={(event) => setRole(event.target.value as UserRole)} className="rounded border border-stone-300 px-3 py-2">
            <option>Employee</option>
            <option>Sales Representative</option>
            <option>Manager</option>
            <option>HR Admin</option>
          </select>
          <button type="button" onClick={runComparison} disabled={loading} className="rounded bg-ink px-4 py-2 font-semibold text-white disabled:opacity-60">
            {loading ? "Running..." : "Compare modes"}
          </button>
        </div>
        <p className="mt-3 text-sm text-stone-700">
          This comparison shows why evaluation matters: vector retrieval is best overall, but keyword and multi-document retrieval can recover different evidence depending on the question.
        </p>
      </div>

      <div className="grid gap-5 xl:grid-cols-2">
        {results.map(({ label, result, error }) => {
          const outcome = outcomeFor(label, result);
          const emphasize = outcome.text === "Best for this query";
          return (
          <article key={label} className={`rounded-md border bg-white p-5 ${emphasize ? "border-moss" : "border-stone-300"}`}>
            <div className="flex flex-wrap items-start justify-between gap-3">
              <div>
                <div className="flex flex-wrap items-center gap-2">
                  <h3 className="text-xl font-semibold">{label}</h3>
                  <span className={`rounded border px-2 py-1 text-xs font-semibold ${outcome.tone}`}>{outcome.text}</span>
                </div>
                <p className="mt-1 text-sm text-stone-600">{result ? formatLabel(result.response_type) : "Not run"}</p>
              </div>
              {result ? (
                <div className="text-right text-xs text-stone-600">
                  <p>Confidence: {formatMetric(result.final_confidence)}</p>
                  <p>Latency: {formatLatency(result.total_latency_ms)}</p>
                </div>
              ) : null}
            </div>
            {error ? <p className="mt-4 rounded border border-rust bg-orange-50 p-3 text-sm text-rust">{error}</p> : null}
            {result ? (
              <div className="mt-4 space-y-4">
                <p className="line-clamp-6 text-sm leading-6 text-stone-800">{result.answer}</p>
                <div>
                  <h4 className="mb-2 font-semibold">Citations</h4>
                  <CompactCitations citations={result.citations} />
                </div>
                <details className="rounded border border-stone-300 p-4">
                  <summary className="cursor-pointer font-semibold">Top Retrieved Chunks</summary>
                  <div className="mt-3">
                    <RetrievedContext chunks={result.retrieved_chunks.slice(0, 4)} />
                  </div>
                </details>
              </div>
            ) : (
              <p className="mt-4 text-sm text-stone-600">Run the comparison to populate this mode.</p>
            )}
          </article>
        )})}
      </div>
    </section>
  );
}
