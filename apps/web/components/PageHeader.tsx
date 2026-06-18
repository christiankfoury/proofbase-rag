import type { ReactNode } from "react";

export function PageHeader({
  title,
  description,
  actions,
  className = "",
}: {
  title: string;
  description?: ReactNode;
  actions?: ReactNode;
  className?: string;
}) {
  return (
    <div className={`mb-8 flex flex-col gap-5 md:flex-row md:items-start md:justify-between ${className}`}>
      <div>
        <h2 className="text-3xl font-semibold tracking-tight text-ink">{title}</h2>
        {description ? <div className="mt-3 max-w-3xl text-stone-700">{description}</div> : null}
      </div>
      {actions ? <div className="flex flex-wrap gap-3">{actions}</div> : null}
    </div>
  );
}
