from __future__ import annotations

import json
from typing import Any

from apps.api.app.db.session import get_connection
from apps.api.app.auth.tenant_context import current_tenant_id
from apps.api.app.privacy.redaction import bounded_reason_code, sanitize_for_log
from apps.api.app.monitoring.security_events import emit_audit_security_event


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
    tenant_id: str | None = None,
) -> bool:
    safe_metadata = sanitize_for_log(metadata or {})
    try:
        with get_connection() as conn:
            selected_tenant_id = tenant_id or current_tenant_id()
            conn.execute(
                """
                insert into audit_logs (
                  tenant_id, user_id, user_role, action, document_id, resource_type,
                  outcome, reason, metadata_json
                )
                values (%s::uuid, %s, %s, %s, %s, %s, %s, %s, %s::jsonb)
                """,
                (
                    selected_tenant_id, user_id,
                    user_role,
                    action,
                    document_id,
                    resource_type,
                    outcome,
                    bounded_reason_code(reason),
                    json.dumps(safe_metadata),
                ),
            )
        emit_audit_security_event(
            action=action,
            outcome=outcome,
            reason=bounded_reason_code(reason),
            tenant_id=str(selected_tenant_id),
            user_id=user_id,
            metadata=safe_metadata,
        )
        return True
    except Exception:
        # Audit logging must never expose content or break the user-facing path.
        return False


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
        result: list[dict[str, Any]] = []
        for row in rows:
            event = dict(row)
            event["metadata_json"] = sanitize_for_log(event.get("metadata_json") or {})
            result.append(event)
        return result
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
