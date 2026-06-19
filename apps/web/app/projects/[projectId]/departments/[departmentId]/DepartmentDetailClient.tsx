"use client";

import Link from "next/link";
import { FormEvent, useEffect, useState } from "react";
import { Badge } from "@/components/Badge";
import { EmptyState } from "@/components/EmptyState";
import { SectionHeading } from "@/components/SectionHeading";
import {
  archiveDepartment,
  DepartmentColor,
  DepartmentIcon,
  fetchDepartment,
  fetchDepartmentDocuments,
  ProjectDepartment,
  ProjectDocument,
  updateDepartment,
} from "@/lib/projects";

type DepartmentFormState = {
  name: string;
  icon: DepartmentIcon;
  color: DepartmentColor;
  description: string;
  default_access_roles_text: string;
};

function formatNumber(value: number | null | undefined): string {
  return new Intl.NumberFormat("en-US").format(value ?? 0);
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

function formFromDepartment(department: ProjectDepartment): DepartmentFormState {
  return {
    name: department.name,
    icon: department.icon,
    color: department.color,
    description: department.description,
    default_access_roles_text: department.default_access_roles.join(", "),
  };
}

function statusTone(status: string) {
  if (status === "indexed" || status === "active") return "good" as const;
  if (status === "failed") return "warn" as const;
  return "neutral" as const;
}

function formatDate(value?: string | null): string {
  if (!value) return "Pending";
  return new Date(value).toLocaleDateString();
}

function compactHash(value?: string | null): string {
  return value ? value.slice(0, 12) : "Pending";
}

export function DepartmentDetailClient({
  projectId,
  departmentId,
}: {
  projectId: string;
  departmentId: string;
}) {
  const [department, setDepartment] = useState<ProjectDepartment | null>(null);
  const [documents, setDocuments] = useState<ProjectDocument[]>([]);
  const [selectedDocumentId, setSelectedDocumentId] = useState<string>("");
  const [form, setForm] = useState<DepartmentFormState | null>(null);
  const [loading, setLoading] = useState(true);
  const [saving, setSaving] = useState(false);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    let active = true;
    setLoading(true);
    Promise.all([fetchDepartment(projectId, departmentId, true), fetchDepartmentDocuments(projectId, departmentId, true)])
      .then(([nextDepartment, nextDocuments]) => {
        if (!active) return;
        setDepartment(nextDepartment);
        setDocuments(nextDocuments);
        setSelectedDocumentId((current) =>
          current && nextDocuments.some((document) => document.id === current) ? current : nextDocuments[0]?.id ?? ""
        );
        setForm(formFromDepartment(nextDepartment));
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
  }, [projectId, departmentId]);

  async function handleSave(event: FormEvent<HTMLFormElement>) {
    event.preventDefault();
    if (!form) return;
    setSaving(true);
    setError(null);
    try {
      const nextDepartment = await updateDepartment(projectId, departmentId, {
        name: form.name,
        icon: form.icon,
        color: form.color,
        description: form.description,
        default_access_roles: parseRoles(form.default_access_roles_text),
      });
      setDepartment(nextDepartment);
      setForm(formFromDepartment(nextDepartment));
    } catch (err) {
      setError(err instanceof Error ? err.message : "Department could not be saved.");
    } finally {
      setSaving(false);
    }
  }

  async function handleArchive() {
    if (!department) return;
    const confirmed = window.confirm(`Archive ${department.name}? Linked documents are not deleted.`);
    if (!confirmed) return;
    setSaving(true);
    setError(null);
    try {
      const nextDepartment = await archiveDepartment(projectId, departmentId);
      setDepartment(nextDepartment);
      setForm(formFromDepartment(nextDepartment));
    } catch (err) {
      setError(err instanceof Error ? err.message : "Department could not be archived.");
    } finally {
      setSaving(false);
    }
  }

  if (loading) {
    return <div className="rounded-md border border-stone-300 bg-white p-5 text-sm text-stone-600 shadow-card">Loading department...</div>;
  }

  if (!department || !form) {
    return <EmptyState title="Department unavailable">The department API is unavailable or this department was not found.</EmptyState>;
  }

  const selectedDocument = documents.find((document) => document.id === selectedDocumentId) ?? documents[0] ?? null;

  return (
    <div className="grid gap-5 xl:grid-cols-[minmax(0,1fr)_380px]">
      <section className="space-y-5">
        {error ? (
          <div className="rounded-md border border-rust bg-rust-soft p-4 text-sm text-rust-dark">{error}</div>
        ) : null}
        <div className="rounded-md border border-stone-300 bg-white p-5 shadow-card">
          <div className="flex flex-wrap items-start justify-between gap-4">
            <div className="flex items-start gap-4">
              <div
                className={`flex h-14 w-14 shrink-0 items-center justify-center rounded border text-sm font-semibold ${colorClass(
                  department.color
                )}`}
              >
                {iconLabel(department.icon)}
              </div>
              <div>
                <div className="flex flex-wrap items-center gap-2">
                  <h2 className="text-2xl font-semibold text-ink">{department.name}</h2>
                  <Badge tone={department.status === "active" ? "good" : "neutral"}>{department.status}</Badge>
                  {department.seeded_data_key ? <Badge tone="solid">Seeded</Badge> : null}
                </div>
                <p className="mt-2 max-w-3xl text-stone-700">{department.description || "No description"}</p>
              </div>
            </div>
            <Link href={`/projects/${projectId}`} className="btn-secondary">
              Back to project
            </Link>
          </div>
          <div className="mt-5 grid gap-3 sm:grid-cols-3">
            <div className="rounded border border-stone-200 bg-stone-50 p-3">
              <p className="text-xs font-semibold uppercase tracking-wide text-stone-500">Documents</p>
              <p className="mt-1 text-2xl font-semibold text-ink">{formatNumber(department.document_count)}</p>
            </div>
            <div className="rounded border border-stone-200 bg-stone-50 p-3">
              <p className="text-xs font-semibold uppercase tracking-wide text-stone-500">Indexed chunks</p>
              <p className="mt-1 text-2xl font-semibold text-ink">{formatNumber(department.chunk_count)}</p>
            </div>
            <div className="rounded border border-stone-200 bg-stone-50 p-3">
              <p className="text-xs font-semibold uppercase tracking-wide text-stone-500">Default roles</p>
              <p className="mt-1 text-lg font-semibold text-ink">{department.default_access_roles.length}</p>
            </div>
          </div>
        </div>

        <div className="rounded-md border border-stone-300 bg-white p-5 shadow-card">
          <SectionHeading title="Access Defaults" />
          <p className="text-sm leading-6 text-stone-700">
            {department.default_access_roles.join(", ") || "No default roles assigned."}
          </p>
          <p className="mt-3 text-sm leading-6 text-stone-700">
            Current document roles: {department.access_roles.join(", ") || "No indexed documents linked."}
          </p>
        </div>

        <div className="rounded-md border border-stone-300 bg-white p-5 shadow-card">
          <div className="flex flex-wrap items-start justify-between gap-4">
            <SectionHeading
              title="Document Library"
              description="Indexed documents linked to this department, with ingestion status, active version metadata, and source Markdown preview."
            />
            <button className="btn-secondary" type="button" disabled title="PDF and document extraction starts in Phase 22.">
              Upload disabled
            </button>
          </div>

          {documents.length ? (
            <div className="mt-4 grid gap-4 xl:grid-cols-[minmax(0,0.95fr)_minmax(0,1.05fr)]">
              <div className="space-y-3">
                {documents.map((document) => {
                  const selected = document.id === selectedDocument?.id;
                  return (
                    <button
                      key={document.id}
                      type="button"
                      onClick={() => setSelectedDocumentId(document.id)}
                      className={`w-full rounded border p-4 text-left transition-colors ${
                        selected
                          ? "border-moss bg-moss-soft"
                          : "border-stone-200 bg-white hover:border-stone-300 hover:bg-stone-50"
                      }`}
                    >
                      <div className="flex flex-wrap items-start justify-between gap-3">
                        <div className="min-w-0">
                          <p className="font-semibold text-ink">{document.title}</p>
                          <p className="mt-1 text-xs font-semibold uppercase tracking-wide text-stone-500">
                            {document.external_document_id}
                          </p>
                        </div>
                        <Badge tone={statusTone(document.version.ingestion_status)}>
                          {document.version.ingestion_status}
                        </Badge>
                      </div>
                      <div className="mt-3 grid gap-2 text-sm text-stone-700 sm:grid-cols-3">
                        <span>{formatNumber(document.chunk_count)} chunks</span>
                        <span>{document.source_type}</span>
                        <span>{document.sensitivity}</span>
                      </div>
                      <p className="mt-3 text-xs text-stone-600">
                        Roles: {document.access_roles.join(", ") || "No roles"}
                      </p>
                    </button>
                  );
                })}
              </div>

              {selectedDocument ? (
                <div className="rounded border border-stone-200 bg-stone-50 p-4">
                  <div className="flex flex-wrap items-start justify-between gap-3">
                    <div>
                      <p className="text-sm font-semibold uppercase tracking-wide text-stone-500">Active Version</p>
                      <h3 className="mt-1 text-lg font-semibold text-ink">{selectedDocument.version.version_label ?? "Pending"}</h3>
                    </div>
                    <Badge tone={selectedDocument.restricted ? "warn" : "good"}>
                      {selectedDocument.restricted ? "restricted" : "internal"}
                    </Badge>
                  </div>

                  <dl className="mt-4 grid gap-3 text-sm sm:grid-cols-2">
                    <div>
                      <dt className="font-semibold text-stone-500">Owner</dt>
                      <dd className="mt-1 text-stone-800">{selectedDocument.version.owner ?? "Pending"}</dd>
                    </div>
                    <div>
                      <dt className="font-semibold text-stone-500">Review Cycle</dt>
                      <dd className="mt-1 text-stone-800">{selectedDocument.version.review_cycle ?? "Pending"}</dd>
                    </div>
                    <div>
                      <dt className="font-semibold text-stone-500">Effective Date</dt>
                      <dd className="mt-1 text-stone-800">{formatDate(selectedDocument.version.effective_date)}</dd>
                    </div>
                    <div>
                      <dt className="font-semibold text-stone-500">Indexed</dt>
                      <dd className="mt-1 text-stone-800">{formatDate(selectedDocument.version.indexed_at)}</dd>
                    </div>
                    <div>
                      <dt className="font-semibold text-stone-500">Content Hash</dt>
                      <dd className="mt-1 font-mono text-xs text-stone-800">{compactHash(selectedDocument.version.content_hash)}</dd>
                    </div>
                    <div>
                      <dt className="font-semibold text-stone-500">Source Path</dt>
                      <dd className="mt-1 break-words font-mono text-xs text-stone-800">{selectedDocument.source_path}</dd>
                    </div>
                  </dl>

                  <div className="mt-4 rounded border border-stone-200 bg-white p-3">
                    <p className="text-sm font-semibold text-ink">Ingestion Status</p>
                    <p className="mt-2 text-sm leading-6 text-stone-700">
                      {selectedDocument.ingestion_job?.status_detail ??
                        "Current version metadata is indexed. Detailed upload extraction jobs begin in Phase 22."}
                    </p>
                    {selectedDocument.version.failure_reason ? (
                      <p className="mt-2 text-sm text-rust-dark">{selectedDocument.version.failure_reason}</p>
                    ) : null}
                  </div>

                  <div className="mt-4">
                    <p className="text-sm font-semibold uppercase tracking-wide text-stone-500">Extracted Markdown Preview</p>
                    <pre className="mt-2 max-h-[520px] overflow-auto whitespace-pre-wrap rounded border border-stone-200 bg-white p-4 text-xs leading-5 text-stone-800">
                      {selectedDocument.markdown_preview || "No extracted Markdown preview is available for this document."}
                    </pre>
                  </div>
                </div>
              ) : null}
            </div>
          ) : (
            <EmptyState title="No documents linked">
              Upload and extraction are planned next. Existing seeded corpus documents appear here after ingestion links them to a department.
            </EmptyState>
          )}
        </div>
      </section>

      <div className="space-y-5">
        <div className="rounded-md border border-stone-300 bg-white p-5 shadow-card">
          <SectionHeading
            title="Upload Planning"
            description="The product entry point is visible, but parsing and indexing new files start in Phase 22."
          />
          <div className="rounded border border-dashed border-stone-300 bg-stone-50 p-4">
            <p className="font-semibold text-ink">Drop zone placeholder</p>
            <p className="mt-2 text-sm leading-6 text-stone-700">
              Future uploads will create ingestion jobs, extract Markdown for review, then index approved content.
            </p>
            <button className="btn-secondary mt-4" type="button" disabled title="PDF and document extraction starts in Phase 22.">
              Choose file disabled
            </button>
          </div>
        </div>

        <form onSubmit={handleSave} className="rounded-md border border-stone-300 bg-white p-5 shadow-card">
          <SectionHeading title="Department Settings" />
        <div className="space-y-3">
          <label className="block">
            <span className="text-sm font-medium text-stone-700">Name</span>
            <input
              className="field mt-1 w-full"
              value={form.name}
              onChange={(event) => setForm((current) => current && { ...current, name: event.target.value })}
              required
            />
          </label>
          <label className="block">
            <span className="text-sm font-medium text-stone-700">Icon</span>
            <select
              className="field mt-1 w-full"
              value={form.icon}
              onChange={(event) => setForm((current) => current && { ...current, icon: event.target.value as DepartmentIcon })}
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
              value={form.color}
              onChange={(event) => setForm((current) => current && { ...current, color: event.target.value as DepartmentColor })}
            >
              <option value="steel">Steel</option>
              <option value="moss">Moss</option>
              <option value="rust">Rust</option>
              <option value="stone">Stone</option>
            </select>
          </label>
          <label className="block">
            <span className="text-sm font-medium text-stone-700">Default access roles</span>
            <input
              className="field mt-1 w-full"
              value={form.default_access_roles_text}
              onChange={(event) =>
                setForm((current) => current && { ...current, default_access_roles_text: event.target.value })
              }
            />
          </label>
          <label className="block">
            <span className="text-sm font-medium text-stone-700">Description</span>
            <textarea
              className="field mt-1 min-h-24 w-full"
              value={form.description}
              onChange={(event) => setForm((current) => current && { ...current, description: event.target.value })}
            />
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
      </div>
    </div>
  );
}
