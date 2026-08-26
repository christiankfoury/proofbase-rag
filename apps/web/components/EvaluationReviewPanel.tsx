"use client";

import { FormEvent, useEffect, useState } from "react";
import type { Citation, RetrievedChunk } from "@/lib/api";
import { createEvaluationReview, getEvaluationReviews } from "@/lib/reviews";
import type { EvaluationReview } from "@/lib/reviews";
import type { CorrectnessLabel, ReviewDecision } from "@/lib/reviews";

const scoreOptions: Array<{ value: CorrectnessLabel; label: string }> = [
  { value: "1", label: "1.0 correct" },
  { value: "0.5", label: "0.5 partial" },
  { value: "0", label: "0.0 incorrect" },
];

function correctnessLabel(value: number): CorrectnessLabel {
  if (value === 1) return "1";
  if (value === 0) return "0";
  return "0.5";
}

export function EvaluationReviewPanel({
  sourceType,
  sourceId,
  question,
  answer,
  expectedAnswer,
  expectedSources,
  actualCitations = [],
  retrievedChunks = [],
}: {
  sourceType: "failed_question" | "feedback";
  sourceId: string;
  question: string;
  answer?: string | null;
  expectedAnswer?: string | null;
  expectedSources?: string[];
  actualCitations?: Citation[];
  retrievedChunks?: RetrievedChunk[];
}) {
  const [answerCorrectness, setAnswerCorrectness] = useState<CorrectnessLabel>("0.5");
  const [citationCorrectness, setCitationCorrectness] = useState<CorrectnessLabel>("0.5");
  const [decision, setDecision] = useState<ReviewDecision>("needs_fix");
  const [editableExpectedAnswer, setEditableExpectedAnswer] = useState(expectedAnswer ?? "");
  const [notes, setNotes] = useState("");
  const [status, setStatus] = useState<string | null>(null);
  const [saving, setSaving] = useState(false);
  const [savedReviews, setSavedReviews] = useState<EvaluationReview[]>([]);
  const [historyLoading, setHistoryLoading] = useState(true);
  const [historyError, setHistoryError] = useState<string | null>(null);

  useEffect(() => {
    let active = true;
    setHistoryLoading(true);
    setHistoryError(null);
    setStatus(null);
    setSavedReviews([]);
    setAnswerCorrectness("0.5");
    setCitationCorrectness("0.5");
    setDecision("needs_fix");
    setEditableExpectedAnswer(expectedAnswer ?? "");
    setNotes("");
    getEvaluationReviews({ source_type: sourceType, source_id: sourceId, limit: 10 })
      .then(({ reviews }) => {
        if (!active) return;
        setSavedReviews(reviews);
        const latest = reviews[0];
        if (latest) {
          setAnswerCorrectness(correctnessLabel(latest.answer_correctness));
          setCitationCorrectness(correctnessLabel(latest.citation_correctness));
          setDecision(latest.decision);
          setEditableExpectedAnswer(latest.expected_answer ?? "");
          setNotes(latest.notes);
        } else {
          setAnswerCorrectness("0.5");
          setCitationCorrectness("0.5");
          setDecision("needs_fix");
          setEditableExpectedAnswer(expectedAnswer ?? "");
          setNotes("");
        }
      })
      .catch((exc) => {
        if (!active) return;
        setHistoryError(exc instanceof Error ? exc.message : "Saved reviews could not be loaded.");
      })
      .finally(() => {
        if (active) setHistoryLoading(false);
      });
    return () => {
      active = false;
    };
  }, [expectedAnswer, sourceId, sourceType]);

  async function onSubmit(event: FormEvent) {
    event.preventDefault();
    setSaving(true);
    setStatus(null);
    try {
      const review = await createEvaluationReview({
        source_type: sourceType,
        source_id: sourceId,
        question,
        answer,
        expected_answer: editableExpectedAnswer || null,
        expected_sources: expectedSources ?? [],
        actual_citations: actualCitations,
        retrieved_chunks: retrievedChunks,
        answer_correctness: Number(answerCorrectness),
        citation_correctness: Number(citationCorrectness),
        decision,
        notes,
      });
      setStatus(`Review saved: ${review.id}`);
      setSavedReviews((items) => [review, ...items.filter((item) => item.id !== review.id)]);
    } catch (exc) {
      setStatus(exc instanceof Error ? exc.message : "Review save failed.");
    } finally {
      setSaving(false);
    }
  }

  return (
    <form onSubmit={onSubmit} className="rounded border border-stone-300 bg-stone-50 p-4">
      <div className="grid gap-3 md:grid-cols-3">
        <label className="block">
          <span className="text-sm font-semibold text-ink">Answer label</span>
          <select value={answerCorrectness} onChange={(event) => setAnswerCorrectness(event.target.value as CorrectnessLabel)} className="field mt-1 w-full">
            {scoreOptions.map((option) => <option key={option.value} value={option.value}>{option.label}</option>)}
          </select>
        </label>
        <label className="block">
          <span className="text-sm font-semibold text-ink">Citation label</span>
          <select value={citationCorrectness} onChange={(event) => setCitationCorrectness(event.target.value as CorrectnessLabel)} className="field mt-1 w-full">
            {scoreOptions.map((option) => <option key={option.value} value={option.value}>{option.label}</option>)}
          </select>
        </label>
        <label className="block">
          <span className="text-sm font-semibold text-ink">Decision</span>
          <select value={decision} onChange={(event) => setDecision(event.target.value as ReviewDecision)} className="field mt-1 w-full">
            <option value="needs_fix">Needs fix</option>
            <option value="evaluation_candidate">Evaluation candidate</option>
            <option value="approved_reference">Approved reference</option>
            <option value="rejected">Rejected</option>
          </select>
        </label>
      </div>
      <label className="mt-3 block">
        <span className="text-sm font-semibold text-ink">Expected answer</span>
        <textarea value={editableExpectedAnswer} onChange={(event) => setEditableExpectedAnswer(event.target.value)} rows={3} className="field mt-1 w-full" />
      </label>
      <label className="mt-3 block">
        <span className="text-sm font-semibold text-ink">Review notes</span>
        <textarea value={notes} onChange={(event) => setNotes(event.target.value)} rows={2} className="field mt-1 w-full" placeholder="Why this should become a candidate, remain a bug, or be rejected" />
      </label>
      <div className="mt-3 flex flex-wrap items-center gap-3">
        <button type="submit" disabled={saving} className="btn-accent">{saving ? "Saving..." : "Save review"}</button>
        {status ? <p className="text-sm text-stone-700">{status}</p> : null}
      </div>
      <section className="mt-5 border-t border-stone-300 pt-4" aria-live="polite">
        <div className="flex flex-wrap items-center justify-between gap-2">
          <h5 className="font-semibold text-ink">Saved review history</h5>
          <span className="text-xs text-stone-500">
            {historyLoading ? "Loading..." : `${savedReviews.length} saved`}
          </span>
        </div>
        {historyError ? <p className="mt-2 text-sm text-rust-dark">{historyError}</p> : null}
        {!historyLoading && !historyError && savedReviews.length === 0 ? (
          <p className="mt-2 text-sm text-stone-600">No saved reviews for this item yet.</p>
        ) : null}
        {savedReviews.length ? (
          <ol className="mt-3 space-y-3">
            {savedReviews.map((review, index) => (
              <li key={review.id} className="rounded border border-stone-300 bg-white p-3 text-sm text-stone-700">
                <div className="flex flex-wrap items-center justify-between gap-2">
                  <p className="font-semibold text-ink">
                    {review.decision.replaceAll("_", " ")}{index === 0 ? " · latest" : ""}
                  </p>
                  <time className="text-xs text-stone-500" dateTime={review.created_at}>
                    {new Date(review.created_at).toLocaleString()}
                  </time>
                </div>
                <p className="mt-1 text-xs text-stone-600">
                  Answer {review.answer_correctness.toFixed(1)} · Citation {review.citation_correctness.toFixed(1)} · {review.reviewer_role}
                </p>
                {review.expected_answer ? (
                  <p className="mt-2"><span className="font-semibold text-ink">Expected:</span> {review.expected_answer}</p>
                ) : null}
                {review.notes ? (
                  <p className="mt-1"><span className="font-semibold text-ink">Notes:</span> {review.notes}</p>
                ) : null}
                <p className="mt-2 break-all text-xs text-stone-500">Review ID: {review.id}</p>
              </li>
            ))}
          </ol>
        ) : null}
      </section>
    </form>
  );
}
