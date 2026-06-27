import Link from "next/link";
import { Card } from "@/components/Card";
import { PageHeader } from "@/components/PageHeader";
import { SectionHeading } from "@/components/SectionHeading";
import { Shell } from "@/components/Shell";

const nextCapabilities = [
  {
    title: "Scoped Assistant",
    label: "Project scope",
    detail: "Ask across a workspace or narrow to one department while preserving role-based filtering.",
  },
  {
    title: "Document Library",
    label: "Source review",
    detail: "Review indexed documents and PDF extraction output before approving future uploads.",
  },
  {
    title: "Algorithm Verification",
    label: "Measured quality",
    detail: "Promote retrieval and prompt changes only after evaluation proves the result improved.",
  },
];

const heroActions = [
  {
    title: "Follow the guided demo",
    detail: "Walk project -> department -> upload/review -> scoped answer -> proof in a few minutes.",
    href: "/demo",
    action: "Start guide",
    tone: "moss",
  },
  {
    title: "Open the workspace",
    detail: "Review Northstar Analytics coverage, departments, and indexed source quality.",
    href: "/projects",
    action: "Open projects",
    tone: "steel",
  },
  {
    title: "Ask with scope",
    detail: "Query the assistant with project and department context before checking citations.",
    href: "/chat",
    action: "Ask assistant",
    tone: "moss",
  },
  {
    title: "Prove the controls",
    detail: "Inspect permission behavior, failed questions, evaluations, and audit evidence.",
    href: "/dev-admin",
    action: "View proof",
    tone: "rust",
  },
];

const proofPoints = [
  {
    label: "Permission filtering",
    detail: "Restricted chunks are filtered before generation.",
    tone: "moss",
  },
  {
    label: "Citations",
    detail: "Answers expose sources, confidence, and validation signals.",
    tone: "steel",
  },
  {
    label: "Evaluations",
    detail: "Retrieval, answer quality, memory, and permission checks are benchmarked.",
    tone: "rust",
  },
  {
    label: "Audit logs",
    detail: "Dev & Admin views surface failures, feedback, cost, and audit events.",
    tone: "moss",
  },
];

const demoPath = [
  {
    step: "1",
    title: "Open Northstar Analytics",
    outcome: "Workspace context",
    detail: "Show a durable project with seeded departments, documents, and quality status.",
    href: "/projects",
    action: "Projects",
    tone: "moss",
  },
  {
    step: "2",
    title: "Inspect Department Knowledge",
    outcome: "Indexed evidence",
    detail: "Review source documents, access roles, and extraction metadata before asking.",
    href: "/projects/00000000-0000-0000-0000-000000000019/departments/00000000-0000-0000-0000-000000002001",
    action: "Department",
    tone: "steel",
  },
  {
    step: "3",
    title: "Ask With Scope",
    outcome: "Cited answer",
    detail: "Ask with project and department scope, then inspect citations and retrieved context.",
    href: "/chat",
    action: "Assistant",
    tone: "moss",
  },
  {
    step: "4",
    title: "Prove The Controls",
    outcome: "Admin proof",
    detail: "Move to Dev & Admin for comparison, failed-question review, and permission safety.",
    href: "/dev-admin",
    action: "Dev & Admin",
    tone: "rust",
  },
];

const toneStyles = {
  moss: {
    marker: "border-moss bg-moss-soft text-moss-dark",
    accent: "bg-moss",
    panel: "border-moss bg-moss-soft/50",
  },
  steel: {
    marker: "border-steel bg-steel-soft text-steel-dark",
    accent: "bg-steel",
    panel: "border-steel bg-steel-soft/60",
  },
  rust: {
    marker: "border-rust bg-rust-soft text-rust-dark",
    accent: "bg-rust",
    panel: "border-rust bg-rust-soft/60",
  },
} as const;

