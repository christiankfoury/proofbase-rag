from __future__ import annotations

import json
import logging
import time
from typing import Any, Literal

from openai import OpenAI
from pydantic import BaseModel, ConfigDict, Field, ValidationError

from apps.api.app.core.config import get_settings
from apps.api.app.costing.estimator import estimate_chat_cost
from apps.api.app.observability.auxiliary_telemetry import submit_auxiliary_telemetry
from apps.api.app.prompts.prompt_registry import get_prompt
from apps.api.app.reasoning.request_assessment import RequestAssessment
from apps.api.app.reasoning.source_planner import SourcePlanItem, plan_multi_document_sources
from apps.api.app.retrieval.types import RetrievedChunk


logger = logging.getLogger(__name__)


Answerability = Literal["sufficient", "partial", "insufficient", "conflicting", "uncertain"]
SupportStatus = Literal["supported", "unsupported", "conflicting"]
CoverageStatus = Literal["covered", "missing", "partial"]
ConflictType = Literal["version", "effective_date", "applicability", "precedence", "factual"]
EvidenceAction = Literal["answer", "partial_answer", "clarify", "not_found", "temporary_unavailable"]
EvidenceReasonCode = Literal[
    "authorized_evidence_sufficient",
    "empty_authorized_evidence",
    "required_fact_missing",
    "partial_fact_support",
    "required_source_missing",
    "required_source_coverage_complete",
    "accessible_conflict_unresolved",
    "accessible_precedence_resolved",
    "exact_detail_not_supported",
    "deterministic_default_answer",
    "authorized_source_instruction_guidance",
    "assessment_timeout",
    "assessment_service_error",
    "assessment_schema_invalid",
    "assessment_contract_invalid",
    "unauthorized_reference_rejected",
]
EvidenceRoute = Literal[
    "deterministic_empty",
    "deterministic_source_coverage",
    "deterministic_default",
    "deterministic_source_instruction_safety",
    "hybrid_semantic",
    "semantic_always",
    "fail_safe",
]
EvidenceStatus = Literal["succeeded", "skipped", "failed_safe"]


class RequiredFact(BaseModel):
    model_config = ConfigDict(extra="forbid")

    fact_id: str = Field(min_length=1, max_length=48)
    description: str = Field(min_length=1, max_length=180)
    support: SupportStatus
    supporting_chunk_ids: list[str] = Field(max_length=10)


class RequiredSourceCoverage(BaseModel):
    model_config = ConfigDict(extra="forbid")

    source_label: str = Field(min_length=1, max_length=80)
    status: CoverageStatus
    supporting_chunk_ids: list[str] = Field(max_length=10)


class EvidenceConflict(BaseModel):
    model_config = ConfigDict(extra="forbid")

    topic: str = Field(min_length=1, max_length=160)
    conflict_type: ConflictType
    chunk_ids: list[str] = Field(min_length=2, max_length=10)
    resolved: bool
    resolution_basis: str | None = Field(max_length=180)


class EvidenceAssessmentDecision(BaseModel):
    model_config = ConfigDict(extra="forbid")

    answerability: Answerability
    required_facts: list[RequiredFact] = Field(min_length=1, max_length=10)
    required_source_coverage: list[RequiredSourceCoverage] = Field(max_length=8)
    conflicts: list[EvidenceConflict] = Field(max_length=6)
    missing_information: list[str] = Field(max_length=8)
    recommended_action: EvidenceAction
    supporting_chunk_ids: list[str] = Field(max_length=10)
    reason_codes: list[EvidenceReasonCode] = Field(min_length=1, max_length=6)
    assessment_confidence: float = Field(ge=0.0, le=1.0)
    schema_version: Literal["evidence_assessment.v1"]


