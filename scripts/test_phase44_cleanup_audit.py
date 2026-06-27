from __future__ import annotations

import json
import sys
from pathlib import Path
from typing import Any


ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

from fastapi.testclient import TestClient

from apps.api.app.main import app
import apps.api.app.main as main_app
from apps.api.app.projects import document_store
from apps.api.app.projects.markdown_cleanup import hash_markdown


PROJECT_ID = "00000000-0000-0000-0000-000000000019"
DEPARTMENT_ID = "00000000-0000-0000-0000-000000002011"
DOCUMENT_ID = "00000000-0000-0000-0000-000000009999"
VERSION_ID = "00000000-0000-0000-0000-000000008888"
JOB_ID = "00000000-0000-0000-0000-000000007777"
ADMIN_USER = {
    "id": "00000000-0000-0000-0000-000000002706",
    "business_role": "Admin",
    "is_admin": True,
    "memberships": [],
}


class _FakeFetchOne:
    def __init__(self, row: dict[str, Any] | None = None) -> None:
        self.row = row or {"id": "00000000-0000-0000-0000-000000006666"}

    def fetchone(self) -> dict[str, Any]:
        return self.row


class _FakeConnection:
    def __init__(self, calls: list[tuple[str, object | None]]) -> None:
        self.calls = calls

    def __enter__(self) -> "_FakeConnection":
        return self

    def __exit__(self, exc_type: object, exc: object, traceback: object) -> None:
        return None

    def execute(self, sql: str, params: object | None = None) -> _FakeFetchOne:
        self.calls.append((sql, params))
        return _FakeFetchOne()


def _document(status: str = "pending_review", cleanup: dict[str, Any] | None = None) -> dict[str, Any]:
    return {
        "id": DOCUMENT_ID,
        "project_id": PROJECT_ID,
        "department_id": DEPARTMENT_ID,
        "external_document_id": "UPLOAD-TEST",
        "title": "Uploaded Vendor Guide",
        "source_path": "data/uploads/test.pdf",
        "version": {
            "id": VERSION_ID,
            "ingestion_status": status,
            "metadata": {"ai_cleanup": cleanup} if cleanup else {},
        },
        "markdown_preview": "## Vendor Start\n\nVendors need Operations review before starting work.",
        "review_markdown": "## Vendor Start\n\nVendors need Operations review before starting work.",
        "chunk_count": 0 if status != "indexed" else 1,
    }


def _pending_row(cleaned_markdown: str) -> dict[str, Any]:
    return {
        "id": DOCUMENT_ID,
        "external_document_id": "UPLOAD-TEST",
        "title": "Uploaded Vendor Guide",
        "department": "Operations",
        "category": "Operations",
        "source_path": "data/uploads/test.pdf",
        "access_roles": ["Employee", "Manager"],
        "sensitivity": "internal",
        "restricted": False,
        "version_id": VERSION_ID,
        "version_label": "v1",
        "effective_date": None,
        "owner": "Admin",
        "review_cycle": "manual review required",
        "extracted_text": "## Vendor Start\n\nVendors need Operations review before starting work.",
        "metadata_json": {
            "ai_cleanup": {
                "model": "gpt-4.1-mini",
                "cleanup_timestamp": "2026-06-27T00:00:00+00:00",
                "source_content_hash": "sourcehash",
                "cleaned_content_hash": hash_markdown(cleaned_markdown),
            }
        },
        "ingestion_status": "pending_review",
        "ingestion_job_id": JOB_ID,
    }


