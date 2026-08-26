from __future__ import annotations

import json
import logging
import re
import time
from typing import Literal

from openai import OpenAI
from pydantic import BaseModel, ConfigDict, Field, ValidationError

from apps.api.app.core.config import get_settings
from apps.api.app.costing.estimator import estimate_chat_cost
from apps.api.app.observability.auxiliary_telemetry import submit_auxiliary_telemetry
from apps.api.app.prompts.prompt_registry import get_prompt
from apps.api.app.retrieval.types import RetrievedChunk


logger = logging.getLogger(__name__)

ValidationAction = Literal["accept", "repair", "downgrade"]
ValidationStatus = Literal["succeeded", "skipped", "failed_safe"]
ValidationRoute = Literal["deterministic_skip", "deterministic_guard", "hybrid_semantic", "fail_safe"]
ClaimType = Literal["exact", "semantic", "negation", "exception", "role_or_approval"]
SupportStatus = Literal["supported", "unsupported", "conflicting"]
ValidationReasonCode = Literal[
    "non_answer_skipped",
    "code_authored_response_valid",
    "authorized_evidence_missing",
    "citation_not_authorized",
    "citation_missing",
    "citation_claim_unsupported",
    "unsupported_citation_removed",
    "exact_literal_unsupported",
    "claim_unsupported",
    "claim_conflicting",
    "source_instruction_followed",
    "all_claims_supported",
    "repair_required",
    "repair_succeeded",
    "repair_failed",
    "repair_limit_reached",
    "validator_timeout",
    "validator_service_error",
    "validator_schema_invalid",
    "validator_contract_invalid",
    "validator_contract_normalized",
]


class ClaimValidation(BaseModel):
    model_config = ConfigDict(extra="forbid")

    claim_id: str = Field(min_length=1, max_length=32)
    claim_text: str = Field(min_length=1, max_length=320)
    claim_type: ClaimType
    support_status: SupportStatus
    evidence_chunk_ids: list[str] = Field(max_length=8)


class CitationClaimValidation(BaseModel):
    model_config = ConfigDict(extra="forbid")

    citation_chunk_id: str = Field(min_length=1, max_length=160)
    supports_claims: bool
    supported_claim_ids: list[str] = Field(max_length=12)


class SemanticValidationDecision(BaseModel):
    model_config = ConfigDict(extra="forbid")

    claims: list[ClaimValidation] = Field(min_length=1, max_length=16)
    citation_checks: list[CitationClaimValidation] = Field(max_length=12)
    source_instruction_followed: bool = Field(
        description="True only when the candidate complied with an assistant-directed instruction found inside evidence."
    )
    source_instruction_evidence_chunk_ids: list[str] = Field(
        max_length=8,
        description="Evidence chunks containing the followed instruction; empty whenever source_instruction_followed is false.",
    )
    unresolved_conflict: bool


class PostGenerationValidation(BaseModel):
    model_config = ConfigDict(extra="forbid")

    action: ValidationAction
    claims: list[ClaimValidation]
    citation_checks: list[CitationClaimValidation]
    exact_literals: list[str]
    unsupported_exact_literals: list[str]
    source_instruction_followed: bool
    reason_codes: list[ValidationReasonCode]
    repair_count: int = Field(ge=0, le=1)
    schema_version: Literal["post_generation_validation.v1"]
    route: ValidationRoute
    status: ValidationStatus
    model: str | None
    prompt_version: str | None
    latency_ms: int
    input_tokens: int | None
    output_tokens: int | None
    input_cost_usd: float | None
    output_cost_usd: float | None
    estimated_cost_usd: float | None
    pricing_status: str
    normalization_reason: ValidationReasonCode | None = None