class SemanticEvidenceDecision(BaseModel):
    """Minimal model-authored fields; deterministic fields are added by the service."""

    model_config = ConfigDict(extra="forbid")

    answerability: Answerability
    required_facts: list[RequiredFact] = Field(min_length=1, max_length=10)
    conflicts: list[EvidenceConflict] = Field(max_length=6)
    missing_information: list[str] = Field(max_length=8)
    supporting_chunk_ids: list[str] = Field(max_length=10)
    assessment_confidence: float = Field(ge=0.0, le=1.0)


class EvidenceAssessment(EvidenceAssessmentDecision):
    model_config = ConfigDict(extra="forbid")

    route: EvidenceRoute
    status: EvidenceStatus
    model: str | None
    prompt_version: str | None
    latency_ms: int
    input_tokens: int | None
    output_tokens: int | None
    input_cost_usd: float | None
    output_cost_usd: float | None
    estimated_cost_usd: float | None
    pricing_status: str
    normalization_reason: EvidenceReasonCode | None = None


_ACTION_BY_ANSWERABILITY: dict[Answerability, EvidenceAction] = {
    "sufficient": "answer",
    "partial": "partial_answer",
    "insufficient": "not_found",
    "conflicting": "clarify",
    "uncertain": "temporary_unavailable",
}


def assess_evidence(
    question: str,
    *,
    request_assessment: RequestAssessment,
    authorized_chunks: list[RetrievedChunk],
    multi_document: bool,
    mode: str | None = None,
    client: OpenAI | None = None,
    emit_telemetry: bool = True,
) -> EvidenceAssessment:
    if request_assessment.recommended_action != "continue":
        raise ValueError("Evidence assessment requires a continued request assessment.")

    selected_mode = mode or get_settings().evidence_assessment_mode
    source_plan = _required_source_plan(question) if multi_document else []
    deterministic = _deterministic_assessment(
        question,
        request_assessment=request_assessment,
        authorized_chunks=authorized_chunks,
        source_plan=source_plan,
        mode=selected_mode,
    )
    if deterministic is not None:
        if emit_telemetry:
            _submit_evidence_telemetry(deterministic, question, len(authorized_chunks))
        return deterministic

    route: EvidenceRoute = "semantic_always" if selected_mode == "semantic_always" else "hybrid_semantic"
    return _semantic_assessment(
        question,
        request_assessment=request_assessment,
        authorized_chunks=authorized_chunks,
        source_plan=source_plan,
        route=route,
        client=client,
        emit_telemetry=emit_telemetry,
    )


def evidence_generation_action(assessment: EvidenceAssessment) -> Literal["answer", "partial_answer"] | None:
    if assessment.recommended_action in {"answer", "partial_answer"}:
        return assessment.recommended_action
    return None


def evidence_response_reason(assessment: EvidenceAssessment) -> str:
    if assessment.recommended_action == "not_found":
        return "authorized_evidence_insufficient"
    if assessment.recommended_action == "clarify":
        return "authorized_evidence_conflicting"
    if assessment.recommended_action == "temporary_unavailable":
        return "evidence_assessment_unavailable"
    return "authorized_evidence_available"


