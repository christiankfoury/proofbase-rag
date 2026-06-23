import { Shell } from "@/components/Shell";
import type { ReactNode } from "react";

function Line({ className = "" }: { className?: string }) {
  return <div className={`skeleton h-3 ${className}`} />;
}

function Pill({ className = "" }: { className?: string }) {
  return <div className={`skeleton-soft h-7 rounded-full ${className}`} />;
}

function PageFrame({ children }: { children: ReactNode }) {
  return (
    <Shell>
      <div className="space-y-6" aria-busy="true" aria-live="polite">
        <span className="sr-only">Loading</span>
        {children}
      </div>
    </Shell>
  );
}

function HeaderSkeleton({ actions = 2 }: { actions?: number }) {
  return (
    <div className="flex flex-col gap-4 lg:flex-row lg:items-start lg:justify-between">
      <div className="max-w-3xl space-y-3">
        <div className="skeleton h-7 w-64 max-w-full" />
        <Line className="h-4 w-full max-w-3xl" />
        <Line className="h-4 w-4/5 max-w-2xl" />
      </div>
      <div className="flex shrink-0 gap-2">
        {Array.from({ length: actions }).map((_, index) => (
          <div key={index} className="skeleton-steel h-9 w-28" />
        ))}
      </div>
    </div>
  );
}

function MetricGrid({ count = 4 }: { count?: number }) {
  return (
    <div className="grid gap-4 md:grid-cols-2 xl:grid-cols-4">
      {Array.from({ length: count }).map((_, index) => (
        <section key={index} className="rounded-md border border-stone-300 bg-white p-4 shadow-card" aria-hidden="true">
          <div className="flex items-start justify-between gap-3">
            <Pill className="w-24" />
            <div className="skeleton h-8 w-8 rounded-full" />
          </div>
          <div className="mt-5 space-y-3">
            <Line className="h-8 w-28" />
            <Line className="w-full" />
            <Line className="w-3/4" />
          </div>
        </section>
      ))}
    </div>
  );
}

function TableSkeleton({ rows = 6 }: { rows?: number }) {
  return (
    <section className="overflow-hidden rounded-md border border-stone-300 bg-white shadow-card" aria-hidden="true">
      <div className="border-b border-stone-200 bg-stone-100 px-4 py-3">
        <div className="grid grid-cols-4 gap-4">
          {Array.from({ length: 4 }).map((_, index) => (
            <Line key={index} className="h-4" />
          ))}
        </div>
      </div>
      <div className="divide-y divide-stone-200">
        {Array.from({ length: rows }).map((_, row) => (
          <div key={row} className="grid grid-cols-4 gap-4 px-4 py-4">
            <Line className="h-4" />
            <Line className="h-4 w-5/6" />
            <Line className="h-4 w-2/3" />
            <Line className="h-4 w-3/4" />
          </div>
        ))}
      </div>
    </section>
  );
}

function EvidencePanel() {
  return (
    <section className="rounded-md border border-stone-300 bg-white p-5 shadow-card" aria-hidden="true">
      <div className="flex items-start justify-between gap-4">
        <div className="space-y-3">
          <Pill className="w-28" />
          <Line className="h-5 w-56" />
        </div>
        <div className="skeleton-moss h-9 w-24" />
      </div>
      <div className="mt-5 grid gap-3 md:grid-cols-2">
        {Array.from({ length: 4 }).map((_, index) => (
          <div key={index} className="rounded border border-stone-200 bg-stone-50 p-3">
            <div className="flex items-center gap-3">
              <div className="skeleton h-8 w-8 rounded-full" />
              <Line className="h-4 w-32" />
            </div>
            <div className="mt-4 space-y-2">
              <Line className="w-full" />
              <Line className="w-4/5" />
            </div>
          </div>
        ))}
      </div>
    </section>
  );
}

export function HomeSkeleton() {
  return (
    <PageFrame>
      <HeaderSkeleton actions={3} />
      <section className="grid gap-5 xl:grid-cols-[1.1fr_0.9fr]">
        <EvidencePanel />
        <section className="rounded-md border border-stone-300 bg-white p-5 shadow-card" aria-hidden="true">
          <div className="flex items-start justify-between gap-4">
            <div className="space-y-3">
              <Line className="h-5 w-48" />
              <Line className="w-72 max-w-full" />
            </div>
            <Pill className="w-20" />
          </div>
          <div className="mt-5 grid gap-3 sm:grid-cols-2 xl:grid-cols-1 2xl:grid-cols-2">
            {Array.from({ length: 4 }).map((_, index) => (
              <div key={index} className="rounded border border-stone-200 bg-stone-50 p-3">
                <Line className="h-5 w-36" />
                <Line className="mt-3 w-full" />
                <Line className="mt-2 w-4/5" />
              </div>
            ))}
          </div>
        </section>
      </section>
      <MetricGrid />
    </PageFrame>
  );
}