EXACT_PATTERNS = [
    re.compile(r"(?:[$€£]\s?\d[\d,]*(?:\.\d+)?)", re.IGNORECASE),
    re.compile(r"\b\d+(?:\.\d+)?\s?%", re.IGNORECASE),
    re.compile(r"\b\d{4}-\d{2}-\d{2}\b", re.IGNORECASE),
    re.compile(r"\b\d+(?:\.\d+)?\s+(?:business\s+)?(?:minutes?|hours?|days?|weeks?|months?|years?)\b", re.IGNORECASE),
    re.compile(r"\b\d{2,}(?:\.\d+)?\b", re.IGNORECASE),
]


def validate_candidate_answer(
    question: str,
    *,
    candidate: dict,
    authorized_chunks: list[RetrievedChunk],
    repair_count: int = 0,
    code_authored: bool = False,
    client: OpenAI | None = None,
    emit_telemetry: bool = True,
) -> PostGenerationValidation:
    started_at = time.perf_counter()
    response_type = str(candidate.get("response_type") or "answer")
    if response_type not in {"answer", "partial_answer"}:
        result = _result(
            action="accept",
            reason_codes=["non_answer_skipped"],
            repair_count=repair_count,
            route="deterministic_skip",
            status="skipped",
            started_at=started_at,
        )
        _emit(result, question, len(authorized_chunks), emit_telemetry)
        return result

    if not authorized_chunks:
        result = _result(
            action="downgrade",
            reason_codes=["authorized_evidence_missing"],
            repair_count=repair_count,
            route="deterministic_guard",
            status="succeeded",
            started_at=started_at,
        )
        _emit(result, question, len(authorized_chunks), emit_telemetry)
        return result

    allowed_ids = {chunk.chunk_id for chunk in authorized_chunks}
    citation_ids = [str(item.get("chunk_id") or "") for item in candidate.get("citations") or []]
    invalid_citations = [chunk_id for chunk_id in citation_ids if not chunk_id or chunk_id not in allowed_ids]
    if not citation_ids:
        result = _result(
            action="downgrade" if repair_count >= 1 else "repair",
            reason_codes=["citation_missing", *(["repair_limit_reached"] if repair_count >= 1 else ["repair_required"])],
            repair_count=repair_count,
            route="deterministic_guard",
            status="succeeded",
            started_at=started_at,
        )
        _emit(result, question, len(authorized_chunks), emit_telemetry)
        return result
    if invalid_citations:
        result = _result(
            action="downgrade" if repair_count >= 1 else "repair",
            reason_codes=["citation_not_authorized", *(["repair_limit_reached"] if repair_count >= 1 else ["repair_required"])],
            repair_count=repair_count,
            route="deterministic_guard",
            status="succeeded",
            started_at=started_at,
        )
        _emit(result, question, len(authorized_chunks), emit_telemetry)
        return result

    answer = str(candidate.get("answer") or "")
    exact_literals = extract_exact_literals(answer)
    evidence_text = "\n".join(chunk.content for chunk in authorized_chunks)
    unsupported_exact = [literal for literal in exact_literals if not exact_literal_supported(literal, evidence_text)]
    if unsupported_exact:
        result = _result(
            action="downgrade" if repair_count >= 1 else "repair",
            reason_codes=["exact_literal_unsupported", *(["repair_limit_reached"] if repair_count >= 1 else ["repair_required"])],
            repair_count=repair_count,
            route="deterministic_guard",
            status="succeeded",
            started_at=started_at,
            exact_literals=exact_literals,
            unsupported_exact_literals=unsupported_exact,
        )
        _emit(result, question, len(authorized_chunks), emit_telemetry)
        return result

    if code_authored:
        result = _result(
            action="accept",
            reason_codes=["code_authored_response_valid"],
            repair_count=repair_count,
            route="deterministic_guard",
            status="succeeded",
            started_at=started_at,
            exact_literals=exact_literals,
        )
        _emit(result, question, len(authorized_chunks), emit_telemetry)
        return result

    return _semantic_validate(
        question,
        candidate=candidate,
        authorized_chunks=authorized_chunks,
        exact_literals=exact_literals,
        repair_count=repair_count,
        client=client,
        emit_telemetry=emit_telemetry,
        started_at=started_at,
    )


