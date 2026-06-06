from __future__ import annotations

import json
from typing import Any

from apps.api.app.db.session import get_connection


def log_audit_event(
    *,
    action: str,
    user_role: str,
    outcome: str,
    resource_type: str = "retrieval",
    document_id: str | None = None,
    user_id: str | None = None,
    reason: str | None = None,
    metadata: dict[str, Any] | None = None,
) -> None:
    safe_metadata = metadata or {}
    try:
        with get_connection() as conn:
            conn.execute(
                """
                insert into audit_logs (
                  user_id, user_role, action, document_id, resource_type,
                  outcome, reason, metadata_json
                )
                values (%s, %s, %s, %s, %s, %s, %s, %s::jsonb)
                """,
                (
                    user_id,
                    user_role,
                    action,
                    document_id,
                    resource_type,
                    outcome,
                    reason,
                    json.dumps(safe_metadata),
                ),
            )
    except Exception:
        # Audit logging must never expose content or break the user-facing path.
        return


def list_audit_events(
    *,
    limit: int = 20,
    action: str | None = None,
    outcome: str | None = None,
) -> list[dict[str, Any]]:
    conditions: list[str] = []
    params: list[Any] = []
    if action:
        conditions.append("action = %s")
        params.append(action)
    if outcome:
        conditions.append("outcome = %s")
        params.append(outcome)
    where = ("where " + " and ".join(conditions)) if conditions else ""
    params.append(limit)
    try:
        with get_connection() as conn:
            rows = conn.execute(
                f"""
                select
                  id::text, user_id, user_role, action, document_id,
                  resource_type, outcome, reason, metadata_json, created_at
                from audit_logs
                {where}
                order by created_at desc
                limit %s
                """,
                params,
            ).fetchall()
        return [dict(row) for row in rows]
    except Exception:
        return []


def audit_summary() -> dict[str, Any]:
    try:
        with get_connection() as conn:
            rows = conn.execute(
                """
                select action, count(*) as n
                from audit_logs
                group by action
                order by n desc
                """
            ).fetchall()
        return {"counts_by_action": {row["action"]: row["n"] for row in rows}}
    except Exception:
        return {"counts_by_action": {}}

