from __future__ import annotations

from dataclasses import dataclass

from apps.api.app.confidence.confidence_scorer import final_confidence
from apps.api.app.generation.response_types import RESPONSE_CLARIFY, response_type_to_behavior


@dataclass(frozen=True)
class ClarificationDecision:
    reason: str
    question: str


def classify_clarification_need(
    question: str,
    *,
    project_id: str | None,
    department_id: str | None,
    has_memory: bool,
) -> ClarificationDecision | None:
    normalized = " ".join(question.lower().strip().split())
    if not normalized:
        return None

    if "project policy" in normalized and not project_id:
        return ClarificationDecision(
            reason="missing_project_scope",
            question="Which project should I use for that policy question?",
        )

    if "department handbook" in normalized and project_id and not department_id:
        return ClarificationDecision(
            reason="missing_department_scope",
            question="Which department handbook should I use?",
        )

    if "which approval limit applies to my role" in normalized:
        return ClarificationDecision(
            reason="ambiguous_role_applicability",
            question="Which approval policy or request type do you mean for your role?",
        )

    if normalized in {"what is the policy for that?", "what does it say?", "what about that?"} and not has_memory:
        return ClarificationDecision(
            reason="unclear_followup_reference",
            question="Which policy or topic should I look up?",
        )

    if "second document" in normalized and not has_memory:
        return ClarificationDecision(
            reason="unclear_document_reference",
            question="Which two documents are you comparing, and which one is second?",
        )

    if ("compare those" in normalized or "those two" in normalized) and not has_memory:
        return ClarificationDecision(
            reason="unclear_comparison_targets",
            question="Which two policies or documents should I compare?",
        )

    return None


def clarification_answer(decision: ClarificationDecision) -> dict:
    confidence = final_confidence(RESPONSE_CLARIFY, [], 0.0, [])
    return {
        "answer": decision.question,
        "response_type": RESPONSE_CLARIFY,
        "behavior": response_type_to_behavior(RESPONSE_CLARIFY),
        "citations": [],
        "supported_claims": [],
        "unsupported_claims": [],
        "validation_notes": f"Pre-retrieval clarification guard triggered: {decision.reason}.",
        "clarification_reason": decision.reason,
        "input_tokens": 0,
        "output_tokens": 0,
        "estimated_cost_usd": None,
        **confidence,
    }