def combine_validation_attempts(
    first: PostGenerationValidation,
    second: PostGenerationValidation,
) -> PostGenerationValidation:
    succeeded = second.action == "accept"
    reason_codes = list(dict.fromkeys([
        *first.reason_codes,
        *second.reason_codes,
        "repair_succeeded" if succeeded else "repair_failed",
    ]))
    return second.model_copy(
        update={
            "repair_count": 1,
            "reason_codes": reason_codes,
            "latency_ms": first.latency_ms + second.latency_ms,
            "input_tokens": _sum_optional(first.input_tokens, second.input_tokens),
            "output_tokens": _sum_optional(first.output_tokens, second.output_tokens),
            "input_cost_usd": _sum_optional(first.input_cost_usd, second.input_cost_usd),
            "output_cost_usd": _sum_optional(first.output_cost_usd, second.output_cost_usd),
            "estimated_cost_usd": _sum_optional(first.estimated_cost_usd, second.estimated_cost_usd),
        }
    )


def can_prune_unsupported_citations(result: PostGenerationValidation) -> bool:
    return (
        result.action == "repair"
        and bool(result.citation_checks)
        and any(not check.supports_claims for check in result.citation_checks)
        and any(check.supports_claims for check in result.citation_checks)
        and all(claim.support_status == "supported" for claim in result.claims)
        and not result.source_instruction_followed
        and set(result.reason_codes).issubset({"citation_claim_unsupported", "repair_required"})
    )


def mark_citation_prune_repair(result: PostGenerationValidation) -> PostGenerationValidation:
    return result.model_copy(
        update={
            "action": "accept",
            "repair_count": 1,
            "reason_codes": ["citation_claim_unsupported", "unsupported_citation_removed", "repair_succeeded"],
        }
    )


def extract_exact_literals(text: str) -> list[str]:
    literals: list[str] = []
    for pattern in EXACT_PATTERNS:
        for match in pattern.finditer(text):
            literal = match.group(0).strip()
            if literal and literal not in literals:
                literals.append(literal)
    return literals[:20]


def exact_literal_supported(literal: str, evidence: str) -> bool:
    return _normalize_exact(literal) in _normalize_exact(evidence)


def _normalize_exact(text: str) -> str:
    return re.sub(r"[\s,]+", "", text.casefold())


