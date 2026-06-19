from __future__ import annotations

import json
from decimal import Decimal
from typing import Any

from apps.api.app.db.session import get_connection


def _normalize_review(row: dict[str, Any]) -> dict[str, Any]:
    normalized = dict(row)
    for field in ("answer_correctness", "citation_correctness"):
        if isinstance(normalized.get(field), Decimal):
            normalized[field] = float(normalized[field])
    return normalized


def create_review_decision(
    *,
    source_type: str,
    source_id: str,
    question: str,
    answer: str | None,
    expected_answer: str | None,
    expected_sources: list[str],
    actual_citations: list[dict],
    retrieved_chunks: list[dict],
    answer_correctness: float,
    citation_correctness: float,
    decision: str,
    reviewer_role: str,
    reviewer_id: str | None,
    notes: str,
) -> dict[str, Any]:
    with get_connection() as conn:
        row = conn.execute(
            """
            insert into evaluation_reviews (
              source_type,
              source_id,
              question,
              answer,
              expected_answer,
              expected_sources,
              actual_citations_json,
              retrieved_chunks_json,
              answer_correctness,
              citation_correctness,
              decision,
              reviewer_role,
              reviewer_id,
              notes
            )
            values (%s, %s, %s, %s, %s, %s, %s::jsonb, %s::jsonb, %s, %s, %s, %s, %s, %s)
            returning
              id::text,
              source_type,
              source_id,
              question,
              answer,
              expected_answer,
              expected_sources,
              actual_citations_json,
              retrieved_chunks_json,
              answer_correctness,
              citation_correctness,
              decision,
              reviewer_role,
              reviewer_id,
              notes,
              created_at
            """,
            (
                source_type,
                source_id,
                question,
                answer,
                expected_answer,
                expected_sources,
                json.dumps(actual_citations),
                json.dumps(retrieved_chunks),
                answer_correctness,
                citation_correctness,
                decision,
                reviewer_role,
                reviewer_id,
                notes,
            ),
        ).fetchone()
    return _normalize_review(dict(row))


def list_review_decisions(
    *,
    source_type: str | None = None,
    decision: str | None = None,
    limit: int = 50,
) -> list[dict[str, Any]]:
    conditions: list[str] = []
    params: list[Any] = []
    if source_type:
        conditions.append("source_type = %s")
        params.append(source_type)
    if decision:
        conditions.append("decision = %s")
        params.append(decision)
    where = ("where " + " and ".join(conditions)) if conditions else ""
    params.append(limit)
    with get_connection() as conn:
        rows = conn.execute(
            f"""
            select
              id::text,
              source_type,
              source_id,
              question,
              answer,
              expected_answer,
              expected_sources,
              actual_citations_json,
              retrieved_chunks_json,
              answer_correctness,
              citation_correctness,
              decision,
              reviewer_role,
              reviewer_id,
              notes,
              created_at
            from evaluation_reviews
            {where}
            order by created_at desc
            limit %s
            """,
            params,
        ).fetchall()
    return [_normalize_review(dict(row)) for row in rows]
