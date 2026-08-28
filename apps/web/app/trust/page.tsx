import Link from "next/link";
import type { LucideIcon } from "lucide-react";
import {
  Activity,
  AlertTriangle,
  Brain,
  CheckCircle2,
  ClipboardCheck,
  FileWarning,
  Fingerprint,
  Gauge,
  KeyRound,
  LockKeyhole,
  ScanSearch,
  SearchCheck,
  ServerCog,
  ShieldCheck,
  Siren,
} from "lucide-react";
import { Card } from "@/components/Card";
import { PageHeader } from "@/components/PageHeader";
import { SectionHeading } from "@/components/SectionHeading";
import { Shell } from "@/components/Shell";
import {
  currentDefenseCatalog,
  defenseLifecycle,
  defenseStatusCatalog,
  productionReadinessCatalog,
} from "@/lib/defenseCatalog";
import type { DefenseCatalogItem, DefenseStatus } from "@/lib/defenseCatalog";
import { defenseEvidence, defenseStage } from "@/lib/defenseEvidence";

const controlIcons: Record<string, LucideIcon> = {
  ambiguity: ScanSearch,
  "direct-injection": AlertTriangle,
  "source-injection": FileWarning,
  "permission-filtering": LockKeyhole,
  memory: Brain,
  "semantic-request-assessment": Activity,
  "evidence-sufficiency": SearchCheck,
  "citation-validation": CheckCircle2,
  "audit-evidence": ClipboardCheck,
  "production-identity": Fingerprint,
  "database-authorization": KeyRound,
  "abuse-controls": Gauge,
  "secure-files": FileWarning,
  "secrets-privacy": LockKeyhole,
  "monitoring-response": Siren,
  "penetration-test": ShieldCheck,
  "release-gates": ServerCog,
};

const statusStyles: Record<DefenseStatus, string> = {
  implemented: "border-moss bg-moss-soft text-moss-dark",
  measured: "border-steel bg-steel-soft text-steel-dark",
  planned: "border-stone-300 bg-stone-100 text-stone-700",
  production_dependency: "border-rust bg-rust-soft text-rust-dark",
  independent_validation_required: "border-red-300 bg-red-50 text-red-800",
};

function StatusBadge({ status }: { status: DefenseStatus }) {
  return (
    <span className={`rounded border px-2.5 py-1 text-xs font-semibold uppercase tracking-wide ${statusStyles[status]}`}>
      {defenseStatusCatalog[status].label}
    </span>
  );
}

function ControlCard({ item }: { item: DefenseCatalogItem }) {
  const Icon = controlIcons[item.id] ?? ShieldCheck;
  return (
    <article className="rounded-md border border-stone-300 bg-white p-5 shadow-card">
      <div className="flex flex-col gap-3 sm:flex-row sm:items-start sm:justify-between">
        <div className="flex min-w-0 items-start gap-3">
          <span className="inline-flex h-10 w-10 shrink-0 items-center justify-center rounded border border-moss bg-moss-soft text-moss-dark">
            <Icon className="h-5 w-5" aria-hidden="true" />
          </span>
          <div>
            <p className="text-xs font-semibold uppercase tracking-wide text-stone-500">{item.phase}</p>
            <h3 className="mt-1 text-lg font-semibold text-ink">{item.title}</h3>
          </div>
        </div>
        <StatusBadge status={item.status} />
      </div>

      <p className="mt-4 leading-7 text-stone-700">{item.summary}</p>
      <div className="mt-4 rounded border border-moss/40 bg-moss-soft/40 p-3">
        <p className="text-xs font-semibold uppercase tracking-wide text-moss-dark">Control boundary</p>
        <p className="mt-1 text-sm leading-6 text-stone-700">{item.boundary}</p>
      </div>

      {item.evidence.length ? (
        <div className="mt-4">
          <h4 className="text-sm font-semibold text-ink">Evidence</h4>
          <div className="mt-2 grid gap-2">
            {item.evidence.map((evidence) => (
              <Link
                key={`${item.id}-${evidence.label}`}
                href={evidence.href}
                className="rounded border border-stone-300 bg-stone-50 px-3 py-2 transition-colors hover:border-moss hover:bg-moss-soft/40 focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-moss focus-visible:ring-offset-2"
              >
                <span className="block text-sm font-semibold text-moss-dark">{evidence.label}</span>
                <span className="mt-1 block text-xs leading-5 text-stone-600">{evidence.detail}</span>
              </Link>
            ))}
          </div>
        </div>
      ) : (
        <p className="mt-4 rounded border border-dashed border-stone-300 bg-stone-50 p-3 text-sm text-stone-600">
          No implementation evidence yet. This item remains {defenseStatusCatalog[item.status].label.toLowerCase()}.
        </p>
      )}

      <details className="group mt-4 rounded border border-stone-300 bg-white p-3">
        <summary className="cursor-pointer list-none text-sm font-semibold text-ink focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-moss">
          Limitations and verification
        </summary>
        <ul className="mt-3 list-disc space-y-2 pl-5 text-sm leading-6 text-stone-700">
          {item.limitations.map((limitation) => <li key={limitation}>{limitation}</li>)}
        </ul>
        <p className="mt-3 border-t border-stone-200 pt-3 text-xs text-stone-500">Last verified: {item.last_verified}</p>
      </details>
    </article>
  );
}

