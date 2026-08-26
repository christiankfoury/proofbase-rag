import { API_BASE } from "@/lib/api";
import { demoAuthHeaders } from "@/lib/demoAuth";

export type ProjectStatus = "active" | "paused" | "archived";

export type ProjectDepartment = {
  id: string;
  project_id: string;
  name: string;
  icon: DepartmentIcon;
  color: DepartmentColor;
  description: string;
  default_access_roles: string[];
  seeded_data_key?: string | null;
  status: "active" | "archived";
  created_at: string;
  updated_at: string;
  archived_at?: string | null;
  document_count: number;
  chunk_count: number;
  sensitivity?: string | null;
  access_roles: string[];
};

export type DepartmentIcon = "people" | "shield" | "chart" | "briefcase" | "lock" | "key" | "building";
export type DepartmentColor = "moss" | "steel" | "rust" | "stone";

export type DepartmentPayload = {
  name: string;
  icon: DepartmentIcon;
  color: DepartmentColor;
  description: string;
  default_access_roles: string[];
};

export type ProjectDocument = {
  id: string;
  project_id: string;
  department_id?: string | null;
  external_document_id: string;
  title: string;
  department: string;
  category: string;
  source_type: string;
  source_path: string;
  access_roles: string[];
  sensitivity: string;
  restricted: boolean;
  status: string;
  created_at: string;
  updated_at: string;
  version: {
    id?: string | null;
    version_label?: string | null;
    effective_date?: string | null;
    owner?: string | null;
    review_cycle?: string | null;
    content_hash?: string | null;
    metadata: Record<string, unknown>;
    ingestion_status: string;
    indexed_at?: string | null;
    failed_at?: string | null;
    failure_reason?: string | null;
  };
  chunk_count: number;
  markdown_preview: string;
  review_markdown?: string;
  ingestion_job?: {
    id?: string | null;
    status?: string | null;
    stage?: string | null;
    status_detail?: string | null;
    started_at?: string | null;
    completed_at?: string | null;
    failed_at?: string | null;
    error_message?: string | null;
  } | null;
};

export type CleanupMarkdownResult = {
  cleaned_markdown: string;
  document: ProjectDocument;
  model: string;
  input_tokens?: number | null;
  output_tokens?: number | null;
  input_cost_usd?: number | null;
  output_cost_usd?: number | null;
  estimated_cost_usd?: number | null;
  pricing_status?: string | null;
  source_content_hash: string;
  cleaned_content_hash: string;
  cleanup_timestamp: string;
};

export type ProjectActivity = {
  id: string;
  action: string;
  outcome: string;
  reason: string | null;
  metadata_json: Record<string, unknown>;
  created_at: string;
};

export type ProjectMembership = {
  user_id: string;
  display_name: string;
  email: string;
  business_role: string;
  is_admin: boolean;
  membership_level: "viewer" | "contributor" | "owner" | null;
  created_at?: string | null;
  updated_at?: string | null;
};

export type Project = {
  id: string;
  name: string;
  description: string;
  status: ProjectStatus;
  default_retrieval_profile: string;
  seeded_data_key?: string | null;
  quality_status: string;
  quality_summary: {
    label?: string;
    detail?: string;
    permission_leakage_rate?: number;
    known_open_issue?: string;
  };
  created_at: string;
  updated_at: string;
  archived_at?: string | null;
  document_count: number;
  chunk_count: number;
  department_count: number;
  departments?: ProjectDepartment[];
  recent_activity?: ProjectActivity[];
};

export type ProjectPayload = {
  name: string;
  description: string;
  status?: "active" | "paused";
  default_retrieval_profile?: string;
};

async function projectRequest<T>(path: string, options?: RequestInit): Promise<T> {
  const response = await fetch(`${API_BASE}${path}`, {
    ...options,
    headers: {
      "Content-Type": "application/json",
      ...demoAuthHeaders(),
      ...(options?.headers ?? {}),
    },
  });
  if (!response.ok) {
    const detail = await response.text();
    throw new Error(detail || `Project request failed with ${response.status}`);
  }
  return response.json();
}

