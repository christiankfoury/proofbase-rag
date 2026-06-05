from __future__ import annotations

import json

from apps.api.app.db.session import get_connection


def create_session(user_role: str, user_id: str | None = None) -> str:
    with get_connection() as conn:
        row = conn.execute(
            """
            insert into chat_sessions (user_id, user_role)
            values (%s, %s)
            returning id::text
            """,
            (user_id, user_role),
        ).fetchone()
    return row["id"]


def get_session(session_id: str) -> dict | None:
    with get_connection() as conn:
        row = conn.execute(
            """
            select id::text, user_id, user_role, created_at, updated_at
            from chat_sessions
            where id = %s
            """,
            (session_id,),
        ).fetchone()
    return dict(row) if row else None


def list_messages(session_id: str, limit: int = 8) -> list[dict]:
    with get_connection() as conn:
        rows = conn.execute(
            """
            select
              id::text,
              role,
              content,
              response_type,
              citations_json,
              confidence_json,
              metadata_json,
              created_at
            from chat_messages
            where session_id = %s
            order by created_at desc
            limit %s
            """,
            (session_id, limit),
        ).fetchall()
    return [dict(row) for row in reversed(rows)]


def add_message(
    *,
    session_id: str,
    role: str,
    content: str,
    response_type: str | None = None,
    citations: list[dict] | None = None,
    confidence: dict | None = None,
    metadata: dict | None = None,
) -> str:
    with get_connection() as conn:
        row = conn.execute(
            """
            insert into chat_messages (
              session_id, role, content, response_type,
              citations_json, confidence_json, metadata_json
            )
            values (%s, %s, %s, %s, %s::jsonb, %s::jsonb, %s::jsonb)
            returning id::text
            """,
            (
                session_id,
                role,
                content,
                response_type,
                json.dumps(citations or []),
                json.dumps(confidence or {}),
                json.dumps(metadata or {}),
            ),
        ).fetchone()
        conn.execute(
            "update chat_sessions set updated_at = now() where id = %s",
            (session_id,),
        )
    return row["id"]

