"use client";

export const ACCESS_ROLE_OPTIONS = ["Employee", "Sales Representative", "Manager", "HR Admin", "IT Admin"];

type RoleMultiSelectProps = {
  label: string;
  selectedRoles: string[];
  onChange: (roles: string[]) => void;
  className?: string;
};

export function RoleMultiSelect({ label, selectedRoles, onChange, className = "" }: RoleMultiSelectProps) {
  const roleOptions = Array.from(new Set([...ACCESS_ROLE_OPTIONS, ...selectedRoles])).filter(Boolean);

  function toggleRole(role: string) {
    const selected = selectedRoles.includes(role);
    const nextRoles = selected ? selectedRoles.filter((item) => item !== role) : [...selectedRoles, role];
    onChange(roleOptions.filter((option) => nextRoles.includes(option)));
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
