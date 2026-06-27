from __future__ import annotations

import sys
from pathlib import Path
from types import SimpleNamespace
from typing import Any


ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

from apps.api.app.embeddings import openai_embeddings
from apps.api.app.permissions import permission_filter
from apps.api.app.retrieval.types import RetrievedChunk


def test_embedding_cache_deduplicates_texts_per_process() -> None:
    calls: list[list[str]] = []
    original_client = openai_embeddings._client
    original_get_settings = openai_embeddings.get_settings
    openai_embeddings.clear_embedding_cache()

    class _FakeEmbeddings:
        def create(self, *, model: str, input: list[str]) -> Any:
            calls.append(list(input))
            return SimpleNamespace(
                data=[
                    SimpleNamespace(embedding=[float(index), float(len(text))])
                    for index, text in enumerate(input, start=1)
                ]
            )

    class _FakeClient:
        embeddings = _FakeEmbeddings()

    try:
        openai_embeddings.get_settings = lambda: SimpleNamespace(openai_embedding_model="text-embedding-test")  # type: ignore[assignment]
        openai_embeddings._client = lambda: _FakeClient()  # type: ignore[assignment]

        first = openai_embeddings.embed_texts(["same question", "same question", "other question"])
        second = openai_embeddings.embed_texts(["same question"])
    finally:
        openai_embeddings._client = original_client  # type: ignore[assignment]
        openai_embeddings.get_settings = original_get_settings  # type: ignore[assignment]
        openai_embeddings.clear_embedding_cache()

    assert calls == [["same question", "other question"]]
    assert first[0] == first[1]
    assert second[0] == first[0]


def test_permission_trace_records_hybrid_component_metadata() -> None:
    events: list[dict[str, Any]] = []
    original_log = permission_filter.log_audit_event
    try:
        permission_filter.log_audit_event = lambda **kwargs: events.append(kwargs) or True  # type: ignore[assignment]
        trace = permission_filter.build_permission_trace(
            user_role="Employee",
            retrieval_mode="vector_only",
            candidate_rows=[
                {
                    "document_id": "MGR-001",
                    "access_roles": ["Manager"],
                }
            ],
            allowed_chunks=[
                RetrievedChunk(
                    chunk_id="chunk-1",
                    document_id="HR-001",
                    document_title="Handbook",
                    section_heading="Intro",
                    content="Employees can read this.",
                    access_roles=["Employee"],
                    restricted=False,
                    sensitivity="internal",
                    rank=1,
                    score=0.9,
                )
            ],
            metadata={
                "parent_retrieval_mode": "hybrid",
                "hybrid_component": "vector",
                "hybrid_vector_weight": 0.5,
                "hybrid_keyword_weight": 0.5,
            },
        )
        permission_filter.log_permission_trace(trace, chunking_strategy="section_based", top_k=5)
    finally:
        permission_filter.log_audit_event = original_log  # type: ignore[assignment]

    assert events
    metadata = events[0]["metadata"]
    assert metadata["retrieval_mode"] == "vector_only"
    assert metadata["parent_retrieval_mode"] == "hybrid"
    assert metadata["hybrid_component"] == "vector"
    assert metadata["hybrid_vector_weight"] == 0.5
    assert events[1]["action"] == "unauthorized_candidate_blocked"
    assert events[1]["document_id"] == "MGR-001"
    assert events[1]["metadata"]["parent_retrieval_mode"] == "hybrid"
    assert events[1]["metadata"]["hybrid_component"] == "vector"


def main() -> None:
    test_embedding_cache_deduplicates_texts_per_process()
    test_permission_trace_records_hybrid_component_metadata()
    print("Audit backlog polish tests passed.")


if __name__ == "__main__":
    main()