def test_approve_index_records_reviewer_edited_after_cleanup() -> None:
    calls: list[tuple[str, object | None]] = []
    cleaned_markdown = "## Vendor Start\n\n- Vendors need Operations review before starting work."
    reviewed_markdown = "## Vendor Start\n\n- Vendors need Legal review before starting work."
    original_load = document_store._load_current_document_version
    original_update_job = document_store._update_indexing_job
    original_get_connection = document_store.get_connection
    original_embed_texts = document_store.embed_texts
    original_list = document_store.list_project_documents
    try:
        document_store._load_current_document_version = lambda **kwargs: _pending_row(cleaned_markdown)  # type: ignore[assignment]
        document_store._update_indexing_job = lambda *args, **kwargs: None  # type: ignore[assignment]
        document_store.get_connection = lambda: _FakeConnection(calls)  # type: ignore[assignment]
        document_store.embed_texts = lambda texts: [[0.1, 0.2] for _ in texts]  # type: ignore[assignment]
        document_store.list_project_documents = lambda *args, **kwargs: [  # type: ignore[assignment]
            _document("indexed", cleanup=_pending_row(cleaned_markdown)["metadata_json"]["ai_cleanup"])
        ]
        document = document_store.approve_and_index_document(
            project_id=PROJECT_ID,
            department_id=DEPARTMENT_ID,
            document_id=DOCUMENT_ID,
            reviewed_markdown=reviewed_markdown,
        )
    finally:
        document_store._load_current_document_version = original_load  # type: ignore[assignment]
        document_store._update_indexing_job = original_update_job  # type: ignore[assignment]
        document_store.get_connection = original_get_connection  # type: ignore[assignment]
        document_store.embed_texts = original_embed_texts  # type: ignore[assignment]
        document_store.list_project_documents = original_list  # type: ignore[assignment]

    assert document is not None
    metadata_params = [
        params
        for sql, params in calls
        if "set extracted_text = %s" in sql and isinstance(params, tuple) and len(params) >= 3
    ]
    assert metadata_params
    metadata = json.loads(metadata_params[0][2])
    assert metadata["ai_cleanup_review"]["approved_after_cleanup"] is True
    assert metadata["ai_cleanup_review"]["reviewer_edited_after_cleanup"] is True
    assert metadata["ai_cleanup_review"]["approved_content_hash"] == hash_markdown(reviewed_markdown)


def test_revert_route_records_audit_event() -> None:
    events: list[dict[str, Any]] = []
    app.dependency_overrides[main_app.current_demo_user] = lambda: ADMIN_USER
    original_get_department = main_app.get_department
    original_revert = main_app.record_cleanup_revert_metadata
    original_audit = main_app.log_audit_event
    try:
        main_app.get_department = lambda *args, **kwargs: {"id": DEPARTMENT_ID}  # type: ignore[assignment]
        main_app.record_cleanup_revert_metadata = lambda **kwargs: _document()  # type: ignore[assignment]
        main_app.log_audit_event = lambda **kwargs: events.append(kwargs)  # type: ignore[assignment]
        response = TestClient(app).post(
            f"/projects/{PROJECT_ID}/departments/{DEPARTMENT_ID}/documents/{DOCUMENT_ID}/cleanup-markdown/revert",
            json={},
        )
    finally:
        main_app.get_department = original_get_department  # type: ignore[assignment]
        main_app.record_cleanup_revert_metadata = original_revert  # type: ignore[assignment]
        main_app.log_audit_event = original_audit  # type: ignore[assignment]
        app.dependency_overrides.clear()

    assert response.status_code == 200
    assert response.json()["status"] == "reverted"
    assert [event["action"] for event in events] == ["document_markdown_cleanup_reverted"]


def test_cleanup_failure_logs_failed_audit_event() -> None:
    events: list[dict[str, Any]] = []
    app.dependency_overrides[main_app.current_demo_user] = lambda: ADMIN_USER
    original_get_department = main_app.get_department
    original_get_document = main_app.get_project_document
    original_cleanup = main_app.cleanup_uploaded_markdown
    original_audit = main_app.log_audit_event
    try:
        main_app.get_department = lambda *args, **kwargs: {"id": DEPARTMENT_ID}  # type: ignore[assignment]
        main_app.get_project_document = lambda *args, **kwargs: _document()  # type: ignore[assignment]
        main_app.cleanup_uploaded_markdown = lambda **kwargs: (_ for _ in ()).throw(RuntimeError("OPENAI_API_KEY missing"))  # type: ignore[assignment]
        main_app.log_audit_event = lambda **kwargs: events.append(kwargs)  # type: ignore[assignment]
        response = TestClient(app).post(
            f"/projects/{PROJECT_ID}/departments/{DEPARTMENT_ID}/documents/{DOCUMENT_ID}/cleanup-markdown",
            json={},
        )
    finally:
        main_app.get_department = original_get_department  # type: ignore[assignment]
        main_app.get_project_document = original_get_document  # type: ignore[assignment]
        main_app.cleanup_uploaded_markdown = original_cleanup  # type: ignore[assignment]
        main_app.log_audit_event = original_audit  # type: ignore[assignment]
        app.dependency_overrides.clear()

    assert response.status_code == 503
    assert [event["action"] for event in events] == [
        "document_markdown_cleanup_requested",
        "document_markdown_cleanup_failed",
    ]


