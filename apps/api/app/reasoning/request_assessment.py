from __future__ import annotations

import logging
import re
import time
from typing import Any, Literal

from openai import OpenAI
from pydantic import BaseModel, ConfigDict, Field, ValidationError

from apps.api.app.core.config import get_settings
from apps.api.app.costing.estimator import estimate_chat_cost
from apps.api.app.observability.auxiliary_telemetry import submit_auxiliary_telemetry
from apps.api.app.prompts.prompt_registry import get_prompt
from apps.api.app.reasoning.clarification import ClarificationDecision, classify_clarification_need


logger = logging.getLogger(__name__)


Intent = Literal["question", "command", "source_discussion", "evaluation", "unknown"]
Topic = Literal[
    "approval",
    "benefits",
    "contracts",
    "customer_support",
    "data_governance",
    "deployment",
    "expenses",
    "identity_or_access",
    "procurement",
    "security",
    "travel",
    "workplace_policy",
    "unknown",
]
Referents = Literal["resolved", "unresolved", "not_applicable"]
Ambiguity = Literal["none", "resolvable_from_conversation", "clarification_required"]
InjectionRisk = Literal[
    "none",
    "source_discussion",
    "direct_override",
    "indirect_or_obfuscated",
    "uncertain",
]
RecommendedAction = Literal["continue", "clarify", "block", "temporary_unavailable"]
ReasonCode = Literal[
    "no_risk",
    "missing_context",
    "unresolved_reference",
    "missing_decision_variables",
    "direct_override_request",
    "indirect_or_obfuscated_attack",
    "source_discussion_context",
    "mixed_valid_and_override",
    "memory_scope_escalation",
    "citation_suppression",
    "unknown_intent",
    "deterministic_guard",
    "semantic_assessment_required",
    "assessment_timeout",
    "assessment_service_error",
    "assessment_schema_invalid",
]
AssessmentRoute = Literal[
    "deterministic_guard",
    "deterministic_continue",
    "semantic_assessment",
    "semantic_skipped_confident",
    "fail_safe",
]
AssessmentStatus = Literal["succeeded", "skipped", "failed_safe"]
NormalizationReason = Literal[
    "clear_information_request",
    "searchable_named_subject",
]


class RequestAssessmentDecision(BaseModel):
    model_config = ConfigDict(extra="forbid")

    intent: Intent
    topic: Topic
    topic_description: str | None
    referents: Referents
    missing_referents: list[str] = Field(max_length=6)
    decision_variables: list[str] = Field(max_length=8)
    ambiguity: Ambiguity
    injection_risk: InjectionRisk
    recommended_action: RecommendedAction
    reason_codes: list[ReasonCode] = Field(min_length=1, max_length=6)
    assessment_confidence: float = Field(ge=0.0, le=1.0)
    schema_version: Literal["request_assessment.v1"]


class RequestAssessment(RequestAssessmentDecision):
    model_config = ConfigDict(extra="forbid")

    route: AssessmentRoute
    status: AssessmentStatus
    response_reason: str | None
    model: str | None
    prompt_version: str | None
    latency_ms: int
    input_tokens: int | None
    output_tokens: int | None
    input_cost_usd: float | None
    output_cost_usd: float | None
    estimated_cost_usd: float | None
    pricing_status: str
    normalization_reason: NormalizationReason | None = None


DETERMINISTIC_REASON_CODES: dict[str, ReasonCode] = {
    "unsafe_user_instruction_override": "direct_override_request",
    "unclear_followup_reference": "unresolved_reference",
    "unclear_document_reference": "unresolved_reference",
    "unclear_comparison_targets": "unresolved_reference",
    "missing_project_scope": "missing_context",
    "missing_department_scope": "missing_context",
    "ambiguous_role_applicability": "missing_context",
    "missing_approval_context": "missing_decision_variables",
    "missing_remote_country": "missing_decision_variables",
    "missing_ai_tool_or_data_classification": "missing_decision_variables",
    "missing_purchase_amount_or_vendor_risk": "missing_decision_variables",
    "missing_sales_stage_readiness": "missing_decision_variables",
    "missing_contract_status": "missing_decision_variables",
    "missing_deployment_context": "missing_decision_variables",
    "missing_support_tier_or_severity": "missing_decision_variables",
    "missing_credit_contract_context": "missing_decision_variables",
}


