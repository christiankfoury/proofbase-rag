from __future__ import annotations

import uuid
from typing import Any

from fastapi import HTTPException
from psycopg import Error as PsycopgError

from apps.api.app.core.config import get_settings
from apps.api.app.db.session import get_connection


DEMO_USER_HEADER = "X-Demo-User-Id"
EDITOR_LEVELS = {"contributor", "owner"}
VALID_MEMBERSHIP_LEVELS = {"viewer", "contributor", "owner"}


def _membership_from_row(row: dict[str, Any]) -> dict[str, Any]:
    return {
        "project_id": row["project_id"],
        "project_name": row["project_name"],
        "membership_level": row["membership_level"],
    }


def _user_from_row(row: dict[str, Any], memberships: list[dict[str, Any]]) -> dict[str, Any]:
    return {
        "id": row["id"],
        "display_name": row["display_name"],
        "email": row["email"],
        "business_role": row["business_role"],
        "is_admin": row["is_admin"],
        "status": row["status"],
        "memberships": memberships,
    }


def _load_memberships(conn, user_id: str) -> list[dict[str, Any]]:
    rows = conn.execute(
        """
        select
          pm.project_id::text,
          p.name as project_name,
          pm.membership_level
        from project_memberships pm
        join projects p on p.id = pm.project_id
        where pm.user_id = %s::uuid
          and p.status <> 'archived'
        order by p.name asc
        """,
        (user_id,),
    ).fetchall()
    return [_membership_from_row(dict(row)) for row in rows]


def list_demo_users() -> list[dict[str, Any]]:
    with get_connection() as conn:
        rows = conn.execute(
            """
            select id::text, display_name, email, business_role, is_admin, status
            from demo_users
            where status = 'active'
            order by is_admin asc, display_name asc
            """
        ).fetchall()
        users = []
        for row in rows:
            user_row = dict(row)
            users.append(_user_from_row(user_row, _load_memberships(conn, user_row["id"])))
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
            from demo_users u
            left join project_memberships pm
              on pm.user_id = u.id
             and pm.project_id = %s::uuid
            where u.status = 'active'
              and u.is_admin = false
            order by u.display_name asc
            """,
            (project_id,),
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
            insert into project_memberships (project_id, user_id, membership_level)
            values (%s::uuid, %s::uuid, %s)
            on conflict (project_id, user_id) do update set
              membership_level = excluded.membership_level,
              updated_at = now()
            """,
            (project_id, user_id, membership_level),
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


def get_demo_user(user_id: str) -> dict[str, Any] | None:
    with get_connection() as conn:
        row = conn.execute(
            """
            select id::text, display_name, email, business_role, is_admin, status
            from demo_users
            where id = %s::uuid
              and status = 'active'
            """,
            (user_id,),
        ).fetchone()
        if not row:
            return None
        user_row = dict(row)
        return _user_from_row(user_row, _load_memberships(conn, user_row["id"]))


def resolve_demo_user(user_id: str | None) -> dict[str, Any]:
    selected_user_id = user_id or get_settings().default_demo_user_id
    try:
        uuid.UUID(selected_user_id)
        user = get_demo_user(selected_user_id)
    except ValueError as exc:
        raise HTTPException(status_code=400, detail="X-Demo-User-Id must be a valid seeded demo user UUID.") from exc
    except PsycopgError as exc:
        raise HTTPException(status_code=503, detail="Demo auth schema is not ready.") from exc
    if not user:
        raise HTTPException(status_code=401, detail="Demo user is not active or does not exist.")
    return user


def membership_for_project(user: dict[str, Any], project_id: str) -> dict[str, Any] | None:
    return next((item for item in user["memberships"] if item["project_id"] == project_id), None)


def accessible_project_ids(user: dict[str, Any]) -> set[str] | None:
    if user["is_admin"]:
        return None
    return {item["project_id"] for item in user["memberships"]}


def require_admin(user: dict[str, Any]) -> None:
    if not user["is_admin"]:
        raise HTTPException(status_code=403, detail="Dev & Admin access requires the Admin demo user.")


def require_project_member(user: dict[str, Any], project_id: str) -> dict[str, Any] | None:
    if user["is_admin"]:
        return None
    membership = membership_for_project(user, project_id)
    if not membership:
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
