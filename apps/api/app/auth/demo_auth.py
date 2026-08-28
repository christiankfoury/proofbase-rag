from __future__ import annotations

import uuid
import hashlib
from typing import Any

from fastapi import HTTPException
from psycopg import Error as PsycopgError

from apps.api.app.core.config import get_settings
from apps.api.app.db.session import get_connection


DEMO_USER_HEADER = "X-Demo-User-Id"
TENANT_HEADER = "X-Tenant-Id"
EDITOR_LEVELS = {"contributor", "owner"}
VALID_MEMBERSHIP_LEVELS = {"viewer", "contributor", "owner"}


def _membership_from_row(row: dict[str, Any]) -> dict[str, Any]:
    return {
        "tenant_id": row["tenant_id"],
        "project_id": row["project_id"],
        "project_name": row["project_name"],
        "membership_level": row["membership_level"],
    }


def _user_from_row(
    row: dict[str, Any],
    memberships: list[dict[str, Any]],
    *,
    tenant_id: str,
    tenant_role: str,
    tenants: list[dict[str, Any]],
    identity_source: str,
) -> dict[str, Any]:
    return {
        "id": row["id"],
        "display_name": row["display_name"],
        "email": row["email"],
        "business_role": row["business_role"],
        "is_admin": row["is_admin"],
        "status": row["status"],
        "memberships": memberships,
        "tenant_id": tenant_id,
        "tenant_role": tenant_role,
        "tenants": tenants,
        "identity_source": identity_source,
    }


def _load_memberships(conn, user_id: str, tenant_id: str) -> list[dict[str, Any]]:
    rows = conn.execute(
        """
        select
          pm.tenant_id::text,
          pm.project_id::text,
          p.name as project_name,
          pm.membership_level
        from project_memberships pm
        join projects p on p.id = pm.project_id
        where pm.user_id = %s::uuid
          and pm.tenant_id = %s::uuid
          and p.status <> 'archived'
        order by p.name asc
        """,
        (user_id, tenant_id),
    ).fetchall()
    return [_membership_from_row(dict(row)) for row in rows]


def _tenant_memberships(conn, user_id: str) -> list[dict[str, Any]]:
    rows = conn.execute(
        """
        select t.id::text, t.name, t.slug, tm.tenant_role
        from tenant_memberships tm
        join tenants t on t.id = tm.tenant_id
        where tm.user_id = %s::uuid
          and tm.status = 'active'
          and t.status = 'active'
        order by t.name
        """,
        (user_id,),
    ).fetchall()
    return [dict(row) for row in rows]


def list_demo_users(tenant_id: str | None = None) -> list[dict[str, Any]]:
    selected_tenant_id = tenant_id or get_settings().default_demo_tenant_id
    with get_connection() as conn:
        rows = conn.execute(
            """
            select u.id::text, u.display_name, u.email, u.business_role, u.is_admin, u.status,
                   tm.tenant_role
            from demo_users u
            join tenant_memberships tm on tm.user_id = u.id
            where u.status = 'active'
              and tm.status = 'active'
              and tm.tenant_id = %s::uuid
            order by is_admin asc, display_name asc
            """,
            (selected_tenant_id,),
        ).fetchall()
        users = []
        for row in rows:
            user_row = dict(row)
            users.append(
                _user_from_row(
                    user_row,
                    _load_memberships(conn, user_row["id"], selected_tenant_id),
                    tenant_id=selected_tenant_id,
                    tenant_role=user_row["tenant_role"],
                    tenants=_tenant_memberships(conn, user_row["id"]),
                    identity_source="local_demo",
                )
            )
    return users


def list_project_memberships(project_id: str) -> list[dict[str, Any]]:
    with get_connection() as conn:
        rows = conn.execute(
            """
            select
              u.id::text as user_id,
              u.display_name,
              u.email,
              u.business_role,
              u.is_admin,
              pm.membership_level,
              pm.created_at,
              pm.updated_at
            from projects p
            join tenant_memberships tm
              on tm.tenant_id = p.tenant_id
             and tm.status = 'active'
            join demo_users u on u.id = tm.user_id
            left join project_memberships pm
              on pm.user_id = u.id
             and pm.project_id = %s::uuid
            where p.id = %s::uuid
              and u.status = 'active'
              and u.is_admin = false
            order by u.display_name asc
            """,
            (project_id, project_id),
        ).fetchall()
    return [dict(row) for row in rows]


