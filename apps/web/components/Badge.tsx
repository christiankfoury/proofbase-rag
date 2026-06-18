import type { ReactNode } from "react";

const toneClass = {
  neutral: "badge-neutral",
  good: "badge-good",
  warn: "badge-warn",
  info: "badge-info",
  solid: "badge-solid",
} as const;

export type BadgeTone = keyof typeof toneClass;

export function Badge({
  tone = "neutral",
  children,
  className = "",
}: {
  tone?: BadgeTone;
  children: ReactNode;
  className?: string;
}) {
  return <span className={`${toneClass[tone]} ${className}`}>{children}</span>;
}