export default function AppHomePage() {
  return (
    <Shell>
      <PageHeader
        title="Enterprise Knowledge Assistant"
        description={
          <>
            <p className="text-lg text-stone-800">
              A permission-aware internal assistant for asking questions across company knowledge with citations, confidence, and safe refusal behavior.
            </p>
          </>
        }
        actions={
          <>
            <Link href="/projects" className="btn-primary">
              Open projects
            </Link>
            <Link href="/demo" className="btn-secondary">
              Guided demo
            </Link>
            <Link href="/chat" className="btn-secondary">
              Ask the assistant
            </Link>
            <Link href="/dev-admin" className="btn-secondary">
              View Dev & Admin proof
            </Link>
          </>
        }
      />

      <section className="grid gap-5 xl:grid-cols-[1.1fr_0.9fr]">
        <Card tone="good" className="overflow-hidden">
          <div className="flex flex-col gap-5 lg:flex-row lg:items-start lg:justify-between">
            <div className="max-w-3xl">
              <p className="badge-good">App workflow</p>
              <h2 className="mt-3 text-2xl font-semibold text-ink">Start with a real knowledge workspace</h2>
              <p className="mt-3 max-w-3xl text-stone-700">
                Northstar Analytics can be queried across the whole project or narrowed to a department before role filtering runs.
              </p>
              <div className="mt-4 flex flex-wrap gap-2">
                {["Project scope", "Role filtering", "Citations", "Feedback"].map((item) => (
                  <span key={item} className="rounded border border-stone-300 bg-white px-3 py-1 text-sm font-semibold text-ink">
                    {item}
                  </span>
                ))}
              </div>
            </div>
            <Link href="/projects" className="btn-primary shrink-0 px-5 py-2.5">
              Open Northstar
            </Link>
          </div>

          <div className="mt-6 grid gap-3 md:grid-cols-2 xl:grid-cols-4">
            {heroActions.map((item) => (
              <Link
                key={item.title}
                href={item.href}
                className={`group rounded-md border p-4 transition-colors hover:bg-white ${toneStyles[item.tone as keyof typeof toneStyles].panel}`}
              >
                <span className={`block h-1.5 w-10 rounded-full ${toneStyles[item.tone as keyof typeof toneStyles].accent}`} />
                <p className="mt-3 font-semibold text-ink group-hover:text-moss-dark">{item.title}</p>
                <p className="mt-2 text-sm leading-6 text-stone-700">{item.detail}</p>
                <span className="mt-4 inline-flex text-sm font-semibold text-ink group-hover:text-moss-dark">{item.action}</span>
              </Link>
            ))}
          </div>
        </Card>

        <Card>
          <div className="flex items-start justify-between gap-4">
            <SectionHeading
              title="Measured Trust Signals"
              description="The demo claim is backed by visible controls, not hidden terminal output."
              className="mb-0"
            />
            <span className="badge-solid shrink-0">Proof</span>
          </div>
          <div className="mt-5 grid gap-3 sm:grid-cols-2 xl:grid-cols-1 2xl:grid-cols-2">
            {proofPoints.map((item) => (
              <div key={item.label} className="rounded border border-stone-200 bg-stone-50 p-3">
                <div className="flex items-center gap-2">
                  <span className={`h-2.5 w-2.5 rounded-full ${toneStyles[item.tone as keyof typeof toneStyles].accent}`} />
                  <p className="font-semibold text-ink">{item.label}</p>
                </div>
                <p className="mt-2 text-sm leading-6 text-stone-700">{item.detail}</p>
              </div>
            ))}
          </div>
        </Card>
      </section>

      <section className="mt-8">
        <SectionHeading
          title="Five-Minute Demo Path"
          description="Follow the product story first, then hand off to engineering proof without terminal commands."
        />
        <div className="relative grid gap-4 md:grid-cols-2 xl:grid-cols-4">
          <div className="absolute left-6 top-8 hidden h-px w-[calc(100%-3rem)] bg-stone-300 xl:block" />
          {demoPath.map((item) => (
            <Card key={item.step} padding="compact" className="relative flex h-full flex-col justify-between">
              <div className="absolute bottom-4 left-7 top-14 w-px bg-stone-200 md:hidden" />
              <div className="relative">
                <div className="flex items-center gap-3">
                  <span
                    className={`z-10 flex h-10 w-10 items-center justify-center rounded-full border-2 text-sm font-bold ${
                      toneStyles[item.tone as keyof typeof toneStyles].marker
                    }`}
                  >
                    {item.step}
                  </span>
                  <span className="rounded-full bg-stone-100 px-3 py-1 text-xs font-semibold uppercase tracking-wide text-stone-600">
                    {item.outcome}
                  </span>
                </div>
                <p className="mt-4 font-semibold text-ink">{item.title}</p>
                <p className="mt-2 text-sm leading-6 text-stone-700">{item.detail}</p>
              </div>
              <Link href={item.href} className="btn-secondary btn-sm mt-4 self-start">
                {item.action}
              </Link>
            </Card>
          ))}
        </div>
      </section>

      <section className="mt-8">
        <SectionHeading
          title="Implemented App Capabilities"
          description="Projects, departments, indexed document review, PDF extraction, approval/indexing, and scoped retrieval are implemented; AI Markdown cleanup remains a planned phase."
        />
        <div className="grid gap-4 md:grid-cols-3">
          {nextCapabilities.map((item) => (
            <Card key={item.title} padding="compact" className="border-stone-300">
              <div className="flex items-start justify-between gap-3">
                <p className="font-semibold text-ink">{item.title}</p>
                <span className="badge-info shrink-0">{item.label}</span>
              </div>
              <p className="mt-2 text-sm leading-6 text-stone-700">{item.detail}</p>
            </Card>
          ))}
        </div>
      </section>

      <Card className="mt-8" tone="good">
        <div className="grid gap-5 lg:grid-cols-[0.9fr_1.1fr] lg:items-center">
          <div>
            <p className="badge-good">Engineering proof</p>
            <SectionHeading title="Dev & Admin Remains Available" className="mb-0 mt-3" />
            <p className="mt-2 text-stone-700">
              Evaluation runs, failed-question analysis, retrieval comparison, observability, feedback, and audit logs stay separated from the App story.
            </p>
          </div>
          <div className="flex flex-wrap gap-3 lg:justify-end">
            <Link href="/dev-admin/runs" className="btn-secondary">
              Review runs
            </Link>
            <Link href="/dev-admin/failed-questions" className="btn-secondary">
              Inspect failures
            </Link>
            <Link href="/dev-admin/retrieval-playground" className="btn-secondary">
              Open quality lab
            </Link>
          </div>
        </div>
      </Card>
    </Shell>
  );
}
