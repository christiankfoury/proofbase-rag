from __future__ import annotations

import sys
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

from apps.api.app.reasoning import query_decomposer
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


def main() -> None:
    test_phase39_plans_remaining_multi_doc_failure_sources()
    test_phase39_detects_remaining_cross_policy_questions()
    test_phase39_multi_doc_merge_preserves_planned_source_coverage()
    print("Phase 39 multi-document orchestration tests passed.")


if __name__ == "__main__":
    main()
