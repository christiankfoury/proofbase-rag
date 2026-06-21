from __future__ import annotations

import sys
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

from apps.api.app.citations.citation_validator import validate_citations
from apps.api.app.generation.answer_generator import _policy_response
from apps.api.app.retrieval.types import RetrievedChunk


def _chunk(
    chunk_id: str,
    document_id: str,
    section_heading: str,
    content: str,
    rank: int,
) -> RetrievedChunk:
    return RetrievedChunk(
        chunk_id=chunk_id,
        document_id=document_id,
        document_title=f"{document_id} Title",
        section_heading=section_heading,
        content=content,
        access_roles=["Employee"],
        restricted=False,
        sensitivity="internal",
        rank=rank,
        score=0.82,
    )


def test_sentence_level_citation_supports_multi_document_answers() -> None:
    chunks = [
        _chunk(
            "hr-pto",
            "HR-002",
            "Vacation Entitlement",
            "Full-time employees receive 20 paid vacation days per calendar year.",
            1,
        ),
        _chunk(
            "hr-help",
            "HR-001",
            "Employee Support Channels",
            "For PTO questions, employees should contact People Operations.",
            2,
        ),
    ]
    answer = (
        "Employees should contact People Operations for PTO questions. "
        "Full-time employees receive 20 paid vacation days per calendar year."
    )
    validation = validate_citations(
        answer,
        [
            {
                "document_id": "HR-001",
                "document_title": "HR-001 Title",
                "section_heading": "Employee Support Channels",
                "chunk_id": "hr-help",
                "citation_text": "For PTO questions, employees should contact People Operations.",
            },
            {
                "document_id": "HR-002",
                "document_title": "HR-002 Title",
                "section_heading": "Vacation Entitlement",
                "chunk_id": "hr-pto",
                "citation_text": "Full-time employees receive 20 paid vacation days per calendar year.",
            },
        ],
        chunks,
    )
    assert validation["citation_confidence"] >= 0.7
    assert validation["unsupported_claims"] == []


def test_exact_unpublished_detail_policy_abstains_before_generation() -> None:
    response = _policy_response(
        "Who exactly is listed in the Legal signature authority register?",
        [],
        user_role="Manager",
    )
    assert response is not None
    assert response["response_type"] == "not_found"
    assert response["citations"] == []


def main() -> None:
    test_sentence_level_citation_supports_multi_document_answers()
    test_exact_unpublished_detail_policy_abstains_before_generation()
    print("Phase 34 grounding control tests passed")


if __name__ == "__main__":
    main()
