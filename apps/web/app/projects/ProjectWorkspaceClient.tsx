"use client";

import Link from "next/link";
import { FormEvent, useEffect, useMemo, useState } from "react";
import { Badge } from "@/components/Badge";
import { EmptyState } from "@/components/EmptyState";
import { SectionHeading } from "@/components/SectionHeading";
import {
  archiveProject,
  createDepartment,
  createProject,
  DepartmentColor,
  DepartmentIcon,
  fetchProject,
  fetchProjects,
  Project,
  updateProject,
} from "@/lib/projects";

type ProjectFormState = {
  name: string;
  description: string;
  status: "active" | "paused";
  default_retrieval_profile: string;
};

const emptyForm: ProjectFormState = {
  name: "",
  description: "",
  status: "active",
  default_retrieval_profile: "vector-section",
};

const retrievalProfileOptions = [
  {
    value: "vector-section",
    label: "Vector section",
    detail: "Current stable default for project-scoped chat.",
  },
  {
    value: "keyword-section",
    label: "Keyword section",
    detail: "Lexical baseline for exact policy terms.",
  },
  {
    value: "hybrid-section-0.5",
    label: "Hybrid 50/50",
    detail: "Blends vector and keyword scores.",
  },
  {
    value: "vector-lexical-rerank",
    label: "Vector + lexical rerank",
    detail: "Best measured precision candidate; available as an explicit project setting.",
  },
];

type DepartmentFormState = {
  name: string;
  icon: DepartmentIcon;
  color: DepartmentColor;
  description: string;
  default_access_roles_text: string;
};

const emptyDepartmentForm: DepartmentFormState = {
  name: "",
  icon: "building",
  color: "steel",
  description: "",
  default_access_roles_text: "Employee",
};

function formatNumber(value: number | null | undefined): string {
  return new Intl.NumberFormat("en-US").format(value ?? 0);
}

function statusTone(status: Project["status"]) {
  if (status === "active") return "good" as const;
  if (status === "paused") return "warn" as const;
  return "neutral" as const;
}

function formatLabel(value: string): string {
  return value.replaceAll("_", " ").replaceAll("-", " ");
}

function retrievalProfileLabel(value: string): string {
  return retrievalProfileOptions.find((option) => option.value === value)?.label ?? formatLabel(value);
}

function iconLabel(icon: string): string {
  const labels: Record<string, string> = {
    people: "PE",
    shield: "SH",
    chart: "CH",
    briefcase: "BR",
    lock: "LO",
    key: "KE",
    building: "BU",
  };
  return labels[icon] ?? "DE";
}

function colorClass(color: string): string {
  const classes: Record<string, string> = {
    moss: "border-moss bg-moss-soft text-moss-dark",
    steel: "border-steel bg-steel-soft text-steel-dark",
    rust: "border-rust bg-rust-soft text-rust-dark",
    stone: "border-stone-300 bg-stone-100 text-stone-700",
  };
  return classes[color] ?? classes.stone;
}

function parseRoles(value: string): string[] {
  return Array.from(new Set(value.split(",").map((role) => role.trim()).filter(Boolean)));
}