def _zero_cost() -> dict[str, float | str | None]:
    return {
        "input_cost_usd": 0.0,
        "output_cost_usd": 0.0,
        "estimated_cost_usd": 0.0,
        "pricing_status": "not_applicable",
    }


def _base_continue_decision() -> RequestAssessmentDecision:
    return RequestAssessmentDecision(
        intent="question",
        topic="unknown",
        topic_description=None,
        referents="not_applicable",
        missing_referents=[],
        decision_variables=[],
        ambiguity="none",
        injection_risk="none",
        recommended_action="continue",
        reason_codes=["no_risk"],
        assessment_confidence=0.5,
        schema_version="request_assessment.v1",
    )


def deterministic_request_assessment(
    question: str,
    *,
    project_id: str | None,
    department_id: str | None,
    has_memory: bool,
    rewritten_question: str | None = None,
) -> RequestAssessment | None:
    started_at = time.perf_counter()
    decision = classify_clarification_need(
        question,
        project_id=project_id,
        department_id=department_id,
        has_memory=has_memory,
        rewritten_question=rewritten_question,
    )
    if decision is None:
        return None

    injection = decision.reason == "unsafe_user_instruction_override"
    reason_code = DETERMINISTIC_REASON_CODES.get(decision.reason, "missing_context")
    result = RequestAssessmentDecision(
        intent="command" if injection else "question",
        topic="identity_or_access" if injection else _topic_for_text(question),
        topic_description=None,
        referents="unresolved" if reason_code == "unresolved_reference" else "not_applicable",
        missing_referents=["request reference"] if reason_code == "unresolved_reference" else [],
        decision_variables=["required request context"] if reason_code == "missing_decision_variables" else [],
        ambiguity="none" if injection else "clarification_required",
        injection_risk="direct_override" if injection else "none",
        recommended_action="block" if injection else "clarify",
        reason_codes=["deterministic_guard", reason_code],
        assessment_confidence=1.0,
        schema_version="request_assessment.v1",
    )
    return RequestAssessment(
        **result.model_dump(),
        route="deterministic_guard",
        status="succeeded",
        response_reason=decision.reason,
        model=None,
        prompt_version=None,
        latency_ms=max(int((time.perf_counter() - started_at) * 1000), 0),
        input_tokens=0,
        output_tokens=0,
        **_zero_cost(),
    )


def assess_request(
    question: str,
    *,
    project_id: str | None,
    department_id: str | None,
    has_memory: bool,
    rewritten_question: str | None = None,
    previous_turns: list[dict[str, Any]] | None = None,
    mode: str | None = None,
    emit_telemetry: bool = True,
) -> RequestAssessment:
    deterministic = deterministic_request_assessment(
        question,
        project_id=project_id,
        department_id=department_id,
        has_memory=has_memory,
        rewritten_question=rewritten_question,
    )
    if deterministic is not None:
        return deterministic

    selected_mode = mode or get_settings().request_assessment_mode
    if selected_mode == "deterministic_only":
        decision = _base_continue_decision()
        return RequestAssessment(
            **decision.model_dump(),
            route="deterministic_continue",
            status="skipped",
            response_reason=None,
            model=None,
            prompt_version=None,
            latency_ms=0,
            input_tokens=0,
            output_tokens=0,
            **_zero_cost(),
        )
    if selected_mode == "semantic_uncertain_only" and not _is_semantically_uncertain(question, has_memory=has_memory):
        decision = _base_continue_decision()
        return RequestAssessment(
            **decision.model_dump(),
            route="semantic_skipped_confident",
            status="skipped",
            response_reason=None,
            model=None,
            prompt_version=None,
            latency_ms=0,
            input_tokens=0,
            output_tokens=0,
            **_zero_cost(),
        )
    return semantic_request_assessment(
        question,
        previous_turns=previous_turns or [],
        standalone_question=rewritten_question,
        emit_telemetry=emit_telemetry,
    )


