import { MetricCard } from "@/components/MetricCard";
import { RetrievalChart } from "@/components/RetrievalChart";
import { RunTable } from "@/components/RunTable";
import { Shell } from "@/components/Shell";
import { PageHeader } from "@/components/PageHeader";
import { Card } from "@/components/Card";
import { SectionHeading } from "@/components/SectionHeading";
import { getDashboardData } from "@/lib/dashboard";
import { serverDemoAuthHeaders } from "@/lib/serverDemoAuth";
import Link from "next/link";

const proofPath = [
  {
    title: "Algorithm comparison",
    detail: "Named profiles show historical metrics, live source coverage, citations, latency, cost signals, and review notes.",
    href: "/dev-admin/retrieval-playground",
  },
  {
    title: "Failure inspection",
    detail: "Failed benchmark questions keep expected answers, actual answers, citations, root causes, fixes, and human review labels together.",
    href: "/dev-admin/failed-questions",
  },
  {
    title: "Permission safety",
    detail: "Role-restricted questions demonstrate that unauthorized chunks do not reach generation.",
    href: "/dev-admin/permission-safety",
  },
];

export default async function OverviewPage() {
  const authHeaders = await serverDemoAuthHeaders();
  const data = await getDashboardData(authHeaders);
  const metrics = data.overview.headline_metrics;
  const progressSummary = data.overview.progress_summary ?? {
    improved: [
      "Permission tests reached zero leakage.",
      "Memory follow-up tests reached full accuracy.",
      "Chat-generation cost tracking is implemented.",
    ],
    still_needs_work: [
      "Hybrid retrieval still did not beat vector-only overall.",
      `${data.overview.current_failed_question_count ?? data.failed_questions.length} failed-question cases remain in the current improvement backlog.`,
      "Embedding, infrastructure, cached-input, and batch cost modeling remain pending.",
    ],
  };

  return (
    <Shell>
      <PageHeader
        title="Measured Enterprise RAG Progress"
        description={
          <>
            <p className="text-lg text-stone-800">
              A permission-aware enterprise RAG assistant with citations, confidence scoring, benchmark evaluation, and interactive demos.
            </p>
            <p className="mt-3 text-stone-700">
              This dashboard compares real evaluation runs across retrieval, answer quality, citations, permission safety, and memory.
            </p>
          </>
        }
        actions={
          <>
            <Link href="/chat" className="btn-primary">
              Try Chat Demo
            </Link>
            <Link href="/dev-admin/permission-demo" className="btn-secondary">
              Run Permission Demo
            </Link>
            <Link href="/dev-admin/retrieval-playground" className="btn-secondary">
              Open Algorithm Lab
            </Link>
          </>
        }
      />
      <section className="mb-8 grid gap-4 lg:grid-cols-[0.9fr_1.1fr]">
        <Card>
          <SectionHeading
            title="Proof Without Hiding Failures"
            description="Dev & Admin is the evidence layer behind the App demo: benchmark outputs, known misses, review decisions, and audit trails stay visible."
          />
          <p className="text-sm leading-6 text-stone-700">
            The App side shows a usable project workspace. This surface shows whether the assistant is safe enough to trust, where it still fails, and what evidence supports any retrieval or prompt change.
          </p>
        </Card>
        <div className="grid gap-4 md:grid-cols-3">
          {proofPath.map((item) => (
            <Card key={item.title} padding="compact" className="flex h-full flex-col justify-between">
              <div>
                <p className="font-semibold text-ink">{item.title}</p>
                <p className="mt-2 text-sm leading-6 text-stone-700">{item.detail}</p>
              </div>
              <Link href={item.href} className="btn-secondary btn-sm mt-4 self-start">
                Open
              </Link>
            </Card>
          ))}
        </div>
      </section>
      <section className="grid gap-4 md:grid-cols-2 xl:grid-cols-4">
        <MetricCard
          label="Source Recall"
          value={metrics.retrieval_hit_rate}
          detail="All expected sources retrieved."
          badge="Best"
          tone="good"
        />
        <MetricCard label="Precision@k" value={metrics.precision_at_k} detail="Expected-source chunks in top-k." />
        <MetricCard label="MRR / First Source Rank" value={metrics.mrr} detail="Rank quality for first expected source." />
        <MetricCard label="Answer Accuracy" value={metrics.answer_accuracy} detail="Deterministic answer scoring." />
        <MetricCard label="Citation Accuracy" value={metrics.citation_accuracy} detail="Citations match expected documents." />
        <MetricCard label="Hallucination Rate" value={metrics.hallucination_rate} detail="Unsupported-answer signal." badge="Risk" tone="warn" />
        <MetricCard label="Permission Leakage Rate" value={metrics.permission_leakage_rate} detail="Restricted-source leakage." badge="Safety" tone="good" />
        <MetricCard label="Memory Answer Accuracy" value={metrics.memory_accuracy} detail="Follow-up benchmark answers." tone="good" />
      </section>
      <Card tone="good" className="mt-8">
        <SectionHeading title="Experiment Conclusion" />
        <p className="text-stone-700">
          Vector retrieval with section-based chunks remains the best overall configuration; hybrid did not outperform it on this corpus.
        </p>
      </Card>
      <section className="mt-8 grid gap-4 lg:grid-cols-2">
        <RetrievalChart runs={data.runs} />
        <Card>
          <SectionHeading title="What Improved / Still Needs Work" />
          <div className="grid gap-4 md:grid-cols-2">
            <div>
              <p className="font-semibold text-moss-dark">Improved</p>
              <ul className="mt-2 space-y-2 text-sm text-stone-700">
                {progressSummary.improved.map((item) => (
                  <li key={item}>{item}</li>
                ))}
              </ul>
            </div>
            <div>
              <p className="font-semibold text-rust-dark">Still Needs Work</p>
              <ul className="mt-2 space-y-2 text-sm text-stone-700">
                {progressSummary.still_needs_work.map((item) => (
                  <li key={item}>{item}</li>
                ))}
              </ul>
            </div>
          </div>
        </Card>
      </section>
      <section className="mt-8">
        <SectionHeading title="Evaluation Runs" />
        <RunTable runs={data.runs} bestRunName={data.overview.best_retrieval_run} />
      </section>
    </Shell>
  );
}
