from __future__ import annotations

import sys
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

from apps.api.app.reasoning import query_decomposer
from apps.api.app.generation.answer_generator import generate_answer
from apps.api.app.reasoning.multi_doc_detector import is_multi_document_question
from apps.api.app.reasoning.source_planner import plan_multi_document_sources
from apps.api.app.retrieval.config import default_retrieval_config
from apps.api.app.retrieval.types import RetrievedChunk


def _chunk(chunk_id: str, document_id: str, score: float) -> RetrievedChunk:
    return RetrievedChunk(
        chunk_id=chunk_id,
        document_id=document_id,
        document_title=f"{document_id} Title",
        section_heading="Policy",
        content=f"{document_id} content",
        access_roles=["Employee", "Sales Representative", "Manager", "IT Admin", "HR Admin"],
        restricted=False,
        sensitivity="internal",
        rank=1,
        score=score,
        retrieval_source="vector",
    )


def test_phase39_plans_remaining_multi_doc_failure_sources() -> None:
    expected = {
        "Before a deal moves to proposal, what sales-stage and implementation constraints should I check?": {
            "SALES-001",
            "SALES-002",
        },
        "What should I do if I need benefits help and also want to use my learning budget?": {
            "HR-001",
            "HR-004",
        },
        "If an Enterprise customer reports suspected data exposure, what support escalation and engineering response target apply?": {
            "SUPPORT-001",
            "ENG-001",
        },
        "How should a manager handle ongoing performance concerns?": {
            "MGR-001",
            "MGR-002",
        },
        "For an API that exposes customer data, what authorization and review principles apply?": {
            "ENG-001",
            "IT-003",
        },
        "When policies overlap for software or vendor purchases, what approval path should be used?": {
            "FIN-001",
            "OPS-001",
        },
    }
    for question, expected_docs in expected.items():
        plan = plan_multi_document_sources(question)
        planned_docs = {document_id for item in plan for document_id in item.target_document_ids}
        assert expected_docs.issubset(planned_docs)


def test_phase39_detects_remaining_cross_policy_questions() -> None:
    questions = [
        "If an Enterprise customer reports suspected data exposure, what support escalation and engineering response target apply?",
        "How should a manager handle ongoing performance concerns?",
        "For an API that exposes customer data, what authorization and review principles apply?",
        "When policies overlap for software or vendor purchases, what approval path should be used?",
    ]
    for question in questions:
        assert is_multi_document_question(question)


def test_phase39_multi_doc_merge_preserves_planned_source_coverage() -> None:
    calls: list[str] = []

    def fake_retrieve_chunks(question: str, user_role: str, config):
        calls.append(question)
        if "sales stages" in question:
            return [
                _chunk("sales-001-a", "SALES-001", 0.95),
                _chunk("sales-001-b", "SALES-001", 0.94),
            ]
        if "implementation" in question:
            return [
                _chunk("sales-001-c", "SALES-001", 0.93),
                _chunk("sales-002-a", "SALES-002", 0.40),
            ]
        return []

    original_retrieve_chunks = query_decomposer.retrieve_chunks
    try:
        query_decomposer.retrieve_chunks = fake_retrieve_chunks  # type: ignore[assignment]
        chunks = query_decomposer.retrieve_multi_doc(
            "Before a deal moves to proposal, what sales-stage and implementation constraints should I check?",
            "Sales Representative",
            default_retrieval_config(),
        )
    finally:
        query_decomposer.retrieve_chunks = original_retrieve_chunks  # type: ignore[assignment]

    assert len(calls) == 2
    assert [chunk.document_id for chunk in chunks[:2]] == ["SALES-001", "SALES-002"]
    assert {chunk.document_id for chunk in chunks} >= {"SALES-001", "SALES-002"}


def _evidence_chunk(document_id: str, section: str, content: str, rank: int = 1) -> RetrievedChunk:
    return RetrievedChunk(
        chunk_id=f"{document_id}-{section}".replace(" ", "-"),
        document_id=document_id,
        document_title=f"{document_id} Title",
        section_heading=section,
        content=content,
        access_roles=["Employee", "Sales Representative", "Manager", "IT Admin", "HR Admin"],
        restricted=False,
        sensitivity="internal",
        rank=rank,
        score=0.95,
        retrieval_source="test",
    )