def _deterministic_assessment(
    question: str,
    *,
    request_assessment: RequestAssessment,
    authorized_chunks: list[RetrievedChunk],
    source_plan: list[SourcePlanItem],
    mode: str,
) -> EvidenceAssessment | None:
    started_at = time.perf_counter()
    if not authorized_chunks and mode != "semantic_always":
        decision = EvidenceAssessmentDecision(
            answerability="insufficient",
            required_facts=[
                RequiredFact(
                    fact_id="requested_information",
                    description="The information requested by the user",
                    support="unsupported",
                    supporting_chunk_ids=[],
                )
            ],
            required_source_coverage=[],
            conflicts=[],
            missing_information=["The requested information is not supported by the available evidence."],
            recommended_action="not_found",
            supporting_chunk_ids=[],
            reason_codes=["empty_authorized_evidence"],
            assessment_confidence=1.0,
            schema_version="evidence_assessment.v1",
        )
        return _with_metadata(decision, route="deterministic_empty", status="succeeded", started_at=started_at)

    source_instruction_support = _source_instruction_safety_support(
        question,
        request_assessment=request_assessment,
        authorized_chunks=authorized_chunks,
    )
    if source_instruction_support and mode != "semantic_always":
        decision = EvidenceAssessmentDecision(
            answerability="sufficient",
            required_facts=[
                RequiredFact(
                    fact_id="source_instruction_handling",
                    description="How the embedded source instruction must be treated",
                    support="supported",
                    supporting_chunk_ids=source_instruction_support,
                )
            ],
            required_source_coverage=[],
            conflicts=[],
            missing_information=[],
            recommended_action="answer",
            supporting_chunk_ids=source_instruction_support,
            reason_codes=["authorized_source_instruction_guidance"],
            assessment_confidence=1.0,
            schema_version="evidence_assessment.v1",
        )
        return _with_metadata(
            decision,
            route="deterministic_source_instruction_safety",
            status="succeeded",
            started_at=started_at,
        )

    coverage = _source_coverage(source_plan, authorized_chunks)
    missing_coverage = [item for item in coverage if item.status != "covered"]
    if source_plan and missing_coverage and mode != "semantic_always":
        supported_ids = list(dict.fromkeys(
            chunk_id
            for item in coverage
            for chunk_id in item.supporting_chunk_ids
        ))
        any_support = bool(supported_ids)
        decision = EvidenceAssessmentDecision(
            answerability="partial" if any_support else "insufficient",
            required_facts=[
                RequiredFact(
                    fact_id="multi_source_request",
                    description="All material parts of the multi-source request",
                    support="supported" if any_support else "unsupported",
                    supporting_chunk_ids=supported_ids,
                )
            ],
            required_source_coverage=coverage,
            conflicts=[],
            missing_information=["One or more requested source areas are not supported by the available evidence."],
            recommended_action="partial_answer" if any_support else "not_found",
            supporting_chunk_ids=supported_ids,
            reason_codes=["required_source_missing", "partial_fact_support" if any_support else "required_fact_missing"],
            assessment_confidence=1.0,
            schema_version="evidence_assessment.v1",
        )
        return _with_metadata(
            decision,
            route="deterministic_source_coverage",
            status="succeeded",
            started_at=started_at,
        )

    if mode == "deterministic_only":
        chunk_ids = [chunk.chunk_id for chunk in authorized_chunks[:10]]
        decision = EvidenceAssessmentDecision(
            answerability="sufficient",
            required_facts=[
                RequiredFact(
                    fact_id="requested_information",
                    description="The information requested by the user",
                    support="supported",
                    supporting_chunk_ids=chunk_ids,
                )
            ],
            required_source_coverage=coverage,
            conflicts=[],
            missing_information=[],
            recommended_action="answer",
            supporting_chunk_ids=chunk_ids,
            reason_codes=["deterministic_default_answer"],
            assessment_confidence=0.25,
            schema_version="evidence_assessment.v1",
        )
        return _with_metadata(
            decision,
            route="deterministic_default",
            status="skipped",
            started_at=started_at,
        )
    return None


