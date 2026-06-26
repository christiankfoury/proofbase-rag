from __future__ import annotations

import sys
from pathlib import Path
from typing import Any


ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

from apps.api.app.projects import document_store


PROJECT_ID = "00000000-0000-0000-0000-000000000019"
DEPARTMENT_ID = "00000000-0000-0000-0000-000000002011"
DOCUMENT_ID = "00000000-0000-0000-0000-000000009999"
VERSION_ID = "00000000-0000-0000-0000-000000008888"
JOB_ID = "00000000-0000-0000-0000-000000007777"


class _FakeFetchOne:
    def __init__(self, row: dict[str, Any] | None = None) -> None:
        self.row = row or {"id": "00000000-0000-0000-0000-000000006666"}

    def fetchone(self) -> dict[str, Any]:
        return self.row


class _FakeConnection:
    def __init__(self, statements: list[str]) -> None:
        self.statements = statements

    def __enter__(self) -> "_FakeConnection":
        return self

    def __exit__(self, exc_type: object, exc: object, traceback: object) -> None:
        return None

    def execute(self, sql: str, params: object | None = None) -> _FakeFetchOne:
        self.statements.append(sql)
        return _FakeFetchOne()


def _pending_row() -> dict[str, Any]:
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
        "extracted_text": "## Vendor Start\n\nVendors need operations review before starting work.",
        "ingestion_status": "pending_review",
        "ingestion_job_id": JOB_ID,
    }


def test_approve_and_index_document_uses_mocked_embeddings_and_marks_indexed() -> None:
    statements: list[str] = []
    job_updates: list[tuple[str, str, str]] = []
    original_load = document_store._load_current_document_version
    original_update_job = document_store._update_indexing_job
    original_get_connection = document_store.get_connection
    original_embed_texts = document_store.embed_texts
    original_list = document_store.list_project_documents
    try:
        document_store._load_current_document_version = lambda **kwargs: _pending_row()  # type: ignore[assignment]
        document_store._update_indexing_job = (  # type: ignore[assignment]
            lambda job_id, *, status, stage, status_detail: job_updates.append((status, stage, status_detail))
        )
        document_store.get_connection = lambda: _FakeConnection(statements)  # type: ignore[assignment]
        document_store.embed_texts = lambda texts: [[0.1, 0.2] for _ in texts]  # type: ignore[assignment]
        document_store.list_project_documents = lambda *args, **kwargs: [  # type: ignore[assignment]
            {"id": DOCUMENT_ID, "title": "Uploaded Vendor Guide", "version": {"ingestion_status": "indexed"}, "chunk_count": 1}
        ]
        document = document_store.approve_and_index_document(
            project_id=PROJECT_ID,
            department_id=DEPARTMENT_ID,
            document_id=DOCUMENT_ID,
        )
    finally:
        document_store._load_current_document_version = original_load  # type: ignore[assignment]
        document_store._update_indexing_job = original_update_job  # type: ignore[assignment]
        document_store.get_connection = original_get_connection  # type: ignore[assignment]
        document_store.embed_texts = original_embed_texts  # type: ignore[assignment]
        document_store.list_project_documents = original_list  # type: ignore[assignment]

    assert document is not None
    assert document["version"]["ingestion_status"] == "indexed"
    assert any("insert into chunks" in statement for statement in statements)
    assert any("insert into chunk_embeddings" in statement for statement in statements)
    assert any("ingestion_status = 'indexed'" in statement for statement in statements)
    assert [status for status, _, _ in job_updates] == ["chunking", "embedding"]


def test_approve_and_index_document_marks_failed_when_embedding_fails() -> None:
    failures: list[tuple[str, str | None, str]] = []
    original_load = document_store._load_current_document_version
    original_update_job = document_store._update_indexing_job
    original_mark_failed = document_store._mark_indexing_failed
    original_embed_texts = document_store.embed_texts
    try:
        document_store._load_current_document_version = lambda **kwargs: _pending_row()  # type: ignore[assignment]
        document_store._update_indexing_job = lambda *args, **kwargs: None  # type: ignore[assignment]
        document_store._mark_indexing_failed = (  # type: ignore[assignment]
            lambda *, version_id, job_id, reason: failures.append((version_id, job_id, reason))
        )

        def fail_embed(texts: list[str]) -> list[list[float]]:
            raise RuntimeError("OPENAI_API_KEY is required for embedding generation")

        document_store.embed_texts = fail_embed  # type: ignore[assignment]
        try:
            document_store.approve_and_index_document(
                project_id=PROJECT_ID,
                department_id=DEPARTMENT_ID,
                document_id=DOCUMENT_ID,
            )
        except RuntimeError as exc:
            assert "OPENAI_API_KEY" in str(exc)
        else:
            raise AssertionError("Expected embedding failure")
    finally:
        document_store._load_current_document_version = original_load  # type: ignore[assignment]
        document_store._update_indexing_job = original_update_job  # type: ignore[assignment]
        document_store._mark_indexing_failed = original_mark_failed  # type: ignore[assignment]
        document_store.embed_texts = original_embed_texts  # type: ignore[assignment]

    assert failures == [(VERSION_ID, JOB_ID, "OPENAI_API_KEY is required for embedding generation")]


def main() -> None:
    test_approve_and_index_document_uses_mocked_embeddings_and_marks_indexed()
    test_approve_and_index_document_marks_failed_when_embedding_fails()
    print("Phase 40 upload indexing tests passed.")


if __name__ == "__main__":
    main()
