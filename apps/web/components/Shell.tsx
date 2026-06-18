"use client";

import Link from "next/link";
import { usePathname } from "next/navigation";
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
  const pathname = usePathname();

  return (
    <main className="min-h-screen bg-paper text-ink">
      <header className="sticky top-0 z-10 border-b border-stone-300 bg-white/95 backdrop-blur">
        <div className="mx-auto flex max-w-7xl flex-col gap-4 px-6 py-5 md:flex-row md:items-center md:justify-between">
          <div>
            <p className="text-sm font-semibold uppercase tracking-wide text-rust">Enterprise Knowledge Agent</p>
            <h1 className="text-2xl font-semibold">Interactive Demo Dashboard</h1>
          </div>
          <nav className="flex flex-wrap gap-2 text-sm">
            {links.map(([label, href]) => {
              const active = href === "/" ? pathname === "/" : pathname?.startsWith(href);
              return (
                <Link
                  key={href}
                  href={href}
                  aria-current={active ? "page" : undefined}
                  className={`rounded border px-3 py-2 font-medium transition-colors focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-moss focus-visible:ring-offset-2 ${
                    active
                      ? "border-moss bg-moss-soft text-moss-dark"
                      : "border-stone-300 bg-white text-stone-700 hover:border-moss hover:text-moss-dark"
                  }`}
                >
                  {label}
                </Link>
              );
            })}
          </nav>
        </div>
      </header>
      <div className="mx-auto max-w-7xl px-6 py-8">{children}</div>
    </main>
  );
}