def set_project_membership(project_id: str, user_id: str, membership_level: str) -> dict[str, Any] | None:
    if membership_level not in VALID_MEMBERSHIP_LEVELS:
        raise ValueError("Membership level must be viewer, contributor, or owner.")
    with get_connection() as conn:
        eligible = conn.execute(
            """
            select u.id
            from demo_users u
            join projects p on p.id = %s::uuid
            join tenant_memberships tm
              on tm.user_id = u.id
             and tm.tenant_id = p.tenant_id
             and tm.status = 'active'
            where u.id = %s::uuid
              and u.status = 'active'
              and u.is_admin = false
              and p.status <> 'archived'
            """,
            (project_id, user_id),
        ).fetchone()
        if not eligible:
            return None
        conn.execute(
            """
            insert into project_memberships (tenant_id, project_id, user_id, membership_level)
            select p.tenant_id, p.id, %s::uuid, %s
            from projects p
            where p.id = %s::uuid
            on conflict (project_id, user_id) do update set
              tenant_id = excluded.tenant_id,
              membership_level = excluded.membership_level,
              updated_at = now()
            """,
            (user_id, membership_level, project_id),
        )
    return next((item for item in list_project_memberships(project_id) if item["user_id"] == user_id), None)


def remove_project_membership(project_id: str, user_id: str) -> bool:
    with get_connection() as conn:
        cursor = conn.execute(
            """
            delete from project_memberships
            where project_id = %s::uuid
              and user_id = %s::uuid
            """,
            (project_id, user_id),
        )
    return cursor.rowcount > 0


def get_demo_user(user_id: str, tenant_id: str | None = None) -> dict[str, Any] | None:
    selected_tenant_id = tenant_id or get_settings().default_demo_tenant_id
    with get_connection() as conn:
        row = conn.execute(
            """
            select u.id::text, u.display_name, u.email, u.business_role, u.is_admin, u.status,
                   tm.tenant_role
            from demo_users u
            join tenant_memberships tm on tm.user_id = u.id
            join tenants t on t.id = tm.tenant_id
            where u.id = %s::uuid
              and u.status = 'active'
              and tm.tenant_id = %s::uuid
              and tm.status = 'active'
              and t.status = 'active'
            """,
            (user_id, selected_tenant_id),
        ).fetchone()
        if not row:
            return None
        user_row = dict(row)
        return _user_from_row(
            user_row,
            _load_memberships(conn, user_row["id"], selected_tenant_id),
            tenant_id=selected_tenant_id,
            tenant_role=user_row["tenant_role"],
            tenants=_tenant_memberships(conn, user_row["id"]),
            identity_source="local_demo",
        )


def resolve_demo_user(user_id: str | None, tenant_id: str | None = None) -> dict[str, Any]:
    selected_user_id = user_id or get_settings().default_demo_user_id
    try:
        uuid.UUID(selected_user_id)
        selected_tenant_id = tenant_id or get_settings().default_demo_tenant_id
        uuid.UUID(selected_tenant_id)
        user = get_demo_user(selected_user_id, selected_tenant_id)
    except ValueError as exc:
        raise HTTPException(status_code=400, detail="X-Demo-User-Id must be a valid seeded demo user UUID.") from exc
    except PsycopgError as exc:
        raise HTTPException(status_code=503, detail="Demo auth schema is not ready.") from exc
    if not user:
        raise HTTPException(status_code=401, detail="Demo user is not active or does not exist.")
    return user


