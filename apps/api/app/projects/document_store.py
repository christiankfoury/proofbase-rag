from __future__ import annotations

import json
from datetime import UTC, datetime
import hashlib
from typing import Any

from apps.api.app.db.session import get_connection
from apps.api.app.permissions.access_control import sensitivity_from_restricted


def _json_value(value: Any, default: Any) -> Any:
    if value is None:
        return default
    if isinstance(value, str):
        return json.loads(value)
    return value


def _document_from_row(row: dict[str, Any]) -> dict[str, Any]:
    return {
        "id": row["id"],
        "project_id": row["project_id"],
        "department_id": row.get("department_id"),
        "external_document_id": row["external_document_id"],
        "title": row["title"],
        "department": row["department"],
        "category": row["category"],
        "source_type": row["source_type"],
        "source_path": row["source_path"],
        "access_roles": list(row["access_roles"] or []),
        "sensitivity": row["sensitivity"],
        "restricted": row["restricted"],
        "status": row["status"],
        "created_at": row["created_at"],
        "updated_at": row["updated_at"],
        "version": {
            "id": row.get("version_id"),
            "version_label": row.get("version_label"),
            "effective_date": row.get("effective_date"),
            "owner": row.get("owner"),
            "review_cycle": row.get("review_cycle"),
            "content_hash": row.get("content_hash"),
            "metadata": _json_value(row.get("version_metadata_json"), {}),
            "ingestion_status": row.get("ingestion_status") or "not_indexed",
            "indexed_at": row.get("indexed_at"),
            "failed_at": row.get("failed_at"),
            "failure_reason": row.get("failure_reason"),
        },
        "chunk_count": row.get("chunk_count", 0),
        "markdown_preview": row.get("markdown_preview") or "",
        "ingestion_job": {
            "id": row.get("ingestion_job_id"),
            "status": row.get("job_status"),
            "stage": row.get("job_stage"),
            "status_detail": row.get("job_status_detail"),
            "started_at": row.get("job_started_at"),
            "completed_at": row.get("job_completed_at"),
            "failed_at": row.get("job_failed_at"),
            "error_message": row.get("job_error_message"),
        }
        if row.get("ingestion_job_id")
        else None,
    }


def _hash_bytes(content: bytes) -> str:
    return hashlib.sha256(content).hexdigest()


def _hash_text(text: str) -> str:
    return hashlib.sha256(text.encode("utf-8")).hexdigest()


def list_project_documents(
    project_id: str,
    *,
    department_id: str | None = None,
    include_archived: bool = False,
) -> list[dict[str, Any]]:
    status_clause = "" if include_archived else "and d.status <> 'archived'"
    department_clause = "and d.department_id = %s::uuid" if department_id else ""
    params: list[Any] = [project_id]
    if department_id:
        params.append(department_id)

    with get_connection() as conn:
        rows = conn.execute(
            f"""
            select
              d.id::text,
              d.project_id::text,
              d.department_id::text,
              d.external_document_id,
              d.title,
              d.department,
              d.category,
              d.source_type,
              d.source_path,
              d.access_roles,
              d.sensitivity,
              d.restricted,
              d.status,
              d.created_at,
              d.updated_at,
              dv.id::text as version_id,
              dv.version_label,
              dv.effective_date,
              dv.owner,
              dv.review_cycle,
              dv.content_hash,
              dv.metadata_json as version_metadata_json,
              dv.ingestion_status,
              dv.indexed_at,
              dv.failed_at,
              dv.failure_reason,
              coalesce(chunk_stats.chunk_count, 0)::int as chunk_count,
              left(coalesce(dv.extracted_text, ''), 4000) as markdown_preview,
              ij.id::text as ingestion_job_id,
              ij.status as job_status,
              ij.stage as job_stage,
              ij.status_detail as job_status_detail,
              ij.started_at as job_started_at,
              ij.completed_at as job_completed_at,
              ij.failed_at as job_failed_at,
              ij.error_message as job_error_message
            from documents d
            left join lateral (
              select *
              from document_versions version_candidate
              where version_candidate.document_id = d.id
              order by
                case when version_candidate.id = d.current_version_id then 0 else 1 end,
                version_candidate.created_at desc
              limit 1
            ) dv on true
            left join lateral (
              select count(*) as chunk_count
              from chunks c
              where c.document_version_id = dv.id
            ) chunk_stats on true
            left join lateral (
              select *
              from ingestion_jobs job_candidate
              where job_candidate.document_id = d.id
                and (
                  dv.id is null
                  or job_candidate.document_version_id = dv.id
                )
              order by job_candidate.created_at desc
              limit 1
            ) ij on true
            where d.project_id = %s::uuid
              {department_clause}
              {status_clause}
            order by d.external_document_id asc
            """,
            params,
        ).fetchall()

    return [_document_from_row(dict(row)) for row in rows]


