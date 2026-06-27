import Link from "next/link";
import { Card } from "@/components/Card";
import { PageHeader } from "@/components/PageHeader";
import { SectionHeading } from "@/components/SectionHeading";
import { Shell } from "@/components/Shell";

const NORTHSTAR_PROJECT_ID = "00000000-0000-0000-0000-000000000019";
const PEOPLE_DEPARTMENT_ID = "00000000-0000-0000-0000-000000002001";

const projectHref = `/projects/${NORTHSTAR_PROJECT_ID}`;
const departmentHref = `${projectHref}/departments/${PEOPLE_DEPARTMENT_ID}`;
const scopedQuestion = "Where does Northstar Analytics have offices?";
const chatHref = `/chat?project=${NORTHSTAR_PROJECT_ID}&department=${PEOPLE_DEPARTMENT_ID}&question=${encodeURIComponent(scopedQuestion)}`;

const demoSteps = [
  {
    number: "1",
    title: "Open the project home",
    outcome: "Workspace map",
    detail: "Start with Northstar Analytics, then point out departments, representative documents, upload/indexing status, and scoped question chips.",
    href: projectHref,
    action: "Open project",
    tone: "moss",
  },
  {
    number: "2",
    title: "Inspect department knowledge",
    outcome: "Source evidence",
    detail: "Open People Operations to show document roles, active version metadata, extracted Markdown, upload review, and indexing state.",
    href: departmentHref,
    action: "Open department",
    tone: "steel",
  },
  {
    number: "3",
    title: "Ask with scope",
    outcome: "Cited answer",
    detail: "Use the scoped question link so chat opens with the project, department, and question already visible.",
    href: chatHref,
    action: "Ask scoped question",
    tone: "moss",
  },
  {
    number: "4",
    title: "Inspect why",
    outcome: "Answer proof",
    detail: "Open the chat proof panel to check citations, retrieved snippets, permission scope, confidence, and validation notes.",
    href: chatHref,
    action: "Open proof moment",
    tone: "steel",
  },
  {
    number: "5",
    title: "Show admin evidence",
    outcome: "Measured controls",
    detail: "Finish in Dev/Admin when a reviewer wants benchmark runs, permission safety, failed-question review, observability, or audit logs.",
    href: "/dev-admin",
    action: "Open Dev/Admin",
    tone: "rust",
  },
];

const proofItems = [
  {
    label: "Citations",
    detail: "Document and chunk references are shown next to the answer instead of hidden in logs.",
    tone: "moss",
  },
  {
    label: "Permission scope",
    detail: "Chat displays the demo role, project scope, department scope, and whether unauthorized chunks reached generation.",
    tone: "steel",
  },
  {
    label: "Confidence",
    detail: "Confidence is framed as answer-support or behavior confidence, depending on the response type.",
    tone: "rust",
  },
  {
    label: "Dev/Admin links",
    detail: "The App proof surface links to measured runs, permission safety, observability, and audit evidence without changing the answer.",
    tone: "moss",
  },
];

const toneStyles = {
  moss: {
    marker: "border-moss bg-moss-soft text-moss-dark",
    accent: "bg-moss",
    line: "bg-moss/50",
    panel: "border-moss bg-moss-soft/50",
    badge: "border-moss/30 bg-white/80 text-moss-dark",
  },
  steel: {
    marker: "border-steel bg-steel-soft text-steel-dark",
    accent: "bg-steel",
    line: "bg-steel/50",
    panel: "border-steel bg-steel-soft/60",
    badge: "border-steel/30 bg-white/80 text-steel-dark",
  },
  rust: {
    marker: "border-rust bg-rust-soft text-rust-dark",
    accent: "bg-rust",
    line: "bg-rust/50",
    panel: "border-rust bg-rust-soft/60",
    badge: "border-rust/30 bg-white/80 text-rust-dark",
  },
} as const;

