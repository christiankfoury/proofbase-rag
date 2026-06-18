import type { ReactNode } from "react";

export function EmptyState({ title, children }: { title?: string; children: ReactNode }) {
  return (
    <div className="card text-stone-700">
      {title ? <p className="mb-2 font-semibold text-ink">{title}</p> : null}
      <div className="text-sm leading-6">{children}</div>
    </div>
  );
}
