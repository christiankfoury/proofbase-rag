"use client";

import Link from "next/link";
import { FormEvent, useEffect, useMemo, useState } from "react";
import { FileText, MessageSquare, Search } from "lucide-react";
import { Badge } from "@/components/Badge";
import type { BadgeTone } from "@/components/Badge";
import { DepartmentIconTile } from "@/components/DepartmentIconTile";
import { EmptyState } from "@/components/EmptyState";
import { RoleMultiSelect } from "@/components/RoleMultiSelect";
import { SectionHeading } from "@/components/SectionHeading";
import {
  archiveProject,
  createDepartment,
  createProject,
  DepartmentColor,
  DepartmentIcon,
  fetchProject,
  fetchProjectDocuments,
  fetchProjects,
  Project,
  ProjectDocument,
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
  default_access_roles: string[];
};

const emptyDepartmentForm: DepartmentFormState = {
  name: "",
  icon: "building",
  color: "steel",
  description: "",
  default_access_roles: ["Employee"],
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

function chatHref(projectId: string, departmentId?: string | null, question?: string): string {
  const params = new URLSearchParams({ project: projectId });
  if (departmentId) params.set("department", departmentId);
  if (question) params.set("question", question);
  return `/chat?${params.toString()}`;
}

function documentStatusTone(status: string): BadgeTone {
  if (status === "indexed") return "good";
  if (status === "pending_review") return "info";
  if (status === "failed") return "warn";
  return "neutral";
}

function formatDocumentStatus(status: string): string {
  return status.replaceAll("_", " ");
}

function formatDate(value: string | null | undefined): string {
  if (!value) return "pending";
  return new Date(value).toLocaleDateString(undefined, { month: "short", day: "numeric", year: "numeric" });
}

function isUploadedDocument(document: ProjectDocument): boolean {
  return document.external_document_id.startsWith("UPLOAD-") || document.source_path.startsWith("data/uploads/");
}

export function ProjectWorkspaceClient({ initialProjectId }: { initialProjectId?: string }) {
  const [projects, setProjects] = useState<Project[]>([]);
  const [selectedId, setSelectedId] = useState(initialProjectId ?? "");
  const [selectedProject, setSelectedProject] = useState<Project | null>(null);
  const [projectDocuments, setProjectDocuments] = useState<ProjectDocument[]>([]);
  const [documentsLoading, setDocumentsLoading] = useState(false);
  const [documentsError, setDocumentsError] = useState<string | null>(null);
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
  const activeProject = selectedProject ?? selectedListProject ?? null;

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

  useEffect(() => {
    if (!activeProject?.id) {
      setProjectDocuments([]);
      setDocumentsError(null);
      return;
    }
    let active = true;
    setDocumentsLoading(true);
    setDocumentsError(null);
    setProjectDocuments([]);
    fetchProjectDocuments(activeProject.id)
      .then((documents) => {
        if (!active) return;
        setProjectDocuments(documents);
      })
      .catch((err: Error) => {
        if (!active) return;
        setProjectDocuments([]);
        setDocumentsError(err.message);
      })
      .finally(() => {
        if (active) setDocumentsLoading(false);
      });
    return () => {
      active = false;
    };
  }, [activeProject?.id]);

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
        default_access_roles: departmentForm.default_access_roles,
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

  const departments = activeProject?.departments ?? [];
  const indexedDocuments = projectDocuments.filter((document) => document.version.ingestion_status === "indexed").length;
  const pendingDocuments = projectDocuments.filter((document) => document.version.ingestion_status === "pending_review").length;
  const failedDocuments = projectDocuments.filter((document) => document.version.ingestion_status === "failed").length;
  const uploadedDocuments = projectDocuments.filter(isUploadedDocument).length;
  const representativeDocuments = useMemo(
    () =>
      [...projectDocuments]
        .sort((a, b) => {
          const statusRank = (status: string) => (status === "pending_review" ? 0 : status === "failed" ? 1 : status === "indexed" ? 2 : 3);
          const rankDelta = statusRank(a.version.ingestion_status) - statusRank(b.version.ingestion_status);
          if (rankDelta !== 0) return rankDelta;
          return new Date(b.updated_at).getTime() - new Date(a.updated_at).getTime();
        })
        .slice(0, 5),
    [projectDocuments]
  );
  const suggestedQuestions = useMemo(() => {
    const findDepartment = (...terms: string[]) =>
      departments.find((department) => {
        const name = department.name.toLowerCase();
        const seededKey = department.seeded_data_key?.toLowerCase() ?? "";
        return terms.some((term) => name.includes(term) || seededKey.includes(term));
      });
    const people = findDepartment("people", "hr public");
    const sales = findDepartment("sales");
    const operations = findDepartment("operations");
    return [
      {
        label: "Office locations",
        question: "Where does Northstar Analytics have offices?",
        departmentId: people?.id ?? null,
        scope: people?.name ?? "All departments",
      },
      {
        label: "Remote work proof",
        question: "If I work remotely, what approval and device security expectations apply?",
        departmentId: null,
        scope: "All departments",
      },
      {
        label: "Sales positioning",
        question: "How should I position Northstar against BI tools while avoiding prohibited claims?",
        departmentId: sales?.id ?? null,
        scope: sales?.name ?? "All departments",
      },
      {
        label: "Equipment requests",
        question: "What is the equipment request process?",
        departmentId: operations?.id ?? null,
        scope: operations?.name ?? "All departments",
      },
    ];
  }, [departments]);

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
            Start the API and apply the project schema to load workspaces, departments, documents, and scoped chat links.
          </EmptyState>
        ) : (
          <div className="space-y-5">
            <div className="rounded-md border border-stone-300 bg-white shadow-card">
              <div className="grid gap-5 border-b border-stone-200 p-5 lg:grid-cols-[minmax(0,1.35fr)_minmax(300px,0.65fr)]">
                <div className="min-w-0">
                  <div className="flex flex-wrap items-center gap-2">
                    <h2 className="text-2xl font-semibold text-ink">{activeProject.name}</h2>
                    <Badge tone={statusTone(activeProject.status)}>{activeProject.status}</Badge>
                    {activeProject.seeded_data_key ? <Badge tone="solid">Seeded corpus</Badge> : null}
                  </div>
                  <p className="mt-2 max-w-3xl text-stone-700">{activeProject.description || "No description"}</p>
                  <div className="mt-4 flex flex-wrap gap-2">
                    <Link href={chatHref(activeProject.id)} className="btn-primary">
                      <MessageSquare className="h-4 w-4" />
                      Ask this project
                    </Link>
                    <a href="#departments" className="btn-secondary">
                      <Search className="h-4 w-4" />
                      Browse departments
                    </a>
                    {departments[0] ? (
                      <Link href={`/projects/${activeProject.id}/departments/${departments[0].id}`} className="btn-secondary">
                        <FileText className="h-4 w-4" />
                        Review documents
                      </Link>
                    ) : null}
                  </div>
                </div>
                <div className="rounded-md border border-steel bg-steel-soft p-4 text-steel-dark">
                  <p className="text-xs font-semibold uppercase tracking-wide">One-minute demo path</p>
                  <ol className="mt-3 space-y-2 text-sm leading-6">
                    <li>1. Pick a department shortcut.</li>
                    <li>2. Inspect documents and upload status.</li>
                    <li>3. Ask a scoped question with citations.</li>
                  </ol>
                </div>
              </div>

              <div className="grid gap-3 p-5 sm:grid-cols-2 xl:grid-cols-4">
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

            <div className="rounded-md border border-stone-300 bg-white p-5 shadow-card">
              <SectionHeading
                title="Suggested Scoped Questions"
                description="Each chip opens chat with this project scope preserved; department chips also narrow retrieval before role filtering."
              />
              <div className="mt-4 grid gap-3 md:grid-cols-2 xl:grid-cols-4">
                {suggestedQuestions.map((item) => (
                  <Link
                    key={item.label}
                    href={chatHref(activeProject.id, item.departmentId, item.question)}
                    className="group rounded-md border border-stone-200 bg-stone-50 p-4 transition-colors hover:border-moss hover:bg-moss-soft focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-moss"
                  >
                    <span className="flex items-start justify-between gap-3">
                      <span className="font-semibold text-ink">{item.label}</span>
                      <MessageSquare className="h-4 w-4 shrink-0 text-moss-dark" />
                    </span>
                    <span className="mt-2 block text-sm leading-6 text-stone-700">{item.question}</span>
                    <span className="mt-3 block text-xs font-semibold uppercase tracking-wide text-stone-500">
                      Scope: {item.scope}
                    </span>
                  </Link>
                ))}
              </div>
            </div>

            <div className="grid gap-5 xl:grid-cols-[minmax(0,1fr)_380px]">
              <div className="space-y-5">
                <div id="departments" className="scroll-mt-24 rounded-md border border-stone-300 bg-white p-5 shadow-card">
                  <SectionHeading
                    title="Department Shortcuts"
                    description="Open a department workspace, or ask with that department as a strict retrieval scope."
                  />
                  <form onSubmit={handleCreateDepartment} className="mb-5 rounded border border-stone-200 bg-stone-50 p-4">
                    <div className="grid items-start gap-4 lg:grid-cols-[minmax(0,1fr)_minmax(280px,0.85fr)]">
                      <div className="rounded border border-stone-200 bg-white p-4">
                        <p className="text-sm font-semibold text-ink">Department details</p>
                        <div className="mt-3 space-y-3">
                          <label className="block">
                            <span className="text-sm font-medium text-stone-700">Name</span>
                            <input
                              className="field mt-1 w-full"
                              value={departmentForm.name}
                              onChange={(event) => setDepartmentForm((form) => ({ ...form, name: event.target.value }))}
                              placeholder="Department name"
                              required
                            />
                          </label>
                          <div className="grid gap-3 sm:grid-cols-2">
                            <label className="block">
                              <span className="text-sm font-medium text-stone-700">Icon</span>
                              <select
                                className="field mt-1 w-full"
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
                            </label>
                            <label className="block">
                              <span className="text-sm font-medium text-stone-700">Color</span>
                              <select
                                className="field mt-1 w-full"
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
                            </label>
                          </div>
                          <label className="block">
                            <span className="text-sm font-medium text-stone-700">Description</span>
                            <textarea
                              className="field mt-1 min-h-24 w-full"
                              value={departmentForm.description}
                              onChange={(event) =>
                                setDepartmentForm((form) => ({ ...form, description: event.target.value }))
                              }
                              placeholder="Description"
                            />
                          </label>
                        </div>
                        <div className="mt-4">
                          <button className="btn-primary" type="submit" disabled={saving}>
                            Create department
                          </button>
                        </div>
                      </div>
                      <div className="rounded border border-stone-200 bg-white p-4">
                        <RoleMultiSelect
                          label="Default access roles"
                          selectedRoles={departmentForm.default_access_roles}
                          onChange={(roles) => setDepartmentForm((form) => ({ ...form, default_access_roles: roles }))}
                          variant="compact"
                        />
                      </div>
                    </div>
                  </form>
                  {activeProject.departments?.length ? (
                    <div className="grid gap-3 md:grid-cols-2">
                      {activeProject.departments.map((department) => (
                        <article key={department.id} className="rounded border border-stone-200 bg-white p-4">
                          <div className="flex items-start gap-3">
                            <DepartmentIconTile
                              icon={department.icon}
                              color={department.color}
                              className="h-10 w-10"
                              iconClassName="h-4 w-4"
                            />
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
                          <div className="mt-4 flex flex-wrap gap-2">
                            <Link href={`/projects/${activeProject.id}/departments/${department.id}`} className="btn-secondary btn-sm">
                              Open
                            </Link>
                            <Link href={chatHref(activeProject.id, department.id)} className="btn-secondary btn-sm">
                              Ask
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
                  <SectionHeading
                    title="Representative Documents"
                    description="Recent indexed or pending sources in this project, with review and indexing state visible."
                  />
                  {documentsError ? (
                    <div className="mt-4 rounded-md border border-rust bg-rust-soft p-4 text-sm text-rust-dark">
                      Document library is unavailable: {documentsError}
                    </div>
                  ) : documentsLoading ? (
                    <div className="mt-4 grid gap-3 md:grid-cols-2">
                      <div className="h-28 skeleton-soft" />
                      <div className="h-28 skeleton-soft" />
                    </div>
                  ) : representativeDocuments.length ? (
                    <div className="mt-4 grid gap-3 md:grid-cols-2">
                      {representativeDocuments.map((document) => (
                        <article key={document.id} className="rounded-md border border-stone-200 bg-stone-50 p-4">
                          <div className="flex items-start justify-between gap-3">
                            <div className="min-w-0">
                              <p className="line-clamp-2 font-semibold text-ink">{document.title}</p>
                              <p className="mt-1 text-xs text-stone-500">{document.external_document_id}</p>
                            </div>
                            <Badge tone={documentStatusTone(document.version.ingestion_status)}>
                              {formatDocumentStatus(document.version.ingestion_status)}
                            </Badge>
                          </div>
                          <div className="mt-3 flex flex-wrap gap-2 text-xs text-stone-600">
                            <span>{document.department}</span>
                            <span>{formatNumber(document.chunk_count)} chunks</span>
                            <span>{document.source_type}</span>
                          </div>
                          <p className="mt-3 text-xs text-stone-600">
                            Roles: {document.access_roles.join(", ") || "No roles"} | Updated {formatDate(document.updated_at)}
                          </p>
                          {document.department_id ? (
                            <div className="mt-4 flex flex-wrap gap-2">
                              <Link href={`/projects/${activeProject.id}/departments/${document.department_id}`} className="btn-secondary btn-sm">
                                Open department
                              </Link>
                              {document.version.ingestion_status === "indexed" ? (
                                <Link href={chatHref(activeProject.id, document.department_id)} className="btn-secondary btn-sm">
                                  Ask scoped
                                </Link>
                              ) : null}
                            </div>
                          ) : null}
                        </article>
                      ))}
                    </div>
                  ) : (
                    <div className="mt-4">
                      <EmptyState title="No project documents loaded">
                        Ingest the seeded corpus or upload a PDF in a department to populate the project document library.
                      </EmptyState>
                    </div>
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
                <div className="rounded-md border border-stone-300 bg-white p-5 shadow-card">
                  <SectionHeading
                    title="Upload And Indexing"
                    description="Uploaded files stay reviewable before indexing; failed items can be edited and retried."
                  />
                  <div className="mt-4 grid gap-3 sm:grid-cols-2">
                    <div className="rounded border border-stone-200 bg-stone-50 p-3">
                      <p className="text-xs font-semibold uppercase tracking-wide text-stone-500">Indexed</p>
                      <p className="mt-1 text-2xl font-semibold text-ink">{formatNumber(indexedDocuments)}</p>
                    </div>
                    <div className="rounded border border-stone-200 bg-stone-50 p-3">
                      <p className="text-xs font-semibold uppercase tracking-wide text-stone-500">Pending review</p>
                      <p className="mt-1 text-2xl font-semibold text-ink">{formatNumber(pendingDocuments)}</p>
                    </div>
                    <div className="rounded border border-stone-200 bg-stone-50 p-3">
                      <p className="text-xs font-semibold uppercase tracking-wide text-stone-500">Failed</p>
                      <p className="mt-1 text-2xl font-semibold text-ink">{formatNumber(failedDocuments)}</p>
                    </div>
                    <div className="rounded border border-stone-200 bg-stone-50 p-3">
                      <p className="text-xs font-semibold uppercase tracking-wide text-stone-500">Uploads</p>
                      <p className="mt-1 text-2xl font-semibold text-ink">{formatNumber(uploadedDocuments)}</p>
                    </div>
                  </div>
                </div>

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
