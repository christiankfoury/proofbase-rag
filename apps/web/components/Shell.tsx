"use client";

import Link from "next/link";
import { usePathname } from "next/navigation";
import type { ReactNode } from "react";

const navGroups = [
  {
    title: "App",
    links: [
      ["Home", "/"],
      ["Projects", "/projects"],
      ["Assistant", "/chat"],
    ],
  },
  {
    title: "Dev/Admin",
    links: [
      ["Overview", "/dev-admin"],
      ["Runs", "/dev-admin/runs"],
      ["Failed Questions", "/dev-admin/failed-questions"],
      ["Retrieval Playground", "/dev-admin/retrieval-playground"],
      ["Permission Demo", "/dev-admin/permission-demo"],
      ["Multi-Doc", "/dev-admin/multi-doc"],
      ["Observability", "/dev-admin/observability"],
      ["Feedback", "/dev-admin/feedback"],
      ["Audit Logs", "/dev-admin/audit"],
    ],
  },
  {
    title: "Deep Evaluation",
    links: [
      ["Retrieval Experiments", "/dev-admin/retrieval-experiments"],
      ["Prompt Experiments", "/dev-admin/prompt-experiments"],
      ["Permission Safety", "/dev-admin/permission-safety"],
      ["Memory Evaluation", "/dev-admin/memory-evaluation"],
    ],
  },
];

export function Shell({ children }: { children: ReactNode }) {
  const pathname = usePathname();

  return (
    <main className="min-h-screen bg-paper text-ink lg:flex">
      <aside className="border-b border-stone-300 bg-white lg:sticky lg:top-0 lg:h-screen lg:w-72 lg:shrink-0 lg:overflow-y-auto lg:border-b-0 lg:border-r xl:w-80">
        <div className="px-5 py-5">
          <p className="text-xs font-semibold uppercase tracking-wide text-rust">Enterprise Knowledge Agent</p>
          <h1 className="mt-1 text-2xl font-semibold">Knowledge Workspace</h1>
          <p className="mt-2 text-sm leading-6 text-stone-600">
            App experience first, with Dev/Admin proof for quality, safety, and operations.
          </p>
        </div>
        <nav className="flex gap-3 overflow-x-auto px-5 pb-5 text-sm lg:block lg:space-y-6 lg:overflow-visible">
          {navGroups.map((group) => (
            <div key={group.title} className="min-w-52 lg:min-w-0">
              <p className="mb-2 text-xs font-semibold uppercase tracking-wide text-stone-500">{group.title}</p>
              <div className="flex gap-2 lg:block lg:space-y-1">
                {group.links.map(([label, href]) => {
                  const active = href === "/" ? pathname === "/" : pathname === href || pathname?.startsWith(`${href}/`);
                  return (
                    <Link
                      key={href}
                      href={href}
                      aria-current={active ? "page" : undefined}
                      className={`block whitespace-nowrap rounded border px-3 py-2 font-medium transition-colors focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-moss focus-visible:ring-offset-2 ${
                        active
                          ? "border-moss bg-moss-soft text-moss-dark"
                          : "border-transparent bg-white text-stone-700 hover:border-stone-300 hover:text-moss-dark"
                      }`}
                    >
                      {label}
                    </Link>
                  );
                })}
              </div>
            </div>
          ))}
        </nav>
      </aside>
      <div className="min-w-0 flex-1 px-5 py-8 md:px-8 2xl:px-10">
        <div className="mx-auto w-full max-w-[1920px]">{children}</div>
      </div>
    </main>
  );
}
