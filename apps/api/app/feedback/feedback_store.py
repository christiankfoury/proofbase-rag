from __future__ import annotations

import json
from typing import Any

from apps.api.app.db.session import get_connection
from apps.api.app.auth.tenant_context import current_tenant_id


VALID_RATINGS = {"thumbs_up", "thumbs_down"}
VALID_CATEGORIES = {
    "correct",
    "incorrect_answer",
    "missing_citation",
    "wrong_citation",
    "hallucination",
    "refused_incorrectly",
    "should_have_refused",
    "not_found_incorrectly",
    "permission_issue",
    "unclear_answer",
    "other",
}
NEGATIVE_CATEGORIES = VALID_CATEGORIES - {"correct", "other"}


def submit_feedback(
    *,
    session_id: str | None,
    message_id: str | None,
    question: str,
    answer: str,
    response_type: str | None,
    citations: list[dict] | None,
    user_role: str,
    rating: str,
    user_comment: str | None,
    feedback_category: str,
    tenant_id: str | None = None,
) -> str:
    if rating not in VALID_RATINGS:
        raise ValueError(f"Invalid rating '{rating}'. Must be one of: {sorted(VALID_RATINGS)}")
    if feedback_category not in VALID_CATEGORIES:
        feedback_category = "other"
    with get_connection() as conn:
        selected_tenant_id = tenant_id or current_tenant_id()
        row = conn.execute(
            """
            insert into feedback (
              tenant_id, session_id, message_id, question, answer, response_type,
              citations_json, user_role, rating, user_comment, feedback_category
            )
            values (%s::uuid, %s, %s, %s, %s, %s, %s::jsonb, %s, %s, %s, %s)
            returning id::text
            """,
            (
                selected_tenant_id, session_id,
                message_id,
                question,
                answer,
                response_type,
                json.dumps(citations or []),
                user_role,
                rating,
                user_comment,
                feedback_category,
            ),
        ).fetchone()
    return row["id"]


def list_feedback(
    *,
    rating: str | None = None,
    feedback_category: str | None = None,
    limit: int = 50,
    offset: int = 0,
) -> list[dict[str, Any]]:
    conditions: list[str] = []
    params: list[Any] = []
    if rating:
        conditions.append("rating = %s")
        params.append(rating)
    if feedback_category:
        conditions.append("feedback_category = %s")
        params.append(feedback_category)
    where = ("where " + " and ".join(conditions)) if conditions else ""
    params.extend([limit, offset])
    with get_connection() as conn:
        rows = conn.execute(
            f"""
            select
              id::text as feedback_id,
              session_id::text,
              message_id::text,
              question,
              answer,
              response_type,
              citations_json,
              user_role,
              rating,
              user_comment,
              feedback_category,
              created_at
            from feedback
            {where}
            order by created_at desc
            limit %s offset %s
            """,
            params,
        ).fetchall()
    return [dict(row) for row in rows]


def feedback_summary() -> dict[str, Any]:
    with get_connection() as conn:
        total = conn.execute("select count(*) as n from feedback").fetchone()["n"]
        up = conn.execute("select count(*) as n from feedback where rating = 'thumbs_up'").fetchone()["n"]
        down = conn.execute("select count(*) as n from feedback where rating = 'thumbs_down'").fetchone()["n"]
        category_rows = conn.execute(
            """
            select feedback_category, count(*) as n
            from feedback
            where rating = 'thumbs_down'
            group by feedback_category
            order by n desc
            """
        ).fetchall()
    return {
        "total": total,
        "thumbs_up": up,
        "thumbs_down": down,
        "negative_category_breakdown": {row["feedback_category"]: row["n"] for row in category_rows},
    }
