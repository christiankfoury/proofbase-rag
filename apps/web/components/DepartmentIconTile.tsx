import { BarChart3, Briefcase, Building2, Key, Lock, Shield, Users } from "lucide-react";
import type { LucideIcon } from "lucide-react";

const departmentIcons: Record<string, LucideIcon> = {
  building: Building2,
  people: Users,
  shield: Shield,
  chart: BarChart3,
  briefcase: Briefcase,
  lock: Lock,
  key: Key,
};

const departmentIconNames: Record<string, string> = {
  building: "Building",
  people: "People",
  shield: "Shield",
  chart: "Chart",
  briefcase: "Briefcase",
  lock: "Lock",
  key: "Key",
};

export function departmentColorClass(color: string): string {
  const classes: Record<string, string> = {
    moss: "border-moss bg-moss-soft text-moss-dark",
    steel: "border-steel bg-steel-soft text-steel-dark",
    rust: "border-rust bg-rust-soft text-rust-dark",
    stone: "border-stone-300 bg-stone-100 text-stone-700",
  };
  return classes[color] ?? classes.stone;
}

export function departmentIconName(icon: string): string {
  return departmentIconNames[icon] ?? "Department";
}

type DepartmentIconTileProps = {
  icon: string;
  color: string;
  className?: string;
  iconClassName?: string;
};

export function DepartmentIconTile({
  icon,
  color,
  className = "h-10 w-10",
  iconClassName = "h-5 w-5",
}: DepartmentIconTileProps) {
  const Icon = departmentIcons[icon] ?? Building2;

  return (
    <span
      aria-label={`${departmentIconName(icon)} icon`}
      className={`flex shrink-0 items-center justify-center rounded border ${departmentColorClass(color)} ${className}`}
    >
      <Icon aria-hidden="true" className={iconClassName} />
    </span>
  );
}