def semantic_request_assessment(
    question: str,
    *,
    previous_turns: list[dict[str, Any]],
    standalone_question: str | None = None,
    client: OpenAI | None = None,
    emit_telemetry: bool = True,
) -> RequestAssessment:
    settings = get_settings()
    prompt = get_prompt("request_assessment", settings.request_assessment_prompt_version)
    selected_model = settings.request_assessment_model or prompt.model or settings.openai_chat_model
    started_at = time.perf_counter()
    try:
        if not settings.openai_api_key and client is None:
            raise RuntimeError("request assessment service unavailable")
        api = client or OpenAI(
            api_key=settings.openai_api_key,
            timeout=settings.request_assessment_timeout_seconds,
            max_retries=1,
        )
        response = api.chat.completions.create(
            model=selected_model,
            temperature=prompt.temperature,
            messages=[
                {"role": "system", "content": prompt.content},
                {
                    "role": "user",
                    "content": _assessment_user_input(
                        question,
                        previous_turns,
                        standalone_question=standalone_question,
                    ),
                },
            ],
            response_format={
                "type": "json_schema",
                "json_schema": {
                    "name": "request_assessment_v1",
                    "strict": True,
                    "schema": RequestAssessmentDecision.model_json_schema(),
                },
            },
        )
        message = response.choices[0].message
        refusal = getattr(message, "refusal", None)
        if refusal:
            raise RuntimeError("request assessment refused")
        decision = RequestAssessmentDecision.model_validate_json(message.content or "")
        decision, normalization_reason = _enforce_semantic_contract(question, decision)
        usage = response.usage
        input_tokens = usage.prompt_tokens if usage else None
        output_tokens = usage.completion_tokens if usage else None
        cost = estimate_chat_cost(model=selected_model, input_tokens=input_tokens, output_tokens=output_tokens)
        latency_ms = max(int((time.perf_counter() - started_at) * 1000), 0)
        assessment = RequestAssessment(
            **decision.model_dump(),
            route="semantic_assessment",
            status="succeeded",
            response_reason=_semantic_response_reason(decision),
            model=selected_model,
            prompt_version=prompt.version,
            latency_ms=latency_ms,
            input_tokens=input_tokens,
            output_tokens=output_tokens,
            **cost,
            normalization_reason=normalization_reason,
        )
        if emit_telemetry:
            _submit_assessment_telemetry(assessment, question)
        return assessment
    except Exception as exc:
        latency_ms = max(int((time.perf_counter() - started_at) * 1000), 0)
        reason: ReasonCode
        if isinstance(exc, ValidationError):
            reason = "assessment_schema_invalid"
        elif "timeout" in type(exc).__name__.lower() or "timeout" in str(exc).lower():
            reason = "assessment_timeout"
        else:
            reason = "assessment_service_error"
        logger.warning(
            "request_assessment_failed error_category=%s reason=%s",
            type(exc).__name__,
            reason,
        )
        assessment = _fail_safe_assessment(
            reason=reason,
            model=selected_model,
            prompt_version=prompt.version,
            latency_ms=latency_ms,
        )
        if emit_telemetry:
            _submit_assessment_telemetry(assessment, question)
        return assessment


def assessment_response_decision(assessment: RequestAssessment) -> ClarificationDecision | None:
    action = assessment.recommended_action
    if action == "continue":
        return None
    if action == "block":
        return ClarificationDecision(
            reason=assessment.response_reason or "semantic_injection_block",
            question=(
                "I can’t follow instructions that bypass source evidence, citations, or access controls. "
                "Please ask the source-grounded company question you want answered."
            ),
        )
    if action == "temporary_unavailable":
        return ClarificationDecision(
            reason=assessment.response_reason or "request_assessment_unavailable",
            question=(
                "I can’t safely assess this request right now, so I haven’t searched any company sources. "
                "Please try again shortly."
            ),
        )
    missing = [*assessment.missing_referents, *assessment.decision_variables]
    if missing:
        fields = ", ".join(dict.fromkeys(missing[:4]))
        question = f"Please clarify {fields} so I can search the right company guidance."
    else:
        question = "Please clarify which policy, activity, or decision you mean so I can search the right company guidance."
    return ClarificationDecision(
        reason=assessment.response_reason or "semantic_clarification_required",
        question=question,
    )


