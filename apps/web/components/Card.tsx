import type { ElementType, ReactNode } from "react";

const toneBorder = {
  neutral: "border-stone-300",
  good: "border-moss",
  warn: "border-rust",
  risk: "border-red-500",
} as const;

export type CardTone = keyof typeof toneBorder;

export function Card({
  children,
  tone = "neutral",
  padding = "default",
  className = "",
  as,
}: {
  children: ReactNode;
  tone?: CardTone;
  padding?: "default" | "compact";
  className?: string;
  as?: ElementType;
}) {
  const Component = as ?? "section";
  return (
    <Component
      className={`rounded-md border bg-white shadow-card ${toneBorder[tone]} ${
        padding === "compact" ? "p-4" : "p-5"
      } ${className}`}
    >
      {children}
    </Component>
  );
}