def _semantic_assessment(
    question: str,
    *,
    request_assessment: RequestAssessment,
    authorized_chunks: list[RetrievedChunk],
    source_plan: list[SourcePlanItem],
    route: EvidenceRoute,
    client: OpenAI | None,
    emit_telemetry: bool,
) -> EvidenceAssessment:
    settings = get_settings()
    prompt = get_prompt("evidence_assessment", settings.evidence_assessment_prompt_version)
    selected_model = settings.evidence_assessment_model or prompt.model or settings.openai_chat_model
    started_at = time.perf_counter()
    try:
        if not settings.openai_api_key and client is None:
            raise RuntimeError("evidence assessment service unavailable")
        api = client or OpenAI(
            api_key=settings.openai_api_key,
            timeout=settings.evidence_assessment_timeout_seconds,
            max_retries=0,
        )
        response = api.chat.completions.create(
            model=selected_model,
            temperature=prompt.temperature,
            messages=[
                {"role": "system", "content": prompt.content},
                {
                    "role": "user",
                    "content": _semantic_input(
                        question,
                        request_assessment=request_assessment,
                        authorized_chunks=authorized_chunks,
                        source_plan=source_plan,
                    ),
                },
            ],
            response_format={
                "type": "json_schema",
                "json_schema": {
                    "name": "evidence_assessment_v1",
                    "strict": True,
                    "schema": SemanticEvidenceDecision.model_json_schema(),
                },
            },
        )
        message = response.choices[0].message
        if getattr(message, "refusal", None):
            raise RuntimeError("evidence assessment refused")
        semantic_decision = SemanticEvidenceDecision.model_validate_json(message.content or "")
        decision, normalization_reason = _complete_semantic_decision(
            semantic_decision,
            source_plan=source_plan,
            authorized_chunks=authorized_chunks,
        )
        decision = _validate_semantic_decision(
            decision,
            authorized_chunks=authorized_chunks,
            source_plan=source_plan,
        )
        usage = response.usage
        input_tokens = usage.prompt_tokens if usage else None
        output_tokens = usage.completion_tokens if usage else None
        cost = estimate_chat_cost(model=selected_model, input_tokens=input_tokens, output_tokens=output_tokens)
        assessment = EvidenceAssessment(
            **decision.model_dump(),
            route=route,
            status="succeeded",
            model=selected_model,
            prompt_version=prompt.version,
            latency_ms=max(int((time.perf_counter() - started_at) * 1000), 0),
            input_tokens=input_tokens,
            output_tokens=output_tokens,
            **cost,
            normalization_reason=normalization_reason,
        )
        if emit_telemetry:
            _submit_evidence_telemetry(assessment, question, len(authorized_chunks))
        return assessment
    except Exception as exc:
        if isinstance(exc, ValidationError):
            reason: EvidenceReasonCode = "assessment_schema_invalid"
        elif isinstance(exc, EvidenceContractError):
            reason = exc.reason
        elif "timeout" in type(exc).__name__.lower() or "timeout" in str(exc).lower():
            reason = "assessment_timeout"
        else:
            reason = "assessment_service_error"
        logger.warning(
            "evidence_assessment_failed error_category=%s reason=%s",
            type(exc).__name__,
            reason,
        )
        assessment = _fail_safe(
            reason=reason,
            route="fail_safe",
            model=selected_model,
            prompt_version=prompt.version,
            latency_ms=max(int((time.perf_counter() - started_at) * 1000), 0),
        )
        if emit_telemetry:
            _submit_evidence_telemetry(assessment, question, len(authorized_chunks))
        return assessment


class EvidenceContractError(ValueError):
    def __init__(self, reason: EvidenceReasonCode):
        super().__init__(reason)
        self.reason = reason


