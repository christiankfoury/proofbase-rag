"use client";

import { useMemo, useState } from "react";
import { CitationTable, RetrievedContext } from "@/components/QueryResultPanel";
import { EnrichedFailure } from "@/lib/api";
import { formatLabel, formatMetric } from "@/lib/dashboard";

const failureTone: Record<string, string> = {
  answer_not_generated: "border-rust bg-orange-50 text-rust",
  incomplete_answer: "border-steel bg-slate-50 text-steel",
  multi_document_failure: "border-rust bg-orange-50 text-rust",
  unsupported_answer: "border-rust bg-orange-50 text-rust",
  wrong_citation: "border-steel bg-slate-50 text-steel",
};

export function FailedQuestionsClient({ failures }: { failures: EnrichedFailure[] }) {
  const [expanded, setExpanded] = useState<string | null>("MULTI-005");
  const [failureType, setFailureType] = useState("all");

  const failureTypes = useMemo(() => Array.from(new Set(failures.map((item) => item.failure_type))).sort(), [failures]);
  const filtered = failureType === "all" ? failures : failures.filter((item) => item.failure_type === failureType);

  return (
    <section className="space-y-4">
      <div className="rounded-md border border-stone-300 bg-white p-4">
        <label className="text-sm font-semibold" htmlFor="failure-type">Failure type</label>
        <select id="failure-type" value={failureType} onChange={(event) => setFailureType(event.target.value)} className="ml-0 mt-2 block rounded border border-stone-300 px-3 py-2 md:ml-3 md:mt-0 md:inline-block">
          <option value="all">All failures</option>
          {failureTypes.map((item) => <option key={item}>{item}</option>)}
        </select>
      </div>

      {filtered.map((item) => {
        const isOpen = expanded === item.question_id;
        return (
          <article key={`${item.phase}-${item.question_id}`} className={`rounded-md border bg-white ${item.known_open_issue ? "border-rust" : "border-stone-300"}`}>
            <button type="button" onClick={() => setExpanded(isOpen ? null : item.question_id)} className="w-full p-5 text-left">
              <div className="flex flex-wrap items-start justify-between gap-3">
                <div>
                  <div className="flex flex-wrap items-center gap-2">
                    <h3 className="text-lg font-semibold">{item.question_id}</h3>
                    <span className={`rounded border px-2 py-1 text-xs font-semibold ${failureTone[item.failure_type] ?? "border-stone-300 bg-stone-50 text-stone-700"}`}>
                      {formatLabel(item.failure_type)}
                    </span>
                    {item.known_open_issue ? <span className="rounded bg-rust px-2 py-1 text-xs font-semibold text-white">Known open issue</span> : null}
                  </div>
                  <p className="mt-2 max-w-4xl text-sm text-stone-700">{item.question ?? "Question text unavailable."}</p>
                </div>
                <div className="text-right text-sm text-stone-600">
                  <p>{item.phase}</p>
                  <p>{formatLabel(item.actual_response_type)}</p>
                </div>
              </div>
            </button>

            {isOpen ? (
              <div className="border-t border-stone-200 p-5">
                {item.known_open_issue_note ? (
                  <p className="mb-4 rounded border border-rust bg-orange-50 p-3 text-sm text-rust">{item.known_open_issue_note}</p>
                ) : null}
                <div className="grid gap-4 lg:grid-cols-2">
                  <section>
                    <h4 className="font-semibold">Expected Answer</h4>
                    <p className="mt-2 text-sm leading-6 text-stone-700">{item.expected_answer ?? "n/a"}</p>
                  </section>
                  <section>
                    <h4 className="font-semibold">Actual Answer</h4>
                    <p className="mt-2 text-sm leading-6 text-stone-700">{item.actual_answer ?? "Detailed actual answer unavailable for this failure export."}</p>
                  </section>
                </div>
                <div className="mt-4 grid gap-4 lg:grid-cols-2">
                  <section className="rounded border border-stone-300 p-4">
                    <h4 className="font-semibold">Expected Sources</h4>
                    <p className="mt-2 text-sm text-stone-700">{(item.expected_source_document ?? []).join(", ") || "n/a"}</p>
                    <h4 className="mt-4 font-semibold">Actual Citation Documents</h4>
                    <p className="mt-2 text-sm text-stone-700">{(item.actual_citation_documents ?? []).join(", ") || "n/a"}</p>
                  </section>
                  <section className="rounded border border-stone-300 p-4">
                    <h4 className="font-semibold">Scoring</h4>
                    <div className="mt-2 grid grid-cols-2 gap-2 text-sm text-stone-700">
                      <p>Citation confidence: {formatMetric(item.citation_confidence)}</p>
                      <p>Answer confidence: {formatMetric(item.answer_confidence)}</p>
                      <p>Final confidence: {formatMetric(item.confidence)}</p>
                      <p>Expected behavior: {formatLabel(item.expected_behavior)}</p>
                    </div>
                  </section>
                </div>
                <section className="mt-4">
                  <h4 className="mb-2 font-semibold">Actual Citations</h4>
                  <CitationTable citations={item.actual_citations ?? []} />
                </section>
                <section className="mt-4">
                  <h4 className="mb-2 font-semibold">Retrieved Documents</h4>
                  <p className="rounded border border-stone-300 p-3 text-sm text-stone-700">{(item.retrieved_documents ?? []).join(", ") || "Detailed retrieved documents unavailable."}</p>
                </section>
                {item.retrieved_chunks?.length ? (
                  <section className="mt-4">
                    <h4 className="mb-2 font-semibold">Retrieved Chunks</h4>
                    <RetrievedContext chunks={item.retrieved_chunks} />
                  </section>
                ) : null}
                <p className="mt-4 rounded border border-stone-300 bg-stone-50 p-3 text-sm">
                  <span className="font-semibold">Recommended fix: </span>{item.recommended_fix ?? "n/a"}
                </p>
              </div>
            ) : null}
          </article>
        );
      })}
    </section>
  );
}
