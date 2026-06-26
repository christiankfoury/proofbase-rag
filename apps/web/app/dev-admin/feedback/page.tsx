import { EmptyState } from "@/components/EmptyState";
import { MetricCard } from "@/components/MetricCard";
import { PageHeader } from "@/components/PageHeader";
import { SectionHeading } from "@/components/SectionHeading";
import { Shell } from "@/components/Shell";
import { getFeedback, getFeedbackSummary } from "@/lib/feedback";
import { serverDemoAuthHeaders } from "@/lib/serverDemoAuth";
import { FeedbackReviewClient } from "./FeedbackReviewClient";

export default async function FeedbackPage() {
  const authHeaders = await serverDemoAuthHeaders();
  const [summary, { feedback: negativeItems }] = await Promise.all([
    getFeedbackSummary(authHeaders),
    getFeedback({ rating: "thumbs_down", limit: 20 }, authHeaders),
  ]);
  const categories = Object.entries(summary.negative_category_breakdown).sort(([, a], [, b]) => b - a);

  return (
    <Shell>
      <PageHeader
        title="Feedback Overview"
        description="User ratings and category breakdown from live query feedback. Negative feedback can become evaluation candidates only after human review."
      />

      <section className="grid gap-4 md:grid-cols-3">
        <MetricCard label="Total Feedback" value={summary.total} format="integer" />
        <MetricCard label="Thumbs Up" value={summary.thumbs_up} tone="good" format="integer" />
        <MetricCard label="Thumbs Down" value={summary.thumbs_down} tone={summary.thumbs_down > 0 ? "warn" : "neutral"} format="integer" />
      </section>

      {summary.total === 0 && (
        <div className="mt-8">
          <EmptyState>
            No feedback submitted yet. Use <code className="rounded bg-stone-100 px-1 py-0.5 text-sm">POST /feedback</code> to submit ratings on answers.
          </EmptyState>
        </div>
      )}

      {categories.length > 0 && (
        <section className="mt-8">
          <SectionHeading title="Negative Category Breakdown" />
          <div className="overflow-x-auto rounded-md border border-stone-300 bg-white shadow-card">
            <table className="data-table">
              <thead>
                <tr>
                  <th>Category</th>
                  <th className="text-right">Count</th>
                </tr>
              </thead>
              <tbody>
                {categories.map(([cat, count]) => (
                  <tr key={cat}>
                    <td>{cat.replaceAll("_", " ")}</td>
                    <td className="text-right font-medium text-ink">{count}</td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
        </section>
      )}

      {negativeItems.length > 0 && (
        <section className="mt-8">
          <SectionHeading title="Negative Feedback Review" />
          <FeedbackReviewClient items={negativeItems} />
          <p className="mt-3 text-sm text-stone-500">
            Save a review with decision <span className="font-semibold">Evaluation candidate</span> before adding feedback to benchmark work. Nothing is auto-promoted.
          </p>
        </section>
      )}
    </Shell>
  );
}
