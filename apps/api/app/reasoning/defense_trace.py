from __future__ import annotations

from typing import Literal

from pydantic import BaseModel, ConfigDict, Field

from apps.api.app.permissions.access_control import unauthorized_chunks
from apps.api.app.reasoning.evidence_assessment import EvidenceAssessment
from apps.api.app.reasoning.post_generation_validation import PostGenerationValidation
from apps.api.app.reasoning.request_assessment import RequestAssessment


StageName = Literal[
    "deterministic_guard",
    "semantic_request_assessment",
    "permission_filter",
    "evidence_assessment",
    "generator",
    "post_generation_validation",
    "final_response",
]
StageStatus = Literal["succeeded", "skipped", "failed_safe"]


class DefenseTraceStage(BaseModel):
    model_config = ConfigDict(extra="forbid")

    name: StageName
    status: StageStatus
    route: str = Field(min_length=1, max_length=64)
    action: str = Field(min_length=1, max_length=64)
    reason_codes: list[str] = Field(max_length=8)
    latency_ms: int | None = Field(default=None, ge=0)
    estimated_cost_usd: float | None = Field(default=None, ge=0.0)
    authorized_chunk_count: int | None = Field(default=None, ge=0)
    unauthorized_chunk_count: int | None = Field(default=None, ge=0)
    memory_used_as_evidence: bool | None = None
    repair_count: int | None = Field(default=None, ge=0, le=1)


class DefenseTrace(BaseModel):
    model_config = ConfigDict(extra="forbid")

    schema_version: Literal["defense_trace.v1"] = "defense_trace.v1"
    privacy_mode: Literal["bounded_metadata_only"] = "bounded_metadata_only"
    stages: list[DefenseTraceStage] = Field(min_length=7, max_length=7)


def build_defense_trace(
    *,
    request_assessment: RequestAssessment,
    evidence_assessment: EvidenceAssessment | None,
    post_generation_validation: dict | PostGenerationValidation | None,
    answer: dict,
    authorized_chunks: list,
    effective_role: str,
    generation_latency_ms: int | None,
) -> DefenseTrace:
    """Build the default privacy-safe trace; no request, source, prompt, or identity content is accepted."""
    post = (
        post_generation_validation
        if isinstance(post_generation_validation, PostGenerationValidation)
        else PostGenerationValidation.model_validate(post_generation_validation)
        if post_generation_validation
        else None
    )
    deterministic = request_assessment.route == "deterministic_guard"
    semantic = request_assessment.route in {"semantic_assessment", "fail_safe"}
    unauthorized_count = len(unauthorized_chunks(authorized_chunks, effective_role))
    generated = bool(answer.get("model")) or bool(answer.get("input_tokens")) or bool(answer.get("output_tokens"))

    return DefenseTrace(
        stages=[
            DefenseTraceStage(
                name="deterministic_guard",
                status="succeeded" if deterministic else "skipped",
                route="deterministic_guard" if deterministic else "not_selected",
                action=request_assessment.recommended_action if deterministic else "continue",
                reason_codes=list(request_assessment.reason_codes) if deterministic else [],
                latency_ms=request_assessment.latency_ms if deterministic else 0,
                estimated_cost_usd=0.0,
            ),
            DefenseTraceStage(
                name="semantic_request_assessment",
                status=("failed_safe" if request_assessment.status == "failed_safe" else "succeeded") if semantic else "skipped",
                route=request_assessment.route,
                action=request_assessment.recommended_action,
                reason_codes=list(request_assessment.reason_codes),
                latency_ms=request_assessment.latency_ms,
                estimated_cost_usd=request_assessment.estimated_cost_usd,
                memory_used_as_evidence=False,
            ),
            DefenseTraceStage(
                name="permission_filter",
                status="succeeded" if unauthorized_count == 0 else "failed_safe",
                route="application_authorization",
                action="allow_authorized_only" if unauthorized_count == 0 else "security_invariant_failed",
                reason_codes=[
                    "pre_generation_role_filter",
                    *(["unauthorized_chunk_invariant"] if unauthorized_count else []),
                ],
                authorized_chunk_count=len(authorized_chunks) - unauthorized_count,
                unauthorized_chunk_count=unauthorized_count,
                memory_used_as_evidence=False,
            ),
            DefenseTraceStage(
                name="evidence_assessment",
                status=("failed_safe" if evidence_assessment and evidence_assessment.status == "failed_safe" else "succeeded") if evidence_assessment else "skipped",
                route=evidence_assessment.route if evidence_assessment else "pre_retrieval_stop",
                action=evidence_assessment.recommended_action if evidence_assessment else "not_run",
                reason_codes=list(evidence_assessment.reason_codes) if evidence_assessment else [],
                latency_ms=evidence_assessment.latency_ms if evidence_assessment else 0,
                estimated_cost_usd=evidence_assessment.estimated_cost_usd if evidence_assessment else 0.0,
                authorized_chunk_count=len(authorized_chunks) - unauthorized_count,
                memory_used_as_evidence=False,
            ),
            DefenseTraceStage(
                name="generator",
                status="succeeded" if generated else "skipped",
                route="authorized_evidence_only" if generated else "code_authored_response",
                action="generated" if generated else "not_run",
                reason_codes=["authorized_chunks_only"] if generated else [],
                latency_ms=generation_latency_ms or 0,
                estimated_cost_usd=answer.get("estimated_cost_usd") or 0.0,
                authorized_chunk_count=len(authorized_chunks) - unauthorized_count,
                unauthorized_chunk_count=unauthorized_count,
                memory_used_as_evidence=False,
            ),
            DefenseTraceStage(
                name="post_generation_validation",
                status=post.status if post else "skipped",
                route=post.route if post else "no_generated_candidate",
                action=post.action if post else "not_run",
                reason_codes=list(post.reason_codes) if post else [],
                latency_ms=post.latency_ms if post else 0,
                estimated_cost_usd=post.estimated_cost_usd if post else 0.0,
                authorized_chunk_count=len(authorized_chunks) - unauthorized_count,
                memory_used_as_evidence=False,
                repair_count=post.repair_count if post else 0,
            ),
            DefenseTraceStage(
                name="final_response",
                status="succeeded",
                route="application_response_policy",
                action=str(answer.get("response_type") or "unknown")[:64],
                reason_codes=[],
                memory_used_as_evidence=False,
            ),
        ]
    )
