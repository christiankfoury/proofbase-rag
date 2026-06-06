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
  const toneClass = {
    neutral: "border-stone-300",
    good: "border-moss bg-white",
    warn: "border-rust bg-white",
    risk: "border-red-500 bg-white",
  }[tone];

  return (
    <section className={`rounded-md border ${toneClass} p-5`}>
      <div className="flex items-center justify-between gap-3">
        <p className="text-sm font-medium text-steel">{label}</p>
        {badge ? <span className="rounded border border-stone-300 px-2 py-1 text-xs font-semibold text-stone-700">{badge}</span> : null}
      </div>
      <p className="mt-2 text-3xl font-semibold text-ink">{formatMetric(value)}</p>
      {detail ? <p className="mt-2 text-sm text-stone-600">{detail}</p> : null}
    </section>
  );
}