def create_pending_review_document(
    *,
    project_id: str,
    department: dict[str, Any],
    external_document_id: str,
    title: str,
    source_path: str,
    source_file_name: str,
    source_file_type: str,
    raw_file_bytes: bytes,
    access_roles: list[str],
    restricted: bool,
    extracted_markdown: str,
    extraction_metadata: dict[str, Any],
) -> dict[str, Any]:
    sensitivity = sensitivity_from_restricted(restricted)
    category = department.get("seeded_data_key") or department["name"]
    now = datetime.now(UTC).isoformat()
    version_metadata = {
        "document_id": external_document_id,
        "title": title,
        "department": department["name"],
        "category": category,
        "access_roles": access_roles,
        "restricted": restricted,
        "source_path": source_path,
        "source_file_name": source_file_name,
        "source_file_type": source_file_type,
        "uploaded_at": now,
        **extraction_metadata,
    }
    status_detail = (
        "PDF text was extracted deterministically and is waiting for human review. "
        "No chunks or embeddings were created."
    )

    with get_connection() as conn:
        document_row = conn.execute(
            """
            insert into documents (
              project_id, department_id, external_document_id, title, department, category,
              source_type, source_path, access_roles, sensitivity, restricted, status, updated_at
            )
            values (
              %s::uuid, %s::uuid, %s, %s, %s, %s,
              %s, %s, %s, %s, %s, 'active', now()
            )
            returning id::text
            """,
            (
                project_id,
                department["id"],
                external_document_id,
                title,
                department["name"],
                category,
                source_file_type,
                source_path,
                access_roles,
                sensitivity,
                restricted,
            ),
        ).fetchone()
        document_id = document_row["id"]
        version_row = conn.execute(
            """
            insert into document_versions (
              document_id, version_label, effective_date, owner, review_cycle,
              content_hash, extracted_text, metadata_json, ingestion_status
            )
            values (
              %s::uuid, 'v1', null, %s, 'manual review required',
              %s, %s, %s::jsonb, 'pending_review'
            )
            returning id::text
            """,
            (
                document_id,
                "Knowledge Manager",
                _hash_text(extracted_markdown),
                extracted_markdown,
                json.dumps(version_metadata, default=str),
            ),
        ).fetchone()
        version_id = version_row["id"]
        conn.execute(
            "update documents set current_version_id = %s::uuid where id = %s::uuid",
            (version_id, document_id),
        )
        conn.execute(
            """
            insert into ingestion_jobs (
              project_id, department_id, document_id, document_version_id,
              source_file_name, source_file_type, status, stage, status_detail,
              content_hash, started_at, completed_at, metadata_json
            )
            values (
              %s::uuid, %s::uuid, %s::uuid, %s::uuid,
              %s, %s, 'pending_review', 'review_pending', %s,
              %s, now(), now(), %s::jsonb
            )
            """,
            (
                project_id,
                department["id"],
                document_id,
                version_id,
                source_file_name,
                source_file_type,
                status_detail,
                _hash_bytes(raw_file_bytes),
                json.dumps(version_metadata, default=str),
            ),
        )

    documents = list_project_documents(project_id, department_id=department["id"], include_archived=True)
    return next(document for document in documents if document["id"] == document_id)
