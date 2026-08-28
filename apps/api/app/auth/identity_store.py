from __future__ import annotations

import hashlib
from datetime import UTC, datetime

from apps.api.app.db.session import get_connection


def token_is_revoked(*, issuer: str, token_id: str) -> bool:
    token_hash = hashlib.sha256(token_id.encode("utf-8")).hexdigest()
    with get_connection() as conn:
        row = conn.execute(
            """
            select 1
            from revoked_oidc_tokens
            where issuer = %s
              and token_id_hash = %s
              and expires_at > now()
            """,
            (issuer, token_hash),
        ).fetchone()
    return row is not None


def revoke_token(*, issuer: str, token_id: str, expires_at: datetime, reason_code: str) -> None:
    token_hash = hashlib.sha256(token_id.encode("utf-8")).hexdigest()
    with get_connection() as conn:
        conn.execute(
            """
            insert into revoked_oidc_tokens (issuer, token_id_hash, expires_at, reason_code)
            values (%s, %s, %s, %s)
            on conflict (issuer, token_id_hash) do update set
              expires_at = greatest(revoked_oidc_tokens.expires_at, excluded.expires_at),
              revoked_at = now(),
              reason_code = excluded.reason_code
            """,
            (issuer, token_hash, expires_at.astimezone(UTC), reason_code),
        )


def revoke_tenant_access(*, tenant_id: str, user_id: str, reason_code: str = "offboarded") -> bool:
    """Disable tenant access and every active server session in one transaction."""
    with get_connection() as conn:
        membership = conn.execute(
            """
            update tenant_memberships
            set status = 'disabled', disabled_at = now(), updated_at = now()
            where tenant_id = %s::uuid and user_id = %s::uuid and status in ('invited', 'active')
            returning id
            """,
            (tenant_id, user_id),
        ).fetchone()
        conn.execute(
            """
            update auth_sessions
            set status = 'revoked', revoked_at = now()
            where tenant_id = %s::uuid and user_id = %s::uuid and status = 'active'
            """,
            (tenant_id, user_id),
        )
        conn.execute(
            """
            insert into audit_logs (
              tenant_id, user_id, user_role, action, resource_type, outcome, reason, metadata_json
            ) values (%s::uuid, %s, 'System', 'tenant_access_revoked', 'identity', %s, %s, '{}'::jsonb)
            """,
            (tenant_id, user_id, "success" if membership else "not_found", reason_code),
        )
    return membership is not None


def revoke_sessions_after_privilege_change(*, tenant_id: str, user_id: str) -> int:
    with get_connection() as conn:
        cursor = conn.execute(
            """
            update auth_sessions
            set status = 'revoked', revoked_at = now()
            where tenant_id = %s::uuid and user_id = %s::uuid and status = 'active'
            """,
            (tenant_id, user_id),
        )
    return cursor.rowcount
