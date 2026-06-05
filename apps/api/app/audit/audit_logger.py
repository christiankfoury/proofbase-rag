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

