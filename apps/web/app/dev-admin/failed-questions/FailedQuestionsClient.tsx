"use client";

import { useMemo, useState } from "react";
import { Badge, BadgeTone } from "@/components/Badge";
import { Card } from "@/components/Card";
import { EvaluationReviewPanel } from "@/components/EvaluationReviewPanel";
import { PhaseLabel } from "@/components/PhaseLabel";
import { CitationTable, RetrievedContext } from "@/components/QueryResultPanel";
import { EnrichedFailure } from "@/lib/api";
import { formatLabel, formatMetric } from "@/lib/dashboard";

const failureTone: Record<string, BadgeTone> = {
  answer_not_generated: "warn",
  incomplete_answer: "info",
  multi_document_failure: "warn",
  unsupported_answer: "warn",
  wrong_citation: "info",
};

export function FailedQuestionsClient({ failures }: { failures: EnrichedFailure[] }) {
  const [expanded, setExpanded] = useState<string | null>("MULTI-005");
  const [failureType, setFailureType] = useState("all");

  const failureTypes = useMemo(() => Array.from(new Set(failures.map((item) => item.failure_type))).sort(), [failures]);
  const filtered = failureType === "all" ? failures : failures.filter((item) => item.failure_type === failureType);

  return (
    <section className="space-y-4">
      <Card padding="compact">
        <label className="text-sm font-semibold text-ink" htmlFor="failure-type">Failure type</label>
        <select id="failure-type" value={failureType} onChange={(event) => setFailureType(event.target.value)} className="field ml-0 mt-2 block md:ml-3 md:mt-0 md:inline-block">
          <option value="all">All failures</option>
          {failureTypes.map((item) => <option key={item}>{item}</option>)}
        </select>
      </Card>

      {filtered.map((item) => {
        const isOpen = expanded === item.question_id;
        return (
          <Card key={`${item.phase}-${item.question_id}`} as="article" tone={item.known_open_issue ? "warn" : "neutral"} padding="default" className="overflow-hidden !p-0">
            <button
              type="button"
              onClick={() => setExpanded(isOpen ? null : item.question_id)}
              className="w-full p-5 text-left focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-moss"
            >
              <div className="flex flex-wrap items-start justify-between gap-3">
                <div>
                  <div className="flex flex-wrap items-center gap-2">
                    <h3 className="text-lg font-semibold text-ink">{item.question_id}</h3>
                    <Badge tone={failureTone[item.failure_type] ?? "neutral"}>{formatLabel(item.failure_type)}</Badge>
                    {item.known_open_issue ? <Badge tone="warn">Known open issue</Badge> : null}
                  </div>
                  <p className="mt-2 max-w-4xl text-sm text-stone-700">{item.question ?? "Question text unavailable."}</p>
                </div>
                <div className="text-right text-sm text-stone-600">
                  <p><PhaseLabel phase={item.phase} /></p>
                  <p>{formatLabel(item.actual_response_type)}</p>
                </div>
              </div>
            </button>

            {isOpen ? (
              <div className="border-t border-stone-200 p-5">
                {item.known_open_issue_note ? (
                  <p className="mb-4 rounded border border-rust bg-rust-soft p-3 text-sm font-medium text-rust-dark">{item.known_open_issue_note}</p>
                ) : null}
                <div className="grid gap-4 lg:grid-cols-2">
                  <section>
                    <h4 className="font-semibold text-ink">Expected Answer</h4>
                    <p className="mt-2 text-sm leading-6 text-stone-700">{item.expected_answer ?? "n/a"}</p>
                  </section>
                  <section>
                    <h4 className="font-semibold text-ink">Actual Answer</h4>
                    <p className="mt-2 text-sm leading-6 text-stone-700">{item.actual_answer ?? "Detailed actual answer unavailable for this failure export."}</p>
                  </section>
                </div>
                <div className="mt-4 grid gap-4 lg:grid-cols-2">
                  <section className="rounded border border-stone-300 p-4">
                    <h4 className="font-semibold text-ink">Expected Sources</h4>
                    <p className="mt-2 text-sm text-stone-700">{(item.expected_source_document ?? []).join(", ") || "n/a"}</p>
                    <h4 className="mt-4 font-semibold text-ink">Actual Citation Documents</h4>
                    <p className="mt-2 text-sm text-stone-700">{(item.actual_citation_documents ?? []).join(", ") || "n/a"}</p>
                    <h4 className="mt-4 font-semibold text-ink">Citation Failure Categories</h4>
                    <p className="mt-2 text-sm text-stone-700">{(item.citation_failure_labels ?? item.citation_failure_categories ?? []).join(", ") || "n/a"}</p>
                  </section>
                  <section className="rounded border border-stone-300 p-4">
                    <h4 className="font-semibold text-ink">Scoring</h4>
                    <div className="mt-2 grid grid-cols-2 gap-2 text-sm text-stone-700">
                      <p>Citation confidence: {formatMetric(item.citation_confidence)}</p>
                      <p>Answer confidence: {formatMetric(item.answer_confidence)}</p>
                      <p>Final confidence: {formatMetric(item.confidence)}</p>
                      <p>Expected behavior: {formatLabel(item.expected_behavior)}</p>
                    </div>
                    <h4 className="mt-4 font-semibold text-ink">Citation Document Gaps</h4>
                    <div className="mt-2 space-y-1 text-sm text-stone-700">
                      <p>Missing: {(item.missing_citation_documents ?? []).join(", ") || "None"}</p>
                      <p>Unexpected: {(item.unexpected_citation_documents ?? []).join(", ") || "None"}</p>
                      <p>Restricted: {(item.restricted_citation_documents ?? []).join(", ") || "None"}</p>
                    </div>
                  </section>
                </div>
                <section className="mt-4">
                  <h4 className="mb-2 font-semibold text-ink">Actual Citations</h4>
                  <CitationTable citations={item.actual_citations ?? []} />
                </section>
                <section className="mt-4">
                  <h4 className="mb-2 font-semibold text-ink">Retrieved Documents</h4>
                  <p className="rounded border border-stone-300 p-3 text-sm text-stone-700">{(item.retrieved_documents ?? []).join(", ") || "Detailed retrieved documents unavailable."}</p>
                </section>
                {item.retrieved_chunks?.length ? (
                  <section className="mt-4">
                    <h4 className="mb-2 font-semibold text-ink">Retrieved Chunks</h4>
                    <RetrievedContext chunks={item.retrieved_chunks} />
                  </section>
                ) : null}
                <p className="mt-4 rounded border border-stone-300 bg-stone-50 p-3 text-sm text-stone-700">
                  <span className="font-semibold text-ink">Recommended fix: </span>{item.recommended_fix ?? "n/a"}
                </p>
                <section className="mt-4">
                  <h4 className="mb-2 font-semibold text-ink">Human Review Decision</h4>
                  <EvaluationReviewPanel
                    sourceType="failed_question"
                    sourceId={item.question_id}
                    question={item.question ?? item.question_id}
                    answer={item.actual_answer}
                    expectedAnswer={item.expected_answer}
                    expectedSources={item.expected_source_document ?? []}
                    actualCitations={item.actual_citations ?? []}
                    retrievedChunks={item.retrieved_chunks ?? []}
                  />
                </section>
              </div>
            ) : null}
          </Card>
        );
      })}
    </section>
  );
}
