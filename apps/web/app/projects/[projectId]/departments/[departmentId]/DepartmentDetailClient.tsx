"use client";

import Link from "next/link";
import { FormEvent, useEffect, useState } from "react";
import { Badge } from "@/components/Badge";
import { DepartmentIconTile } from "@/components/DepartmentIconTile";
import { EmptyState } from "@/components/EmptyState";
import { RoleMultiSelect } from "@/components/RoleMultiSelect";
import { SectionHeading } from "@/components/SectionHeading";
import {
  approveDepartmentDocument,
  archiveDepartment,
  cleanupDepartmentDocumentMarkdown,
  CleanupMarkdownResult,
  DepartmentColor,
  DepartmentIcon,
  fetchDepartment,
  fetchDepartmentDocument,
  fetchDepartmentDocuments,
  ProjectDepartment,
  ProjectDocument,
  revertDepartmentDocumentCleanup,
  uploadDepartmentDocument,
  updateDepartment,
} from "@/lib/projects";

type DepartmentFormState = {
  name: string;
  icon: DepartmentIcon;
  color: DepartmentColor;
  description: string;
  default_access_roles: string[];
};

function formatNumber(value: number | null | undefined): string {
  return new Intl.NumberFormat("en-US").format(value ?? 0);
}

function formatLabel(value: string): string {
  return value
    .split("_")
    .map((part) => part.charAt(0).toUpperCase() + part.slice(1))
    .join(" ");
}

