"use client";

import { FormEvent, useState } from "react";
import type { Citation, RetrievedChunk } from "@/lib/api";
import { createEvaluationReview } from "@/lib/reviews";
import type { CorrectnessLabel, ReviewDecision } from "@/lib/reviews";

const scoreOptions: Array<{ value: CorrectnessLabel; label: string }> = [
  { value: "1", label: "1.0 correct" },
  { value: "0.5", label: "0.5 partial" },
  { value: "0", label: "0.0 incorrect" },
];

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
      setNotes("");
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
    </form>
  );
}
