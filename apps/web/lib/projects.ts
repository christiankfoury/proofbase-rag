import { API_BASE } from "@/lib/api";

export type ProjectStatus = "active" | "paused" | "archived";

export type ProjectDepartment = {
  name: string;
  document_count: number;
  chunk_count: number;
  sensitivity?: string | null;
  access_roles: string[];
};

export type ProjectActivity = {
  id: string;
  action: string;
  outcome: string;
  reason: string | null;
  metadata_json: Record<string, unknown>;
  created_at: string;
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
