import Link from "next/link";
import { Card } from "@/components/Card";
import { PageHeader } from "@/components/PageHeader";
import { SectionHeading } from "@/components/SectionHeading";
import { Shell } from "@/components/Shell";

const nextCapabilities = [
  {
    title: "Scoped Assistant",
    detail: "Ask from a selected project or narrow to one department while preserving role-based filtering.",
  },
  {
    title: "Document Library",
    detail: "Review indexed documents and upload PDFs for extracted Markdown review before indexing.",
  },
  {
    title: "Algorithm Verification",
    detail: "Promote retrieval and prompt changes only after evaluation proves the result improved.",
  },
];

const proofPoints = [
  "Permission-filtered retrieval before generation.",
  "Cited answers with confidence and validation signals.",
  "Benchmark runs for retrieval, answer quality, memory, and permissions.",
  "Dev/Admin views for failures, observability, feedback, cost, and audit events.",
];

const demoPath = [
  {
    step: "1",
    title: "Open Northstar Analytics",
    detail: "Start from Projects to show a durable workspace with seeded departments and quality status.",
    href: "/projects",
    action: "Projects",
  },
  {
    step: "2",
    title: "Inspect Department Knowledge",
    detail: "Open a department document library to review indexed sources, role metadata, and PDF extraction review.",
    href: "/projects/00000000-0000-0000-0000-000000000019/departments/00000000-0000-0000-0000-000000002001",
    action: "Department",
  },
  {
    step: "3",
    title: "Ask With Scope",
    detail: "Use the assistant with project, department, and role controls before checking citations and retrieved context.",
    href: "/chat",
    action: "Assistant",
  },
  {
    step: "4",
    title: "Prove The Controls",
    detail: "Move to Dev/Admin for algorithm comparison, failed-question review, permission safety, and audit evidence.",
    href: "/dev-admin",
    action: "Dev/Admin",
  },
];

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
            <p className="mt-3 text-stone-700">
              Projects are now first-class workspaces. The seeded Northstar Analytics project can be queried as a whole or narrowed to a department before role-based filtering.
            </p>
          </>
        }
        actions={
          <>
            <Link href="/projects" className="btn-primary">
              Open projects
            </Link>
            <Link href="/chat" className="btn-secondary">
              Ask the assistant
            </Link>
            <Link href="/dev-admin" className="btn-secondary">
              View Dev/Admin proof
            </Link>
          </>
        }
      />

      <section className="grid gap-4 lg:grid-cols-[1.2fr_0.8fr]">
        <Card tone="good" className="flex flex-col justify-between">
          <div>
            <SectionHeading
              title="Start In A Project Workspace"
              description="Open Northstar Analytics to review coverage, quality status, and workspace settings before asking questions."
            />
            <p className="text-stone-700">
              The App side now has project CRUD, departments, document review, and a scoped assistant for the existing corpus. The assistant can answer supported questions, refuse restricted requests, show citations, expose retrieved context, and collect feedback.
            </p>
          </div>
          <div className="mt-6 flex flex-wrap gap-3">
            <Link href="/projects" className="btn-primary">
              Open projects
            </Link>
            <Link href="/chat" className="btn-secondary">
              Open assistant
            </Link>
            <Link href="/dev-admin/permission-demo" className="btn-secondary">
              Check permission behavior
            </Link>
          </div>
        </Card>

        <Card>
          <SectionHeading title="Measured Trust Signals" />
          <ul className="space-y-3 text-sm text-stone-700">
            {proofPoints.map((item) => (
              <li key={item} className="border-l-4 border-moss pl-3">
                {item}
              </li>
            ))}
          </ul>
        </Card>
      </section>

      <section className="mt-8">
        <SectionHeading
          title="Five-Minute Demo Path"
          description="The first screen now leads with the App workflow, then hands off to the engineering proof without requiring terminal commands for the main story."
        />
        <div className="grid gap-4 md:grid-cols-2 xl:grid-cols-4">
          {demoPath.map((item) => (
            <Card key={item.step} padding="compact" className="flex h-full flex-col justify-between">
              <div>
                <span className="badge-info">{item.step}</span>
                <p className="mt-3 font-semibold text-ink">{item.title}</p>
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
          description="Projects, departments, indexed document review, PDF extraction, and scoped retrieval are implemented; upload approval/indexing remains a planned phase."
        />
        <div className="grid gap-4 md:grid-cols-2 xl:grid-cols-4">
          {nextCapabilities.map((item) => (
            <Card key={item.title} padding="compact">
              <p className="font-semibold text-ink">{item.title}</p>
              <p className="mt-2 text-sm leading-6 text-stone-700">{item.detail}</p>
            </Card>
          ))}
        </div>
      </section>

      <Card className="mt-8">
        <SectionHeading title="Dev/Admin Remains Available" />
        <p className="text-stone-700">
          Evaluation runs, failed-question analysis, retrieval comparison, observability, feedback, and audit logs now live under the Dev/Admin section so the product story and engineering proof are clearly separated.
        </p>
        <div className="mt-4 flex flex-wrap gap-3">
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
      </Card>
    </Shell>
  );
}
