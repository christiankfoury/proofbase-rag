from __future__ import annotations

import json
from typing import Any

from apps.api.app.db.session import get_connection


VALID_PROJECT_STATUSES = {"active", "paused", "archived"}


def _project_from_row(row: dict[str, Any]) -> dict[str, Any]:
    quality_summary = row.get("quality_summary")
    if isinstance(quality_summary, str):
        quality_summary = json.loads(quality_summary)

    return {
        "id": row["id"],
        "name": row["name"],
        "description": row["description"],
        "status": row["status"],
        "default_retrieval_profile": row["default_retrieval_profile"],
        "seeded_data_key": row.get("seeded_data_key"),
        "quality_status": row["quality_status"],
        "quality_summary": quality_summary or {},
        "created_at": row["created_at"],
        "updated_at": row["updated_at"],
        "archived_at": row.get("archived_at"),
        "document_count": row.get("document_count", 0),
        "chunk_count": row.get("chunk_count", 0),
        "department_count": row.get("department_count", 0),
    }


def _base_project_select(where_clause: str) -> str:
    return f"""
        select
          p.id::text,
          p.name,
          p.description,
          p.status,
          p.default_retrieval_profile,
          p.seeded_data_key,
          p.quality_status,
          p.quality_summary,
          p.created_at,
          p.updated_at,
          p.archived_at,
          count(distinct d.id) filter (where d.status = 'active')::int as document_count,
          count(c.id) filter (where d.status = 'active')::int as chunk_count,
          count(distinct d.department) filter (where d.status = 'active')::int as department_count
        from projects p
        left join documents d on d.project_id = p.id
        left join chunks c on c.document_id = d.id
        {where_clause}
        group by p.id
    """


def list_projects(*, include_archived: bool = False) -> list[dict[str, Any]]:
    where = "" if include_archived else "where p.status <> 'archived'"
    with get_connection() as conn:
        rows = conn.execute(
            _base_project_select(where)
            + """
              order by
                case when p.seeded_data_key = 'northstar_synthetic' then 0 else 1 end,
                p.updated_at desc,
                p.name asc
            """
        ).fetchall()
    return [_project_from_row(dict(row)) for row in rows]


def get_project(project_id: str, *, include_archived: bool = False) -> dict[str, Any] | None:
    where = "where p.id = %s::uuid" + ("" if include_archived else " and p.status <> 'archived'")
    with get_connection() as conn:
        row = conn.execute(_base_project_select(where), (project_id,)).fetchone()
        if not row:
            return None
        project = _project_from_row(dict(row))
        department_rows = conn.execute(
            """
            select
              d.department as name,
              count(distinct d.id)::int as document_count,
              count(c.id)::int as chunk_count,
              min(d.sensitivity) as sensitivity,
              array(
                select distinct role
                from documents rd
                cross join lateral unnest(rd.access_roles) as roles(role)
                where rd.project_id = %s::uuid
                  and rd.department = d.department
                  and rd.status = 'active'
                order by role
              ) as access_roles
            from documents d
            left join chunks c on c.document_id = d.id
            where d.project_id = %s::uuid
              and d.status = 'active'
            group by d.department
            order by d.department asc
            """,
            (project_id, project_id),
        ).fetchall()
        activity_rows = conn.execute(
            """
            select id::text, action, outcome, reason, metadata_json, created_at
            from audit_logs
            where resource_type = 'project'
              and (
                document_id = %s
                or metadata_json->>'project_id' = %s
              )
            order by created_at desc
            limit 8
            """,
            (project_id, project_id),
        ).fetchall()

    project["departments"] = [dict(row) for row in department_rows]
    project["recent_activity"] = [dict(row) for row in activity_rows]
    return project


def create_project(
    *,
    name: str,
    description: str = "",
    status: str = "active",
    default_retrieval_profile: str = "vector-section",
) -> dict[str, Any]:
    if status not in {"active", "paused"}:
        raise ValueError("Project status must be active or paused.")
    with get_connection() as conn:
        row = conn.execute(
            """
            insert into projects (
              name, description, status, default_retrieval_profile, quality_status, quality_summary
            )
            values (
              %s, %s, %s, %s, 'project_evaluation_pending',
              '{"label": "Project evaluation pending", "detail": "No project-scoped benchmark has been run for this workspace yet."}'::jsonb
            )
            returning id::text
            """,
            (name, description, status, default_retrieval_profile),
        ).fetchone()
    project = get_project(row["id"], include_archived=True)
    if project is None:
        raise RuntimeError("Created project could not be loaded.")
    return project


def update_project(
    project_id: str,
    *,
    name: str | None = None,
    description: str | None = None,
    status: str | None = None,
    default_retrieval_profile: str | None = None,
) -> dict[str, Any] | None:
    assignments: list[str] = []
    params: list[Any] = []
    if name is not None:
        assignments.append("name = %s")
        params.append(name)
    if description is not None:
        assignments.append("description = %s")
        params.append(description)
    if status is not None:
        if status not in VALID_PROJECT_STATUSES:
            raise ValueError("Project status must be active, paused, or archived.")
        assignments.append("status = %s")
        params.append(status)
        assignments.append("archived_at = case when %s = 'archived' then coalesce(archived_at, now()) else null end")
        params.append(status)
    if default_retrieval_profile is not None:
        assignments.append("default_retrieval_profile = %s")
        params.append(default_retrieval_profile)

    if not assignments:
        return get_project(project_id, include_archived=True)

    params.append(project_id)
    with get_connection() as conn:
        row = conn.execute(
            f"""
            update projects
            set {", ".join(assignments)}, updated_at = now()
            where id = %s::uuid
            returning id::text
            """,
            params,
        ).fetchone()
    if not row:
        return None
    return get_project(row["id"], include_archived=True)


def archive_project(project_id: str) -> dict[str, Any] | None:
    return update_project(project_id, status="archived")
