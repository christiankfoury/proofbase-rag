import { Badge, BadgeTone } from "@/components/Badge";
import { Card } from "@/components/Card";
import { EmptyState } from "@/components/EmptyState";
import { PageHeader } from "@/components/PageHeader";
import { SectionHeading } from "@/components/SectionHeading";
import { Shell } from "@/components/Shell";
import { getAuditEvents, getAuditSummary } from "@/lib/feedback";

function outcomeTone(outcome: string): BadgeTone {
  if (outcome === "success" || outcome === "completed" || outcome === "started") return "good";
  if (outcome === "blocked" || outcome === "refused") return "warn";
  return "neutral";
}

export default async function AuditPage() {
  const [{ events }, summary] = await Promise.all([
    getAuditEvents({ limit: 20 }),
    getAuditSummary(),
  ]);
  const actionCounts = Object.entries(summary.counts_by_action).sort(([, a], [, b]) => b - a);

  return (
    <Shell>
      <PageHeader
        title="Audit Log"
        description="Recent audit events covering query refusals, permission blocks, feedback submissions, and evaluation runs."
      />

      {actionCounts.length > 0 && (
        <section className="grid gap-3 sm:grid-cols-2 md:grid-cols-3 xl:grid-cols-4">
          {actionCounts.map(([action, count]) => (
            <Card key={action} as="article" padding="compact">
              <p className="text-sm font-medium text-steel">{action.replaceAll("_", " ")}</p>
              <p className="mt-2 text-2xl font-semibold text-ink">{count}</p>
            </Card>
          ))}
        </section>
      )}

      <section className="mt-8">
        <SectionHeading title="Recent Events" />
        {events.length === 0 ? (
          <EmptyState>
            No audit events found. Events are logged automatically during queries, feedback submissions, and evaluation runs.
          </EmptyState>
        ) : (
          <div className="overflow-x-auto rounded-md border border-stone-300 bg-white shadow-card">
            <table className="data-table min-w-[800px]">
              <thead>
                <tr>
                  <th>Time</th>
                  <th>Action</th>
                  <th>Role</th>
                  <th>Resource</th>
                  <th>Outcome</th>
                  <th>Reason</th>
                </tr>
              </thead>
              <tbody>
                {events.map((event) => (
                  <tr key={event.id}>
                    <td className="whitespace-nowrap text-stone-500">
                      {new Date(event.created_at).toLocaleString()}
                    </td>
                    <td className="whitespace-nowrap font-medium text-ink">
                      {event.action.replaceAll("_", " ")}
                    </td>
                    <td className="whitespace-nowrap">{event.user_role}</td>
                    <td className="whitespace-nowrap">{event.resource_type}</td>
                    <td>
                      <Badge tone={outcomeTone(event.outcome)}>{event.outcome}</Badge>
                    </td>
                    <td className="text-stone-600">{event.reason ?? "-"}</td>
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