def _assessment_user_input(
    question: str,
    previous_turns: list[dict[str, Any]],
    *,
    standalone_question: str | None,
) -> str:
    safe_question = question.strip()[:4000]
    recent_user_turns = [
        str(turn.get("content") or "").strip()[:500]
        for turn in previous_turns[-6:]
        if turn.get("role") == "user" and str(turn.get("content") or "").strip()
    ][-2:]
    context = "\n".join(f"- {turn}" for turn in recent_user_turns) or "- none"
    standalone = (standalone_question or question).strip()[:4000]
    return (
        "<conversation_context_for_reference_resolution_only>\n"
        f"{context}\n"
        "</conversation_context_for_reference_resolution_only>\n"
        "<current_request>\n"
        f"{safe_question}\n"
        "</current_request>\n"
        "<standalone_question_for_reference_resolution_only>\n"
        f"{standalone}\n"
        "</standalone_question_for_reference_resolution_only>"
    )


def _is_semantically_uncertain(question: str, *, has_memory: bool) -> bool:
    normalized = " ".join(question.lower().split())
    if len(normalized.split()) <= 5:
        return True
    if re.search(r"\b(it|that|this|those|them|earlier|previous)\b", normalized):
        return True
    if any(term in normalized for term in ("ignore", "bypass", "without citations", "act as", "pretend", "decode", "system prompt")):
        return True
    if has_memory:
        return True
    return normalized.endswith("?") and any(term in normalized for term in ("can i", "should i", "may i", "which"))


_PLAIN_INFORMATION_REQUEST = re.compile(r"^\s*(what|who|where|when|which|how)\b", re.IGNORECASE)
_BEHAVIOR_MANIPULATION_MARKERS = re.compile(
    r"\b(ignore|disregard|bypass|override|omit|hide|conceal|suppress|invent|fabricate|"
    r"pretend|decode|obey|promote|authorize|disable|discard|replace|reveal any|"
    r"act as|system prompt|higher authority|without (?:a )?(?:source|citation)|"
    r"outside (?:my|the) (?:project|scope)|all workspaces)\b",
    re.IGNORECASE,
)
_UNRESOLVED_REFERENCE_WORDS = {
    "it",
    "that",
    "this",
    "those",
    "them",
    "here",
    "there",
    "earlier",
    "previous",
    "she",
    "he",
    "they",
}


def _enforce_semantic_contract(
    question: str,
    decision: RequestAssessmentDecision,
) -> tuple[RequestAssessmentDecision, NormalizationReason | None]:
    """Reconcile model output with the router's narrow, non-authorizing contract.

    Clear information requests must reach permission-filtered retrieval even when
    their subject is sensitive or may be absent. The deterministic injection guard
    has already run; this check only rejects cross-field semantic contradictions and
    never grants scope, role, document, or tool access.
    """
    if decision.recommended_action == "continue":
        return decision, None

    normalized = " ".join(question.lower().split())
    words = re.findall(r"[a-z0-9]+", normalized)
    plain_information_request = bool(_PLAIN_INFORMATION_REQUEST.search(question)) and len(words) >= 7
    contains_manipulation = bool(_BEHAVIOR_MANIPULATION_MARKERS.search(normalized))

    if (
        decision.recommended_action == "block"
        and plain_information_request
        and not contains_manipulation
        and decision.injection_risk in {"none", "direct_override"}
    ):
        return _normalized_continue(decision), "clear_information_request"

    if decision.recommended_action != "clarify" or not plain_information_request:
        return decision, None
    if decision.injection_risk not in {"none", "source_discussion"} or contains_manipulation:
        return decision, None

    if decision.ambiguity == "none" and decision.referents != "unresolved":
        return _normalized_continue(decision), "clear_information_request"

    missing_phrases = [" ".join(value.lower().split()) for value in decision.missing_referents]
    searchable_subject = any(
        phrase
        and phrase in normalized
        and len(re.findall(r"[a-z0-9]+", phrase)) >= 2
        and not any(word in _UNRESOLVED_REFERENCE_WORDS for word in phrase.split())
        for phrase in missing_phrases
    )
    if searchable_subject:
        return _normalized_continue(decision), "searchable_named_subject"
    has_unresolved_reference = any(word in _UNRESOLVED_REFERENCE_WORDS for word in words)
    if not has_unresolved_reference and not decision.decision_variables:
        return _normalized_continue(decision), "clear_information_request"
    return decision, None


