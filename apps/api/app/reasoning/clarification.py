from __future__ import annotations

import re
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
    rewritten_question: str | None = None,
) -> ClarificationDecision | None:
    normalized = " ".join(question.lower().strip().split())
    contextual = " ".join((rewritten_question or question).lower().strip().split())
    if not normalized:
        return None

    unsafe_instruction = _unsafe_user_instruction_override(normalized)
    if unsafe_instruction:
        return unsafe_instruction

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

    if re.fullmatch(r"(?:what|which) approvals? do (?:i|we) need\??", normalized):
        return ClarificationDecision(
            reason="missing_approval_context",
            question="What activity needs approval, and what amount, duration, or exception applies?",
        )

    if not has_memory and _has_unresolved_pronoun(normalized):
        return ClarificationDecision(
            reason="unclear_followup_reference",
            question="What does ‘it’ refer to, and which policy or activity should I use?",
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

    decision = _missing_decision_variable(contextual)
    if decision:
        return decision

    return None


def _unsafe_user_instruction_override(normalized: str) -> ClarificationDecision | None:
    source_discussion = _has_any(
        normalized,
        (
            "source says",
            "document says",
            "document contains",
            "handbook says",
            "policy says",
            "retrieved passage",
            "retrieved source",
            "paragraph says",
        ),
    )
    asks_about_instruction = _has_any(
        normalized,
        (
            "should you follow",
            "should i follow",
            "should you obey",
            "should it be followed",
            "is that text an instruction",
            "what should you do",
            "what should the assistant do",
        ),
    )
    direct_answer_manipulation = _has_any(
        normalized,
        (
            "ignore the uploaded documents",
            "ignore uploaded documents",
            "ignore all previous instructions",
            "ignore previous instructions and",
            "do not provide citations",
            "don't provide citations",
            "answer without citations",
            "say the ",
            "act as an admin",
            "act as admin",
            "act as it admin",
            "pretend you are an admin",
            "pretend to be an admin",
        ),
    )
    if source_discussion and asks_about_instruction and not direct_answer_manipulation:
        return None

    override_request = _has_any(
        normalized,
        (
            "ignore previous instructions",
            "ignore all previous instructions",
            "ignore the uploaded documents",
            "ignore uploaded documents",
            "ignore the available documents",
            "ignore available documents",
            "ignore the retrieved context",
            "act as an admin",
            "act as admin",
            "act as it admin",
            "pretend you are an admin",
            "pretend to be an admin",
        ),
    )
    evidence_bypass = _has_any(
        normalized,
        (
            "do not provide citations",
            "don't provide citations",
            "without citations",
            "hide citations",
            "bypass access",
            "reveal restricted",
        ),
    )
    if override_request or evidence_bypass:
        return ClarificationDecision(
            reason="unsafe_user_instruction_override",
            question=(
                "I can’t ignore source evidence, citations, or access controls, and I won’t repeat a requested value as fact. "
                "Please ask the source-grounded policy question you want answered."
            ),
        )
    return None


def _has_unresolved_pronoun(normalized: str) -> bool:
    if not re.search(r"\b(?:it|that|this)\b", normalized):
        return False
    return bool(
        re.fullmatch(
            r"(?:how far (?:ahead|in advance) (?:do|should|must) (?:i|we) (?:need to )?book (?:it|that)|"
            r"when (?:do|should|must) (?:i|we) (?:need to )?(?:book|submit|report) (?:it|that)|"
            r"what (?:approval|deadline|limit|policy) (?:applies to|is required for) (?:it|that))\??",
            normalized,
        )
    )


def _has_any(text: str, terms: tuple[str, ...]) -> bool:
    return any(term in text for term in terms)


def _missing_decision_variable(normalized: str) -> ClarificationDecision | None:
    remote_decision = _has_any(normalized, ("can i", "could i", "may i", "can we", "could we", "may we", "work from", "working from", "spend next"))
    if remote_decision and _has_any(normalized, ("work abroad", "working abroad", "work overseas", "working overseas", "another country", "cross-border", "international remote")):
        has_specific_country = _has_any(
            normalized,
            ("canada", "united states", " u.s.", " us ", "mexico", "uk", "united kingdom", "france", "germany", "spain"),
        )
        if not has_specific_country:
            return ClarificationDecision(
                reason="missing_remote_country",
                question="Which country would you work from, and for how long?",
            )

    if _has_any(normalized, ("ai tool", "ai assistant", "copilot", "llm", "artificial intelligence")) and _has_any(
        normalized, ("data", "file", "document", "record", "summarize", "paste", "upload")
    ):
        has_data_class = _has_any(normalized, ("public data", "public information", "internal data", "internal information", "confidential", "restricted", "customer data"))
        demonstrative_unknown = _has_any(normalized, ("this report", "this file", "this document", "these records", "paste this", "upload this"))
        if demonstrative_unknown or not has_data_class:
            return ClarificationDecision(
                reason="missing_ai_tool_or_data_classification",
                question="Which AI tool would you use, and what is the data classification?",
            )

    if _has_any(normalized, ("buy software", "purchase software", "software purchase", "procure software", "procure this software", "software package", "start this vendor", "onboard this vendor")):
        has_amount = bool(re.search(r"(?:usd|cad|\$)\s*[\d,]+|[\d,]+\s*(?:usd|cad)", normalized))
        has_vendor_scope = _has_any(normalized, ("company data", "customer data", "credentials", "building access", "low risk", "high risk", "contract"))
        if not has_amount or not has_vendor_scope:
            return ClarificationDecision(
                reason="missing_purchase_amount_or_vendor_risk",
                question="What is the annualized amount, and will the vendor handle data, credentials, building access, or a contract?",
            )

    sales_stage_decision = _has_any(normalized, ("can i", "can we", "should i", "should we", "move this opportunity", "move the opportunity", "advance this deal"))
    if sales_stage_decision and _has_any(normalized, ("move this opportunity", "move the opportunity", "advance this deal", "proposal stage")):
        if not _has_any(normalized, ("discovery notes", "stakeholder mapping", "complete discovery", "completed discovery")):
            return ClarificationDecision(
                reason="missing_sales_stage_readiness",
                question="Are the discovery notes and stakeholder mapping complete?",
            )

    if _has_any(normalized, ("delete contract", "delete these contract", "remove contract draft", "dispose of contract")):
        if not _has_any(normalized, ("expired", "executed", "draft", "retention", "legal hold", "years after")):
            return ClarificationDecision(
                reason="missing_contract_status",
                question="Are these drafts, executed contracts, expired contracts, or records subject to a legal hold?",
            )

    deployment_decision = _has_any(normalized, ("can i", "can we", "could we", "may we", "should we", "deploy tonight", "deploy now", "release tonight", "release to production"))
    if deployment_decision and _has_any(normalized, ("deploy tonight", "deploy now", "release tonight", "release to production", "production deployment")):
        if not _has_any(normalized, ("sev-1", "incident", "approved window", "emergency", "friday", "monday", "tuesday", "wednesday", "thursday")):
            return ClarificationDecision(
                reason="missing_deployment_context",
                question="Is this an approved deployment window or an emergency incident change?",
            )

    if _has_any(normalized, ("support response", "support respond", "support update", "support get back", "escalate this customer")):
        if not _has_any(normalized, ("enterprise", "standard", "sev-1", "sev-2", "severity", "data exposure")):
            return ClarificationDecision(
                reason="missing_support_tier_or_severity",
                question="What is the customer support tier and incident severity?",
            )

    if _has_any(normalized, ("offer a credit", "customer credit", "promise a refund", "issue a refund")):
        if not _has_any(normalized, ("contract", "manager", "legal", "amount", "usd", "cad", "$")):
            return ClarificationDecision(
                reason="missing_credit_contract_context",
                question="What amount and contract terms apply to the proposed credit or refund?",
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