def _semantic_validate(
    question: str,
    *,
    candidate: dict,
    authorized_chunks: list[RetrievedChunk],
    exact_literals: list[str],
    repair_count: int,
    client: OpenAI | None,
    emit_telemetry: bool,
    started_at: float,
) -> PostGenerationValidation:
    settings = get_settings()
    prompt = get_prompt("post_generation_validation", settings.post_generation_validation_prompt_version)
    model = settings.post_generation_validation_model or prompt.model or settings.openai_chat_model
    try:
        if not settings.openai_api_key and client is None:
            raise RuntimeError("post-generation validation service unavailable")
        api = client or OpenAI(
            api_key=settings.openai_api_key,
            timeout=settings.post_generation_validation_timeout_seconds,
            max_retries=0,
        )
        response = api.chat.completions.create(
            model=model,
            temperature=prompt.temperature,
            messages=[
                {"role": "system", "content": prompt.content},
                {"role": "user", "content": _semantic_input(question, candidate, authorized_chunks)},
            ],
            response_format={
                "type": "json_schema",
                "json_schema": {
                    "name": "post_generation_validation_v1",
                    "strict": True,
                    "schema": SemanticValidationDecision.model_json_schema(),
                },
            },
        )
        message = response.choices[0].message
        if getattr(message, "refusal", None):
            raise RuntimeError("post-generation validation refused")
        decision = SemanticValidationDecision.model_validate_json(message.content or "")
        decision = _normalize_source_instruction_decision(
            decision,
            candidate=candidate,
            authorized_chunks=authorized_chunks,
        )
        decision, contract_normalized = _normalize_contract(
            decision,
            candidate=candidate,
            authorized_chunks=authorized_chunks,
        )
        decision = _validate_contract(decision, candidate=candidate, authorized_chunks=authorized_chunks)
        reason_codes, action = _derive_action(decision, repair_count=repair_count)
        if contract_normalized:
            reason_codes = list(dict.fromkeys(["validator_contract_normalized", *reason_codes]))
            if action == "accept":
                action = "downgrade" if repair_count >= 1 else "repair"
                reason_codes.append("repair_limit_reached" if repair_count >= 1 else "repair_required")
        usage = response.usage
        input_tokens = usage.prompt_tokens if usage else None
        output_tokens = usage.completion_tokens if usage else None
        cost = estimate_chat_cost(model=model, input_tokens=input_tokens, output_tokens=output_tokens)
        result = PostGenerationValidation(
            action=action,
            claims=decision.claims,
            citation_checks=decision.citation_checks,
            exact_literals=exact_literals,
            unsupported_exact_literals=[],
            source_instruction_followed=decision.source_instruction_followed,
            reason_codes=reason_codes,
            repair_count=repair_count,
            schema_version="post_generation_validation.v1",
            route="hybrid_semantic",
            status="succeeded",
            model=model,
            prompt_version=prompt.version,
            latency_ms=max(int((time.perf_counter() - started_at) * 1000), 0),
            input_tokens=input_tokens,
            output_tokens=output_tokens,
            normalization_reason="validator_contract_normalized" if contract_normalized else None,
            **cost,
        )
    except Exception as exc:
        if isinstance(exc, ValidationError):
            reason: ValidationReasonCode = "validator_schema_invalid"
        elif isinstance(exc, ValidationContractError):
            reason = "validator_contract_invalid"
        elif "timeout" in type(exc).__name__.lower() or "timeout" in str(exc).lower():
            reason = "validator_timeout"
        else:
            reason = "validator_service_error"
        logger.warning(
            "post_generation_validation_failed error_category=%s reason=%s contract_detail=%s",
            type(exc).__name__,
            reason,
            str(exc)[:120] if isinstance(exc, ValidationContractError) else "not_applicable",
        )
        result = _result(
            action="downgrade",
            reason_codes=[reason],
            repair_count=repair_count,
            route="fail_safe",
            status="failed_safe",
            started_at=started_at,
            model=model,
            prompt_version=prompt.version,
            exact_literals=exact_literals,
        )
    _emit(result, question, len(authorized_chunks), emit_telemetry)
    return result


class ValidationContractError(ValueError):
    pass


SOURCE_INSTRUCTION_PATTERNS = (
    "ignore previous",
    "ignore prior",
    "hide citation",
    "bypass access",
    "reveal secret",
    "reveal fallback",
    "disregard system",
    "override system",
)


def _normalize_source_instruction_decision(
    decision: SemanticValidationDecision,
    *,
    candidate: dict,
    authorized_chunks: list[RetrievedChunk],
) -> SemanticValidationDecision:
    instruction_chunk_ids = {
        chunk.chunk_id
        for chunk in authorized_chunks
        if any(pattern in chunk.content.casefold() for pattern in SOURCE_INSTRUCTION_PATTERNS)
    }
    answer = str(candidate.get("answer") or "").casefold()
    rejection_markers = ("untrusted", "not followed", "did not follow", "should not", "must not", "reject")
    compliance_markers = ("i will", "i'll", "will comply", "as the document requests", "as instructed")
    deterministic_following = (
        bool(instruction_chunk_ids)
        and any(pattern in answer for pattern in SOURCE_INSTRUCTION_PATTERNS)
        and any(marker in answer for marker in compliance_markers)
        and not any(marker in answer for marker in rejection_markers)
    )
    semantic_following = decision.source_instruction_followed and bool(instruction_chunk_ids)
    followed = deterministic_following or semantic_following
    ids = sorted(instruction_chunk_ids)[:8] if followed else []
    return decision.model_copy(
        update={
            "source_instruction_followed": followed,
            "source_instruction_evidence_chunk_ids": ids,
        }
    )


