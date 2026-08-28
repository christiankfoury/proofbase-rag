from __future__ import annotations

import json
from typing import Any

from apps.api.app.db.session import get_connection


VALID_PROJECT_STATUSES = {"active", "paused", "archived"}
VALID_DEPARTMENT_STATUSES = {"active", "archived"}
VALID_DEPARTMENT_ICONS = {"people", "shield", "chart", "briefcase", "lock", "key", "building"}
VALID_DEPARTMENT_COLORS = {"moss", "steel", "rust", "stone"}


def _project_from_row(row: dict[str, Any]) -> dict[str, Any]:
    quality_summary = row.get("quality_summary")
    if isinstance(quality_summary, str):
        quality_summary = json.loads(quality_summary)

    return {
        "id": row["id"],
        "tenant_id": row.get("tenant_id"),
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
          p.tenant_id::text,
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
          coalesce(doc_stats.document_count, 0)::int as document_count,
          coalesce(doc_stats.chunk_count, 0)::int as chunk_count,
          coalesce(dept_stats.department_count, 0)::int as department_count
        from projects p
        left join lateral (
          select
            count(distinct d.id) filter (where d.status = 'active') as document_count,
            count(c.id) filter (where d.status = 'active') as chunk_count
          from documents d
          left join chunks c on c.document_id = d.id
          where d.project_id = p.id
        ) doc_stats on true
        left join lateral (
          select count(*) as department_count
          from project_departments pd
          where pd.project_id = p.id
            and pd.status <> 'archived'
        ) dept_stats on true
        {where_clause}
    """


def list_projects(*, tenant_id: str | None = None, include_archived: bool = False) -> list[dict[str, Any]]:
    conditions: list[str] = []
    params: list[Any] = []
    if tenant_id is not None:
        conditions.append("p.tenant_id = %s::uuid")
        params.append(tenant_id)
    if not include_archived:
        conditions.append("p.status <> 'archived'")
    where = ("where " + " and ".join(conditions)) if conditions else ""
    with get_connection() as conn:
        rows = conn.execute(
            _base_project_select(where)
            + """
              order by
                case when p.seeded_data_key = 'northstar_synthetic' then 0 else 1 end,
                p.updated_at desc,
                p.name asc
            """,
            params,
        ).fetchall()
    return [_project_from_row(dict(row)) for row in rows]


def get_project(project_id: str, *, tenant_id: str | None = None, include_archived: bool = False) -> dict[str, Any] | None:
    where = "where p.id = %s::uuid"
    params: list[Any] = [project_id]
    if tenant_id is not None:
        where += " and p.tenant_id = %s::uuid"
        params.append(tenant_id)
    if not include_archived:
        where += " and p.status <> 'archived'"
    with get_connection() as conn:
        row = conn.execute(_base_project_select(where), params).fetchone()
        if not row:
            return None
        project = _project_from_row(dict(row))
        department_rows = _department_rows(conn, project_id, include_archived=False)
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


def _department_rows(conn, project_id: str, *, include_archived: bool = False):
    status_clause = "" if include_archived else "and pd.status <> 'archived'"
    return conn.execute(
        f"""
        select
          pd.id::text,
          pd.project_id::text,
          pd.name,
          pd.icon,
          pd.color,
          pd.description,
          pd.default_access_roles,
          pd.seeded_data_key,
          pd.status,
          pd.created_at,
          pd.updated_at,
          pd.archived_at,
          count(distinct d.id) filter (where d.status = 'active')::int as document_count,
          count(c.id) filter (where d.status = 'active')::int as chunk_count,
          coalesce(array(
            select distinct role
            from documents rd
            cross join lateral unnest(rd.access_roles) as roles(role)
            where rd.department_id = pd.id
              and rd.status = 'active'
            order by role
          ), '{{}}') as access_roles
        from project_departments pd
        left join documents d on d.department_id = pd.id
        left join chunks c on c.document_id = d.id
        where pd.project_id = %s::uuid
          {status_clause}
        group by pd.id
        order by
          case
            when pd.seeded_data_key = 'HR Public' then 0
            when pd.seeded_data_key = 'HR Admin' then 1
            when pd.seeded_data_key = 'IT Public' then 2
            when pd.seeded_data_key = 'IT Admin' then 3
            when pd.seeded_data_key = 'Sales Enablement' then 4
            when pd.seeded_data_key = 'Manager Only' then 5
            when pd.seeded_data_key = 'Finance' then 6
            when pd.seeded_data_key = 'Legal' then 7
            when pd.seeded_data_key = 'Engineering' then 8
            when pd.seeded_data_key = 'Support' then 9
            when pd.seeded_data_key = 'Operations' then 10
            else 20
          end,
          pd.name asc
        """,
        (project_id,),
    ).fetchall()


def get_department(project_id: str, department_id: str, *, include_archived: bool = False) -> dict[str, Any] | None:
    with get_connection() as conn:
        rows = _department_rows(conn, project_id, include_archived=include_archived)
    return next((dict(row) for row in rows if row["id"] == department_id), None)


def create_project(
    *,
    tenant_id: str,
    created_by_user_id: str,
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
              tenant_id, name, description, status, default_retrieval_profile, quality_status, quality_summary
            )
            values (
              %s::uuid, %s, %s, %s, %s, 'project_evaluation_pending',
              '{"label": "Project evaluation pending", "detail": "No project-scoped benchmark has been run for this workspace yet."}'::jsonb
            )
            returning id::text
            """,
            (tenant_id, name, description, status, default_retrieval_profile),
        ).fetchone()
        conn.execute(
            """
            insert into project_memberships (tenant_id, project_id, user_id, membership_level)
            values (%s::uuid, %s::uuid, %s::uuid, 'owner')
            on conflict (project_id, user_id) do update set
              tenant_id = excluded.tenant_id,
              membership_level = 'owner',
              updated_at = now()
            """,
            (tenant_id, row["id"], created_by_user_id),
        )
    project = get_project(row["id"], tenant_id=tenant_id, include_archived=True)
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