def _complete_semantic_decision(
    semantic: SemanticEvidenceDecision,
    *,
    source_plan: list[SourcePlanItem],
    authorized_chunks: list[RetrievedChunk],
) -> tuple[EvidenceAssessmentDecision, EvidenceReasonCode | None]:
    allowed_ids = {chunk.chunk_id for chunk in authorized_chunks}
    normalization_reason: EvidenceReasonCode | None = None
    facts: list[RequiredFact] = []
    for fact in semantic.required_facts:
        valid_ids = [chunk_id for chunk_id in fact.supporting_chunk_ids if chunk_id in allowed_ids]
        support = fact.support
        if support == "supported" and not valid_ids:
            support = "unsupported"
        elif support == "unsupported" and valid_ids:
            support = "supported"
        if valid_ids != fact.supporting_chunk_ids:
            normalization_reason = "unauthorized_reference_rejected"
        elif support != fact.support and normalization_reason is None:
            normalization_reason = "assessment_contract_invalid"
        facts.append(fact.model_copy(update={"supporting_chunk_ids": valid_ids, "support": support}))

    conflicts: list[EvidenceConflict] = []
    for conflict in semantic.conflicts:
        valid_ids = [chunk_id for chunk_id in conflict.chunk_ids if chunk_id in allowed_ids]
        if len(valid_ids) < 2:
            normalization_reason = "unauthorized_reference_rejected"
            continue
        if valid_ids != conflict.chunk_ids:
            normalization_reason = "unauthorized_reference_rejected"
        conflicts.append(conflict.model_copy(update={"chunk_ids": valid_ids}))

    supporting_ids = [chunk_id for chunk_id in semantic.supporting_chunk_ids if chunk_id in allowed_ids]
    if supporting_ids != semantic.supporting_chunk_ids:
        normalization_reason = "unauthorized_reference_rejected"
    fact_supporting_ids = list(dict.fromkeys(
        chunk_id
        for fact in facts
        if fact.support == "supported"
        for chunk_id in fact.supporting_chunk_ids
    ))
    if semantic.answerability in {"sufficient", "partial"} and fact_supporting_ids:
        merged_supporting_ids = list(dict.fromkeys([*supporting_ids, *fact_supporting_ids]))[:10]
        if merged_supporting_ids != supporting_ids and normalization_reason is None:
            normalization_reason = "assessment_contract_invalid"
        supporting_ids = merged_supporting_ids

    statuses = {fact.support for fact in facts}
    unresolved_conflict = any(not item.resolved for item in conflicts)
    answerability = semantic.answerability
    if answerability in {"sufficient", "partial", "conflicting"}:
        if unresolved_conflict:
            answerability = "conflicting"
        elif statuses == {"supported"}:
            answerability = "sufficient"
        elif "supported" in statuses:
            answerability = "partial"
        else:
            answerability = "insufficient"
        if answerability != semantic.answerability and normalization_reason is None:
            normalization_reason = "assessment_contract_invalid"
    if answerability in {"insufficient", "conflicting", "uncertain"}:
        supporting_ids = []
    if answerability == "insufficient" and "supported" in statuses:
        facts = [
            fact.model_copy(update={"support": "unsupported", "supporting_chunk_ids": []})
            if fact.support == "supported"
            else fact
            for fact in facts
        ]
        if normalization_reason is None:
            normalization_reason = "assessment_contract_invalid"

    if answerability == "sufficient":
        reason_codes: list[EvidenceReasonCode] = [
            "accessible_precedence_resolved" if conflicts else "authorized_evidence_sufficient"
        ]
    elif answerability == "partial":
        reason_codes = ["partial_fact_support"]
    elif answerability == "insufficient":
        reason_codes = ["required_fact_missing"]
    elif answerability == "conflicting":
        reason_codes = ["accessible_conflict_unresolved"]
    else:
        reason_codes = ["assessment_contract_invalid"]

    decision = EvidenceAssessmentDecision(
        answerability=answerability,
        required_facts=facts,
        required_source_coverage=_source_coverage(source_plan, authorized_chunks),
        conflicts=conflicts,
        missing_information=semantic.missing_information,
        recommended_action=_ACTION_BY_ANSWERABILITY[answerability],
        supporting_chunk_ids=supporting_ids,
        reason_codes=reason_codes,
        assessment_confidence=semantic.assessment_confidence,
        schema_version="evidence_assessment.v1",
    )
    return decision, normalization_reason