def _normalized_continue(decision: RequestAssessmentDecision) -> RequestAssessmentDecision:
    return decision.model_copy(
        update={
            "referents": "resolved",
            "missing_referents": [],
            "decision_variables": [],
            "ambiguity": "none",
            "injection_risk": "none",
            "recommended_action": "continue",
        }
    )


def _topic_for_text(question: str) -> Topic:
    normalized = question.lower()
    topics: list[tuple[tuple[str, ...], Topic]] = [
        (("approval", "approve"), "approval"),
        (("travel", "flight", "booking"), "travel"),
        (("vendor", "software purchase", "procure"), "procurement"),
        (("deploy", "production release"), "deployment"),
        (("access", "admin", "role"), "identity_or_access"),
        (("security", "device", "incident"), "security"),
        (("contract", "nda"), "contracts"),
        (("expense", "refund", "credit"), "expenses"),
        (("benefit", "vacation", "leave"), "benefits"),
    ]
    for markers, topic in topics:
        if any(marker in normalized for marker in markers):
            return topic
    return "unknown"


def _semantic_response_reason(decision: RequestAssessmentDecision) -> str | None:
    if decision.recommended_action == "block":
        return "semantic_injection_block"
    if decision.recommended_action == "clarify":
        return "semantic_clarification_required"
    if decision.recommended_action == "temporary_unavailable":
        return "request_assessment_unavailable"
    return None


def _fail_safe_assessment(
    *,
    reason: ReasonCode,
    model: str,
    prompt_version: str,
    latency_ms: int,
) -> RequestAssessment:
    return RequestAssessment(
        intent="unknown",
        topic="unknown",
        topic_description=None,
        referents="not_applicable",
        missing_referents=[],
        decision_variables=[],
        ambiguity="clarification_required",
        injection_risk="uncertain",
        recommended_action="temporary_unavailable",
        reason_codes=[reason],
        assessment_confidence=0.0,
        schema_version="request_assessment.v1",
        route="fail_safe",
        status="failed_safe",
        response_reason="request_assessment_unavailable",
        model=model,
        prompt_version=prompt_version,
        latency_ms=latency_ms,
        input_tokens=None,
        output_tokens=None,
        input_cost_usd=None,
        output_cost_usd=None,
        estimated_cost_usd=None,
        pricing_status="missing_token_usage",
    )


def _submit_assessment_telemetry(assessment: RequestAssessment, question: str) -> None:
    submit_auxiliary_telemetry(
        operation_type="request_assessment",
        model=assessment.model or "unknown",
        status="succeeded" if assessment.status == "succeeded" else "failed",
        prompt_name="request_assessment",
        prompt_version=assessment.prompt_version,
        input_tokens=assessment.input_tokens,
        output_tokens=assessment.output_tokens,
        estimated_cost_usd=assessment.estimated_cost_usd,
        pricing_status=assessment.pricing_status,
        latency_ms=assessment.latency_ms,
        question=question,
        metadata={
            "schema_version": assessment.schema_version,
            "route": assessment.route,
            "recommended_action": assessment.recommended_action,
            "reason_codes": list(assessment.reason_codes),
            "normalization_reason": assessment.normalization_reason,
        },
    )
