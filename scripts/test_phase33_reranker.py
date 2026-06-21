from __future__ import annotations

import sys
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

from apps.api.app.retrieval.reranker import lexical_overlap_score, rerank_chunks
from apps.api.app.retrieval.types import RetrievedChunk


def _chunk(
    chunk_id: str,
    document_id: str,
    title: str,
    heading: str,
    content: str,
    score: float,
) -> RetrievedChunk:
    return RetrievedChunk(
        chunk_id=chunk_id,
        document_id=document_id,
        document_title=title,
        section_heading=heading,
        content=content,
        access_roles=["Employee"],
        restricted=False,
        sensitivity="internal",
        rank=0,
        score=score,
        vector_score=score,
    )


def test_lexical_overlap_weights_headings() -> None:
    query = "What is the implementation timeline?"
    strong_heading = _chunk(
        "chunk-1",
        "SALES-002",
        "Product Positioning and FAQ",
        "Implementation Timeline",
        "Standard deployments usually complete in a predictable window.",
        0.6,
    )
    weak_heading = _chunk(
        "chunk-2",
        "SALES-001",
        "Sales Playbook",
        "Sales Stages",
        "Implementation questions should be confirmed before proposal.",
        0.7,
    )
    assert lexical_overlap_score(query, strong_heading) > lexical_overlap_score(query, weak_heading)


def test_rerank_prefers_strong_lexical_match() -> None:
    query = "What is the implementation timeline?"
    chunks = [
        _chunk("chunk-1", "SALES-001", "Sales Playbook", "Sales Stages", "Proposal readiness.", 0.8),
        _chunk("chunk-2", "SALES-002", "Product Positioning and FAQ", "Implementation Timeline", "Six to ten weeks.", 0.75),
    ]
    reranked = rerank_chunks(query, chunks)
    assert [chunk.chunk_id for chunk in reranked] == ["chunk-2", "chunk-1"]
    assert [chunk.rank for chunk in reranked] == [1, 2]
    assert all(chunk.retrieval_source == "vector_lexical_rerank" for chunk in reranked)


def test_rerank_preserves_vector_order_without_overlap() -> None:
    chunks = [
        _chunk("chunk-1", "HR-001", "Employee Handbook", "Company Overview", "Northstar offices.", 0.8),
        _chunk("chunk-2", "IT-001", "Acceptable Use Policy", "Approved Use", "Use approved software.", 0.7),
    ]
    reranked = rerank_chunks("zzzz yyyy xxxx", chunks)
    assert [chunk.chunk_id for chunk in reranked] == ["chunk-1", "chunk-2"]


def main() -> None:
    test_lexical_overlap_weights_headings()
    test_rerank_prefers_strong_lexical_match()
    test_rerank_preserves_vector_order_without_overlap()
    print("Phase 33 reranker tests passed")


if __name__ == "__main__":
    main()