def test_phase39_direct_evidence_answers_use_required_sources() -> None:
    cases = [
        (
            "How should I position Northstar against BI tools while avoiding prohibited claims?",
            [
                _evidence_chunk("SALES-002", "Core Value Proposition", "Northstar Analytics gives operations teams one place to monitor workflows, approvals, data quality issues, and executive KPIs. The strongest message is operational visibility with measurable process improvement."),
                _evidence_chunk("SALES-003", "Positioning Against Generic BI Tools", "When compared with generic BI tools, position Northstar as workflow-aware analytics. Generic BI tools can report metrics, but Northstar connects metrics to approvals, queues, owners, and operational follow-up. Approved response: Northstar complements BI by helping operations teams act on workflow issues, not just view dashboards."),
                _evidence_chunk("SALES-003", "Prohibited Claims", "Sales Representatives must not claim that Northstar guarantees revenue improvement, replaces all existing systems, meets every regulatory requirement, or has committed roadmap features."),
            ],
            {"SALES-002", "SALES-003"},
        ),
        (
            "How should a manager handle ongoing performance concerns?",
            [
                _evidence_chunk("MGR-001", "Manager Responsibilities", "Managers are responsible for setting clear expectations, maintaining team operating rhythm, supporting employee growth, approving time off, and escalating risks early. Managers should document important decisions and keep role expectations current."),
                _evidence_chunk("MGR-002", "Performance Documentation", "Performance feedback should include specific examples, business impact, expected behavior, and follow-up actions."),
                _evidence_chunk("MGR-002", "Performance Improvement Process", "When serious performance issues continue after feedback, managers should consult People Operations before starting a formal performance improvement process."),
            ],
            {"MGR-001", "MGR-002"},
        ),
        (
            "For an API that exposes customer data, what authorization and review principles apply?",
            [
                _evidence_chunk("ENG-001", "API Standards", "APIs that expose customer or employee data must enforce authorization before database fetches whenever practical. If pre-fetch filtering is not possible, the exception must be documented in the design review."),
                _evidence_chunk("IT-003", "Storage Rules", "Internal, Confidential, and Restricted data must be stored in approved company systems. Restricted data must not be downloaded to personal devices. Confidential data should not be stored in local folders unless there is a documented business need."),
            ],
            {"ENG-001", "IT-003"},
        ),
        (
            "When policies overlap for software or vendor purchases, what approval path should be used?",
            [
                _evidence_chunk("FIN-001", "Expense Categories", "Software subscription trial | USD 500 annualized value | IT review and manager approval."),
                _evidence_chunk("OPS-001", "Vendor Onboarding", "High-risk vendors processing company or customer data require Operations, Legal, and IT Admin review."),
                _evidence_chunk("OPS-001", "Overlap With Other Policies", "Expense reimbursement follows Finance policy. Contract signature follows Legal policy. Device configuration and data security follow IT security policy. When policies overlap, the stricter approval path applies."),
            ],
            {"FIN-001", "OPS-001"},
        ),
    ]
    for question, chunks, expected_docs in cases:
        answer = generate_answer(question, chunks, user_role="Manager", prompt_version="v8", multi_doc=True)
        cited_docs = {citation["document_id"] for citation in answer["citations"]}
        assert expected_docs.issubset(cited_docs)
        assert answer["response_type"] == "answer"
        assert not answer["unsupported_claims"]


def main() -> None:
    test_phase39_plans_remaining_multi_doc_failure_sources()
    test_phase39_detects_remaining_cross_policy_questions()
    test_phase39_multi_doc_merge_preserves_planned_source_coverage()
    test_phase39_direct_evidence_answers_use_required_sources()
    print("Phase 39 multi-document orchestration tests passed.")


if __name__ == "__main__":
    main()
