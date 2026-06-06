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
      <h2 className="text-3xl font-semibold">Feedback Overview</h2>
      <p className="mt-3 max-w-3xl text-stone-700">
        User ratings and category breakdown from live query feedback. Negative feedback can be exported as benchmark candidates via{" "}
        <code className="rounded bg-stone-100 px-1 py-0.5 text-sm">scripts/export_feedback_candidates.py</code>.
      </p>

      <section className="mt-6 grid gap-4 md:grid-cols-3">
        <article className="rounded-md border border-stone-300 bg-white p-5">
          <p className="text-sm font-semibold text-steel">Total Feedback</p>
          <p className="mt-3 text-3xl font-semibold">{summary.total}</p>
        </article>
        <article className="rounded-md border border-moss bg-white p-5">
          <p className="text-sm font-semibold text-steel">Thumbs Up</p>
          <p className="mt-3 text-3xl font-semibold">{summary.thumbs_up}</p>
        </article>
        <article className="rounded-md border border-rust bg-white p-5">
          <p className="text-sm font-semibold text-steel">Thumbs Down</p>
          <p className="mt-3 text-3xl font-semibold">{summary.thumbs_down}</p>
        </article>
      </section>

      {summary.total === 0 && (
        <section className="mt-8 rounded-md border border-stone-300 bg-white p-5">
          <p className="text-stone-700">
            No feedback submitted yet. Use <code className="rounded bg-stone-100 px-1 py-0.5 text-sm">POST /feedback</code> to submit ratings on answers.
          </p>
        </section>
      )}

      {categories.length > 0 && (
        <section className="mt-8">
          <h3 className="mb-3 text-xl font-semibold">Negative Category Breakdown</h3>
          <div className="overflow-x-auto rounded-md border border-stone-300 bg-white">
            <table className="w-full text-left text-sm">
              <thead className="bg-stone-100">
                <tr>
                  <th className="px-4 py-3">Category</th>
                  <th className="px-4 py-3 text-right">Count</th>
                </tr>
              </thead>
              <tbody>
                {categories.map(([cat, count]) => (
                  <tr key={cat} className="border-t border-stone-200">
                    <td className="px-4 py-3">{cat.replaceAll("_", " ")}</td>
                    <td className="px-4 py-3 text-right font-medium">{count}</td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
        </section>
      )}

      {negativeItems.length > 0 && (
        <section className="mt-8">
          <h3 className="mb-3 text-xl font-semibold">Recent Negative Feedback</h3>
          <div className="overflow-x-auto rounded-md border border-stone-300 bg-white">
            <table className="w-full min-w-[700px] text-left text-sm">
              <thead className="bg-stone-100">
                <tr>
                  <th className="px-4 py-3">Question</th>
                  <th className="px-4 py-3">Category</th>
                  <th className="px-4 py-3">Role</th>
                  <th className="px-4 py-3">Comment</th>
                  <th className="px-4 py-3">Date</th>
                </tr>
              </thead>
              <tbody>
                {negativeItems.map((item) => (
                  <tr key={item.feedback_id} className="border-t border-stone-200">
                    <td className="max-w-xs px-4 py-3 text-stone-700">{item.question.slice(0, 80)}{item.question.length > 80 ? "…" : ""}</td>
                    <td className="whitespace-nowrap px-4 py-3">
                      <span className="rounded border border-rust bg-orange-50 px-2 py-1 text-xs font-semibold text-rust">
                        {item.feedback_category.replaceAll("_", " ")}
                      </span>
                    </td>
                    <td className="whitespace-nowrap px-4 py-3">{item.user_role}</td>
                    <td className="max-w-xs px-4 py-3 text-stone-600">{item.user_comment ?? "-"}</td>
                    <td className="whitespace-nowrap px-4 py-3 text-stone-500">
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
