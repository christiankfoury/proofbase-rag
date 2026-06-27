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
    def __init__(self, calls: list[dict[str, Any]]) -> None:
        self.calls = calls

    def __enter__(self) -> "_FakeConnection":
        return self

    def __exit__(self, exc_type: object, exc: object, traceback: object) -> None:
        return None

    def execute(self, sql: str, params: object | None = None) -> _FakeResult:
        self.calls.append({"sql": sql, "params": params})
        return _FakeResult()


def _captured_calls_for_vector(excluded_document_prefixes: tuple[str, ...] = ()) -> list[dict[str, Any]]:
    calls: list[dict[str, Any]] = []
    original_get_connection = vector_retriever.get_connection
    original_embed_text = vector_retriever.embed_text
    original_log_permission_trace = vector_retriever.log_permission_trace
    try:
        vector_retriever.get_connection = lambda: _FakeConnection(calls)  # type: ignore[assignment]
        vector_retriever.embed_text = lambda question: [0.0, 0.1]  # type: ignore[assignment]
        vector_retriever.log_permission_trace = lambda trace, **kwargs: None  # type: ignore[assignment]
        vector_retriever.retrieve_chunks(
            "What changed?",
            "Employee",
            top_k=2,
            excluded_document_prefixes=excluded_document_prefixes,
        )
    finally:
        vector_retriever.get_connection = original_get_connection  # type: ignore[assignment]
        vector_retriever.embed_text = original_embed_text  # type: ignore[assignment]
        vector_retriever.log_permission_trace = original_log_permission_trace  # type: ignore[assignment]
    return calls


def _captured_calls_for_keyword(excluded_document_prefixes: tuple[str, ...] = ()) -> list[dict[str, Any]]:
    calls: list[dict[str, Any]] = []
    original_get_connection = keyword_retriever.get_connection
    original_log_permission_trace = keyword_retriever.log_permission_trace
    try:
        keyword_retriever.get_connection = lambda: _FakeConnection(calls)  # type: ignore[assignment]
        keyword_retriever.log_permission_trace = lambda trace, **kwargs: None  # type: ignore[assignment]
        keyword_retriever.retrieve_chunks(
            "What changed?",
            "Employee",
            top_k=2,
            excluded_document_prefixes=excluded_document_prefixes,
        )
    finally:
        keyword_retriever.get_connection = original_get_connection  # type: ignore[assignment]
        keyword_retriever.log_permission_trace = original_log_permission_trace  # type: ignore[assignment]
    return calls


def test_vector_retrieval_filters_to_current_document_version() -> None:
    queries = [call["sql"] for call in _captured_calls_for_vector()]
    assert len(queries) == 2
    assert all("c.document_version_id = d.current_version_id" in query for query in queries)


def test_keyword_retrieval_filters_to_current_document_version() -> None:
    queries = [call["sql"] for call in _captured_calls_for_keyword()]
    assert len(queries) == 2
    assert all("c.document_version_id = d.current_version_id" in query for query in queries)


def test_vector_retrieval_excludes_eval_document_prefixes_before_permission_filtering() -> None:
    calls = _captured_calls_for_vector(("UPLOAD-",))
    assert len(calls) == 2
    assert all("d.external_document_id not like %s" in call["sql"] for call in calls)
    assert all("UPLOAD-%" in call["params"] for call in calls)


def test_keyword_retrieval_excludes_eval_document_prefixes_before_permission_filtering() -> None:
    calls = _captured_calls_for_keyword(("UPLOAD-",))
    assert len(calls) == 2
    assert all("d.external_document_id not like %s" in call["sql"] for call in calls)
    assert all("UPLOAD-%" in call["params"] for call in calls)


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
    test_vector_retrieval_excludes_eval_document_prefixes_before_permission_filtering()
    test_keyword_retrieval_excludes_eval_document_prefixes_before_permission_filtering()
    test_legacy_eval_scripts_require_explicit_external_ai_approval()
    test_legacy_retrieval_experiments_require_embedding_approval()
    print("Pre-Phase 39 guardrail tests passed.")


if __name__ == "__main__":
    main()
