"use client";

import { FormEvent, useMemo, useState } from "react";
import { Badge, BadgeTone } from "@/components/Badge";
import { Card } from "@/components/Card";
import { MetricCard } from "@/components/MetricCard";
import { RetrievedContext } from "@/components/QueryResultPanel";
import { Citation, QueryResponse, UserRole, queryRag, submitAlgorithmReview } from "@/lib/api";
import { EvalRun, FailedQuestion, formatLabel, formatMetric, formatTableMetric } from "@/lib/dashboard";

type Profile = {
  name: string;
  label: string;
  runName?: string;
  retrieval_mode: "vector_only" | "keyword_only" | "hybrid";
  multi_doc_mode: "off" | "force";
  chunking_strategy: string;
  summary: string;
};

const profiles: Profile[] = [
  {
    name: "vector-section",
    label: "Vector section",
    runName: "vector-section",
    retrieval_mode: "vector_only",
    multi_doc_mode: "off",
    chunking_strategy: "section_based",
    summary: "Current default. Best historical retrieval profile by source coverage and precision tradeoff.",
  },
  {
    name: "keyword-section",
    label: "Keyword section",
    runName: "keyword-section",
    retrieval_mode: "keyword_only",
    multi_doc_mode: "off",
    chunking_strategy: "section_based",
    summary: "Fast lexical baseline. Useful when exact policy terms matter, weaker on noisy precision.",
  },
  {
    name: "hybrid-section-0.5",
    label: "Hybrid 50/50",
    runName: "hybrid-section-0.5",
    retrieval_mode: "hybrid",
    multi_doc_mode: "off",
    chunking_strategy: "section_based",
    summary: "Blends vector and keyword scores. Historical hit rate matches vector, but precision is lower.",
  },
  {
    name: "multi-doc-forced",
    label: "Forced multi-doc",
    retrieval_mode: "vector_only",
    multi_doc_mode: "force",
    chunking_strategy: "section_based",
    summary: "Uses query decomposition for multi-source questions. Review against failures instead of treating it as a default.",
  },
];

type ProfileResult = {
  profile: Profile;
  result?: QueryResponse;
  error?: string;
};

type ReviewDecision = "review_only" | "candidate" | "rejected";

function formatLatency(value: number | null | undefined): string {
  if (value === null || value === undefined) return "pending";
  if (value >= 1000) return `${(value / 1000).toFixed(1)}s`;
  return `${Math.round(value)} ms`;
}

function formatUsd(value: number | null | undefined): string {
  if (value === null || value === undefined) return "pending";
  return `$${value.toFixed(6)}`;
}

function parseExpectedSources(value: string): string[] {
  return value
    .split(/[,\n]/)
    .map((item) => item.trim())
    .filter(Boolean);
}

function uniqueDocumentsFromCitations(citations: Citation[]): string[] {
  return Array.from(new Set(citations.map((citation) => citation.document_id).filter(Boolean) as string[]));
}

function uniqueDocumentsFromResult(result?: QueryResponse): string[] {
  if (!result) return [];
  return Array.from(new Set(result.retrieved_chunks.map((chunk) => chunk.document_id).filter(Boolean)));
}

function coverage(expectedSources: string[], actualSources: string[]): number | null {
  if (!expectedSources.length) return null;
  const actual = new Set(actualSources);
  return expectedSources.filter((source) => actual.has(source)).length / expectedSources.length;
}

function profileOutcome(result: QueryResponse | undefined, expectedSources: string[]): { text: string; tone: BadgeTone } {
  if (!result) return { text: "Not run", tone: "neutral" };
  if (result.permission_check.unauthorized_chunks_reached_generation) return { text: "Reject: leakage", tone: "warn" };
  const retrievedCoverage = coverage(expectedSources, uniqueDocumentsFromResult(result));
  const citationCoverage = coverage(expectedSources, uniqueDocumentsFromCitations(result.citations));
  if (retrievedCoverage !== null && retrievedCoverage < 1) return { text: "Missed source", tone: "warn" };
  if (citationCoverage !== null && citationCoverage < 1) return { text: "Citation gap", tone: "warn" };
  if (result.response_type === "not_found" || result.response_type === "partial_answer") return { text: "Needs answer review", tone: "warn" };
  if ((result.final_confidence ?? 0) < 0.7) return { text: "Low confidence", tone: "info" };
  return { text: "Candidate on this query", tone: "good" };
}