export async function fetchProjects(includeArchived = false): Promise<Project[]> {
  const params = includeArchived ? "?include_archived=true" : "";
  const payload = await projectRequest<{ projects: Project[] }>(`/projects${params}`, { cache: "no-store" });
  return payload.projects;
}

export async function fetchProject(projectId: string, includeArchived = false): Promise<Project> {
  const params = includeArchived ? "?include_archived=true" : "";
  const payload = await projectRequest<{ project: Project }>(`/projects/${encodeURIComponent(projectId)}${params}`, {
    cache: "no-store",
  });
  return payload.project;
}

export async function fetchProjectDocuments(
  projectId: string,
  options: { departmentId?: string; includeArchived?: boolean } = {}
): Promise<ProjectDocument[]> {
  const params = new URLSearchParams();
  if (options.departmentId) params.set("department_id", options.departmentId);
  if (options.includeArchived) params.set("include_archived", "true");
  const query = params.toString() ? `?${params.toString()}` : "";
  const payload = await projectRequest<{ documents: ProjectDocument[] }>(
    `/projects/${encodeURIComponent(projectId)}/documents${query}`,
    { cache: "no-store" }
  );
  return payload.documents;
}

export async function createProject(payload: ProjectPayload): Promise<Project> {
  const result = await projectRequest<{ project: Project }>("/projects", {
    method: "POST",
    body: JSON.stringify(payload),
  });
  return result.project;
}

export async function updateProject(projectId: string, payload: Partial<ProjectPayload>): Promise<Project> {
  const result = await projectRequest<{ project: Project }>(`/projects/${encodeURIComponent(projectId)}`, {
    method: "PATCH",
    body: JSON.stringify(payload),
  });
  return result.project;
}

export async function archiveProject(projectId: string): Promise<Project> {
  const result = await projectRequest<{ project: Project }>(`/projects/${encodeURIComponent(projectId)}`, {
    method: "DELETE",
  });
  return result.project;
}

export async function fetchProjectMemberships(projectId: string): Promise<ProjectMembership[]> {
  const result = await projectRequest<{ memberships: ProjectMembership[] }>(
    `/projects/${encodeURIComponent(projectId)}/memberships`,
    { cache: "no-store" }
  );
  return result.memberships;
}

export async function updateProjectMembership(
  projectId: string,
  userId: string,
  membershipLevel: "viewer" | "contributor" | "owner"
): Promise<ProjectMembership> {
  const result = await projectRequest<{ membership: ProjectMembership }>(
    `/projects/${encodeURIComponent(projectId)}/memberships/${encodeURIComponent(userId)}`,
    {
      method: "PUT",
      body: JSON.stringify({ membership_level: membershipLevel }),
    }
  );
  return result.membership;
}

export async function removeProjectMembership(projectId: string, userId: string): Promise<void> {
  await projectRequest(
    `/projects/${encodeURIComponent(projectId)}/memberships/${encodeURIComponent(userId)}`,
    { method: "DELETE" }
  );
}

export async function fetchDepartment(projectId: string, departmentId: string, includeArchived = false): Promise<ProjectDepartment> {
  const params = includeArchived ? "?include_archived=true" : "";
  const result = await projectRequest<{ department: ProjectDepartment }>(
    `/projects/${encodeURIComponent(projectId)}/departments/${encodeURIComponent(departmentId)}${params}`,
    { cache: "no-store" }
  );
  return result.department;
}

export async function fetchDepartmentDocuments(
  projectId: string,
  departmentId: string,
  includeArchived = false
): Promise<ProjectDocument[]> {
  const params = includeArchived ? "?include_archived=true" : "";
  const result = await projectRequest<{ documents: ProjectDocument[] }>(
    `/projects/${encodeURIComponent(projectId)}/departments/${encodeURIComponent(departmentId)}/documents${params}`,
    { cache: "no-store" }
  );
  return result.documents;
}