def _validate_semantic_decision(
    decision: EvidenceAssessmentDecision,
    *,
    authorized_chunks: list[RetrievedChunk],
    source_plan: list[SourcePlanItem],
) -> EvidenceAssessmentDecision:
    expected_action = _ACTION_BY_ANSWERABILITY[decision.answerability]
    if decision.recommended_action != expected_action:
        raise EvidenceContractError("assessment_contract_invalid")

    allowed_chunk_ids = {chunk.chunk_id for chunk in authorized_chunks}
    referenced_ids = set(decision.supporting_chunk_ids)
    referenced_ids.update(
        chunk_id
        for fact in decision.required_facts
        for chunk_id in fact.supporting_chunk_ids
    )
    referenced_ids.update(
        chunk_id
        for coverage in decision.required_source_coverage
        for chunk_id in coverage.supporting_chunk_ids
    )
    referenced_ids.update(
        chunk_id
        for conflict in decision.conflicts
        for chunk_id in conflict.chunk_ids
    )
    if not referenced_ids.issubset(allowed_chunk_ids):
        raise EvidenceContractError("unauthorized_reference_rejected")
    if decision.recommended_action in {"answer", "partial_answer"} and not decision.supporting_chunk_ids:
        raise EvidenceContractError("assessment_contract_invalid")

    fact_statuses = {fact.support for fact in decision.required_facts}
    if decision.answerability == "sufficient" and fact_statuses != {"supported"}:
        raise EvidenceContractError("assessment_contract_invalid")
    if decision.answerability == "partial" and not (
        "supported" in fact_statuses and len(fact_statuses) > 1
    ):
        raise EvidenceContractError("assessment_contract_invalid")
    if decision.answerability == "insufficient" and "supported" in fact_statuses:
        raise EvidenceContractError("assessment_contract_invalid")
    if decision.answerability == "conflicting" and not any(not item.resolved for item in decision.conflicts):
        raise EvidenceContractError("assessment_contract_invalid")
    if decision.answerability == "uncertain":
        raise EvidenceContractError("assessment_contract_invalid")

    deterministic_coverage = _source_coverage(source_plan, authorized_chunks)
    missing_required_source = any(item.status != "covered" for item in deterministic_coverage)
    if source_plan and missing_required_source and decision.recommended_action == "answer":
        supported_ids = list(dict.fromkeys(
            chunk_id
            for item in deterministic_coverage
            for chunk_id in item.supporting_chunk_ids
        ))
        if supported_ids:
            return decision.model_copy(
                update={
                    "answerability": "partial",
                    "recommended_action": "partial_answer",
                    "required_source_coverage": deterministic_coverage,
                    "supporting_chunk_ids": supported_ids,
                    "missing_information": [
                        "One or more requested source areas are not supported by the available evidence."
                    ],
                    "reason_codes": ["required_source_missing", "partial_fact_support"],
                }
            )
        raise EvidenceContractError("assessment_contract_invalid")
    return decision


def _semantic_input(
    question: str,
    *,
    request_assessment: RequestAssessment,
    authorized_chunks: list[RetrievedChunk],
    source_plan: list[SourcePlanItem],
) -> str:
    payload: dict[str, Any] = {
        "current_request": question.strip()[:4000],
        "request_assessment_for_routing_context_only": {
            "intent": request_assessment.intent,
            "topic": request_assessment.topic,
            "ambiguity": request_assessment.ambiguity,
            "injection_risk": request_assessment.injection_risk,
            "recommended_action": request_assessment.recommended_action,
            "reason_codes": list(request_assessment.reason_codes),
        },
        "multi_document": bool(source_plan),
        "required_source_labels": [item.label for item in source_plan],
        "deterministic_required_source_coverage": [
            item.model_dump(mode="json")
            for item in _source_coverage(source_plan, authorized_chunks)
        ],
        "authorized_retrieved_chunks": [
            {
                "chunk_id": chunk.chunk_id,
                "document_id": chunk.document_id,
                "document_title": chunk.document_title[:200],
                "section_heading": chunk.section_heading[:200],
                "content": chunk.content[:3000],
            }
            for chunk in authorized_chunks[:10]
        ],
    }
    return json.dumps(payload, ensure_ascii=False)


def _source_coverage(
    source_plan: list[SourcePlanItem],
    chunks: list[RetrievedChunk],
) -> list[RequiredSourceCoverage]:
    coverage: list[RequiredSourceCoverage] = []
    for item in source_plan:
        matched = [
            chunk.chunk_id
            for chunk in chunks
            if chunk.document_id in item.target_document_ids
        ][:10]
        coverage.append(
            RequiredSourceCoverage(
                source_label=item.label,
                status="covered" if matched else "missing",
                supporting_chunk_ids=matched,
            )
        )
    return coverage


