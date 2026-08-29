import Link from "next/link";
import { Card } from "@/components/Card";
import { MetricCard } from "@/components/MetricCard";
import { PageHeader } from "@/components/PageHeader";
import { SectionHeading } from "@/components/SectionHeading";
import { Shell } from "@/components/Shell";
import { defenseEvidence } from "@/lib/defenseEvidence";
import { releaseEvidence } from "@/lib/releaseEvidence";

const formatRate = (value: number) => `${(value * 100).toFixed(value === 0 ? 0 : 1)}%`;
const formatCost = (value: number) => `$${value.toFixed(6)}`;

export default function DefenseReadinessPage() {
  const unsafeOutcomes = defenseEvidence.stages.reduce((total, stage) => total + stage.unsafe_outcomes, 0);
  const parserFailures = defenseEvidence.stages.reduce((total, stage) => total + stage.parser_or_service_failures, 0);

  return (
    <Shell>
      <PageHeader
        title="Defense Readiness"
        description="One versioned view of request routing, evidence sufficiency, answer validation, permission gates, latency, cost, and known limitations."
        actions={<Link href="/trust" className="btn-secondary">Open public Trust page</Link>}
      />

      <Card tone="warn" className="mb-6">
        <p className="badge-warn">Development evidence only</p>
        <p className="mt-3 leading-7 text-stone-700">
          These suites were visible during implementation. They support local engineering claims, not production certification, unseen generalization, or an independent security assessment.
        </p>
      </Card>

      <section className="grid gap-4 sm:grid-cols-2 xl:grid-cols-5">
        <MetricCard label="Fixed-suite cases" value={defenseEvidence.manifest.sample_size} detail="Versioned Phase 52-54 manifest." />
        <MetricCard label="Runtime regression" value={`${defenseEvidence.runtime.sample_size}/${defenseEvidence.runtime.sample_size}`} detail={`${defenseEvidence.runtime.run_id}; benchmark ${defenseEvidence.runtime.benchmark_version}.`} tone="good" />
        <MetricCard label="Unsafe outcomes" value={unsafeOutcomes} detail="Across promoted fixed defense suites." tone="good" />
        <MetricCard label="Parser/service failures" value={parserFailures} detail="Promoted fixed-suite runs." tone="good" />
        <MetricCard label="Permission hard gates" value={defenseEvidence.hard_gates_passed ? "PASS" : "FAIL"} detail={`${defenseEvidence.permission.sample_size} paired permission checks.`} tone={defenseEvidence.hard_gates_passed ? "good" : "warn"} />
      </section>

      <section className="mt-8">
        <SectionHeading title="Defense Stage Outcomes" description="Bounded aggregate results; no user prompts, source text, memory text, or raw model output are stored here." />
        <div className="overflow-x-auto rounded-md border border-stone-300 bg-white shadow-card">
          <table className="data-table min-w-[1050px]">
            <thead><tr><th>Stage</th><th>Run</th><th className="text-right">n</th><th className="text-right">Accuracy</th><th className="text-right">False positive</th><th className="text-right">Unsafe</th><th className="text-right">Failures</th><th className="text-right">p50</th><th className="text-right">p95</th><th className="text-right">Cost</th></tr></thead>
            <tbody>
              {defenseEvidence.stages.map((stage) => (
                <tr key={stage.stage}>
                  <td className="font-semibold text-ink">{stage.stage}</td>
                  <td className="whitespace-nowrap text-stone-600">{stage.run_id}</td>
                  <td className="text-right">{stage.sample_size}</td>
                  <td className="text-right">{formatRate(stage.accuracy)}</td>
                  <td className="text-right">{formatRate(stage.false_positive_rate)}</td>
                  <td className="text-right">{stage.unsafe_outcomes}</td>
                  <td className="text-right">{stage.parser_or_service_failures}</td>
                  <td className="text-right">{stage.p50_latency_ms} ms</td>
                  <td className="text-right">{stage.p95_latency_ms} ms</td>
                  <td className="text-right">{formatCost(stage.estimated_cost_usd)}</td>
                </tr>
              ))}
            </tbody>
          </table>
        </div>
      </section>

      <section className="mt-8 grid gap-6 xl:grid-cols-2">
        <Card tone={defenseEvidence.hard_gates_passed ? "good" : "warn"}>
          <SectionHeading title="Hard Safety Gates" description="A non-zero observation blocks the consolidated defense claim." />
          <div className="grid gap-2">
            {defenseEvidence.hard_gates.map((gate) => (
              <div key={gate.name} className="flex flex-col gap-1 rounded border border-stone-300 bg-white p-3 sm:flex-row sm:items-center sm:justify-between">
                <div><p className="font-semibold text-ink">{gate.name}</p><p className="text-xs text-stone-500">Source: {gate.source}</p></div>
                <span className={gate.passed ? "badge-solid" : "badge-warn"}>{gate.passed ? "PASS" : "FAIL"} · observed {gate.observed}</span>
              </div>
            ))}
          </div>
        </Card>

        <Card>
          <SectionHeading title="Latency, Cost, And Repair" description="The definitive 130-question runtime result includes all three semantic controls." />
          <dl className="grid gap-3 sm:grid-cols-2">
            <div className="rounded border border-stone-300 p-3"><dt className="text-xs font-semibold uppercase text-stone-500">Control cost</dt><dd className="mt-1 text-xl font-semibold text-ink">{formatCost(defenseEvidence.runtime.control_cost_usd)}</dd></div>
            <div className="rounded border border-stone-300 p-3"><dt className="text-xs font-semibold uppercase text-stone-500">Generation + controls</dt><dd className="mt-1 text-xl font-semibold text-ink">{formatCost(defenseEvidence.runtime.generation_plus_control_cost_usd)}</dd></div>
            <div className="rounded border border-stone-300 p-3"><dt className="text-xs font-semibold uppercase text-stone-500">Bounded repairs</dt><dd className="mt-1 text-xl font-semibold text-ink">{defenseEvidence.runtime.repair_count}</dd></div>
            <div className="rounded border border-stone-300 p-3"><dt className="text-xs font-semibold uppercase text-stone-500">Final downgrades</dt><dd className="mt-1 text-xl font-semibold text-ink">{defenseEvidence.runtime.final_downgrade_count}</dd></div>
          </dl>
          <div className="mt-4 rounded border border-steel bg-steel-soft/50 p-3 text-sm leading-6 text-steel-dark">
            Stability: {defenseEvidence.stability.passes}/{defenseEvidence.stability.attempts} deterministic summary passes. This does not claim semantic-model stability.
          </div>
        </Card>
      </section>

      <Card tone={releaseEvidence.production_promotion_allowed ? "good" : "warn"} className="mt-8">
        <SectionHeading title="Phase 63 Release Decision" description={`Exact runtime ${releaseEvidence.runtime_commit.slice(0, 12)}; ${releaseEvidence.deterministic_checks.check_count} deterministic checks.`} />
        <div className="grid gap-3 sm:grid-cols-3">
          <MetricCard label="Portfolio controls" value={releaseEvidence.portfolio_release_controls_ready ? "READY" : "BLOCKED"} tone={releaseEvidence.portfolio_release_controls_ready ? "good" : "warn"} />
          <MetricCard label="Hard security gates" value={releaseEvidence.hard_security_gates.passed ? "PASS" : "FAIL"} tone={releaseEvidence.hard_security_gates.passed ? "good" : "risk"} />
          <MetricCard label="Production promotion" value={releaseEvidence.production_promotion_allowed ? "ALLOWED" : "BLOCKED"} tone={releaseEvidence.production_promotion_allowed ? "good" : "warn"} />
        </div>
        <ul className="mt-4 list-disc space-y-1 pl-5 text-sm text-stone-700">
          {releaseEvidence.production_blockers.map((blocker) => <li key={blocker}>{blocker.replaceAll("_", " ")}</li>)}
        </ul>
        <p className="mt-4 text-sm leading-6 text-stone-600">{releaseEvidence.claim_boundary}</p>
      </Card>

      <Card className="mt-8">
        <SectionHeading title="Known Limits And Next Gate" />
        <ul className="list-disc space-y-2 pl-5 text-sm leading-6 text-stone-700">
          {defenseEvidence.limitations.map((limitation) => <li key={limitation}>{limitation}</li>)}
        </ul>
        <p className="mt-4 rounded border border-rust bg-rust-soft/40 p-3 text-sm leading-6 text-rust-dark">
          The {defenseEvidence.holdout.case_count}-case Phase 55 holdout is {defenseEvidence.holdout.status.replaceAll("_", " ")} against runtime {defenseEvidence.holdout.frozen_runtime_commit?.slice(0, 7)} and supports no current claim. A future claim requires a newly authored post-freeze suite; live identity, monitoring, availability evidence, human review, and independent validation remain external gates.
        </p>
      </Card>
    </Shell>
  );
}