def create_department(
    *,
    project_id: str,
    name: str,
    icon: str = "building",
    color: str = "steel",
    description: str = "",
    default_access_roles: list[str] | None = None,
) -> dict[str, Any]:
    _validate_department_metadata(icon=icon, color=color)
    roles = default_access_roles or []
    with get_connection() as conn:
        row = conn.execute(
            """
            insert into project_departments (
              tenant_id, project_id, name, icon, color, description, default_access_roles
            )
            select tenant_id, id, %s, %s, %s, %s, %s
            from projects
            where id = %s::uuid
            returning id::text
            """,
            (name, icon, color, description, roles, project_id),
        ).fetchone()
    department = get_department(project_id, row["id"], include_archived=True)
    if department is None:
        raise RuntimeError("Created department could not be loaded.")
    return department


def update_department(
    project_id: str,
    department_id: str,
    *,
    name: str | None = None,
    icon: str | None = None,
    color: str | None = None,
    description: str | None = None,
    default_access_roles: list[str] | None = None,
    status: str | None = None,
) -> dict[str, Any] | None:
    assignments: list[str] = []
    params: list[Any] = []
    if name is not None:
        assignments.append("name = %s")
        params.append(name)
    if icon is not None:
        _validate_department_metadata(icon=icon)
        assignments.append("icon = %s")
        params.append(icon)
    if color is not None:
        _validate_department_metadata(color=color)
        assignments.append("color = %s")
        params.append(color)
    if description is not None:
        assignments.append("description = %s")
        params.append(description)
    if default_access_roles is not None:
        assignments.append("default_access_roles = %s")
        params.append(default_access_roles)
    if status is not None:
        if status not in VALID_DEPARTMENT_STATUSES:
            raise ValueError("Department status must be active or archived.")
        assignments.append("status = %s")
        params.append(status)
        assignments.append("archived_at = case when %s = 'archived' then coalesce(archived_at, now()) else null end")
        params.append(status)

    if not assignments:
        return get_department(project_id, department_id, include_archived=True)

    params.extend([project_id, department_id])
    with get_connection() as conn:
        row = conn.execute(
            f"""
            update project_departments
            set {", ".join(assignments)}, updated_at = now()
            where project_id = %s::uuid
              and id = %s::uuid
            returning id::text
            """,
            params,
        ).fetchone()
    if not row:
        return None
    return get_department(project_id, row["id"], include_archived=True)


def archive_department(project_id: str, department_id: str) -> dict[str, Any] | None:
    return update_department(project_id, department_id, status="archived")


def _validate_department_metadata(*, icon: str | None = None, color: str | None = None) -> None:
    if icon is not None and icon not in VALID_DEPARTMENT_ICONS:
        raise ValueError(f"Department icon must be one of: {', '.join(sorted(VALID_DEPARTMENT_ICONS))}.")
    if color is not None and color not in VALID_DEPARTMENT_COLORS:
        raise ValueError(f"Department color must be one of: {', '.join(sorted(VALID_DEPARTMENT_COLORS))}.")
