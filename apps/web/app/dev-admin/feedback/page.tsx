import { Badge } from "@/components/Badge";
import { EmptyState } from "@/components/EmptyState";
import { MetricCard } from "@/components/MetricCard";
import { PageHeader } from "@/components/PageHeader";
import { SectionHeading } from "@/components/SectionHeading";
import { Shell } from "@/components/Shell";
import { getFeedback, getFeedbackSummary } from "@/lib/feedback";

export default async function FeedbackPage() {
  const [summary, { feedback: negativeItems }] = await Promise.all([
    getFeedbackSummary(),
    getFeedback({ rating: "thumbs_down", limit: 20 }),
  ]);
  const categories = Object.entries(summary.negative_category_breakdown).sort(([, a], [, b]) => b - a);

  return (
    <Shell>
      <PageHeader
        title="Feedback Overview"
        description={
          <>
            User ratings and category breakdown from live query feedback. Negative feedback can be exported as benchmark candidates via{" "}
            <code className="rounded bg-stone-100 px-1 py-0.5 text-sm">scripts/export_feedback_candidates.py</code>.
          </>
        }
      />

      <section className="grid gap-4 md:grid-cols-3">
        <MetricCard label="Total Feedback" value={summary.total} />
        <MetricCard label="Thumbs Up" value={summary.thumbs_up} tone="good" />
        <MetricCard label="Thumbs Down" value={summary.thumbs_down} tone={summary.thumbs_down > 0 ? "warn" : "neutral"} />
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
          <SectionHeading title="Recent Negative Feedback" />
          <div className="overflow-x-auto rounded-md border border-stone-300 bg-white shadow-card">
            <table className="data-table min-w-[700px]">
              <thead>
                <tr>
                  <th>Question</th>
                  <th>Category</th>
                  <th>Role</th>
                  <th>Comment</th>
                  <th>Date</th>
                </tr>
              </thead>
              <tbody>
                {negativeItems.map((item) => (
                  <tr key={item.feedback_id}>
                    <td className="max-w-xs text-stone-700">{item.question.slice(0, 80)}{item.question.length > 80 ? "…" : ""}</td>
                    <td className="whitespace-nowrap">
                      <Badge tone="warn">{item.feedback_category.replaceAll("_", " ")}</Badge>
                    </td>
                    <td className="whitespace-nowrap">{item.user_role}</td>
                    <td className="max-w-xs text-stone-600">{item.user_comment ?? "-"}</td>
                    <td className="whitespace-nowrap text-stone-500">
                      {new Date(item.created_at).toLocaleDateString()}
                    </td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
          <p className="mt-3 text-sm text-stone-500">
            Run <code className="rounded bg-stone-100 px-1 py-0.5">python scripts/export_feedback_candidates.py</code> to export these as benchmark review candidates.
          </p>
        </section>
      )}
    </Shell>
  );
}
