import { PageHeader } from "@/components/PageHeader";
import { Shell } from "@/components/Shell";
import { getDashboardData } from "@/lib/dashboard";
import { serverDemoAuthHeaders } from "@/lib/serverDemoAuth";
import { RetrievalPlaygroundClient } from "./RetrievalPlaygroundClient";

export default async function RetrievalPlaygroundPage() {
  const authHeaders = await serverDemoAuthHeaders();
  const data = await getDashboardData(authHeaders);
  const historicalRuns = data.runs.filter((run) => run.phase === "phase-6");

  return (
    <Shell>
      <PageHeader
        title="Algorithm Quality Lab"
        description="Compare named retrieval profiles with real historical metrics, live source coverage, citations, latency, cost, and known failure visibility."
      />
      <RetrievalPlaygroundClient historicalRuns={historicalRuns} failures={data.failed_questions} />
    </Shell>
  );
}
