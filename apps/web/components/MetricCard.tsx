import { formatMetric } from "@/lib/dashboard";

export function MetricCard({
  label,
  value,
  detail,
  badge,
  tone = "neutral",
}: {
  label: string;
  value: number | string | null | undefined;
  detail?: string;
  badge?: string;
  tone?: "neutral" | "good" | "warn" | "risk";
}) {
  const styles = {
    neutral: { border: "border-stone-300", bg: "bg-white", value: "text-ink" },
    good: { border: "border-moss", bg: "bg-moss-soft", value: "text-moss-dark" },
    warn: { border: "border-rust", bg: "bg-rust-soft", value: "text-rust-dark" },
    risk: { border: "border-red-500", bg: "bg-red-50", value: "text-red-600" },
  }[tone];

  return (
    <section className={`rounded-md border ${styles.border} ${styles.bg} p-5 shadow-card`}>
      <div className="flex items-center justify-between gap-3">
        <p className="text-sm font-medium text-steel">{label}</p>
        {badge ? (
          <span className="rounded border border-stone-300 bg-white px-2 py-1 text-2xs font-semibold uppercase tracking-wide text-stone-700">
            {badge}
          </span>
        ) : null}
      </div>
      <p className={`mt-2 text-3xl font-semibold ${styles.value}`}>{formatMetric(value)}</p>
      {detail ? <p className="mt-2 text-sm text-stone-600">{detail}</p> : null}
    </section>
  );
}