export function ChatSkeleton() {
  return (
    <PageFrame>
      <HeaderSkeleton actions={1} />
      <section className="grid gap-5 xl:grid-cols-[0.9fr_1.1fr]">
        <section className="rounded-md border border-stone-300 bg-white p-5 shadow-card" aria-hidden="true">
          <div className="grid gap-3 md:grid-cols-2">
            <div>
              <Line className="h-4 w-24" />
              <div className="skeleton mt-2 h-10 w-full" />
            </div>
            <div>
              <Line className="h-4 w-28" />
              <div className="skeleton mt-2 h-10 w-full" />
            </div>
          </div>
          <div className="mt-5">
            <Line className="h-4 w-32" />
            <div className="skeleton mt-2 h-36 w-full" />
          </div>
          <div className="mt-5 flex justify-end">
            <div className="skeleton-moss h-10 w-32" />
          </div>
        </section>
        <section className="rounded-md border border-stone-300 bg-white p-5 shadow-card" aria-hidden="true">
          <div className="space-y-4">
            <div className="ml-auto max-w-[75%] rounded-md bg-moss-soft p-4">
              <Line className="h-4 w-full" />
              <Line className="mt-2 h-4 w-3/4" />
            </div>
            <div className="max-w-[82%] rounded-md border border-stone-200 bg-stone-50 p-4">
              <Line className="h-4 w-full" />
              <Line className="mt-2 h-4 w-5/6" />
              <Line className="mt-2 h-4 w-2/3" />
              <div className="mt-4 grid gap-2 sm:grid-cols-2">
                <Pill className="w-full" />
                <Pill className="w-full" />
              </div>
            </div>
          </div>
        </section>
      </section>
    </PageFrame>
  );
}

export function ProjectsSkeleton() {
  return (
    <PageFrame>
      <HeaderSkeleton actions={1} />
      <MetricGrid count={3} />
      <section className="grid gap-4 lg:grid-cols-2">
        {Array.from({ length: 4 }).map((_, index) => (
          <EvidencePanel key={index} />
        ))}
      </section>
    </PageFrame>
  );
}

export function ProjectWorkspaceSkeleton() {
  return (
    <PageFrame>
      <HeaderSkeleton actions={2} />
      <section className="grid gap-5 xl:grid-cols-[0.75fr_1.25fr]">
        <EvidencePanel />
        <section className="grid gap-4 md:grid-cols-2">
          {Array.from({ length: 4 }).map((_, index) => (
            <EvidencePanel key={index} />
          ))}
        </section>
      </section>
      <TableSkeleton rows={5} />
    </PageFrame>
  );
}

export function DepartmentSkeleton() {
  return (
    <PageFrame>
      <HeaderSkeleton actions={2} />
      <section className="grid gap-5 xl:grid-cols-[0.8fr_1.2fr]">
        <EvidencePanel />
        <section className="space-y-4">
          <TableSkeleton rows={4} />
          <EvidencePanel />
        </section>
      </section>
    </PageFrame>
  );
}

export function DevAdminOverviewSkeleton() {
  return (
    <PageFrame>
      <HeaderSkeleton actions={3} />
      <MetricGrid count={4} />
      <section className="grid gap-5 xl:grid-cols-[1.2fr_0.8fr]">
        <EvidencePanel />
        <EvidencePanel />
      </section>
      <TableSkeleton rows={5} />
    </PageFrame>
  );
}

export function EvaluationSkeleton() {
  return (
    <PageFrame>
      <HeaderSkeleton actions={1} />
      <MetricGrid count={3} />
      <section className="grid gap-5 xl:grid-cols-[0.9fr_1.1fr]">
        <TableSkeleton rows={6} />
        <EvidencePanel />
      </section>
    </PageFrame>
  );
}

export function FailedQuestionsSkeleton() {
  return (
    <PageFrame>
      <HeaderSkeleton actions={1} />
      <section className="grid gap-5 xl:grid-cols-[0.7fr_1.3fr]">
        <section className="rounded-md border border-stone-300 bg-white p-4 shadow-card" aria-hidden="true">
          {Array.from({ length: 6 }).map((_, index) => (
            <div key={index} className="border-b border-stone-200 py-3 last:border-0">
              <Line className="h-5 w-32" />
              <Line className="mt-2 w-4/5" />
            </div>
          ))}
        </section>
        <EvidencePanel />
      </section>
    </PageFrame>
  );
}

export function LabSkeleton() {
  return (
    <PageFrame>
      <HeaderSkeleton actions={2} />
      <section className="grid gap-5 xl:grid-cols-[0.85fr_1.15fr]">
        <section className="rounded-md border border-stone-300 bg-white p-5 shadow-card" aria-hidden="true">
          <div className="grid gap-3 sm:grid-cols-2">
            {Array.from({ length: 4 }).map((_, index) => (
              <div key={index}>
                <Line className="h-4 w-28" />
                <div className="skeleton mt-2 h-10 w-full" />
              </div>
            ))}
          </div>
          <div className="skeleton mt-5 h-28 w-full" />
          <div className="skeleton-moss mt-5 h-10 w-36" />
        </section>
        <section className="space-y-4">
          <MetricGrid count={2} />
          <TableSkeleton rows={4} />
        </section>
      </section>
    </PageFrame>
  );
}

export function PermissionDemoSkeleton() {
  return (
    <PageFrame>
      <HeaderSkeleton actions={1} />
      <section className="grid gap-4 lg:grid-cols-3">
        {Array.from({ length: 3 }).map((_, index) => (
          <EvidencePanel key={index} />
        ))}
      </section>
      <TableSkeleton rows={4} />
    </PageFrame>
  );
}

export function ObservabilitySkeleton() {
  return (
    <PageFrame>
      <HeaderSkeleton actions={1} />
      <MetricGrid count={4} />
      <section className="grid gap-5 xl:grid-cols-[0.8fr_1.2fr]">
        <EvidencePanel />
        <TableSkeleton rows={7} />
      </section>
    </PageFrame>
  );
}

export function RunDetailSkeleton() {
  return (
    <PageFrame>
      <HeaderSkeleton actions={2} />
      <MetricGrid count={4} />
      <section className="grid gap-5 xl:grid-cols-[0.8fr_1.2fr]">
        <EvidencePanel />
        <TableSkeleton rows={8} />
      </section>
    </PageFrame>
  );
}