export default function GuidedDemoPage() {
  return (
    <Shell>
      <PageHeader
        title="Guided Demo"
        description="Follow the short product path: project, department, upload/review, scoped ask, answer proof, then Dev/Admin evidence."
        actions={
          <>
            <Link href={projectHref} className="btn-primary">
              Start demo
            </Link>
            <Link href={chatHref} className="btn-secondary">
              Ask scoped question
            </Link>
          </>
        }
      />

      <section className="grid gap-5 xl:grid-cols-[minmax(0,1.2fr)_minmax(360px,0.8fr)]">
        <Card tone="good">
          <div className="flex flex-wrap items-start justify-between gap-4">
            <div>
              <p className="badge-good">Five-minute path</p>
              <h2 className="mt-3 text-2xl font-semibold text-ink">Tell the product story before the metrics story</h2>
              <p className="mt-3 max-w-3xl text-stone-700">
                This route keeps the recruiter demo grounded in visible App behavior, then hands off to Dev/Admin only when proof is needed.
              </p>
            </div>
            <Link href={projectHref} className="btn-primary">
              Start at Northstar
            </Link>
          </div>

          <ol className="mt-6 space-y-4">
            {demoSteps.map((step, index) => {
              const styles = toneStyles[step.tone as keyof typeof toneStyles];
              return (
                <li key={step.number} className={`relative rounded-md border p-4 ${styles.panel}`}>
                  {index < demoSteps.length - 1 ? (
                    <span aria-hidden="true" className={`absolute left-9 top-14 h-[calc(100%+1rem)] w-px ${styles.line}`} />
                  ) : null}
                  <div className="flex flex-wrap items-start justify-between gap-4">
                    <div className="flex min-w-0 gap-3">
                      <span className={`relative z-10 flex h-10 w-10 shrink-0 items-center justify-center rounded-full border-2 text-sm font-bold ${styles.marker}`}>
                        {step.number}
                      </span>
                      <div className="min-w-0">
                        <div className="flex flex-wrap items-center gap-2">
                          <p className="font-semibold text-ink">{step.title}</p>
                          <span className={`rounded border px-2 py-1 text-xs font-semibold uppercase tracking-wide ${styles.badge}`}>
                            {step.outcome}
                          </span>
                        </div>
                        <p className="mt-2 text-sm leading-6 text-stone-700">{step.detail}</p>
                      </div>
                    </div>
                    <Link href={step.href} className="btn-secondary btn-sm shrink-0">
                      {step.action}
                    </Link>
                  </div>
                </li>
              );
            })}
          </ol>
        </Card>

        <div className="space-y-5">
          <Card>
            <SectionHeading
              title="Proof Checklist"
              description="Use this when explaining why the answer is inspectable and permission-aware."
            />
            <div className="space-y-3">
              {proofItems.map((item) => (
                <div key={item.label} className="rounded-md border border-stone-200 bg-stone-50 p-3">
                  <div className="flex items-center gap-2">
                    <span className={`h-2.5 w-2.5 rounded-full ${toneStyles[item.tone as keyof typeof toneStyles].accent}`} />
                    <p className="font-semibold text-ink">{item.label}</p>
                  </div>
                  <p className="mt-1 text-sm leading-6 text-stone-700">{item.detail}</p>
                </div>
              ))}
            </div>
          </Card>

          <Card tone="warn">
            <p className="badge-warn">Honest limits</p>
            <ul className="mt-4 list-disc space-y-2 pl-5 text-sm leading-6 text-stone-700">
              <li>Local demo auth is not production SSO.</li>
              <li>Azure Blob Storage and hosted storage remain future work.</li>
              <li>AI Markdown cleanup starts in Phase 43 and must remain editor-triggered and reviewable.</li>
              <li>Metrics must be read with their run IDs, sample sizes, and skipped checks.</li>
            </ul>
          </Card>
        </div>
      </section>
    </Shell>
  );
}
