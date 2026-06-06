import { Shell } from "@/components/Shell";
import { getAuditEvents, getAuditSummary } from "@/lib/feedback";

export default async function AuditPage() {
  const [{ events }, summary] = await Promise.all([
    getAuditEvents({ limit: 20 }),
    getAuditSummary(),
  ]);
  const actionCounts = Object.entries(summary.counts_by_action).sort(([, a], [, b]) => b - a);

  return (
    <Shell>
      <h2 className="text-3xl font-semibold">Audit Log</h2>
      <p className="mt-3 max-w-3xl text-stone-700">
        Recent audit events covering query refusals, permission blocks, feedback submissions, and evaluation runs.
      </p>

      {actionCounts.length > 0 && (
        <section className="mt-6 grid gap-3 sm:grid-cols-2 md:grid-cols-3 xl:grid-cols-4">
          {actionCounts.map(([action, count]) => (
            <article key={action} className="rounded-md border border-stone-300 bg-white p-4">
              <p className="text-sm font-medium text-steel">{action.replaceAll("_", " ")}</p>
              <p className="mt-2 text-2xl font-semibold">{count}</p>
            </article>
          ))}
        </section>
      )}

      <section className="mt-8">
        <h3 className="mb-3 text-xl font-semibold">Recent Events</h3>
        {events.length === 0 ? (
          <div className="rounded-md border border-stone-300 bg-white p-5">
            <p className="text-stone-700">
              No audit events found. Events are logged automatically during queries, feedback submissions, and evaluation runs.
            </p>
          </div>
        ) : (
          <div className="overflow-x-auto rounded-md border border-stone-300 bg-white">
            <table className="w-full min-w-[800px] text-left text-sm">
              <thead className="bg-stone-100">
                <tr>
                  <th className="px-4 py-3">Time</th>
                  <th className="px-4 py-3">Action</th>
                  <th className="px-4 py-3">Role</th>
                  <th className="px-4 py-3">Resource</th>
                  <th className="px-4 py-3">Outcome</th>
                  <th className="px-4 py-3">Reason</th>
                </tr>
              </thead>
              <tbody>
                {events.map((event) => (
                  <tr key={event.id} className="border-t border-stone-200">
                    <td className="whitespace-nowrap px-4 py-3 text-stone-500">
                      {new Date(event.created_at).toLocaleString()}
                    </td>
                    <td className="whitespace-nowrap px-4 py-3 font-medium">
                      {event.action.replaceAll("_", " ")}
                    </td>
                    <td className="whitespace-nowrap px-4 py-3">{event.user_role}</td>
                    <td className="whitespace-nowrap px-4 py-3">{event.resource_type}</td>
                    <td className="px-4 py-3">
                      <span
                        className={`rounded border px-2 py-1 text-xs font-semibold ${
                          event.outcome === "success" || event.outcome === "completed" || event.outcome === "started"
                            ? "border-moss bg-white text-moss"
                            : event.outcome === "blocked" || event.outcome === "refused"
                            ? "border-rust bg-orange-50 text-rust"
                            : "border-stone-300 bg-stone-50 text-stone-700"
                        }`}
                      >
                        {event.outcome}
                      </span>
                    </td>
                    <td className="px-4 py-3 text-stone-600">{event.reason ?? "-"}</td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
        )}
      </section>
    </Shell>
  );
}
