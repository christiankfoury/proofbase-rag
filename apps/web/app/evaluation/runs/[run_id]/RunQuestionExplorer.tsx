"use client";

import { Fragment, useMemo, useState } from "react";
import { CitationTable } from "@/components/QueryResultPanel";
import { RunQuestionResponse, RunQuestionRow } from "@/lib/api";
import { formatLabel, formatMetric } from "@/lib/dashboard";

function stringValue(value: unknown): string {
  if (typeof value === "string") return value;
  if (typeof value === "number") return String(value);
  if (typeof value === "boolean") return String(value);
  return "";
}

function uniqueValues(rows: RunQuestionRow[], key: keyof RunQuestionRow): string[] {
  return Array.from(new Set(rows.map((row) => stringValue(row[key])).filter(Boolean))).sort();
}

function rowPassed(row: RunQuestionRow): boolean {
  if (typeof row.passed === "boolean") return row.passed;
  const answer = typeof row.answer_accuracy === "number" ? row.answer_accuracy : 1;
  const citation = typeof row.citation_accuracy === "number" ? row.citation_accuracy : 1;
  return answer >= 1 && citation >= 1 && !row.failure_type;
}

export function RunQuestionExplorer({ data }: { data: RunQuestionResponse }) {
  const [questionType, setQuestionType] = useState("all");
  const [passState, setPassState] = useState("all");
  const [failureType, setFailureType] = useState("all");
  const [responseType, setResponseType] = useState("all");
  const [expanded, setExpanded] = useState<string | null>(null);

  const filteredRows = useMemo(() => {
    return data.rows.filter((row) => {
      if (questionType !== "all" && row.question_type !== questionType) return false;
      if (failureType !== "all" && row.failure_type !== failureType) return false;
      if (responseType !== "all" && row.actual_response_type !== responseType) return false;
      if (passState === "passed" && !rowPassed(row)) return false;
      if (passState === "failed" && rowPassed(row)) return false;
      return true;
    });
  }, [data.rows, failureType, passState, questionType, responseType]);

  if (!data.detail_available) {
    return (
      <section className="rounded-md border border-stone-300 bg-white p-5">
        <h3 className="text-xl font-semibold">Per-question rows unavailable</h3>
        <p className="mt-2 text-stone-700">{data.message}</p>
      </section>
    );
  }

  return (
    <section className="space-y-4">
      <div className="grid gap-3 rounded-md border border-stone-300 bg-white p-5 md:grid-cols-4">
        <select value={questionType} onChange={(event) => setQuestionType(event.target.value)} className="rounded border border-stone-300 px-3 py-2">
          <option value="all">All question types</option>
          {uniqueValues(data.rows, "question_type").map((item) => <option key={item}>{item}</option>)}
        </select>
        <select value={passState} onChange={(event) => setPassState(event.target.value)} className="rounded border border-stone-300 px-3 py-2">
          <option value="all">Passed and failed</option>
          <option value="passed">Passed only</option>
          <option value="failed">Failed only</option>
        </select>
        <select value={failureType} onChange={(event) => setFailureType(event.target.value)} className="rounded border border-stone-300 px-3 py-2">
          <option value="all">All failure types</option>
          {uniqueValues(data.rows, "failure_type").map((item) => <option key={item}>{item}</option>)}
        </select>
        <select value={responseType} onChange={(event) => setResponseType(event.target.value)} className="rounded border border-stone-300 px-3 py-2">
          <option value="all">All response types</option>
          {uniqueValues(data.rows, "actual_response_type").map((item) => <option key={item}>{item}</option>)}
        </select>
      </div>

      <div className="overflow-x-auto rounded-md border border-stone-300 bg-white">
        <table className="w-full min-w-[1120px] text-left text-sm">
          <thead className="bg-stone-100 text-stone-700">
            <tr>
              <th className="p-3">Question</th>
              <th className="p-3">Expected</th>
              <th className="p-3">Actual</th>
              <th className="p-3">Sources</th>
              <th className="p-3 text-right">Answer</th>
              <th className="p-3 text-right">Citation</th>
              <th className="p-3">Failure</th>
              <th className="p-3 text-right">Confidence</th>
            </tr>
          </thead>
          <tbody>
            {filteredRows.map((row) => (
              <Fragment key={row.question_id}>
                <tr className="cursor-pointer border-t border-stone-200 align-top hover:bg-stone-50" onClick={() => setExpanded(expanded === row.question_id ? null : row.question_id)}>
                  <td className="p-3">
                    <p className="font-semibold">{row.question_id}</p>
                    <p className="mt-1 max-w-sm text-stone-700">{row.question}</p>
                  </td>
                  <td className="p-3">{formatLabel(row.expected_behavior)}</td>
                  <td className="p-3">{formatLabel(row.actual_response_type)}</td>
                  <td className="p-3">{(row.expected_source_document ?? []).join(", ") || "n/a"}</td>
                  <td className="p-3 text-right">{formatMetric(row.answer_accuracy)}</td>
                  <td className="p-3 text-right">{formatMetric(row.citation_accuracy)}</td>
                  <td className="p-3">{row.failure_type ? formatLabel(row.failure_type) : "Passed"}</td>
                  <td className="p-3 text-right">{formatMetric(row.final_confidence ?? row.confidence)}</td>
                </tr>
                {expanded === row.question_id ? (
                  <tr key={`${row.question_id}-detail`} className="border-t border-stone-200 bg-stone-50">
                    <td colSpan={8} className="p-5">
                      <div className="grid gap-4 lg:grid-cols-2">
                        <div>
                          <h4 className="font-semibold">Expected Answer</h4>
                          <p className="mt-2 text-sm leading-6 text-stone-700">{row.expected_answer ?? "n/a"}</p>
                        </div>
                        <div>
                          <h4 className="font-semibold">Actual Answer</h4>
                          <p className="mt-2 text-sm leading-6 text-stone-700">{row.actual_answer ?? "n/a"}</p>
                        </div>
                      </div>
                      <div className="mt-4">
                        <h4 className="mb-2 font-semibold">Actual Citations</h4>
                        <CitationTable citations={row.actual_citations ?? []} />
                      </div>
                      {row.recommended_fix ? (
                        <p className="mt-4 rounded border border-stone-300 bg-white p-3 text-sm">
                          <span className="font-semibold">Recommended fix: </span>{row.recommended_fix}
                        </p>
                      ) : null}
                    </td>
                  </tr>
                ) : null}
              </Fragment>
            ))}
          </tbody>
        </table>
      </div>
    </section>
  );
}