function CompactCitations({ citations }: { citations: Citation[] }) {
  if (!citations.length) return <p className="text-sm text-stone-600">No citations returned.</p>;
  return (
    <div className="space-y-2">
      {citations.slice(0, 5).map((citation, index) => (
        <div key={`${citation.chunk_id ?? citation.document_id}-${index}`} className="rounded border border-stone-200 p-3 text-sm">
          <div className="flex flex-wrap items-start justify-between gap-2">
            <div>
              <p className="font-semibold text-ink">{citation.document_title ?? "Untitled"}</p>
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

function HistoricalProfileTable({ runs }: { runs: EvalRun[] }) {
  const rows = profiles.map((profile) => ({
    profile,
    run: profile.runName ? runs.find((item) => item.run_name === profile.runName) : undefined,
  }));
  return (
    <div className="overflow-x-auto rounded-md border border-stone-300 bg-white">
      <table className="data-table min-w-[980px]">
        <thead>
          <tr>
            <th>Profile</th>
            <th>Historical run</th>
            <th className="text-right">All sources</th>
            <th className="text-right">Recall</th>
            <th className="text-right">Precision@k</th>
            <th className="text-right">MRR</th>
            <th className="text-right">Latency</th>
            <th>Known misses</th>
          </tr>
        </thead>
        <tbody>
          {rows.map(({ profile, run }) => (
            <tr key={profile.name}>
              <td>
                <p className="font-semibold text-ink">{profile.label}</p>
                <p className="max-w-[300px] text-xs text-stone-600">{profile.summary}</p>
              </td>
              <td>{run?.run_name ?? "No retrieval-only benchmark yet"}</td>
              <td className="text-right">{formatTableMetric(run?.metrics.all_sources_hit)}</td>
              <td className="text-right">{formatTableMetric(run?.metrics.expected_source_recall)}</td>
              <td className="text-right">{formatTableMetric(run?.metrics.precision_at_k)}</td>
              <td className="text-right">{formatTableMetric(run?.metrics.mrr)}</td>
              <td className="text-right">{run?.metrics.average_latency_ms ? `${formatTableMetric(run.metrics.average_latency_ms)} ms` : "-"}</td>
              <td>{run?.failed_questions?.length ? run.failed_questions.join(", ") : run ? "None" : "Pending"}</td>
            </tr>
          ))}
        </tbody>
      </table>
    </div>
  );
}

export function RetrievalPlaygroundClient({
  historicalRuns,
  failures,
}: {
  historicalRuns: EvalRun[];
  failures: FailedQuestion[];
}) {
  const [question, setQuestion] = useState("If I work remotely, what approval and device security expectations apply?");
  const [expectedSourcesInput, setExpectedSourcesInput] = useState("HR-003, IT-002");
  const [role, setRole] = useState<UserRole>("Employee");
  const [results, setResults] = useState<ProfileResult[]>(profiles.map((profile) => ({ profile })));
  const [loading, setLoading] = useState(false);
  const [reviewProfileName, setReviewProfileName] = useState(profiles[0].name);
  const [reviewDecision, setReviewDecision] = useState<ReviewDecision>("review_only");
  const [reviewNotes, setReviewNotes] = useState("");
  const [reviewStatus, setReviewStatus] = useState<string | null>(null);

  const expectedSources = useMemo(() => parseExpectedSources(expectedSourcesInput), [expectedSourcesInput]);
  const knownMultiDocFailure = failures.find((failure) => failure.question_id === "MULTI-005");
  const failureBuckets = {
    multi_document_failure: failures.filter((failure) => failure.failure_type === "multi_document_failure").length,
    wrong_citation: failures.filter((failure) => failure.failure_type === "wrong_citation").length,
    answer_not_generated: failures.filter((failure) => failure.failure_type === "answer_not_generated").length,
  };

  async function runComparison() {
    setLoading(true);
    setReviewStatus(null);
    const nextResults: ProfileResult[] = [];
    for (const profile of profiles) {
      try {
        const result = await queryRag({
          question,
          user_role: role,
          retrieval_mode: profile.retrieval_mode,
          chunking_strategy: profile.chunking_strategy,
          multi_doc_mode: profile.multi_doc_mode,
        });
        nextResults.push({ profile, result });
      } catch (exc) {
        nextResults.push({ profile, error: exc instanceof Error ? exc.message : "Query failed." });
      }
    }
    setResults(nextResults);
    setLoading(false);
  }

  async function submitReview(event: FormEvent) {
    event.preventDefault();
    const selected = results.find((item) => item.profile.name === reviewProfileName);
    if (!selected?.result) {
      setReviewStatus("Run the selected profile before recording a review note.");
      return;
    }
    const retrievedDocuments = uniqueDocumentsFromResult(selected.result);
    const citedDocuments = uniqueDocumentsFromCitations(selected.result.citations);
    try {
      const response = await submitAlgorithmReview({
        profile_name: selected.profile.name,
        decision: reviewDecision,
        question,
        user_role: "Knowledge Manager",
        primary_metric: "source_coverage",
        expected_sources: expectedSources,
        notes: reviewNotes,
        result_summary: {
          response_type: selected.result.response_type,
          retrieved_source_coverage: coverage(expectedSources, retrievedDocuments),
          citation_source_coverage: coverage(expectedSources, citedDocuments),
          retrieved_documents: retrievedDocuments,
          cited_documents: citedDocuments,
          final_confidence: selected.result.final_confidence,
          latency_ms: selected.result.total_latency_ms,
          estimated_cost_usd: selected.result.estimated_cost_usd,
          unauthorized_chunks_reached_generation: selected.result.permission_check.unauthorized_chunks_reached_generation,
        },
      });
      setReviewStatus(`Review recorded: ${response.review_id}`);
      setReviewNotes("");
    } catch (exc) {
      setReviewStatus(exc instanceof Error ? exc.message : "Review note failed.");
    }
  }

  return (
    <section className="space-y-6">
      <section className="grid gap-4 md:grid-cols-2 xl:grid-cols-4">
        <MetricCard label="Named profiles" value={profiles.length} detail="Compared with one shared query shape." />
        <MetricCard label="Historical runs" value={historicalRuns.length} detail="Existing retrieval-only benchmarks." tone="good" />
        <MetricCard label="Known multi-doc misses" value={failureBuckets.multi_document_failure} detail="Must remain visible during promotion." tone="warn" />
        <MetricCard label="Citation issue backlog" value={failureBuckets.wrong_citation} detail="Profile wins still need citation review." tone="warn" />
      </section>

      <Card>
        <div className="grid gap-3 xl:grid-cols-[1fr_220px_160px_auto]">
          <input value={question} onChange={(event) => setQuestion(event.target.value)} className="field" />
          <input
            value={expectedSourcesInput}
            onChange={(event) => setExpectedSourcesInput(event.target.value)}
            className="field"
            aria-label="Expected source documents"
            placeholder="Expected docs, e.g. HR-003, IT-002"
          />
          <select value={role} onChange={(event) => setRole(event.target.value as UserRole)} className="field">
            <option>Employee</option>
            <option>Sales Representative</option>
            <option>Manager</option>
            <option>HR Admin</option>
            <option>IT Admin</option>
          </select>
          <button type="button" onClick={runComparison} disabled={loading} className="btn-primary">
            {loading ? "Running..." : "Run profiles"}
          </button>
        </div>
        <p className="mt-3 text-sm text-stone-700">
          The live gate checks retrieved-source coverage, citation-source coverage, permission leakage, confidence, latency, and estimated cost for one question. Full promotion still requires benchmark evidence.
        </p>
      </Card>

      <section>
        <div className="mb-3 flex flex-wrap items-center justify-between gap-3">
          <h3 className="text-xl font-semibold text-ink">Historical Profile Evidence</h3>
          <Badge tone="solid">Real exported metrics</Badge>
        </div>
        <HistoricalProfileTable runs={historicalRuns} />
      </section>

      {knownMultiDocFailure ? (
        <Card tone="warn">
          <h3 className="text-lg font-semibold text-ink">Known Failure Stays Visible</h3>
          <p className="mt-2 text-sm text-stone-700">
            {knownMultiDocFailure.question_id}: {knownMultiDocFailure.recommended_fix}
          </p>
        </Card>
      ) : null}

      <div className="grid gap-5 xl:grid-cols-2">
        {results.map(({ profile, result, error }) => {
          const outcome = profileOutcome(result, expectedSources);
          const retrievedDocuments = uniqueDocumentsFromResult(result);
          const citedDocuments = result ? uniqueDocumentsFromCitations(result.citations) : [];
          return (
            <Card key={profile.name} tone={outcome.tone === "good" ? "good" : "neutral"}>
              <div className="flex flex-wrap items-start justify-between gap-3">
                <div>
                  <div className="flex flex-wrap items-center gap-2">
                    <h3 className="text-xl font-semibold text-ink">{profile.label}</h3>
                    <Badge tone={outcome.tone}>{outcome.text}</Badge>
                  </div>
                  <p className="mt-1 text-sm text-stone-600">{profile.summary}</p>
                </div>
                {result ? (
                  <div className="text-right text-xs text-stone-600">
                    <p>{formatLabel(result.response_type)}</p>
                    <p>{formatLatency(result.total_latency_ms)}</p>
                  </div>
                ) : null}
              </div>
              {error ? <p className="mt-4 rounded border border-rust bg-rust-soft p-3 text-sm font-medium text-rust-dark">{error}</p> : null}
              {result ? (
                <div className="mt-4 space-y-4">
                  <div className="grid gap-2 text-xs text-stone-700 md:grid-cols-3">
                    <span>Retrieved coverage: {formatMetric(coverage(expectedSources, retrievedDocuments))}</span>
                    <span>Citation coverage: {formatMetric(coverage(expectedSources, citedDocuments))}</span>
                    <span>Final confidence: {formatMetric(result.final_confidence)}</span>
                    <span>Cost: {formatUsd(result.estimated_cost_usd)}</span>
                    <span>Chunks: {result.retrieved_chunks.length}</span>
                    <span>Leakage: {result.permission_check.unauthorized_chunks_reached_generation ? "yes" : "no"}</span>
                  </div>
                  <p className="line-clamp-6 text-sm leading-6 text-stone-800">{result.answer}</p>
                  <div>
                    <h4 className="mb-2 font-semibold text-ink">Citations</h4>
                    <CompactCitations citations={result.citations} />
                  </div>
                  <details className="rounded border border-stone-300 p-4">
                    <summary className="cursor-pointer font-semibold text-ink focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-moss">
                      Top Retrieved Chunks
                    </summary>
                    <div className="mt-3">
                      <RetrievedContext chunks={result.retrieved_chunks.slice(0, 4)} />
                    </div>
                  </details>
                </div>
              ) : (
                <p className="mt-4 text-sm text-stone-600">Run the profiles to populate this result.</p>
              )}
            </Card>
          );
        })}
      </div>

      <Card>
        <h3 className="text-lg font-semibold text-ink">Review Note</h3>
        <form onSubmit={submitReview} className="mt-3 grid gap-3 lg:grid-cols-[220px_180px_1fr_auto]">
          <select value={reviewProfileName} onChange={(event) => setReviewProfileName(event.target.value)} className="field">
            {profiles.map((profile) => (
              <option key={profile.name} value={profile.name}>{profile.label}</option>
            ))}
          </select>
          <select value={reviewDecision} onChange={(event) => setReviewDecision(event.target.value as ReviewDecision)} className="field">
            <option value="review_only">Review only</option>
            <option value="candidate">Candidate</option>
            <option value="rejected">Rejected</option>
          </select>
          <input value={reviewNotes} onChange={(event) => setReviewNotes(event.target.value)} className="field" placeholder="Promotion rationale or rejection reason" />
          <button type="submit" className="btn-accent">Record review</button>
        </form>
        {reviewStatus ? <p className="mt-2 text-sm text-stone-700">{reviewStatus}</p> : null}
      </Card>
    </section>
  );
}
