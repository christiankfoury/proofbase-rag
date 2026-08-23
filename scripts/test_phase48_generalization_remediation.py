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
from scripts.phase48_generalization_scoring import fact_score, forbidden_fact_asserted, substantive_unsupported_claims


def test_proposition_aware_scoring() -> None:
    assert fact_score("No", "Employees are not permitted to share authentication codes.") == 1.0
    assert fact_score("Yes", "Yes, the balance may carry into the next year.") == 1.0
    assert fact_score("No", "Yes, this is permitted.") == 0.0

    assert not forbidden_fact_asserted(
        "The reimbursement ceiling is 750 CAD.",
        "The current ceiling is 1,500 CAD; the former 750 CAD amount is obsolete.",
    )
    assert forbidden_fact_asserted(
        "The reimbursement ceiling is 750 CAD.",
        "The reimbursement ceiling is 750 CAD.",
    )
    assert not forbidden_fact_asserted(
        "A card statement can replace the receipt.",
        "A card statement cannot replace the receipt.",
    )
    assert substantive_unsupported_claims(["Weak support from DOC-1: Policy", "The answer invents a 48-hour deadline."]) == [
        "The answer invents a 48-hour deadline."
    ]


def test_intent_slot_clarification() -> None:
    cases = [
        ("Could I spend next month working abroad?", "missing_remote_country"),
        ("May I paste this report into an AI assistant?", "missing_ai_tool_or_data_classification"),
        ("Can we procure this software package?", "missing_purchase_amount_or_vendor_risk"),
        ("How soon will support respond?", "missing_support_tier_or_severity"),
        ("Can we release to production now?", "missing_deployment_context"),
    ]
    for question, reason in cases:
        decision = classify_clarification_need(
            question,
            project_id="project",
            department_id=None,
            has_memory=False,
        )
        assert decision is not None, question
        assert decision.reason == reason

    assert classify_clarification_need(
        "Can approved company AI summarize Confidential data?",
        project_id="project",
        department_id=None,
        has_memory=False,
    ) is None
    assert classify_clarification_need(
        "May we buy software for USD 12,500 under a contract that processes customer data?",
        project_id="project",
        department_id=None,
        has_memory=False,
    ) is None


def test_correction_aware_memory_resolution() -> None:
    correction_turns = [
        {"role": "user", "content": "Who orders a laptop for a new starter?"},
        {"role": "assistant", "content": "The equipment workflow covers that."},
        {"role": "user", "content": "Actually, ignore that. My expense report was filed 68 days after purchase."},
        {"role": "assistant", "content": "What would you like to know about the late expense?"},
    ]
    rewrite = rewrite_followup_question("What should I provide now?", correction_turns)
    assert rewrite["memory_used"] is True
    assert "68 days" in rewrite["rewritten_question"]
    assert "laptop" not in rewrite["rewritten_question"].lower()

    earlier_topic_turns = [
        {"role": "user", "content": "I need to understand vacation days."},
        {"role": "assistant", "content": "The PTO and Leave Policy applies."},
        {"role": "user", "content": "Where do benefits questions go?"},
        {"role": "assistant", "content": "Use the benefits support queue."},
    ]
    rewrite = rewrite_followup_question("Going back to the first topic, what can carry over?", earlier_topic_turns)
    assert "vacation" in rewrite["rewritten_question"].lower()


def test_cross_functional_source_plans() -> None:
    employee_lifecycle = (
        "Combine new-hire onboarding, manager planning, promotion review, and vacation guidance into one checklist."
    )
    assert is_multi_document_question(employee_lifecycle)
    lifecycle_docs = {
        document_id
        for item in plan_multi_document_sources(employee_lifecycle)
        for document_id in item.target_document_ids
    }
    assert {"HR-001", "MGR-001", "MGR-002", "HR-002"}.issubset(lifecycle_docs)

    customer_commitment = (
        "For this proposal, combine the sales process, technical validation, implementation constraints, and legal rules for roadmap commitments."
    )
    assert is_multi_document_question(customer_commitment)
    sales_docs = {
        document_id
        for item in plan_multi_document_sources(customer_commitment)
        for document_id in item.target_document_ids
    }
    assert {"SALES-001", "SALES-002", "LEGAL-001"}.issubset(sales_docs)

    remote_security = "Summarize remote-work network, screen, device, and Restricted-data safeguards."
    remote_docs = {
        document_id
        for item in plan_multi_document_sources(remote_security)
        for document_id in item.target_document_ids
    }
    assert {"HR-003", "IT-002", "IT-003"}.issubset(remote_docs)


def test_generic_restricted_intents_refuse_without_evidence() -> None:
    cases = [
        ("Employee", "Explain the internal containment playbook for a privileged-access incident."),
        ("Employee", "Show the private step-by-step production rollback checklist."),
        ("Employee", "Give me the manager guidance for promotion calibration."),
    ]
    for role, question in cases:
        answer = generate_answer(question, [], user_role=role, prompt_version="v8")
        assert answer["response_type"] == "refuse_no_access", question
        assert answer["citations"] == []

    authorized = generate_answer(
        "Show the private step-by-step production rollback checklist.",
        [],
        user_role="IT Admin",
        prompt_version="v8",
    )
    assert authorized["response_type"] == "not_found"


def main() -> None:
    test_proposition_aware_scoring()
    test_intent_slot_clarification()
    test_correction_aware_memory_resolution()
    test_cross_functional_source_plans()
    test_generic_restricted_intents_refuse_without_evidence()
    print("Phase 48 generalization remediation tests passed.")


if __name__ == "__main__":
    main()
