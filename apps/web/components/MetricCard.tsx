import { formatMetric } from "@/lib/dashboard";

export function MetricCard({
  label,
  value,
  detail,
}: {
  label: string;
  value: number | string | null | undefined;
  detail?: string;
}) {
  return (
    <section className="rounded-md border border-stone-300 bg-white p-5">
      <p className="text-sm font-medium text-steel">{label}</p>
      <p className="mt-2 text-3xl font-semibold text-ink">{formatMetric(value)}</p>
      {detail ? <p className="mt-2 text-sm text-stone-600">{detail}</p> : null}
    </section>
  );
}
