from __future__ import annotations

import sys
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

from apps.api.app.generation.answer_generator import generate_answer
from apps.api.app.memory.query_rewriter import rewrite_followup_question
from apps.api.app.reasoning.clarification import classify_clarification_need
from apps.api.app.reasoning.multi_doc_detector import is_multi_document_question
from apps.api.app.reasoning.source_planner import plan_multi_document_sources
from apps.api.app.retrieval.types import RetrievedChunk


def _chunk(document_id: str, section: str, content: str) -> RetrievedChunk:
    return RetrievedChunk(
        chunk_id=f"{document_id}-{section}".replace(" ", "-"),
        document_id=document_id,
        document_title=f"{document_id} Title",
        section_heading=section,
        content=content,
        access_roles=["Employee", "Sales Representative", "Manager", "IT Admin", "HR Admin"],
        restricted=False,
        sensitivity="internal",
        rank=1,
        score=0.95,
        retrieval_source="test",
    )


def test_phase46_clarification_reasons() -> None:
    cases = [
        (
            "What does the project policy say about approvals?",
            {"project_id": None, "department_id": None, "has_memory": False},
            "missing_project_scope",
        ),
        (
            "What does the department handbook say about approvals?",
            {"project_id": "project", "department_id": None, "has_memory": False},
            "missing_department_scope",
        ),
        (
            "Which approval limit applies to my role?",
            {"project_id": "project", "department_id": None, "has_memory": False},
            "ambiguous_role_applicability",
        ),
        (
            "What is the policy for that?",
            {"project_id": "project", "department_id": None, "has_memory": False},
            "unclear_followup_reference",
        ),
        (
            "What does the second document say about exceptions?",
            {"project_id": "project", "department_id": None, "has_memory": False},
            "unclear_document_reference",
        ),
    ]
    for question, kwargs, expected_reason in cases:
        decision = classify_clarification_need(question, **kwargs)
        assert decision is not None
        assert decision.reason == expected_reason

    assert classify_clarification_need(
        "What does that policy say about carrying unused days?",
        project_id="project",
        department_id=None,
        has_memory=True,
    ) is None


def test_phase46_memory_rewrites_measured_failures() -> None:
    cases = [
        (
            [{"role": "user", "content": "What are remote work approval expectations?"}],
            "In the same department, what security expectations apply?",
            "remote_work_security_expectations",
            ["remote work", "device security"],
        ),
        (
            [{"role": "assistant", "content": "Promotion calibration is covered in manager guidance."}],
            "What does it say about calibration?",
            "promotion_calibration_restricted_topic",
            ["promotion calibration"],
        ),
        (
            [{"role": "user", "content": "Tell me about privileged access incidents."}],
            "What containment steps should I take?",
            "privileged_access_containment_restricted_topic",
            ["privileged access", "containment"],
        ),
        (
            [{"role": "user", "content": "We discussed acceptable use."}],
            "What about BYOD devices?",
            "acceptable_use_byod",
            ["byod", "device security"],
        ),
    ]
    for previous_turns, question, expected_strategy, expected_terms in cases:
        rewrite = rewrite_followup_question(question, previous_turns)
        assert rewrite["memory_used"] is True
        assert rewrite["rewrite_strategy"] == expected_strategy
        rewritten = rewrite["rewritten_question"].lower()
        for term in expected_terms:
            assert term in rewritten


def test_phase46_source_planning_for_failed_generalization_cases() -> None:
    remote_question = "For remote work and personal device use, what approvals and device safeguards apply?"
    sales_question = "For price objections, which objection-handling guidance should a Sales Representative use?"

    assert is_multi_document_question(remote_question)
    remote_docs = {doc for item in plan_multi_document_sources(remote_question) for doc in item.target_document_ids}
    assert {"HR-003", "IT-002"}.issubset(remote_docs)

    sales_docs = {doc for item in plan_multi_document_sources(sales_question) for doc in item.target_document_ids}
    assert "SALES-003" in sales_docs


def test_phase46_direct_answers_use_retrieved_evidence_only() -> None:
    answer = generate_answer(
        "For remote work and personal device use, what approvals and device safeguards apply?",
        [
            _chunk("HR-003", "Approved Remote Work Locations", "Remote employees may work from approved locations in Canada or the United States if their role, tax location, and security requirements support remote work."),
            _chunk("HR-003", "Security Requirements", "Remote work must follow the Device and BYOD Security Policy and the Data Classification and Handling Policy."),
            _chunk("IT-002", "Personal Device Requirements", "Personal devices may be used for limited work access only when enrolled in approved mobile device management or when access occurs through approved browser-based tools."),
            _chunk("IT-002", "Data Storage", "Restricted data must not be downloaded to personal devices."),
        ],
        user_role="Employee",
        prompt_version="v8",
        multi_doc=True,
    )
    assert answer["response_type"] == "answer"
    cited_docs = {citation["document_id"] for citation in answer["citations"]}
    assert {"HR-003", "IT-002"}.issubset(cited_docs)
    assert not answer["unsupported_claims"]

    benefits_answer = generate_answer(
        "What should I do if I need benefits help and also want to use my learning budget?",
        [
            _chunk("HR-001", "Employee Support Channels", "Benefits questions should be sent to the benefits support queue."),
            _chunk("HR-004", "Learning Budget", "Employees receive an annual learning budget of 1,500 CAD or 1,100 USD for approved courses, books, conferences, and certifications related to their role. Manager approval is required before purchase."),
        ],
        user_role="Employee",
        prompt_version="v8",
        multi_doc=True,
    )
    assert benefits_answer["response_type"] == "answer"
    assert "1,500 CAD" in benefits_answer["answer"]
    assert "1,100 USD" in benefits_answer["answer"]
    assert {"HR-001", "HR-004"}.issubset({citation["document_id"] for citation in benefits_answer["citations"]})


def test_phase46_restricted_memory_refusal_has_no_citations() -> None:
    answer = generate_answer(
        "What does manager guidance say about promotion calibration?",
        [],
        user_role="Employee",
        prompt_version="v8",
    )
    assert answer["response_type"] == "refuse_no_access"
    assert answer["citations"] == []
    assert "memory" not in " ".join(str(citation) for citation in answer["citations"]).lower()


def main() -> None:
    test_phase46_clarification_reasons()
    test_phase46_memory_rewrites_measured_failures()
    test_phase46_source_planning_for_failed_generalization_cases()
    test_phase46_direct_answers_use_retrieved_evidence_only()
    test_phase46_restricted_memory_refusal_has_no_citations()
    print("Phase 46 generalization remediation tests passed.")


if __name__ == "__main__":
    main()