def resolve_oidc_user(*, issuer: str, subject: str, tenant_id: str) -> dict[str, Any]:
    try:
        uuid.UUID(tenant_id)
    except ValueError as exc:
        raise HTTPException(status_code=400, detail="X-Tenant-Id must be a valid tenant UUID.") from exc
    with get_connection() as conn:
        row = conn.execute(
            """
            select u.id::text, u.display_name, u.email, u.business_role, u.is_admin, u.status,
                   tm.tenant_role
            from external_identities ei
            join demo_users u on u.id = ei.user_id
            join tenant_memberships tm on tm.user_id = u.id
            join tenants t on t.id = tm.tenant_id
            where ei.issuer = %s
              and ei.subject = %s
              and ei.status = 'active'
              and u.status = 'active'
              and tm.tenant_id = %s::uuid
              and tm.status = 'active'
              and t.status = 'active'
            """,
            (issuer, subject, tenant_id),
        ).fetchone()
        if not row:
            raise HTTPException(status_code=401, detail="Identity is not provisioned for the selected tenant.")
        user_row = dict(row)
        conn.execute(
            """
            update external_identities set last_authenticated_at = now(), updated_at = now()
            where issuer = %s and subject = %s
            """,
            (issuer, subject),
        )
        return _user_from_row(
            user_row,
            _load_memberships(conn, user_row["id"], tenant_id),
            tenant_id=tenant_id,
            tenant_role=user_row["tenant_role"],
            tenants=_tenant_memberships(conn, user_row["id"]),
            identity_source="oidc",
        )


def membership_for_project(user: dict[str, Any], project_id: str) -> dict[str, Any] | None:
    return next((item for item in user["memberships"] if item["project_id"] == project_id), None)


def accessible_project_ids(user: dict[str, Any]) -> set[str] | None:
    if user["is_admin"] and (not user.get("tenant_id") or user.get("tenant_role") in {"admin", "owner"}):
        return None
    return {item["project_id"] for item in user["memberships"]}


def require_admin(user: dict[str, Any]) -> None:
    if not user["is_admin"] or (
        user.get("tenant_id") and user.get("tenant_role") not in {"admin", "owner"}
    ):
        raise HTTPException(status_code=403, detail="Dev & Admin access requires the Admin demo user.")


def _require_project_tenant(user: dict[str, Any], project_id: str) -> None:
    tenant_id = user.get("tenant_id")
    if not tenant_id:
        return
    with get_connection() as conn:
        row = conn.execute(
            "select 1 from projects where id = %s::uuid and tenant_id = %s::uuid and status <> 'archived'",
            (project_id, tenant_id),
        ).fetchone()
    if not row:
        _log_project_denial(user, project_id)
        raise HTTPException(status_code=404, detail="Project not found.")


def _log_project_denial(user: dict[str, Any], project_id: str) -> None:
    from apps.api.app.audit.audit_logger import log_audit_event

    log_audit_event(
        action="project_access_denied",
        user_role=user["business_role"],
        user_id=user["id"],
        resource_type="project",
        outcome="denied",
        reason="not_found_or_not_authorized",
        metadata={"requested_id_hash": hashlib.sha256(project_id.encode("utf-8")).hexdigest()},
    )


def require_project_member(user: dict[str, Any], project_id: str) -> dict[str, Any] | None:
    if user["is_admin"] and (
        not user.get("tenant_id") or user.get("tenant_role") in {"admin", "owner"}
    ):
        _require_project_tenant(user, project_id)
        return None
    membership = membership_for_project(user, project_id)
    if not membership:
        _log_project_denial(user, project_id)
        raise HTTPException(status_code=403, detail="This demo user is not a member of that project.")
    return membership


def require_project_editor(user: dict[str, Any], project_id: str) -> dict[str, Any] | None:
    if user["is_admin"]:
        return None
    membership = require_project_member(user, project_id)
    if membership and membership["membership_level"] not in EDITOR_LEVELS:
        raise HTTPException(status_code=403, detail="Project changes require contributor, owner, or admin access.")
    return membership


def require_project_owner(user: dict[str, Any], project_id: str) -> dict[str, Any] | None:
    if user["is_admin"]:
        return None
    membership = require_project_member(user, project_id)
    if membership and membership["membership_level"] != "owner":
        raise HTTPException(status_code=403, detail="Project membership changes require owner or admin access.")
    return membership