export function ProjectWorkspaceClient({ initialProjectId }: { initialProjectId?: string }) {
  const [projects, setProjects] = useState<Project[]>([]);
  const [selectedId, setSelectedId] = useState(initialProjectId ?? "");
  const [selectedProject, setSelectedProject] = useState<Project | null>(null);
  const [createForm, setCreateForm] = useState(emptyForm);
  const [editForm, setEditForm] = useState(emptyForm);
  const [departmentForm, setDepartmentForm] = useState(emptyDepartmentForm);
  const [loading, setLoading] = useState(true);
  const [saving, setSaving] = useState(false);
  const [error, setError] = useState<string | null>(null);

  const selectedListProject = useMemo(
    () => projects.find((project) => project.id === selectedId) ?? projects[0],
    [projects, selectedId]
  );

  async function refreshProjects(preferredProjectId?: string) {
    const nextProjects = await fetchProjects();
    setProjects(nextProjects);
    const requestedProjectId = preferredProjectId ?? selectedId ?? initialProjectId ?? "";
    const nextSelectedId = nextProjects.some((project) => project.id === requestedProjectId)
      ? requestedProjectId
      : nextProjects[0]?.id ?? "";
    setSelectedId(nextSelectedId);
    return { nextProjects, nextSelectedId };
  }

  useEffect(() => {
    let active = true;
    setLoading(true);
    refreshProjects(initialProjectId)
      .then(({ nextProjects, nextSelectedId }) => {
        if (!active) return;
        if (!nextSelectedId && nextProjects[0]) setSelectedId(nextProjects[0].id);
      })
      .catch((err: Error) => {
        if (active) setError(err.message);
      })
      .finally(() => {
        if (active) setLoading(false);
      });
    return () => {
      active = false;
    };
  }, [initialProjectId]);

  useEffect(() => {
    if (!selectedId) {
      setSelectedProject(null);
      return;
    }
    let active = true;
    fetchProject(selectedId)
      .then((project) => {
        if (!active) return;
        setSelectedProject(project);
        setEditForm({
          name: project.name,
          description: project.description,
          status: project.status === "archived" ? "paused" : project.status,
          default_retrieval_profile: project.default_retrieval_profile,
        });
      })
      .catch((err: Error) => {
        if (active) setError(err.message);
      });
    return () => {
      active = false;
    };
  }, [selectedId]);

  async function handleCreate(event: FormEvent<HTMLFormElement>) {
    event.preventDefault();
    setSaving(true);
    setError(null);
    try {
      const project = await createProject(createForm);
      setCreateForm(emptyForm);
      await refreshProjects(project.id);
      setSelectedProject(project);
    } catch (err) {
      setError(err instanceof Error ? err.message : "Project could not be created.");
    } finally {
      setSaving(false);
    }
  }

  async function handleUpdate(event: FormEvent<HTMLFormElement>) {
    event.preventDefault();
    if (!selectedProject) return;
    setSaving(true);
    setError(null);
    try {
      const project = await updateProject(selectedProject.id, editForm);
      await refreshProjects(project.id);
      setSelectedProject(project);
    } catch (err) {
      setError(err instanceof Error ? err.message : "Project could not be updated.");
    } finally {
      setSaving(false);
    }
  }

  async function handleArchive() {
    if (!selectedProject) return;
    const confirmed = window.confirm(`Archive ${selectedProject.name}? Documents and evaluation artifacts are not deleted.`);
    if (!confirmed) return;
    setSaving(true);
    setError(null);
    try {
      await archiveProject(selectedProject.id);
      const { nextProjects } = await refreshProjects();
      setSelectedProject(null);
      setSelectedId(nextProjects[0]?.id ?? "");
    } catch (err) {
      setError(err instanceof Error ? err.message : "Project could not be archived.");
    } finally {
      setSaving(false);
    }
  }

  async function handleCreateDepartment(event: FormEvent<HTMLFormElement>) {
    event.preventDefault();
    if (!activeProject) return;
    setSaving(true);
    setError(null);
    try {
      await createDepartment(activeProject.id, {
        name: departmentForm.name,
        icon: departmentForm.icon,
        color: departmentForm.color,
        description: departmentForm.description,
        default_access_roles: parseRoles(departmentForm.default_access_roles_text),
      });
      const project = await fetchProject(activeProject.id);
      setSelectedProject(project);
      await refreshProjects(project.id);
      setDepartmentForm(emptyDepartmentForm);
    } catch (err) {
      setError(err instanceof Error ? err.message : "Department could not be created.");
    } finally {
      setSaving(false);
    }
  }

  const activeProject = selectedProject ?? selectedListProject ?? null;

  return (
    <div className="grid gap-5 xl:grid-cols-[360px_minmax(0,1fr)]">
      <aside className="rounded-md border border-stone-300 bg-white shadow-card">
        <div className="border-b border-stone-200 p-4">
          <div className="flex items-center justify-between gap-3">
            <p className="text-sm font-semibold uppercase tracking-wide text-steel">Projects</p>
            <Badge tone="info">{projects.length}</Badge>
          </div>
          <form onSubmit={handleCreate} className="mt-4 space-y-3">
            <input
              className="field w-full"
              value={createForm.name}
              onChange={(event) => setCreateForm((form) => ({ ...form, name: event.target.value }))}
              placeholder="Project name"
              required
            />
            <textarea
              className="field min-h-20 w-full"
              value={createForm.description}
              onChange={(event) => setCreateForm((form) => ({ ...form, description: event.target.value }))}
              placeholder="Description"
            />
            <div className="grid gap-2 sm:grid-cols-[1fr_auto]">
              <select
                className="field w-full"
                value={createForm.status}
                onChange={(event) =>
                  setCreateForm((form) => ({ ...form, status: event.target.value as "active" | "paused" }))
                }
              >
                <option value="active">Active</option>
                <option value="paused">Paused</option>
              </select>
              <button className="btn-primary" type="submit" disabled={saving}>
                Create
              </button>
            </div>
          </form>
        </div>

        {loading ? (
          <div className="p-4 text-sm text-stone-600">Loading projects...</div>
        ) : projects.length === 0 ? (
          <div className="p-4">
            <EmptyState title="No active projects">Create a workspace to organize knowledge before indexing documents.</EmptyState>
          </div>
        ) : (
          <nav className="max-h-[640px] overflow-y-auto p-2">
            {projects.map((project) => {
              const active = project.id === activeProject?.id;
              return (
                <Link
                  href={`/projects/${project.id}`}
                  key={project.id}
                  onClick={() => setSelectedId(project.id)}
                  className={`block rounded border p-3 text-left transition-colors ${
                    active
                      ? "border-moss bg-moss-soft"
                      : "border-transparent hover:border-stone-300 hover:bg-stone-50"
                  }`}
                >
                  <div className="flex items-start justify-between gap-3">
                    <p className="font-semibold text-ink">{project.name}</p>
                    <Badge tone={statusTone(project.status)}>{project.status}</Badge>
                  </div>
                  <p className="mt-2 line-clamp-2 text-sm leading-5 text-stone-600">{project.description || "No description"}</p>
                  <div className="mt-3 grid grid-cols-3 gap-2 text-xs text-stone-600">
                    <span>{formatNumber(project.department_count)} depts</span>
                    <span>{formatNumber(project.document_count)} docs</span>
                    <span>{formatNumber(project.chunk_count)} chunks</span>
                  </div>
                </Link>
              );
            })}
          </nav>
        )}
      </aside>

      <section className="min-w-0">
        {error ? (
          <div className="mb-4 rounded-md border border-rust bg-rust-soft p-4 text-sm text-rust-dark">{error}</div>
        ) : null}

        {!activeProject ? (
          <EmptyState title="Project workspace unavailable">
            The project API is unavailable or the schema has not been applied yet.
          </EmptyState>
        ) : (
          <div className="space-y-5">
            <div className="rounded-md border border-stone-300 bg-white p-5 shadow-card">
              <div className="flex flex-wrap items-start justify-between gap-4">
                <div>
                  <div className="flex flex-wrap items-center gap-2">
                    <h2 className="text-2xl font-semibold text-ink">{activeProject.name}</h2>
                    <Badge tone={statusTone(activeProject.status)}>{activeProject.status}</Badge>
                    {activeProject.seeded_data_key ? <Badge tone="solid">Seeded corpus</Badge> : null}
                  </div>
                  <p className="mt-2 max-w-3xl text-stone-700">{activeProject.description || "No description"}</p>
                </div>
                <Link href="/chat" className="btn-secondary">
                  Open assistant demo
                </Link>
              </div>

              <div className="mt-5 grid gap-3 sm:grid-cols-2 xl:grid-cols-4">
                <div className="rounded border border-stone-200 bg-stone-50 p-3">
                  <p className="text-xs font-semibold uppercase tracking-wide text-stone-500">Departments</p>
                  <p className="mt-1 text-2xl font-semibold text-ink">{formatNumber(activeProject.department_count)}</p>
                </div>
                <div className="rounded border border-stone-200 bg-stone-50 p-3">
                  <p className="text-xs font-semibold uppercase tracking-wide text-stone-500">Documents</p>
                  <p className="mt-1 text-2xl font-semibold text-ink">{formatNumber(activeProject.document_count)}</p>
                </div>
                <div className="rounded border border-stone-200 bg-stone-50 p-3">
                  <p className="text-xs font-semibold uppercase tracking-wide text-stone-500">Indexed chunks</p>
                  <p className="mt-1 text-2xl font-semibold text-ink">{formatNumber(activeProject.chunk_count)}</p>
                </div>
                <div className="rounded border border-stone-200 bg-stone-50 p-3">
                  <p className="text-xs font-semibold uppercase tracking-wide text-stone-500">Retrieval profile</p>
                  <p className="mt-1 text-lg font-semibold text-ink">{retrievalProfileLabel(activeProject.default_retrieval_profile)}</p>
                  <p className="mt-1 text-xs text-stone-500">{activeProject.default_retrieval_profile}</p>
                </div>
              </div>
            </div>

            <div className="grid gap-5 xl:grid-cols-[minmax(0,1fr)_380px]">
              <div className="space-y-5">
                <div className="rounded-md border border-stone-300 bg-white p-5 shadow-card">
                  <SectionHeading
                    title="Department Coverage"
                    description="Create project-local knowledge areas with icons, descriptions, and default access roles."
                  />
                  <form onSubmit={handleCreateDepartment} className="mb-5 grid gap-3 rounded border border-stone-200 bg-stone-50 p-4 lg:grid-cols-2">
                    <input
                      className="field w-full"
                      value={departmentForm.name}
                      onChange={(event) => setDepartmentForm((form) => ({ ...form, name: event.target.value }))}
                      placeholder="Department name"
                      required
                    />
                    <input
                      className="field w-full"
                      value={departmentForm.default_access_roles_text}
                      onChange={(event) =>
                        setDepartmentForm((form) => ({ ...form, default_access_roles_text: event.target.value }))
                      }
                      placeholder="Default roles"
                    />
                    <select
                      className="field w-full"
                      value={departmentForm.icon}
                      onChange={(event) =>
                        setDepartmentForm((form) => ({ ...form, icon: event.target.value as DepartmentIcon }))
                      }
                    >
                      <option value="building">Building</option>
                      <option value="people">People</option>
                      <option value="shield">Shield</option>
                      <option value="chart">Chart</option>
                      <option value="briefcase">Briefcase</option>
                      <option value="lock">Lock</option>
                      <option value="key">Key</option>
                    </select>
                    <select
                      className="field w-full"
                      value={departmentForm.color}
                      onChange={(event) =>
                        setDepartmentForm((form) => ({ ...form, color: event.target.value as DepartmentColor }))
                      }
                    >
                      <option value="steel">Steel</option>
                      <option value="moss">Moss</option>
                      <option value="rust">Rust</option>
                      <option value="stone">Stone</option>
                    </select>
                    <textarea
                      className="field min-h-20 w-full lg:col-span-2"
                      value={departmentForm.description}
                      onChange={(event) => setDepartmentForm((form) => ({ ...form, description: event.target.value }))}
                      placeholder="Description"
                    />
                    <div className="lg:col-span-2">
                      <button className="btn-primary" type="submit" disabled={saving}>
                        Create department
                      </button>
                    </div>
                  </form>
                  {activeProject.departments?.length ? (
                    <div className="grid gap-3 md:grid-cols-2">
                      {activeProject.departments.map((department) => (
                        <article key={department.id} className="rounded border border-stone-200 bg-white p-4">
                          <div className="flex items-start gap-3">
                            <div
                              className={`flex h-10 w-10 shrink-0 items-center justify-center rounded border text-xs font-semibold ${colorClass(
                                department.color
                              )}`}
                            >
                              {iconLabel(department.icon)}
                            </div>
                            <div className="min-w-0 flex-1">
                              <div className="flex flex-wrap items-center gap-2">
                                <p className="font-semibold text-ink">{department.name}</p>
                                {department.seeded_data_key ? <Badge tone="neutral">Seeded</Badge> : null}
                              </div>
                              <p className="mt-1 text-sm leading-5 text-stone-600">
                                {department.description || "No description"}
                              </p>
                            </div>
                          </div>
                          <div className="mt-4 grid grid-cols-3 gap-2 text-sm text-stone-700">
                            <span>{formatNumber(department.document_count)} docs</span>
                            <span>{formatNumber(department.chunk_count)} chunks</span>
                            <span>{department.default_access_roles.length} defaults</span>
                          </div>
                          <p className="mt-3 text-xs text-stone-600">
                            Current roles: {department.access_roles.join(", ") || department.default_access_roles.join(", ") || "-"}
                          </p>
                          <div className="mt-4">
                            <Link href={`/projects/${activeProject.id}/departments/${department.id}`} className="btn-secondary btn-sm">
                              Open
                            </Link>
                          </div>
                        </article>
                      ))}
                    </div>
                  ) : (
                    <EmptyState title="No documents indexed">
                      This workspace has no department coverage until documents are added through ingestion.
                    </EmptyState>
                  )}
                </div>

                <div className="rounded-md border border-stone-300 bg-white p-5 shadow-card">
                  <SectionHeading title="Quality Status" />
                  <div className="rounded border border-stone-200 bg-stone-50 p-4">
                    <p className="font-semibold text-ink">
                      {activeProject.quality_summary.label ?? formatLabel(activeProject.quality_status)}
                    </p>
                    <p className="mt-2 text-sm leading-6 text-stone-700">
                      {activeProject.quality_summary.detail ??
                        "Project-scoped quality gates have not been run for this workspace yet."}
                    </p>
                    {typeof activeProject.quality_summary.permission_leakage_rate === "number" ? (
                      <p className="mt-3 text-sm text-stone-700">
                        Permission leakage rate:{" "}
                        <span className="font-semibold text-moss-dark">
                          {activeProject.quality_summary.permission_leakage_rate.toFixed(3)}
                        </span>
                      </p>
                    ) : null}
                    {activeProject.quality_summary.known_open_issue ? (
                      <p className="mt-3 text-sm text-rust-dark">{activeProject.quality_summary.known_open_issue}</p>
                    ) : null}
                  </div>
                </div>
              </div>

              <div className="space-y-5">
                <form onSubmit={handleUpdate} className="rounded-md border border-stone-300 bg-white p-5 shadow-card">
                  <SectionHeading title="Project Settings" />
                  <div className="space-y-3">
                    <label className="block">
                      <span className="text-sm font-medium text-stone-700">Name</span>
                      <input
                        className="field mt-1 w-full"
                        value={editForm.name}
                        onChange={(event) => setEditForm((form) => ({ ...form, name: event.target.value }))}
                        required
                      />
                    </label>
                    <label className="block">
                      <span className="text-sm font-medium text-stone-700">Description</span>
                      <textarea
                        className="field mt-1 min-h-24 w-full"
                        value={editForm.description}
                        onChange={(event) => setEditForm((form) => ({ ...form, description: event.target.value }))}
                      />
                    </label>
                    <label className="block">
                      <span className="text-sm font-medium text-stone-700">Status</span>
                      <select
                        className="field mt-1 w-full"
                        value={editForm.status}
                        onChange={(event) =>
                          setEditForm((form) => ({ ...form, status: event.target.value as "active" | "paused" }))
                        }
                      >
                        <option value="active">Active</option>
                        <option value="paused">Paused</option>
                      </select>
                    </label>
                    <label className="block">
                      <span className="text-sm font-medium text-stone-700">Default retrieval profile</span>
                      <select
                        className="field mt-1 w-full"
                        value={editForm.default_retrieval_profile}
                        onChange={(event) =>
                          setEditForm((form) => ({ ...form, default_retrieval_profile: event.target.value }))
                        }
                      >
                        {retrievalProfileOptions.map((option) => (
                          <option key={option.value} value={option.value}>
                            {option.label}
                          </option>
                        ))}
                      </select>
                      <span className="mt-1 block text-xs text-stone-500">
                        {retrievalProfileOptions.find((option) => option.value === editForm.default_retrieval_profile)?.detail ??
                          "Custom profile saved on this project."}
                      </span>
                    </label>
                  </div>
                  <div className="mt-4 flex flex-wrap gap-3">
                    <button className="btn-primary" type="submit" disabled={saving}>
                      Save
                    </button>
                    <button className="btn-secondary" type="button" onClick={handleArchive} disabled={saving}>
                      Archive
                    </button>
                  </div>
                </form>

                <div className="rounded-md border border-stone-300 bg-white p-5 shadow-card">
                  <SectionHeading title="Recent Activity" />
                  {activeProject.recent_activity?.length ? (
                    <ol className="space-y-3">
                      {activeProject.recent_activity.map((item) => (
                        <li key={item.id} className="border-l-4 border-moss pl-3 text-sm">
                          <p className="font-medium text-ink">{formatLabel(item.action)}</p>
                          <p className="text-stone-600">{new Date(item.created_at).toLocaleString()}</p>
                        </li>
                      ))}
                    </ol>
                  ) : (
                    <EmptyState>No project audit events recorded yet.</EmptyState>
                  )}
                </div>
              </div>
            </div>
          </div>
        )}
      </section>
    </div>
  );
}
