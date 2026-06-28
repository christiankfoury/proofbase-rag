"use client";

import { FormEvent, useState } from "react";
import { Badge, BadgeTone } from "@/components/Badge";
import { Card } from "@/components/Card";
import { MetricCard } from "@/components/MetricCard";
import { RunLabel } from "@/components/PhaseLabel";
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

type SourceOption = {
  id: string;
  label: string;
  group: string;
};

const sourceOptions: SourceOption[] = [
  { id: "HR-001", label: "Employee Handbook", group: "People Operations" },
  { id: "HR-002", label: "Leave And Time Off Policy", group: "People Operations" },
  { id: "HR-003", label: "Remote And Hybrid Work Policy", group: "People Operations" },
  { id: "HR-004", label: "Benefits Overview", group: "People Operations" },
  { id: "MGR-001", label: "Manager Playbook", group: "Management" },
  { id: "MGR-002", label: "Promotion Calibration Guide", group: "Management" },
  { id: "IT-001", label: "Security Acceptable Use Policy", group: "IT And Security" },
  { id: "IT-002", label: "Device Security Policy", group: "IT And Security" },
  { id: "IT-003", label: "Approved AI Tools Policy", group: "IT And Security" },
  { id: "HR-ADMIN-001", label: "HR Admin Operations Guide", group: "Admin" },
  { id: "IT-ADMIN-001", label: "IT Admin Operations Guide", group: "Admin" },
  { id: "SALES-001", label: "Sales Playbook", group: "Sales" },
  { id: "SALES-002", label: "Product Positioning And FAQ", group: "Sales" },
  { id: "SALES-003", label: "Competitive Battlecard", group: "Sales" },
  { id: "FIN-001", label: "Expense And Purchasing Policy", group: "Finance" },
  { id: "LEGAL-001", label: "Legal Review And NDA Policy", group: "Legal" },
  { id: "ENG-001", label: "Engineering Release Policy", group: "Engineering" },
  { id: "SUPPORT-001", label: "Support Escalation Guide", group: "Support" },
  { id: "OPS-001", label: "Operations Continuity Plan", group: "Operations" },
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

function sourceOptionLabel(sourceId: string): string {
  const option = sourceOptions.find((item) => item.id === sourceId);
  return option ? `${option.id} - ${option.label}` : sourceId;
}

function ExpectedSourcePicker({
  selected,
  onChange,
}: {
  selected: string[];
  onChange: (selected: string[]) => void;
}) {
  const [open, setOpen] = useState(false);
  const selectedSet = new Set(selected);
  const groups = Array.from(new Set(sourceOptions.map((option) => option.group)));

  function toggleSource(sourceId: string) {
    if (selectedSet.has(sourceId)) {
      onChange(selected.filter((item) => item !== sourceId));
      return;
    }
    onChange([...selected, sourceId]);
  }

  function removeSource(sourceId: string) {
    onChange(selected.filter((item) => item !== sourceId));
  }

  return (
    <div className="relative">
      <div className="field flex min-h-10 w-full flex-wrap items-center gap-2 text-left" aria-label="Expected source documents">
        {selected.length ? (
          selected.map((sourceId) => (
            <span
              key={sourceId}
              className="inline-flex max-w-full items-center gap-1 rounded-full border border-moss bg-moss-soft px-2.5 py-1 text-xs font-semibold text-moss-dark"
            >
              <span className="truncate">{sourceOptionLabel(sourceId)}</span>
              <button
                type="button"
                className="rounded-full px-1 text-moss-dark hover:bg-white/70"
                aria-label={`Remove ${sourceId}`}
                onClick={() => removeSource(sourceId)}
              >
                x
              </button>
            </span>
          ))
        ) : (
          <span className="text-stone-500">Select expected source documents</span>
        )}
        <button
          type="button"
          className="ml-auto rounded border border-stone-300 bg-white px-2.5 py-1 text-xs font-semibold text-steel-dark hover:border-steel hover:bg-steel-soft"
          onClick={() => setOpen((value) => !value)}
          aria-expanded={open}
          aria-haspopup="listbox"
        >
          Choose
        </button>
      </div>
      {open ? (
        <div className="absolute left-0 top-[calc(100%+0.35rem)] z-30 max-h-96 w-[min(760px,calc(100vw-3rem))] overflow-y-auto rounded-md border border-stone-300 bg-white p-3 shadow-xl">
          <div className="mb-3 flex items-center justify-between gap-3">
            <p className="text-xs font-semibold uppercase tracking-wide text-stone-500">Expected source documents</p>
            {selected.length ? (
              <button type="button" className="text-xs font-semibold text-rust-dark hover:underline" onClick={() => onChange([])}>
                Clear
              </button>
            ) : null}
          </div>
          <div className="space-y-4" role="listbox" aria-label="Expected source documents" aria-multiselectable="true">
            {groups.map((group) => (
              <section key={group}>
                <p className="mb-2 text-xs font-semibold text-steel-dark">{group}</p>
                <div className="flex flex-wrap gap-2">
                  {sourceOptions
                    .filter((option) => option.group === group)
                    .map((option) => {
                      const active = selectedSet.has(option.id);
                      return (
                        <button
                          key={option.id}
                          type="button"
                          role="option"
                          aria-selected={active}
                          onClick={() => toggleSource(option.id)}
                          className={`inline-flex w-fit items-center gap-2 rounded-full border px-3 py-1.5 text-sm transition-colors ${
                            active
                              ? "border-moss bg-moss-soft font-semibold text-moss-dark"
                              : "border-stone-300 bg-white text-stone-700 hover:border-steel hover:bg-steel-soft"
                          }`}
                        >
                          <span>{option.id}</span>
                          <span className="text-xs">{option.label}</span>
                          {active ? <span className="text-xs">x</span> : null}
                        </button>
                      );
                    })}
                </div>
              </section>
            ))}
          </div>
        </div>
      ) : null}
    </div>
  );
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
              <td>{run ? <RunLabel run={run} /> : "No retrieval-only benchmark yet"}</td>
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
  const [expectedSources, setExpectedSources] = useState(["HR-003", "IT-002"]);
  const [role, setRole] = useState<UserRole>("Employee");
  const [results, setResults] = useState<ProfileResult[]>(profiles.map((profile) => ({ profile })));
  const [loading, setLoading] = useState(false);
  const [reviewProfileName, setReviewProfileName] = useState(profiles[0].name);
  const [reviewDecision, setReviewDecision] = useState<ReviewDecision>("review_only");
  const [reviewNotes, setReviewNotes] = useState("");
  const [reviewStatus, setReviewStatus] = useState<string | null>(null);

  const knownMultiDocFailure = failures.find((failure) => failure.question_id === "MULTI-005");
  const hasLiveResult = results.some((item) => item.result);
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
        user_role: "Admin",
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
        <MetricCard label="Named profiles" value={profiles.length} detail="Compared with one shared query shape." format="integer" />
        <MetricCard label="Historical runs" value={historicalRuns.length} detail="Existing retrieval-only benchmarks." tone="good" format="integer" />
        <MetricCard label="Known multi-doc misses" value={failureBuckets.multi_document_failure} detail="Must remain visible during promotion." tone="warn" format="integer" />
        <MetricCard label="Citation issue backlog" value={failureBuckets.wrong_citation} detail="Profile wins still need citation review." tone="warn" format="integer" />
      </section>

      <Card>
        <div className="grid gap-3 xl:grid-cols-[1fr_minmax(360px,0.7fr)_160px_auto]">
          <input value={question} onChange={(event) => setQuestion(event.target.value)} className="field" />
          <ExpectedSourcePicker selected={expectedSources} onChange={setExpectedSources} />
          <select value={role} onChange={(event) => setRole(event.target.value as UserRole)} className="field" aria-label="Admin simulation role">
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
          Admin-only simulation compares role perspectives for one question while the API still resolves the signed-in demo user.
          The live gate checks retrieved-source coverage, citation-source coverage, permission leakage, confidence, latency, and estimated cost.
          Full promotion still requires benchmark evidence.
        </p>
      </Card>

      <section>
        <h3 className="mb-3 text-xl font-semibold text-ink">Live Profile Results</h3>
        <div className="grid gap-5 xl:grid-cols-2">
          {results.map(({ profile, result, error }) => {
            const outcome = profileOutcome(result, expectedSources);
            const retrievedDocuments = uniqueDocumentsFromResult(result);
            const citedDocuments = result ? uniqueDocumentsFromCitations(result.citations) : [];
            return (
              <Card key={profile.name} tone={outcome.tone === "good" ? "good" : "neutral"} className="flex h-full flex-col">
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
                  <div className="mt-4 flex flex-1 flex-col">
                    <div className="grid gap-2 text-xs text-stone-700 md:grid-cols-3">
                      <span>Retrieved coverage: {formatMetric(coverage(expectedSources, retrievedDocuments))}</span>
                      <span>Citation coverage: {formatMetric(coverage(expectedSources, citedDocuments))}</span>
                      <span>Final confidence: {formatMetric(result.final_confidence)}</span>
                      <span>Cost: {formatUsd(result.estimated_cost_usd)}</span>
                      <span>Chunks: {result.retrieved_chunks.length}</span>
                      <span>Leakage: {result.permission_check.unauthorized_chunks_reached_generation ? "yes" : "no"}</span>
                    </div>
                    <p className="mt-4 line-clamp-6 text-sm leading-6 text-stone-800">{result.answer}</p>
                    <div className="mt-4">
                      <h4 className="mb-2 font-semibold text-ink">Citations</h4>
                      <CompactCitations citations={result.citations} />
                    </div>
                    <details className="mt-auto rounded border border-stone-300 p-4">
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
      </section>

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

      {hasLiveResult ? (
        <Card>
          <h3 className="text-lg font-semibold text-ink">Record Result Review</h3>
          <p className="mt-1 text-sm text-stone-600">
            Save an audit note for one live profile result. This does not promote a profile globally.
          </p>
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
            <input value={reviewNotes} onChange={(event) => setReviewNotes(event.target.value)} className="field" placeholder="Why this result should be reviewed, rejected, or considered a candidate" />
            <button type="submit" className="btn-accent">Record note</button>
          </form>
          {reviewStatus ? <p className="mt-2 text-sm text-stone-700">{reviewStatus}</p> : null}
        </Card>
      ) : null}
    </section>
  );
}
