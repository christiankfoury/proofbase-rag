from __future__ import annotations

import sys
from pathlib import Path
from typing import Any


ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

from apps.api.app.retrieval import keyword_retriever, vector_retriever
from scripts.run_answer_quality_eval import _requires_external_ai_approval as answer_quality_requires_approval
from scripts.run_multi_doc_eval import _requires_external_ai_approval as multi_doc_requires_approval
from scripts.run_retrieval_experiments import _requires_external_embeddings_approval


class _FakeResult:
    def fetchall(self) -> list[dict[str, Any]]:
        return []


class _FakeConnection:
    def __init__(self, queries: list[str]) -> None:
        self.queries = queries

    def __enter__(self) -> "_FakeConnection":
        return self

    def __exit__(self, exc_type: object, exc: object, traceback: object) -> None:
        return None

    def execute(self, sql: str, params: object | None = None) -> _FakeResult:
        self.queries.append(sql)
        return _FakeResult()


def _captured_queries_for_vector() -> list[str]:
    queries: list[str] = []
    original_get_connection = vector_retriever.get_connection
    original_embed_text = vector_retriever.embed_text
    original_log_permission_trace = vector_retriever.log_permission_trace
    try:
        vector_retriever.get_connection = lambda: _FakeConnection(queries)  # type: ignore[assignment]
        vector_retriever.embed_text = lambda question: [0.0, 0.1]  # type: ignore[assignment]
        vector_retriever.log_permission_trace = lambda trace, **kwargs: None  # type: ignore[assignment]
        vector_retriever.retrieve_chunks("What changed?", "Employee", top_k=2)
    finally:
        vector_retriever.get_connection = original_get_connection  # type: ignore[assignment]
        vector_retriever.embed_text = original_embed_text  # type: ignore[assignment]
        vector_retriever.log_permission_trace = original_log_permission_trace  # type: ignore[assignment]
    return queries


def _captured_queries_for_keyword() -> list[str]:
    queries: list[str] = []
    original_get_connection = keyword_retriever.get_connection
    original_log_permission_trace = keyword_retriever.log_permission_trace
    try:
        keyword_retriever.get_connection = lambda: _FakeConnection(queries)  # type: ignore[assignment]
        keyword_retriever.log_permission_trace = lambda trace, **kwargs: None  # type: ignore[assignment]
        keyword_retriever.retrieve_chunks("What changed?", "Employee", top_k=2)
    finally:
        keyword_retriever.get_connection = original_get_connection  # type: ignore[assignment]
        keyword_retriever.log_permission_trace = original_log_permission_trace  # type: ignore[assignment]
    return queries


def test_vector_retrieval_filters_to_current_document_version() -> None:
    queries = _captured_queries_for_vector()
    assert len(queries) == 2
    assert all("c.document_version_id = d.current_version_id" in query for query in queries)


def test_keyword_retrieval_filters_to_current_document_version() -> None:
    queries = _captured_queries_for_keyword()
    assert len(queries) == 2
    assert all("c.document_version_id = d.current_version_id" in query for query in queries)


def test_legacy_eval_scripts_require_explicit_external_ai_approval() -> None:
    assert answer_quality_requires_approval(dry_run=False, allow_external_ai=False)
    assert not answer_quality_requires_approval(dry_run=True, allow_external_ai=False)
    assert not answer_quality_requires_approval(dry_run=False, allow_external_ai=True)
    assert multi_doc_requires_approval(dry_run=False, allow_external_ai=False)
    assert not multi_doc_requires_approval(dry_run=True, allow_external_ai=False)
    assert not multi_doc_requires_approval(dry_run=False, allow_external_ai=True)


def test_legacy_retrieval_experiments_require_embedding_approval() -> None:
    assert _requires_external_embeddings_approval(
        dry_run=False,
        allow_external_embeddings=False,
        allow_external_ai=False,
    )
    assert not _requires_external_embeddings_approval(
        dry_run=True,
        allow_external_embeddings=False,
        allow_external_ai=False,
    )
    assert not _requires_external_embeddings_approval(
        dry_run=False,
        allow_external_embeddings=True,
        allow_external_ai=False,
    )
    assert not _requires_external_embeddings_approval(
        dry_run=False,
        allow_external_embeddings=False,
        allow_external_ai=True,
    )


def main() -> None:
    test_vector_retrieval_filters_to_current_document_version()
    test_keyword_retrieval_filters_to_current_document_version()
    test_legacy_eval_scripts_require_explicit_external_ai_approval()
    test_legacy_retrieval_experiments_require_embedding_approval()
    print("Pre-Phase 39 guardrail tests passed.")


if __name__ == "__main__":
    main()
