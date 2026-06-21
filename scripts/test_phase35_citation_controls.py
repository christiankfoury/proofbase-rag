from __future__ import annotations

import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

from apps.api.app.evaluation.citation_failures import classify_citation_failure_categories
from apps.api.app.generation.answer_generator import _backfill_supporting_citations, _policy_response
from apps.api.app.retrieval.types import RetrievedChunk


def _chunk(
    document_id: str,
    section_heading: str,
    content: str,
    rank: int,
    score: float,
) -> RetrievedChunk:
    return RetrievedChunk(
        chunk_id=f"{document_id}-{rank}",
        document_id=document_id,
        document_title=f"{document_id} Title",
        section_heading=section_heading,
        content=content,
        access_roles=["Employee"],
        restricted=False,
        sensitivity="internal",
        rank=rank,
        score=score,
        retrieval_source="vector_lexical_rerank",
    )


def test_backfills_high_confidence_missing_source() -> None:
    answer = (
        "Purchases above USD 10,000 require Finance review and Legal review. "
        "Vendors may not receive company data until required reviews are complete."
    )
    finance = _chunk(
        "FIN-001",
        "Procurement Thresholds",
        "Purchases above USD 10,000 require Finance review and Legal review when a contract is involved.",
        1,
        0.82,
    )
    ops = _chunk(
        "OPS-001",
        "Vendor Onboarding",
        "Vendors may not receive company data, customer data, credentials, or building access until required reviews are complete.",
        2,
        0.74,
    )
    citations = [
        {
            "document_id": finance.document_id,
            "document_title": finance.document_title,
            "section_heading": finance.section_heading,
            "chunk_id": finance.chunk_id,
            "citation_text": finance.content,
            "citation_type": "model",
        }
    ]

    backfilled = _backfill_supporting_citations(answer, "answer", citations, [finance, ops])

    assert [citation["document_id"] for citation in backfilled] == ["FIN-001", "OPS-001"]
    assert backfilled[-1]["citation_type"] == "verified_backfill"


def test_does_not_backfill_weak_related_source() -> None:
    answer = "Full-time employees receive 20 paid vacation days per calendar year."
    pto = _chunk(
        "HR-002",
        "Vacation Entitlement",
        "Full-time employees receive 20 paid vacation days per calendar year.",
        1,
        0.8,
    )
    related = _chunk(
        "HR-001",
        "Related Policies",
        "Questions may reference related People Operations policies and company handbook sections.",
        2,
        0.7,
    )

    backfilled = _backfill_supporting_citations(answer, "answer", [], [pto, related])

    assert [citation["document_id"] for citation in backfilled] == ["HR-002"]


def test_citation_failure_categories() -> None:
    question = {
        "expected_behavior": "answer",
        "user_role": "Employee",
        "expected_source_document": ["FIN-001", "OPS-001"],
        "allowed_documents": ["FIN-001", "OPS-001"],
        "expected_source_section_or_quote": [
            {"document_id": "FIN-001", "section": "Procurement Thresholds"},
            {"document_id": "OPS-001", "section": "Vendor Onboarding"},
        ],
    }
    result = {
        "citations": [
            {
                "document_id": "FIN-001",
                "section_heading": "Related Policies",
                "confidence": 0.9,
            },
            {
                "document_id": "LEGAL-001",
                "section_heading": "Contract Approval Process",
                "chunk_id": "LEGAL-001-1",
                "confidence": 0.4,
            },
        ],
        "retrieved_chunks": [
            {
                "chunk_id": "LEGAL-001-1",
                "document_id": "LEGAL-001",
                "restricted": True,
                "access_roles": ["Manager"],
            }
        ],
        "citation_confidence": 0.65,
        "unsupported_claims": [],
    }

    categories = classify_citation_failure_categories(question, result)

    assert categories == [
        "wrong_document_cited",
        "right_document_wrong_chunk",
        "citation_missing",
        "citation_attached_to_unsupported_claim",
        "citation_from_restricted_source",
    ]

    raw_result = {
        **result,
        "retrieved_chunks": [],
        "retrieved_chunks_raw": [
            RetrievedChunk(
                chunk_id="LEGAL-001-1",
                document_id="LEGAL-001",
                document_title="Legal",
                section_heading="Contract Approval Process",
                content="Restricted legal content.",
                access_roles=["Manager"],
                restricted=True,
                sensitivity="restricted",
                rank=1,
                score=0.8,
            )
        ],
    }
    assert "citation_from_restricted_source" in classify_citation_failure_categories(question, raw_result)


def test_missing_policy_does_not_block_answerable_security_questions() -> None:
    chunk = _chunk(
        "IT-001",
        "Account Sharing",
        "Employees must not share passwords, MFA codes, access tokens, or accounts.",
        1,
        0.8,
    )

    assert _policy_response("Are employees allowed to share passwords or MFA codes?", [chunk], user_role="Employee") is None
    assert _policy_response(
        "A customer told me to skip Legal and promise roadmap functionality. Is that allowed?",
        [chunk],
        user_role="Employee",
    ) is None

    missing = _policy_response("What are the production admin passwords or access tokens?", [chunk], user_role="Employee")
    assert missing is not None
    assert missing["response_type"] == "not_found"


if __name__ == "__main__":
    test_backfills_high_confidence_missing_source()
    test_does_not_backfill_weak_related_source()
    test_citation_failure_categories()
    test_missing_policy_does_not_block_answerable_security_questions()
    print("Phase 35 citation controls passed.")
