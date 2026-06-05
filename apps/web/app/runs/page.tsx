import { RunTable } from "@/components/RunTable";
import { Shell } from "@/components/Shell";
import { getDashboardData } from "@/lib/dashboard";

export default async function RunsPage() {
  const data = await getDashboardData();

  return (
    <Shell>
      <h2 className="text-3xl font-semibold">Run Comparison</h2>
      <p className="mt-3 max-w-3xl text-stone-700">
        Compare retrieval experiments, answer quality, permission safety, and memory evaluation using the same exported run format.
      </p>
      <div className="mt-6">
        <RunTable runs={data.runs} />
      </div>
      <section className="mt-8 grid gap-4 md:grid-cols-3">
        {Object.entries(data.comparisons).map(([key, comparison]) => (
          <article key={key} className="rounded-md border border-stone-300 bg-white p-5">
            <h3 className="font-semibold">{key.replaceAll("_", " ")}</h3>
            <p className="mt-2 text-sm text-stone-700">{comparison.summary}</p>
          </article>
        ))}
      </section>
    </Shell>
  );
}
