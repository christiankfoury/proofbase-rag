"use client";

export const ACCESS_ROLE_OPTIONS = ["Employee", "Sales Representative", "Manager", "HR Admin", "IT Admin"];

type RoleMultiSelectProps = {
  label: string;
  selectedRoles: string[];
  onChange: (roles: string[]) => void;
  className?: string;
  variant?: "stacked" | "compact";
};

export function RoleMultiSelect({
  label,
  selectedRoles,
  onChange,
  className = "",
  variant = "stacked",
}: RoleMultiSelectProps) {
  const roleOptions = Array.from(new Set([...ACCESS_ROLE_OPTIONS, ...selectedRoles])).filter(Boolean);

  function toggleRole(role: string) {
    const selected = selectedRoles.includes(role);
    const nextRoles = selected ? selectedRoles.filter((item) => item !== role) : [...selectedRoles, role];
    onChange(roleOptions.filter((option) => nextRoles.includes(option)));
  }

  if (variant === "compact") {
    return (
      <fieldset className={className}>
        <legend className="text-sm font-medium text-stone-700">{label}</legend>
        <div className="mt-2 grid gap-2 sm:grid-cols-2">
          {roleOptions.map((role) => {
            const checked = selectedRoles.includes(role);
            return (
              <label
                key={role}
                className={`flex min-h-10 items-center gap-2 rounded border px-3 text-sm transition-colors ${
                  checked
                    ? "border-moss bg-moss-soft text-moss-dark"
                    : "border-stone-200 bg-white text-stone-700 hover:bg-stone-50"
                }`}
              >
                <input type="checkbox" checked={checked} onChange={() => toggleRole(role)} />
                <span>{role}</span>
              </label>
            );
          })}
        </div>
      </fieldset>
    );
  }

  return (
    <fieldset className={className}>
      <legend className="text-sm font-medium text-stone-700">{label}</legend>
      <div className="mt-1 grid gap-2 rounded border border-stone-300 bg-white p-2">
        {roleOptions.map((role) => {
          const checked = selectedRoles.includes(role);
          return (
            <label
              key={role}
              className={`flex min-h-9 items-center gap-2 rounded px-2 text-sm transition-colors ${
                checked ? "bg-moss-soft text-moss-dark" : "text-stone-700 hover:bg-stone-50"
              }`}
            >
              <input type="checkbox" checked={checked} onChange={() => toggleRole(role)} />
              <span>{role}</span>
            </label>
          );
        })}
      </div>
    </fieldset>
  );
}