function formFromDepartment(department: ProjectDepartment): DepartmentFormState {
  return {
    name: department.name,
    icon: department.icon,
    color: department.color,
    description: department.description,
    default_access_roles: department.default_access_roles,
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

function isUploadedDocument(document: ProjectDocument): boolean {
  return document.external_document_id.startsWith("UPLOAD-") || document.source_path.startsWith("data/uploads/");
}

type TimelineStep = {
  label: string;
  status: "complete" | "current" | "pending" | "failed";
  detail: string;
  timestamp?: string | null;
};

type CleanupMetadata = {
  status?: string;
  model?: string;
  cleanup_timestamp?: string;
  source_content_hash?: string;
  cleaned_content_hash?: string;
  input_tokens?: number | null;
  output_tokens?: number | null;
  estimated_cost_usd?: number | null;
  pricing_status?: string | null;
};

type CleanupRevertMetadata = {
  reverted_at?: string;
  reverted_by?: string;
  source_content_hash?: string;
};

type DiffLine = {
  text: string;
  kind: "added" | "removed" | "unchanged";
};

function cleanupMetadata(document: ProjectDocument | null): CleanupMetadata | null {
  const value = document?.version.metadata?.ai_cleanup;
  return value && typeof value === "object" ? (value as CleanupMetadata) : null;
}

function cleanupRevertMetadata(document: ProjectDocument | null): CleanupRevertMetadata | null {
  const value = document?.version.metadata?.ai_cleanup_revert;
  return value && typeof value === "object" ? (value as CleanupRevertMetadata) : null;
}

function formatCost(value?: number | null): string {
  return value == null ? "pending" : `$${value.toFixed(6)}`;
}

function cleanupEditedAfterDraft(cleanedMarkdown: string | null, reviewMarkdown: string): boolean | null {
  if (cleanedMarkdown == null) return null;
  return reviewMarkdown.trim() !== cleanedMarkdown.trim();
}

function markdownDiff(before: string, after: string): DiffLine[] {
  const beforeLines = before.trim().split(/\r?\n/);
  const afterLines = after.trim().split(/\r?\n/);
  const rows: DiffLine[] = [];
  const max = Math.max(beforeLines.length, afterLines.length);
  for (let index = 0; index < max; index += 1) {
    const beforeLine = beforeLines[index];
    const afterLine = afterLines[index];
    if (beforeLine === afterLine) {
      if (afterLine !== undefined) rows.push({ kind: "unchanged", text: afterLine });
    } else {
      if (beforeLine !== undefined) rows.push({ kind: "removed", text: beforeLine });
      if (afterLine !== undefined) rows.push({ kind: "added", text: afterLine });
    }
  }
  return rows.slice(0, 80);
}

function diffLineClass(kind: DiffLine["kind"]): string {
  if (kind === "added") return "border-moss bg-moss-soft text-moss-dark";
  if (kind === "removed") return "border-rust bg-rust-soft text-rust-dark";
  return "border-stone-200 bg-white text-stone-700";
}

function timelineClass(status: TimelineStep["status"]): string {
  if (status === "complete") return "border-moss bg-moss-soft text-moss-dark";
  if (status === "current") return "border-steel bg-steel-soft text-steel-dark";
  if (status === "failed") return "border-rust bg-rust-soft text-rust-dark";
  return "border-stone-300 bg-stone-100 text-stone-600";
}

function uploadTimeline(document: ProjectDocument, reviewMarkdownReady: boolean): TimelineStep[] {
  const ingestionStatus = document.version.ingestion_status;
  const isIndexed = ingestionStatus === "indexed";
  const isFailed = ingestionStatus === "failed";
  const hasExtractedMarkdown = Boolean(document.markdown_preview || document.review_markdown);
  return [
    {
      label: "Uploaded",
      status: "complete",
      detail: "Source file was stored locally for review.",
      timestamp: document.created_at,
    },
    {
      label: "Extracted",
      status: hasExtractedMarkdown ? "complete" : isFailed ? "failed" : "pending",
      detail: hasExtractedMarkdown ? "Deterministic PDF extraction produced Markdown." : "Markdown extraction has not completed.",
      timestamp: document.version.indexed_at ?? document.updated_at,
    },
    {
      label: "Reviewed",
      status: isIndexed ? "complete" : isFailed ? "current" : reviewMarkdownReady ? "current" : "pending",
      detail: isIndexed
        ? "An editor approved the reviewed Markdown for indexing."
        : isFailed
          ? "Review can be edited before retrying indexing."
          : reviewMarkdownReady
            ? "Markdown is ready for editor review and approval."
            : "Waiting for extracted Markdown before review.",
    },
    {
      label: "Indexed",
      status: isIndexed ? "complete" : isFailed ? "failed" : "pending",
      detail: isIndexed ? "Chunks and embeddings are available to scoped retrieval." : isFailed ? "Indexing failed; edit and retry." : "Not searchable until approval/indexing completes.",
      timestamp: document.version.indexed_at,
    },
    {
      label: "Failed",
      status: isFailed ? "failed" : "pending",
      detail: document.version.failure_reason ?? (isFailed ? "Indexing failed." : "No failure recorded."),
      timestamp: document.version.failed_at,
    },
  ];
}

function UploadStatusTimeline({ document, reviewMarkdownReady }: { document: ProjectDocument; reviewMarkdownReady: boolean }) {
  if (!isUploadedDocument(document)) return null;
  const steps = uploadTimeline(document, reviewMarkdownReady);
  return (
    <div className="mt-4 rounded border border-stone-200 bg-white p-3">
      <p className="text-sm font-semibold text-ink">Upload Status Timeline</p>
      <ol className="mt-3 space-y-3">
        {steps.map((step) => (
          <li key={step.label} className="flex gap-3">
            <span className={`mt-0.5 flex h-8 w-8 shrink-0 items-center justify-center rounded-full border text-xs font-bold ${timelineClass(step.status)}`}>
              {step.status === "complete" ? "OK" : step.status === "failed" ? "!" : ""}
            </span>
            <div className="min-w-0">
              <div className="flex flex-wrap items-center gap-2">
                <p className="text-sm font-semibold text-ink">{step.label}</p>
                <span className={`rounded border px-2 py-0.5 text-2xs font-semibold uppercase tracking-wide ${timelineClass(step.status)}`}>
                  {step.status}
                </span>
              </div>
              <p className="mt-1 text-xs leading-5 text-stone-700">{step.detail}</p>
              {step.timestamp ? <p className="mt-1 text-xs text-stone-500">{formatDate(step.timestamp)}</p> : null}
            </div>
          </li>
        ))}
      </ol>
    </div>
  );
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
  const [uploadFile, setUploadFile] = useState<File | null>(null);
  const [uploadTitle, setUploadTitle] = useState("");
  const [uploadRoles, setUploadRoles] = useState<string[]>([]);
  const [uploadRestricted, setUploadRestricted] = useState(false);
  const [loading, setLoading] = useState(true);
  const [saving, setSaving] = useState(false);
  const [uploading, setUploading] = useState(false);
  const [indexingDocumentId, setIndexingDocumentId] = useState<string | null>(null);
  const [cleanupDocumentId, setCleanupDocumentId] = useState<string | null>(null);
  const [cleanupResult, setCleanupResult] = useState<CleanupMarkdownResult | null>(null);
  const [reviewMarkdown, setReviewMarkdown] = useState("");
  const [reviewLoadingDocumentId, setReviewLoadingDocumentId] = useState<string | null>(null);
  const [error, setError] = useState<string | null>(null);
  const [notice, setNotice] = useState<string | null>(null);

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
        setUploadRoles((current) => (current.length ? current : nextDepartment.default_access_roles));
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

  const selectedDocument = documents.find((document) => document.id === selectedDocumentId) ?? documents[0] ?? null;
  const selectedDocumentNeedsReview = selectedDocument
    ? ["pending_review", "failed"].includes(selectedDocument.version.ingestion_status)
    : false;
  const selectedCleanupMetadata = cleanupMetadata(selectedDocument);
  const selectedCleanupRevertMetadata = cleanupRevertMetadata(selectedDocument);

  useEffect(() => {
    let active = true;
    if (!selectedDocument || !selectedDocumentNeedsReview) {
      setReviewMarkdown("");
      setReviewLoadingDocumentId(null);
      return () => {
        active = false;
      };
    }
    setReviewLoadingDocumentId(selectedDocument.id);
    fetchDepartmentDocument(projectId, departmentId, selectedDocument.id)
      .then((document) => {
        if (!active) return;
        setReviewMarkdown(document.review_markdown ?? document.markdown_preview ?? "");
        setDocuments((current) => current.map((item) => (item.id === document.id ? document : item)));
        setCleanupResult(null);
      })
      .catch((err: Error) => {
        if (active) setError(err.message);
      })
      .finally(() => {
        if (active) setReviewLoadingDocumentId(null);
      });
    return () => {
      active = false;
    };
  }, [projectId, departmentId, selectedDocument?.id, selectedDocumentNeedsReview]);

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
        default_access_roles: form.default_access_roles,
      });
      setDepartment(nextDepartment);
      setForm(formFromDepartment(nextDepartment));
    } catch (err) {
      setError(err instanceof Error ? err.message : "Department could not be saved.");
    } finally {
      setSaving(false);
    }
  }

  async function handleUpload(event: FormEvent<HTMLFormElement>) {
    event.preventDefault();
    if (!uploadFile) {
      setError("Choose a PDF before uploading.");
      return;
    }
    setUploading(true);
    setError(null);
    setNotice(null);
    try {
      const document = await uploadDepartmentDocument(projectId, departmentId, {
        file: uploadFile,
        title: uploadTitle,
        access_roles: uploadRoles,
        restricted: uploadRestricted,
      });
      const [nextDepartment, nextDocuments] = await Promise.all([
        fetchDepartment(projectId, departmentId, true),
        fetchDepartmentDocuments(projectId, departmentId, true),
      ]);
      setDepartment(nextDepartment);
      setDocuments(nextDocuments);
      setSelectedDocumentId(document.id);
      setUploadFile(null);
      setUploadTitle("");
      setUploadRestricted(false);
      setNotice("PDF extracted to Markdown and saved for review. It is not indexed for retrieval yet.");
    } catch (err) {
      setError(err instanceof Error ? err.message : "PDF upload could not be processed.");
    } finally {
      setUploading(false);
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

  async function handleApproveIndex(document: ProjectDocument) {
    setIndexingDocumentId(document.id);
    setError(null);
    setNotice(null);
    try {
      const reviewedMarkdown = ["pending_review", "failed"].includes(document.version.ingestion_status)
        ? reviewMarkdown
        : undefined;
      const indexedDocument = await approveDepartmentDocument(projectId, departmentId, document.id, {
        reviewed_markdown: reviewedMarkdown,
      });
      const [nextDepartment, nextDocuments] = await Promise.all([
        fetchDepartment(projectId, departmentId, true),
        fetchDepartmentDocuments(projectId, departmentId, true),
      ]);
      setDepartment(nextDepartment);
      setDocuments(nextDocuments);
      setSelectedDocumentId(indexedDocument.id);
      setNotice(`${indexedDocument.title} is indexed for scoped retrieval.`);
    } catch (err) {
      setError(err instanceof Error ? err.message : "Document could not be indexed.");
      const nextDocuments = await fetchDepartmentDocuments(projectId, departmentId, true).catch(() => null);
      if (nextDocuments) setDocuments(nextDocuments);
    } finally {
      setIndexingDocumentId(null);
    }
  }

  async function handleCleanupMarkdown(document: ProjectDocument) {
    setCleanupDocumentId(document.id);
    setError(null);
    setNotice(null);
    try {
      const result = await cleanupDepartmentDocumentMarkdown(projectId, departmentId, document.id);
      setReviewMarkdown(result.cleaned_markdown);
      setCleanupResult(result);
      setDocuments((current) => current.map((item) => (item.id === result.document.id ? result.document : item)));
      setSelectedDocumentId(result.document.id);
      setNotice(`AI cleanup draft returned to the editor. It is not indexed until you approve it. Estimated cost: ${formatCost(result.estimated_cost_usd)}.`);
    } catch (err) {
      setError(err instanceof Error ? err.message : "Markdown cleanup could not be completed.");
    } finally {
      setCleanupDocumentId(null);
    }
  }

  async function handleRevertMarkdown(document: ProjectDocument) {
    setCleanupDocumentId(document.id);
    setError(null);
    try {
      const revertedDocument = await revertDepartmentDocumentCleanup(projectId, departmentId, document.id);
      setDocuments((current) => current.map((item) => (item.id === revertedDocument.id ? revertedDocument : item)));
      setReviewMarkdown(revertedDocument.review_markdown ?? revertedDocument.markdown_preview ?? "");
      setCleanupResult(null);
      setNotice("Review editor reverted to the deterministic extraction. Nothing was indexed.");
    } catch (err) {
      setError(err instanceof Error ? err.message : "Markdown cleanup revert could not be recorded.");
    } finally {
      setCleanupDocumentId(null);
    }
  }

  if (loading) {
    return <div className="rounded-md border border-stone-300 bg-white p-5 text-sm text-stone-600 shadow-card">Loading department...</div>;
  }

  if (!department || !form) {
    return <EmptyState title="Department unavailable">The department API is unavailable or this department was not found.</EmptyState>;
  }

  const reviewMarkdownReady = reviewMarkdown.trim().length > 0;
  const cleanedDraftMarkdown =
    cleanupResult && selectedDocument && cleanupResult.document.id === selectedDocument.id ? cleanupResult.cleaned_markdown : null;
  const editedAfterCleanup = cleanupEditedAfterDraft(cleanedDraftMarkdown, reviewMarkdown);
  const extractedMarkdown = selectedDocument?.review_markdown ?? selectedDocument?.markdown_preview ?? "";
  const diffRows = selectedDocumentNeedsReview ? markdownDiff(extractedMarkdown, reviewMarkdown) : [];
  return (
    <div className="grid gap-5 xl:grid-cols-[minmax(0,1fr)_380px]">
      <section className="space-y-5">
        {error ? (
          <div className="rounded-md border border-rust bg-rust-soft p-4 text-sm text-rust-dark">{error}</div>
        ) : null}
        {notice ? (
          <div className="rounded-md border border-moss bg-moss-soft p-4 text-sm text-moss-dark">{notice}</div>
        ) : null}
        <div className="rounded-md border border-stone-300 bg-white p-5 shadow-card">
          <div className="flex flex-wrap items-start justify-between gap-4">
            <div className="flex items-start gap-4">
              <DepartmentIconTile
                icon={department.icon}
                color={department.color}
                className="h-14 w-14"
                iconClassName="h-6 w-6"
              />
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
              description="Department documents with ingestion status, active version metadata, access roles, and source Markdown preview."
            />
            <Badge tone="info">PDF review enabled</Badge>
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
                        "Current indexed version metadata is available. New uploads stay pending review until explicit approval and indexing."}
                    </p>
                    {selectedDocument.version.failure_reason ? (
                      <p className="mt-2 text-sm text-rust-dark">{selectedDocument.version.failure_reason}</p>
                    ) : null}
                    {["pending_review", "failed"].includes(selectedDocument.version.ingestion_status) ? (
                      <div className="mt-3 flex flex-wrap gap-2">
                        <button
                          className="btn-secondary"
                          type="button"
                          onClick={() => handleCleanupMarkdown(selectedDocument)}
                          disabled={
                            cleanupDocumentId === selectedDocument.id ||
                            indexingDocumentId === selectedDocument.id ||
                            reviewLoadingDocumentId === selectedDocument.id ||
                            !reviewMarkdownReady
                          }
                        >
                          {cleanupDocumentId === selectedDocument.id ? "Cleaning..." : "Clean up Markdown"}
                        </button>
                        <button
                          className="btn-secondary"
                          type="button"
                          onClick={() => handleRevertMarkdown(selectedDocument)}
                          disabled={cleanupDocumentId === selectedDocument.id || indexingDocumentId === selectedDocument.id || reviewLoadingDocumentId === selectedDocument.id}
                        >
                          Revert to extraction
                        </button>
                        <button
                          className="btn-primary"
                          type="button"
                          onClick={() => handleApproveIndex(selectedDocument)}
                          disabled={
                            indexingDocumentId === selectedDocument.id ||
                            cleanupDocumentId === selectedDocument.id ||
                            reviewLoadingDocumentId === selectedDocument.id ||
                            !reviewMarkdownReady
                          }
                        >
                          {indexingDocumentId === selectedDocument.id
                            ? "Indexing..."
                            : selectedDocument.version.ingestion_status === "failed"
                              ? "Retry indexing"
                              : "Approve and index"}
                        </button>
                      </div>
                    ) : null}
                    {selectedDocument.version.ingestion_status === "indexed" ? (
                      <Link
                        className="btn-secondary mt-3 inline-flex"
                        href={`/chat?project=${encodeURIComponent(projectId)}&department=${encodeURIComponent(departmentId)}`}
                      >
                        Ask in chat
                      </Link>
                    ) : null}
                  </div>

                  <UploadStatusTimeline document={selectedDocument} reviewMarkdownReady={reviewMarkdownReady} />

                  {selectedDocumentNeedsReview ? (
                    <div className="mt-4 rounded border border-stone-200 bg-white p-3">
                      <div className="flex flex-wrap items-center justify-between gap-2">
                        <p className="text-sm font-semibold text-ink">Cleanup Provenance</p>
                        <Badge tone={selectedCleanupMetadata || cleanupResult ? "info" : "neutral"}>
                          {selectedCleanupRevertMetadata ? "reverted" : selectedCleanupMetadata || cleanupResult ? "cleanup draft" : "deterministic extraction"}
                        </Badge>
                      </div>
                      {selectedCleanupMetadata || cleanupResult ? (
                        <dl className="mt-3 grid gap-3 text-xs sm:grid-cols-2">
                          <div>
                            <dt className="font-semibold text-stone-500">Model</dt>
                            <dd className="mt-1 text-stone-800">{cleanupResult?.model ?? selectedCleanupMetadata?.model ?? "Pending"}</dd>
                          </div>
                          <div>
                            <dt className="font-semibold text-stone-500">Cleanup time</dt>
                            <dd className="mt-1 text-stone-800">{formatDate(cleanupResult?.cleanup_timestamp ?? selectedCleanupMetadata?.cleanup_timestamp)}</dd>
                          </div>
                          <div>
                            <dt className="font-semibold text-stone-500">Tokens</dt>
                            <dd className="mt-1 text-stone-800">
                              input {cleanupResult?.input_tokens ?? selectedCleanupMetadata?.input_tokens ?? "pending"} / output{" "}
                              {cleanupResult?.output_tokens ?? selectedCleanupMetadata?.output_tokens ?? "pending"}
                            </dd>
                          </div>
                          <div>
                            <dt className="font-semibold text-stone-500">Estimated cost</dt>
                            <dd className="mt-1 text-stone-800">
                              {formatCost(cleanupResult?.estimated_cost_usd ?? selectedCleanupMetadata?.estimated_cost_usd)}
                            </dd>
                          </div>
                          <div>
                            <dt className="font-semibold text-stone-500">Source hash</dt>
                            <dd className="mt-1 font-mono text-stone-800">{compactHash(cleanupResult?.source_content_hash ?? selectedCleanupMetadata?.source_content_hash)}</dd>
                          </div>
                          <div>
                            <dt className="font-semibold text-stone-500">Cleaned hash</dt>
                            <dd className="mt-1 font-mono text-stone-800">{compactHash(cleanupResult?.cleaned_content_hash ?? selectedCleanupMetadata?.cleaned_content_hash)}</dd>
                          </div>
                          <div>
                            <dt className="font-semibold text-stone-500">Edited after cleanup</dt>
                            <dd className="mt-1 text-stone-800">{editedAfterCleanup == null ? "Pending approval" : editedAfterCleanup ? "Yes" : "No"}</dd>
                          </div>
                          <div>
                            <dt className="font-semibold text-stone-500">Indexing status</dt>
                            <dd className="mt-1 text-stone-800">Not indexed until approval</dd>
                          </div>
                          {selectedCleanupRevertMetadata ? (
                            <div>
                              <dt className="font-semibold text-stone-500">Reverted</dt>
                              <dd className="mt-1 text-stone-800">{formatDate(selectedCleanupRevertMetadata.reverted_at)}</dd>
                            </div>
                          ) : null}
                        </dl>
                      ) : (
                        <p className="mt-2 text-sm leading-6 text-stone-700">
                          No AI cleanup draft has been requested. The editor is reviewing deterministic extraction.
                        </p>
                      )}
                    </div>
                  ) : null}

                  <div className="mt-4">
                    <p className="text-sm font-semibold uppercase tracking-wide text-stone-500">
                      {selectedDocumentNeedsReview ? "Markdown Review" : "Extracted Markdown Preview"}
                    </p>
                    {selectedDocumentNeedsReview ? (
                      <>
                        {cleanupResult?.document.id === selectedDocument.id ? (
                          <div className="mt-2 rounded border border-steel bg-steel-soft p-3 text-xs leading-5 text-steel-dark">
                            <p className="font-semibold">AI cleanup draft is in the editor.</p>
                            <p className="mt-1">
                              Model {cleanupResult.model}; cost {formatCost(cleanupResult.estimated_cost_usd)};
                              source hash {compactHash(cleanupResult.source_content_hash)}; cleaned hash{" "}
                              {compactHash(cleanupResult.cleaned_content_hash)}.
                            </p>
                          </div>
                        ) : null}
                        <textarea
                          className="field mt-2 min-h-[520px] w-full font-mono text-xs leading-5"
                          value={reviewLoadingDocumentId === selectedDocument.id ? "Loading extracted Markdown..." : reviewMarkdown}
                          onChange={(event) => setReviewMarkdown(event.target.value)}
                          disabled={
                            reviewLoadingDocumentId === selectedDocument.id ||
                            indexingDocumentId === selectedDocument.id ||
                            cleanupDocumentId === selectedDocument.id
                          }
                        />
                      </>
                    ) : (
                      <pre className="mt-2 max-h-[520px] overflow-auto whitespace-pre-wrap rounded border border-stone-200 bg-white p-4 text-xs leading-5 text-stone-800">
                        {selectedDocument.markdown_preview || "No extracted Markdown preview is available for this document."}
                      </pre>
                    )}
                  </div>
                  {selectedDocumentNeedsReview && diffRows.length ? (
                    <div className="mt-4 rounded border border-stone-200 bg-white p-3">
                      <div className="flex flex-wrap items-center justify-between gap-2">
                        <p className="text-sm font-semibold text-ink">Extraction vs Current Review</p>
                        <Badge tone={diffRows.some((row) => row.kind !== "unchanged") ? "info" : "neutral"}>
                          {diffRows.some((row) => row.kind !== "unchanged") ? "changes visible" : "unchanged"}
                        </Badge>
                      </div>
                      <div className="mt-3 max-h-72 overflow-auto rounded border border-stone-200 bg-stone-50 p-2 font-mono text-xs leading-5">
                        {diffRows.map((row, index) => (
                          <div key={`${row.kind}-${index}`} className={`mb-1 rounded border px-2 py-1 ${diffLineClass(row.kind)}`}>
                            <span className="mr-2 font-bold">{row.kind === "added" ? "+" : row.kind === "removed" ? "-" : " "}</span>
                            <span className="whitespace-pre-wrap">{row.text || " "}</span>
                          </div>
                        ))}
                      </div>
                    </div>
                  ) : null}
                </div>
              ) : null}
            </div>
          ) : (
            <EmptyState title="No documents linked">
              Upload a PDF for Markdown review, or ingest the seeded corpus to link existing documents to this department.
            </EmptyState>
          )}
        </div>
      </section>

      <div className="space-y-5">
        <div className="rounded-md border border-stone-300 bg-white p-5 shadow-card">
          <SectionHeading
            title="Upload PDF"
            description="Extract text to Markdown for review, then approve it for local indexing."
          />
          <form onSubmit={handleUpload} className="space-y-3 rounded border border-dashed border-stone-300 bg-stone-50 p-4">
            <label className="block">
              <span className="text-sm font-medium text-stone-700">PDF file</span>
              <input
                className="field mt-1 w-full"
                type="file"
                accept="application/pdf,.pdf"
                onChange={(event) => setUploadFile(event.target.files?.[0] ?? null)}
              />
            </label>
            <label className="block">
              <span className="text-sm font-medium text-stone-700">Title</span>
              <input
                className="field mt-1 w-full"
                value={uploadTitle}
                onChange={(event) => setUploadTitle(event.target.value)}
                placeholder="Defaults to file name"
              />
            </label>
            <RoleMultiSelect label="Access roles" selectedRoles={uploadRoles} onChange={setUploadRoles} />
            <label className="flex items-center gap-2 text-sm text-stone-700">
              <input
                type="checkbox"
                checked={uploadRestricted}
                onChange={(event) => setUploadRestricted(event.target.checked)}
              />
              Restricted source
            </label>
            <button className="btn-primary w-full" type="submit" disabled={uploading}>
              {uploading ? "Extracting..." : "Extract for review"}
            </button>
          </form>
        </div>

        <form onSubmit={handleSave} className="rounded-md border border-stone-300 bg-white p-5 shadow-card">
          <SectionHeading title="Department Settings" />
          <div className="mb-4 rounded-md border border-stone-200 bg-stone-50 p-3">
            <p className="text-xs font-semibold uppercase tracking-wide text-stone-500">Current appearance</p>
            <div className="mt-3 flex items-center gap-3">
              <DepartmentIconTile
                icon={form.icon}
                color={form.color}
                className="h-12 w-12"
                iconClassName="h-5 w-5"
              />
              <div>
                <p className="font-semibold text-ink">{form.name || "Department name"}</p>
                <p className="text-sm text-stone-600">
                  Icon: {formatLabel(form.icon)} / Color: {formatLabel(form.color)}
                </p>
              </div>
            </div>
          </div>
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
            <RoleMultiSelect
              label="Default access roles"
              selectedRoles={form.default_access_roles}
              onChange={(roles) => setForm((current) => current && { ...current, default_access_roles: roles })}
            />
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