export default function TrustAndSafetyPage() {
  return (
    <Shell>
      <PageHeader
        title="Trust & Safety"
        description={
          <p className="text-lg text-stone-800">
            A plain-language account of what protects a Proofbase answer today, what has been measured, and what still blocks a production-security claim.
          </p>
        }
        actions={
          <>
            <Link href="/algorithm" className="btn-primary">Open algorithm guide</Link>
            <Link href="/dev-admin/permission-safety" className="btn-secondary">Inspect safety evidence</Link>
          </>
        }
      />

      <div className="grid gap-6">
        <Card tone="warn" className="overflow-hidden">
          <div className="grid gap-5 lg:grid-cols-[1.35fr_0.65fr] lg:items-start">
            <div>
              <p className="badge-warn">Local demo boundary</p>
              <h2 className="mt-3 text-2xl font-semibold text-ink">Useful defenses, not a production security certification</h2>
              <p className="mt-3 leading-7 text-stone-700">
                Proofbase uses local demo identity and synthetic enterprise data by default. Its OIDC-compatible tenant boundary and local signed-token tests provide engineering evidence, but they are not a connected production identity provider, database-enforced tenant isolation, operational monitoring, or an independent security assessment.
              </p>
            </div>
            <div className="rounded-md border border-rust bg-white p-4 shadow-card">
              <p className="text-xs font-semibold uppercase tracking-wide text-rust-dark">Hard confidentiality rule</p>
              <p className="mt-2 font-semibold text-ink">Models do not grant access.</p>
              <p className="mt-2 text-sm leading-6 text-stone-700">
                Identity, scope, membership, and role filters remain independent of request classifiers, prompts, confidence scores, and citations.
              </p>
            </div>
          </div>
        </Card>

        <Card>
          <SectionHeading
            title="Layered Request Flow"
            description="The target flow separates intent routing, authorization, evidence sufficiency, generation, and validation so no single model decision becomes the security boundary."
          />
          <ol className="grid gap-3 md:grid-cols-2 xl:grid-cols-7">
            {defenseLifecycle.map(([number, title, detail]) => (
              <li key={number} className="rounded-md border border-stone-300 bg-stone-50 p-4">
                <span className="inline-flex h-8 min-w-8 items-center justify-center rounded border border-moss bg-moss-soft px-2 text-xs font-semibold text-moss-dark">{number}</span>
                <h3 className="mt-3 font-semibold text-ink">{title}</h3>
                <p className="mt-2 text-sm leading-6 text-stone-700">{detail}</p>
              </li>
            ))}
          </ol>
          <p className="mt-4 rounded border border-steel bg-steel-soft/60 p-3 text-sm leading-6 text-steel-dark">
            Steps 2, 5, and 7 are implemented and measured in Phases 52-54. Phase 56 adds the local identity/tenant boundary; hosted identity, database authorization, operational monitoring, and independent validation remain separate dependencies rather than implied model capabilities.
          </p>
        </Card>

        <Card tone="good">
          <SectionHeading
            title="How To Read Control Status"
            description="The catalog uses one code-owned vocabulary so future work cannot look complete by accident."
          />
          <div className="grid gap-3 md:grid-cols-2 xl:grid-cols-5">
            {(Object.entries(defenseStatusCatalog) as Array<[DefenseStatus, (typeof defenseStatusCatalog)[DefenseStatus]]>).map(([status, definition]) => (
              <article key={status} className="rounded border border-stone-300 bg-white p-3">
                <StatusBadge status={status} />
                <p className="mt-3 text-sm leading-6 text-stone-700">{definition.explanation}</p>
              </article>
            ))}
          </div>
        </Card>

        <section aria-labelledby="current-defenses-heading">
          <SectionHeading
            title="Current Answer Defenses"
            description="Each item states what the control does, where its authority stops, the evidence behind the claim, and the remaining limitation."
          />
          <h2 id="current-defenses-heading" className="sr-only">Current answer defenses catalog</h2>
          <div className="grid gap-4 xl:grid-cols-2">
            {currentDefenseCatalog.map((item) => <ControlCard key={item.id} item={item} />)}
          </div>
        </section>

        <Card tone="good">
          <div className="flex flex-col gap-3 sm:flex-row sm:items-start sm:justify-between">
            <SectionHeading
              title="Measured Evidence Snapshot"
              description="Development results are named and scoped; sealed holdout evidence remains separate and unchanged."
              className="mb-0"
            />
            <span className="badge-solid shrink-0">Verified {defenseEvidence.last_verified}</span>
          </div>
          <div className="mt-5 grid gap-3 md:grid-cols-2 xl:grid-cols-4">
            {[
              [`${defenseEvidence.runtime.sample_size} / ${defenseEvidence.runtime.sample_size}`, `Current benchmark ${defenseEvidence.runtime.benchmark_version}`, "Known development regression, not unseen generalization proof."],
              [`${defenseStage("Request assessment").sample_size} / ${defenseStage("Request assessment").sample_size}`, "Request assessment", `Fixed development suite; ${defenseStage("Request assessment").unsafe_outcomes} unsafe outcomes.`],
              [`${Math.round(defenseStage("Post-generation validation").accuracy * defenseStage("Post-generation validation").sample_size)} / ${defenseStage("Post-generation validation").sample_size}`, "Answer validator", `Fixed development suite; ${defenseStage("Post-generation validation").unsafe_outcomes} unsafe outcomes.`],
              [defenseEvidence.hard_gates.filter((gate) => !gate.passed).length.toString(), "Defense hard-gate failures", `${defenseEvidence.hard_gates.length} consolidated Phase 55 hard gates.`],
            ].map(([value, label, detail]) => (
              <article key={label} className="rounded border border-moss bg-white p-4 shadow-card">
                <p className="text-2xl font-semibold text-moss-dark">{value}</p>
                <h3 className="mt-2 font-semibold text-ink">{label}</h3>
                <p className="mt-2 text-sm leading-6 text-stone-700">{detail}</p>
              </article>
            ))}
          </div>
          <div className="mt-4 flex flex-wrap gap-2">
            <Link href="/dev-admin/runs" className="btn-secondary">Compare named runs</Link>
            <Link href="/dev-admin/failed-questions" className="btn-secondary">Review known failures</Link>
            <Link href="/dev-admin/permission-safety" className="btn-secondary">Open permission evidence</Link>
            <Link href="/dev-admin/defense-readiness" className="btn-secondary">Open defense readiness</Link>
          </div>
        </Card>

        <section aria-labelledby="production-readiness-heading">
          <SectionHeading
            title="Production-Shaped Readiness Checklist"
            description="Phases 56-63 implement production-shaped controls locally first; cloud integrations and independent validation remain optional, separately approved evidence."
          />
          <h2 id="production-readiness-heading" className="sr-only">Production-shaped readiness control catalog</h2>
          <div className="grid gap-4 xl:grid-cols-2">
            {productionReadinessCatalog.map((item) => <ControlCard key={item.id} item={item} />)}
          </div>
        </section>
      </div>
    </Shell>
  );
}