export async function fetchDepartmentDocument(
  projectId: string,
  departmentId: string,
  documentId: string
): Promise<ProjectDocument> {
  const result = await projectRequest<{ document: ProjectDocument }>(
    `/projects/${encodeURIComponent(projectId)}/departments/${encodeURIComponent(departmentId)}/documents/${encodeURIComponent(documentId)}`,
    { cache: "no-store" }
  );
  return result.document;
}

export async function uploadDepartmentDocument(
  projectId: string,
  departmentId: string,
  payload: {
    file: File;
    title?: string;
    access_roles?: string[];
    restricted?: boolean;
  }
): Promise<ProjectDocument> {
  const formData = new FormData();
  formData.append("file", payload.file);
  if (payload.title) formData.append("title", payload.title);
  if (payload.access_roles?.length) formData.append("access_roles", payload.access_roles.join(", "));
  formData.append("restricted", String(Boolean(payload.restricted)));

  const response = await fetch(
    `${API_BASE}/projects/${encodeURIComponent(projectId)}/departments/${encodeURIComponent(departmentId)}/documents/upload`,
    {
      method: "POST",
      headers: demoAuthHeaders(),
      body: formData,
    }
  );
  if (!response.ok) {
    const detail = await response.text();
    throw new Error(detail || `Upload failed with ${response.status}`);
  }
  const result = (await response.json()) as { document: ProjectDocument };
  return result.document;
}

export async function approveDepartmentDocument(
  projectId: string,
  departmentId: string,
  documentId: string,
  payload: { reviewed_markdown?: string } = {}
): Promise<ProjectDocument> {
  const result = await projectRequest<{ document: ProjectDocument }>(
    `/projects/${encodeURIComponent(projectId)}/departments/${encodeURIComponent(departmentId)}/documents/${encodeURIComponent(documentId)}/approve-index`,
    {
      method: "POST",
      body: JSON.stringify(payload),
    }
  );
  return result.document;
}

export async function cleanupDepartmentDocumentMarkdown(
  projectId: string,
  departmentId: string,
  documentId: string
): Promise<CleanupMarkdownResult> {
  return projectRequest<CleanupMarkdownResult>(
    `/projects/${encodeURIComponent(projectId)}/departments/${encodeURIComponent(departmentId)}/documents/${encodeURIComponent(documentId)}/cleanup-markdown`,
    {
      method: "POST",
      body: JSON.stringify({}),
    }
  );
}

export async function revertDepartmentDocumentCleanup(
  projectId: string,
  departmentId: string,
  documentId: string
): Promise<ProjectDocument> {
  const result = await projectRequest<{ document: ProjectDocument }>(
    `/projects/${encodeURIComponent(projectId)}/departments/${encodeURIComponent(departmentId)}/documents/${encodeURIComponent(documentId)}/cleanup-markdown/revert`,
    {
      method: "POST",
      body: JSON.stringify({}),
    }
  );
  return result.document;
}

export async function createDepartment(projectId: string, payload: DepartmentPayload): Promise<ProjectDepartment> {
  const result = await projectRequest<{ department: ProjectDepartment }>(
    `/projects/${encodeURIComponent(projectId)}/departments`,
    {
      method: "POST",
      body: JSON.stringify(payload),
    }
  );
  return result.department;
}

export async function updateDepartment(
  projectId: string,
  departmentId: string,
  payload: Partial<DepartmentPayload> & { status?: "active" | "archived" }
): Promise<ProjectDepartment> {
  const result = await projectRequest<{ department: ProjectDepartment }>(
    `/projects/${encodeURIComponent(projectId)}/departments/${encodeURIComponent(departmentId)}`,
    {
      method: "PATCH",
      body: JSON.stringify(payload),
    }
  );
  return result.department;
}

export async function archiveDepartment(projectId: string, departmentId: string): Promise<ProjectDepartment> {
  const result = await projectRequest<{ department: ProjectDepartment }>(
    `/projects/${encodeURIComponent(projectId)}/departments/${encodeURIComponent(departmentId)}`,
    {
      method: "DELETE",
    }
  );
  return result.department;
}
