"use client";

import { useState } from "react";
import { Badge } from "@/components/Badge";
import { EvaluationReviewPanel } from "@/components/EvaluationReviewPanel";
import type { FeedbackItem } from "@/lib/feedback";

export function FeedbackReviewClient({ items }: { items: FeedbackItem[] }) {
  const [expanded, setExpanded] = useState<string | null>(items[0]?.feedback_id ?? null);

  if (!items.length) return null;

  return (
    <div className="space-y-3">
      {items.map((item) => {
        const isOpen = expanded === item.feedback_id;
        return (
          <article key={item.feedback_id} className="rounded-md border border-stone-300 bg-white shadow-card">
            <button
              type="button"
              onClick={() => setExpanded(isOpen ? null : item.feedback_id)}
              className="w-full p-4 text-left focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-moss"
            >
              <div className="flex flex-wrap items-start justify-between gap-3">
                <div>
                  <div className="flex flex-wrap items-center gap-2">
                    <Badge tone="warn">{item.feedback_category.replaceAll("_", " ")}</Badge>
                    <span className="text-xs text-stone-500">{new Date(item.created_at).toLocaleDateString()}</span>
                  </div>
                  <p className="mt-2 max-w-4xl text-sm font-semibold text-ink">{item.question}</p>
                  <p className="mt-1 text-xs text-stone-600">{item.user_comment ?? "No reviewer comment submitted with feedback."}</p>
                </div>
                <p className="text-sm text-stone-600">{item.user_role}</p>
              </div>
            </button>
            {isOpen ? (
              <div className="border-t border-stone-200 p-4">
                <div className="grid gap-4 lg:grid-cols-2">
                  <section>
                    <h4 className="font-semibold text-ink">Answer Under Review</h4>
                    <p className="mt-2 text-sm leading-6 text-stone-700">{item.answer}</p>
                  </section>
                  <section>
                    <h4 className="font-semibold text-ink">Feedback Context</h4>
                    <dl className="mt-2 grid gap-2 text-sm text-stone-700">
                      <div><dt className="font-semibold text-ink">Response type</dt><dd>{item.response_type ?? "n/a"}</dd></div>
                      <div><dt className="font-semibold text-ink">Message</dt><dd>{item.message_id ?? "n/a"}</dd></div>
                    </dl>
                  </section>
                </div>
                <div className="mt-4">
                  <h4 className="mb-2 font-semibold text-ink">Human Review Decision</h4>
                  <EvaluationReviewPanel
                    sourceType="feedback"
                    sourceId={item.feedback_id}
                    question={item.question}
                    answer={item.answer}
                    actualCitations={item.citations_json}
                  />
                </div>
              </div>
            ) : null}
          </article>
        );
      })}
    </div>
  );
}