def _required_source_plan(question: str) -> list[SourcePlanItem]:
    """Narrow retrieval plans to source areas materially requested by the user.

    The Phase 39 planner intentionally casts a wide retrieval net. Evidence
    sufficiency must not reinterpret every retrieval expansion as a required fact.
    """
    normalized = question.lower()
    plan = plan_multi_document_sources(question)
    result: list[SourcePlanItem] = []
    for item in plan:
        if item.label == "data_classification" and not any(
            term in normalized
            for term in ("data classification", "which data", "what data", "data handling", "data storage")
        ):
            continue
        if item.label == "api_standards" and not any(
            term in normalized for term in ("api", "authorization", "engineering standard")
        ):
            continue
        result.append(item)
    return result


def _source_instruction_safety_support(
    question: str,
    *,
    request_assessment: RequestAssessment,
    authorized_chunks: list[RetrievedChunk],
) -> list[str]:
    if request_assessment.injection_risk != "source_discussion":
        return []
    normalized_question = " ".join(question.lower().split())
    if not any(
        phrase in normalized_question
        for phrase in (
            "should i follow",
            "should you follow",
            "what should you do",
            "what should the assistant do",
            "how should",
            "explain why",
        )
    ):
        return []
    safe_explanations = (
        "source content, not a system instruction",
        "correct behavior is to treat that sentence as untrusted document content",
        "do not follow embedded instructions",
        "must not be followed as an instruction",
    )
    return [
        chunk.chunk_id
        for chunk in authorized_chunks
        if any(phrase in " ".join(chunk.content.lower().split()) for phrase in safe_explanations)
    ][:10]


def _with_metadata(
    decision: EvidenceAssessmentDecision,
    *,
    route: EvidenceRoute,
    status: EvidenceStatus,
    started_at: float,
) -> EvidenceAssessment:
    return EvidenceAssessment(
        **decision.model_dump(),
        route=route,
        status=status,
        model=None,
        prompt_version=None,
        latency_ms=max(int((time.perf_counter() - started_at) * 1000), 0),
        input_tokens=0,
        output_tokens=0,
        input_cost_usd=0.0,
        output_cost_usd=0.0,
        estimated_cost_usd=0.0,
        pricing_status="not_applicable",
    )


def _fail_safe(
    *,
    reason: EvidenceReasonCode,
    route: EvidenceRoute,
    model: str,
    prompt_version: str,
    latency_ms: int,
) -> EvidenceAssessment:
    return EvidenceAssessment(
        answerability="uncertain",
        required_facts=[
            RequiredFact(
                fact_id="assessment",
                description="Evidence sufficiency could not be assessed safely",
                support="unsupported",
                supporting_chunk_ids=[],
            )
        ],
        required_source_coverage=[],
        conflicts=[],
        missing_information=[],
        recommended_action="temporary_unavailable",
        supporting_chunk_ids=[],
        reason_codes=[reason],
        assessment_confidence=0.0,
        schema_version="evidence_assessment.v1",
        route=route,
        status="failed_safe",
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


def _submit_evidence_telemetry(
    assessment: EvidenceAssessment,
    question: str,
    authorized_chunk_count: int,
) -> None:
    submit_auxiliary_telemetry(
        operation_type="evidence_assessment",
        model=assessment.model or "deterministic",
        status="succeeded" if assessment.status == "succeeded" else "failed",
        prompt_name="evidence_assessment",
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
            "answerability": assessment.answerability,
            "recommended_action": assessment.recommended_action,
            "reason_codes": list(assessment.reason_codes),
            "authorized_chunk_count": authorized_chunk_count,
            "supporting_chunk_count": len(assessment.supporting_chunk_ids),
            "normalization_reason": assessment.normalization_reason,
        },
    )