def test_cleanup_metadata_database_failure_logs_failed_audit_event() -> None:
    events: list[dict[str, Any]] = []
    app.dependency_overrides[main_app.current_demo_user] = lambda: ADMIN_USER
    original_get_department = main_app.get_department
    original_get_document = main_app.get_project_document
    original_cleanup = main_app.cleanup_uploaded_markdown
    original_record = main_app.record_cleanup_metadata
    original_audit = main_app.log_audit_event
    try:
        main_app.get_department = lambda *args, **kwargs: {"id": DEPARTMENT_ID}  # type: ignore[assignment]
        main_app.get_project_document = lambda *args, **kwargs: _document()  # type: ignore[assignment]
        main_app.cleanup_uploaded_markdown = lambda **kwargs: {  # type: ignore[assignment]
            "cleaned_markdown": "## Vendor Start\n\n- Vendors need Operations review before starting work.",
            "metadata": {
                "status": "draft_returned_not_indexed",
                "model": "gpt-4.1-mini",
                "cleanup_timestamp": "2026-06-27T00:00:00+00:00",
                "source_content_hash": "sourcehash",
                "cleaned_content_hash": "cleanedhash",
                "input_tokens": 10,
                "output_tokens": 5,
                "input_cost_usd": 0.000004,
                "output_cost_usd": 0.000008,
                "estimated_cost_usd": 0.000012,
                "pricing_status": "estimated",
            },
        }
        main_app.record_cleanup_metadata = lambda **kwargs: (_ for _ in ()).throw(main_app.PsycopgError("db failed"))  # type: ignore[assignment]
        main_app.log_audit_event = lambda **kwargs: events.append(kwargs)  # type: ignore[assignment]
        response = TestClient(app).post(
            f"/projects/{PROJECT_ID}/departments/{DEPARTMENT_ID}/documents/{DOCUMENT_ID}/cleanup-markdown",
            json={},
        )
    finally:
        main_app.get_department = original_get_department  # type: ignore[assignment]
        main_app.get_project_document = original_get_document  # type: ignore[assignment]
        main_app.cleanup_uploaded_markdown = original_cleanup  # type: ignore[assignment]
        main_app.record_cleanup_metadata = original_record  # type: ignore[assignment]
        main_app.log_audit_event = original_audit  # type: ignore[assignment]
        app.dependency_overrides.clear()

    assert response.status_code == 503
    assert [event["action"] for event in events] == [
        "document_markdown_cleanup_requested",
        "document_markdown_cleanup_failed",
    ]
    assert events[1]["reason"] == "database_error_saving_cleanup_metadata"


def test_approve_route_logs_cleanup_approved_indexed_event() -> None:
    cleaned_markdown = "## Vendor Start\n\n- Vendors need Operations review before starting work."
    cleanup = {
        "model": "gpt-4.1-mini",
        "cleaned_content_hash": hash_markdown(cleaned_markdown),
        "source_content_hash": "sourcehash",
    }
    events: list[dict[str, Any]] = []
    app.dependency_overrides[main_app.current_demo_user] = lambda: ADMIN_USER
    original_get_department = main_app.get_department
    original_get_document = main_app.get_project_document
    original_approve = main_app.approve_and_index_document
    original_audit = main_app.log_audit_event
    try:
        main_app.get_department = lambda *args, **kwargs: {"id": DEPARTMENT_ID}  # type: ignore[assignment]
        main_app.get_project_document = lambda *args, **kwargs: _document(cleanup=cleanup)  # type: ignore[assignment]
        main_app.approve_and_index_document = lambda **kwargs: _document("indexed", cleanup=cleanup)  # type: ignore[assignment]
        main_app.log_audit_event = lambda **kwargs: events.append(kwargs)  # type: ignore[assignment]
        response = TestClient(app).post(
            f"/projects/{PROJECT_ID}/departments/{DEPARTMENT_ID}/documents/{DOCUMENT_ID}/approve-index",
            json={"reviewed_markdown": cleaned_markdown},
        )
    finally:
        main_app.get_department = original_get_department  # type: ignore[assignment]
        main_app.get_project_document = original_get_document  # type: ignore[assignment]
        main_app.approve_and_index_document = original_approve  # type: ignore[assignment]
        main_app.log_audit_event = original_audit  # type: ignore[assignment]
        app.dependency_overrides.clear()

    assert response.status_code == 200
    assert [event["action"] for event in events] == [
        "document_approved_for_indexing",
        "document_markdown_cleanup_approved_indexed",
    ]
    approved_event = events[1]
    assert approved_event["metadata"]["reviewer_edited_after_cleanup"] is False
    assert approved_event["metadata"]["approved_content_hash"] == hash_markdown(cleaned_markdown)


def main() -> None:
    test_approve_index_records_reviewer_edited_after_cleanup()
    test_revert_route_records_audit_event()
    test_cleanup_failure_logs_failed_audit_event()
    test_cleanup_metadata_database_failure_logs_failed_audit_event()
    test_approve_route_logs_cleanup_approved_indexed_event()
    print("Phase 44 cleanup audit tests passed.")


if __name__ == "__main__":
    main()