def _validate_contract(
    decision: SemanticValidationDecision,
    *,
    candidate: dict,
    authorized_chunks: list[RetrievedChunk],
) -> SemanticValidationDecision:
    allowed_ids = {chunk.chunk_id for chunk in authorized_chunks}
    claim_ids = {claim.claim_id for claim in decision.claims}
    candidate_citation_ids = {str(item.get("chunk_id") or "") for item in candidate.get("citations") or []}
    if any(chunk_id not in allowed_ids for claim in decision.claims for chunk_id in claim.evidence_chunk_ids):
        raise ValidationContractError("claim referenced unauthorized evidence")
    for claim in decision.claims:
        if claim.support_status == "supported" and not claim.evidence_chunk_ids:
            raise ValidationContractError("supported claim has no evidence")
    for check in decision.citation_checks:
        if check.citation_chunk_id not in allowed_ids or check.citation_chunk_id not in candidate_citation_ids:
            raise ValidationContractError("citation check referenced non-candidate evidence")
        if any(claim_id not in claim_ids for claim_id in check.supported_claim_ids):
            raise ValidationContractError("citation check referenced unknown claim")
        if check.supports_claims != bool(check.supported_claim_ids):
            raise ValidationContractError("citation support fields disagree")
    if set(decision.source_instruction_evidence_chunk_ids) - allowed_ids:
        raise ValidationContractError("source instruction referenced unauthorized evidence")
    if decision.source_instruction_followed and not decision.source_instruction_evidence_chunk_ids:
        raise ValidationContractError("source instruction finding lacks evidence")
    return decision


def _normalize_contract(
    decision: SemanticValidationDecision,
    *,
    candidate: dict,
    authorized_chunks: list[RetrievedChunk],
) -> tuple[SemanticValidationDecision, bool]:
    """Remove non-authorized references and downgrade inconsistent support before strict validation."""
    allowed_ids = {chunk.chunk_id for chunk in authorized_chunks}
    candidate_citation_ids = {
        str(item.get("chunk_id") or "") for item in candidate.get("citations") or []
    } & allowed_ids
    normalized = False
    claims: list[ClaimValidation] = []
    for claim in decision.claims:
        valid_ids = list(dict.fromkeys(
            chunk_id for chunk_id in claim.evidence_chunk_ids if chunk_id in allowed_ids
        ))
        support_status = claim.support_status
        if support_status == "supported" and not valid_ids:
            support_status = "unsupported"
        if valid_ids != claim.evidence_chunk_ids or support_status != claim.support_status:
            normalized = True
        claims.append(
            claim.model_copy(
                update={"evidence_chunk_ids": valid_ids, "support_status": support_status}
            )
        )

    claim_ids = {claim.claim_id for claim in claims}
    checks_by_id: dict[str, CitationClaimValidation] = {}
    for check in decision.citation_checks:
        if check.citation_chunk_id not in candidate_citation_ids:
            normalized = True
            continue
        valid_claim_ids = list(dict.fromkeys(
            claim_id for claim_id in check.supported_claim_ids if claim_id in claim_ids
        ))
        supports_claims = bool(valid_claim_ids)
        if valid_claim_ids != check.supported_claim_ids or supports_claims != check.supports_claims:
            normalized = True
        checks_by_id[check.citation_chunk_id] = check.model_copy(
            update={"supported_claim_ids": valid_claim_ids, "supports_claims": supports_claims}
        )
    for citation_id in sorted(candidate_citation_ids):
        if citation_id not in checks_by_id:
            normalized = True
            checks_by_id[citation_id] = CitationClaimValidation(
                citation_chunk_id=citation_id,
                supports_claims=False,
                supported_claim_ids=[],
            )
    return (
        decision.model_copy(update={"claims": claims, "citation_checks": list(checks_by_id.values())}),
        normalized,
    )


