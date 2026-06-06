import Link from "next/link";
import type { ReactNode } from "react";

const links = [
  ["Overview", "/"],
  ["Chat Demo", "/chat"],
  ["Evaluation", "/runs"],
  ["Failed Questions", "/failed-questions"],
  ["Retrieval Playground", "/retrieval-playground"],
  ["Permission Demo", "/permission-demo"],
  ["Multi-Doc", "/multi-doc"],
  ["Observability", "/observability"],
  ["Feedback", "/feedback"],
  ["Audit Logs", "/audit"],
];

export function Shell({ children }: { children: ReactNode }) {
  return (
    <main className="min-h-screen bg-paper text-ink">
      <header className="border-b border-stone-300 bg-white">
        <div className="mx-auto flex max-w-7xl flex-col gap-4 px-6 py-5 md:flex-row md:items-center md:justify-between">
          <div>
            <p className="text-sm font-semibold uppercase tracking-wide text-rust">Enterprise Knowledge Agent</p>
            <h1 className="text-2xl font-semibold">Interactive Demo Dashboard</h1>
          </div>
          <nav className="flex flex-wrap gap-2 text-sm">
            {links.map(([label, href]) => (
              <Link key={href} href={href} className="rounded border border-stone-300 bg-white px-3 py-2 hover:border-moss">
                {label}
              </Link>
            ))}
          </nav>
        </div>
      </header>
      <div className="mx-auto max-w-7xl px-6 py-8">{children}</div>
    </main>
  );
}
