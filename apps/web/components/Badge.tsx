import type { HTMLAttributes, ReactNode } from "react";

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
  ...rest
}: {
  tone?: BadgeTone;
  children: ReactNode;
  className?: string;
} & HTMLAttributes<HTMLSpanElement>) {
  return <span className={`${toneClass[tone]} ${className}`} {...rest}>{children}</span>;
}
