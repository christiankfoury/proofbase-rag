import Link from "next/link";
import { Card } from "@/components/Card";
import { PageHeader } from "@/components/PageHeader";
import { SectionHeading } from "@/components/SectionHeading";
import { Shell } from "@/components/Shell";

const nextCapabilities = [
  {
    title: "Departments",
    detail: "Turn derived department coverage into editable workspaces with icons and access defaults.",
  },
  {
    title: "Documents",
    detail: "Upload files, review extracted Markdown, and index approved knowledge for retrieval.",
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
              Projects are now first-class workspaces. The seeded Northstar Analytics project shows current corpus coverage while project-scoped retrieval remains planned.
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
              The App side now has project CRUD and a seeded workspace for the existing corpus. The assistant can answer supported questions, refuse restricted requests, show citations, expose retrieved context, and collect feedback.
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
          title="Next App Capabilities"
          description="Projects are implemented; the remaining items are planned product phases."
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
            Compare algorithms
          </Link>
        </div>
      </Card>
    </Shell>
  );
}
