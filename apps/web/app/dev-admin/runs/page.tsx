import { Card } from "@/components/Card";
import { PageHeader } from "@/components/PageHeader";
import { RunTable } from "@/components/RunTable";
import { SectionHeading } from "@/components/SectionHeading";
import { Shell } from "@/components/Shell";
import { getDashboardData } from "@/lib/dashboard";
import { serverDemoAuthHeaders } from "@/lib/serverDemoAuth";

export default async function RunsPage() {
  const authHeaders = await serverDemoAuthHeaders();
  const data = await getDashboardData(authHeaders);

  return (
    <Shell>
      <PageHeader
        title="Run Comparison"
        description="Compare retrieval experiments, answer quality, permission safety, and memory evaluation using the same exported run format."
      />
      <RunTable runs={data.runs} bestRunName={data.overview.best_retrieval_run} />
      <section className="mt-8">
        <SectionHeading title="Comparison Notes" />
        <div className="grid gap-4 md:grid-cols-3">
          {Object.entries(data.comparisons).map(([key, comparison]) => (
            <Card key={key} as="article" padding="compact">
              <h4 className="font-semibold capitalize text-ink">{key.replaceAll("_", " ")}</h4>
              <p className="mt-2 text-sm text-stone-700">{comparison.summary}</p>
            </Card>
          ))}
        </div>
      </section>
    </Shell>
  );
}