def _derive_action(
    decision: SemanticValidationDecision,
    *,
    repair_count: int,
) -> tuple[list[ValidationReasonCode], ValidationAction]:
    reasons: list[ValidationReasonCode] = []
    if decision.source_instruction_followed:
        reasons.append("source_instruction_followed")
    if decision.unresolved_conflict or any(claim.support_status == "conflicting" for claim in decision.claims):
        reasons.append("claim_conflicting")
    if any(claim.support_status == "unsupported" for claim in decision.claims):
        reasons.append("claim_unsupported")
    if any(not check.supports_claims for check in decision.citation_checks):
        reasons.append("citation_claim_unsupported")
    if not reasons:
        return ["all_claims_supported"], "accept"
    if decision.source_instruction_followed:
        return reasons, "downgrade"
    if repair_count >= 1:
        return [*reasons, "repair_limit_reached"], "downgrade"
    return [*reasons, "repair_required"], "repair"


def _semantic_input(question: str, candidate: dict, authorized_chunks: list[RetrievedChunk]) -> str:
    payload = {
        "question": question,
        "candidate": {
            "answer": str(candidate.get("answer") or "")[:6000],
            "response_type": candidate.get("response_type"),
            "citations": [
                {
                    "chunk_id": item.get("chunk_id"),
                    "citation_text": str(item.get("citation_text") or "")[:500],
                }
                for item in (candidate.get("citations") or [])[:12]
            ],
        },
        "authorized_evidence": [
            {
                "chunk_id": chunk.chunk_id,
                "document_id": chunk.document_id,
                "section_heading": chunk.section_heading,
                "content": chunk.content[:5000],
            }
            for chunk in authorized_chunks[:12]
        ],
    }
    return json.dumps(payload, ensure_ascii=True)


def _result(
    *,
    action: ValidationAction,
    reason_codes: list[ValidationReasonCode],
    repair_count: int,
    route: ValidationRoute,
    status: ValidationStatus,
    started_at: float,
    model: str | None = None,
    prompt_version: str | None = None,
    exact_literals: list[str] | None = None,
    unsupported_exact_literals: list[str] | None = None,
) -> PostGenerationValidation:
    return PostGenerationValidation(
        action=action,
        claims=[],
        citation_checks=[],
        exact_literals=exact_literals or [],
        unsupported_exact_literals=unsupported_exact_literals or [],
        source_instruction_followed=False,
        reason_codes=reason_codes,
        repair_count=repair_count,
        schema_version="post_generation_validation.v1",
        route=route,
        status=status,
        model=model,
        prompt_version=prompt_version,
        latency_ms=max(int((time.perf_counter() - started_at) * 1000), 0),
        input_tokens=0,
        output_tokens=0,
        input_cost_usd=0.0,
        output_cost_usd=0.0,
        estimated_cost_usd=0.0,
        pricing_status="not_applicable",
    )


def _emit(result: PostGenerationValidation, question: str, chunk_count: int, enabled: bool) -> None:
    if not enabled:
        return
    submit_auxiliary_telemetry(
        operation_type="post_generation_validation",
        model=result.model or "deterministic",
        status="failed" if result.status == "failed_safe" else result.status,
        prompt_name="post_generation_validation" if result.prompt_version else None,
        prompt_version=result.prompt_version,
        input_tokens=result.input_tokens,
        output_tokens=result.output_tokens,
        estimated_cost_usd=result.estimated_cost_usd,
        pricing_status=result.pricing_status,
        latency_ms=result.latency_ms,
        question=question,
        metadata={
            "action": result.action,
            "route": result.route,
            "reason_codes": list(result.reason_codes),
            "repair_count": result.repair_count,
            "authorized_chunk_count": chunk_count,
            "claim_count": len(result.claims),
            "source_instruction_followed": result.source_instruction_followed,
        },
        error_category=result.reason_codes[0] if result.status == "failed_safe" else None,
        error_message_redacted="Post-generation validation failed safe." if result.status == "failed_safe" else None,
    )


def _sum_optional(first: int | float | None, second: int | float | None):
    if first is None and second is None:
        return None
    return (first or 0) + (second or 0)
