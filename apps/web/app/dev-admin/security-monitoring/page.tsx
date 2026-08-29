import { EmptyState } from "@/components/EmptyState";
import { MetricCard } from "@/components/MetricCard";
import { PageHeader } from "@/components/PageHeader";
import { SectionHeading } from "@/components/SectionHeading";
import { Shell } from "@/components/Shell";
import { getSecurityMonitoring } from "@/lib/securityMonitoring";
import { serverDemoAuthHeaders } from "@/lib/serverDemoAuth";

export default async function SecurityMonitoringPage() {
  const data = await getSecurityMonitoring(await serverDemoAuthHeaders());
  if (!data) {
    return <Shell><PageHeader title="Security Monitoring" /><EmptyState>Local monitoring is unavailable. Start the API and use the Admin demo user.</EmptyState></Shell>;
  }

  return (
    <Shell>
      <PageHeader
        title="Security Monitoring"
        description="Tenant-scoped, content-free security signals with a tamper-evident local event chain. This is portfolio evidence, not a connected SIEM or pager."
      />
      <section className="grid gap-4 sm:grid-cols-3">
        <MetricCard label="Recent tenant events" value={data.events.length} />
        <MetricCard label="Active local alerts" value={data.alerts.length} tone={data.alerts.length ? "warn" : "neutral"} />
        <MetricCard label="Local chain integrity" value={data.integrity.valid ? "Verified" : "Failed"} tone={data.integrity.valid ? "good" : "warn"} detail={`${data.integrity.record_count} chained records`} />
      </section>

      <section className="mt-8 rounded-md border border-amber-300 bg-amber-50 p-5 text-sm text-amber-950">
        <h2 className="font-semibold">External integration gate</h2>
        <ul className="mt-2 list-disc space-y-1 pl-5">{data.limitations.map((item) => <li key={item}>{item}</li>)}</ul>
      </section>

      <section className="mt-8">
        <SectionHeading title="Active alerts" />
        {data.alerts.length === 0 ? <EmptyState>No configured threshold is active for this tenant.</EmptyState> : (
          <div className="overflow-x-auto rounded-md border border-stone-300 bg-white"><table className="data-table min-w-[760px]"><thead><tr><th>Severity</th><th>Category</th><th>Count / window</th><th>Owner</th><th>Delivery</th></tr></thead><tbody>{data.alerts.map((alert) => <tr key={alert.alert_id}><td>{alert.severity}</td><td>{alert.category}</td><td>{alert.event_count} / {alert.window_minutes} min</td><td>{alert.owner}</td><td>{alert.notification_status.replaceAll("_", " ")}</td></tr>)}</tbody></table></div>
        )}
      </section>

      <section className="mt-8">
        <SectionHeading title="Recent content-free events" />
        {data.events.length === 0 ? <EmptyState>No security events have been recorded for this tenant.</EmptyState> : (
          <div className="overflow-x-auto rounded-md border border-stone-300 bg-white"><table className="data-table min-w-[900px]"><thead><tr><th>Time</th><th>Severity</th><th>Category</th><th>Action</th><th>Outcome</th><th>Reason</th><th>Correlation</th></tr></thead><tbody>{data.events.map((event) => <tr key={event.event_id}><td>{new Date(event.occurred_at).toLocaleString()}</td><td>{event.severity}</td><td>{event.category}</td><td>{event.action}</td><td>{event.outcome}</td><td>{event.reason_code ?? "-"}</td><td><code className="text-xs">{event.correlation_fingerprint ?? "not recorded"}</code></td></tr>)}</tbody></table></div>
        )}
      </section>

      <section className="mt-8">
        <SectionHeading title="Alert catalog" />
        <div className="grid gap-3 md:grid-cols-2">{data.taxonomy.map((rule) => <article key={rule.category} className="rounded-md border border-stone-300 bg-white p-4"><div className="flex justify-between gap-4"><h3 className="font-semibold">{rule.category.replaceAll("_", " ")}</h3><span className="text-sm uppercase text-stone-500">{rule.severity}</span></div><p className="mt-2 text-sm text-stone-600">Alert at {rule.threshold} event{rule.threshold === 1 ? "" : "s"} in {rule.window_minutes} minutes. Owner: {rule.owner}.</p></article>)}</div>
      </section>
    </Shell>
  );
}
