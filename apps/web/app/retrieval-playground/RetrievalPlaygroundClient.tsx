"use client";

import { useState } from "react";
import { CitationTable, RetrievedContext } from "@/components/QueryResultPanel";
import { QueryResponse, UserRole, queryRag } from "@/lib/api";
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
      </div>

      <div className="grid gap-5 xl:grid-cols-2">
        {results.map(({ label, result, error }) => (
          <article key={label} className="rounded-md border border-stone-300 bg-white p-5">
            <div className="flex flex-wrap items-start justify-between gap-3">
              <div>
                <h3 className="text-xl font-semibold">{label}</h3>
                <p className="mt-1 text-sm text-stone-600">{result ? formatLabel(result.response_type) : "Not run"}</p>
              </div>
              {result ? (
                <div className="text-right text-xs text-stone-600">
                  <p>Confidence: {formatMetric(result.final_confidence)}</p>
                  <p>Latency: {formatMetric(result.total_latency_ms)} ms</p>
                </div>
              ) : null}
            </div>
            {error ? <p className="mt-4 rounded border border-rust bg-orange-50 p-3 text-sm text-rust">{error}</p> : null}
            {result ? (
              <div className="mt-4 space-y-4">
                <p className="line-clamp-6 text-sm leading-6 text-stone-800">{result.answer}</p>
                <div>
                  <h4 className="mb-2 font-semibold">Citations</h4>
                  <CitationTable citations={result.citations} />
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
        ))}
      </div>
    </section>
  );
}
