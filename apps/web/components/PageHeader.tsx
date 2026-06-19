"use client";

import { useEffect } from "react";
import type { ReactNode } from "react";
import { useShellHeader } from "@/components/Shell";

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
  const shellHeader = useShellHeader();

  useEffect(() => {
    shellHeader?.setHeader({ title, actions: actions ?? null });
    return () => shellHeader?.setHeader({ title: null, actions: null });
  }, [actions, shellHeader, title]);

  if (!description) return null;

  return (
    <div className={`mb-6 ${className}`}>
      <div className="max-w-3xl text-stone-700">{description}</div>
    </div>
  );
}
