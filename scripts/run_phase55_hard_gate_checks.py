from __future__ import annotations

import hashlib
import json
import re
import sys
from datetime import UTC, datetime
from pathlib import Path
from types import SimpleNamespace
from typing import Any


ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

from apps.api.app.reasoning.evidence_assessment import assess_evidence
from apps.api.app.reasoning.post_generation_validation import validate_candidate_answer
from apps.api.app.reasoning.request_assessment import (
    RequestAssessment,
    RequestAssessmentDecision,
    semantic_request_assessment,
)
from apps.api.app.retrieval.types import RetrievedChunk


OUTPUT_PATH = ROOT / "data/evaluation/defense/phase55-focused-hard-gates.json"
RUNTIME_RESULT = ROOT / "data/evaluation/eval-runs/phase54-live-query-regression-v5.json"
BOUND_SOURCES = (
    ROOT / "apps/api/app/main.py",
    ROOT / "apps/api/app/reasoning/request_assessment.py",
    ROOT / "apps/api/app/reasoning/evidence_assessment.py",
    ROOT / "apps/api/app/reasoning/post_generation_validation.py",
    RUNTIME_RESULT,
)
AUTHORITY_FIELDS = {
    "tenant_id",
    "project_id",
    "department_id",
    "user_id",
    "role",
    "document_ids",
    "chunk_ids",
    "tool_access",
}


class FakeClient:
    def __init__(self, payload: dict[str, Any]):
        self.payload = payload
        self.chat = SimpleNamespace(completions=SimpleNamespace(create=self.create))

    def create(self, **_kwargs: Any) -> SimpleNamespace:
        return SimpleNamespace(
            choices=[
                SimpleNamespace(
                    message=SimpleNamespace(content=json.dumps(self.payload), refusal=None)
                )
            ],
            usage=None,
        )


def _sha256(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def _continued_request() -> RequestAssessment:
    return RequestAssessment(
        intent="question",
        topic="approval",
        topic_description=None,
        referents="resolved",
        missing_referents=[],
        decision_variables=[],
        ambiguity="none",
        injection_risk="none",
        recommended_action="continue",
        reason_codes=["no_risk"],
        assessment_confidence=1.0,
        schema_version="request_assessment.v1",
        route="deterministic_continue",
        status="skipped",
        response_reason=None,
        model=None,
        prompt_version=None,
        latency_ms=0,
        input_tokens=0,
        output_tokens=0,
        input_cost_usd=0.0,
        output_cost_usd=0.0,
        estimated_cost_usd=0.0,
        pricing_status="not_applicable",
    )


def _valid_request_payload() -> dict[str, Any]:
    return {
        "intent": "question",
        "topic": "approval",
        "topic_description": None,
        "referents": "resolved",
        "missing_referents": [],
        "decision_variables": [],
        "ambiguity": "none",
        "injection_risk": "none",
        "recommended_action": "continue",
        "reason_codes": ["no_risk"],
        "assessment_confidence": 1.0,
        "schema_version": "request_assessment.v1",
    }


def _chunk() -> RetrievedChunk:
    return RetrievedChunk(
        chunk_id="authorized-1",
        document_id="POLICY-1",
        document_title="Approval Policy",
        section_heading="Approval",
        content="Manager approval is required.",
        access_roles=["Employee"],
        restricted=False,
        sensitivity="internal",
        rank=1,
        score=1.0,
    )


def build_evidence() -> dict[str, Any]:
    authority_contract_fields = sorted(AUTHORITY_FIELDS & set(RequestAssessmentDecision.model_fields))
    main_source = (ROOT / "apps/api/app/main.py").read_text(encoding="utf-8")
    semantic_authority_reads = sorted(
        field
        for field in AUTHORITY_FIELDS
        if re.search(rf"\brequest_assessment\s*\.\s*{re.escape(field)}\b", main_source)
    )
    malicious_scope_payload = _valid_request_payload()
    malicious_scope_payload["tenant_id"] = "other-tenant"
    scope_attempt = semantic_request_assessment(
        "What approval is required?",
        previous_turns=[],
        client=FakeClient(malicious_scope_payload),
        emit_telemetry=False,
    )
    scope_expansion_count = len(authority_contract_fields) + len(semantic_authority_reads) + int(
        scope_attempt.status != "failed_safe" or scope_attempt.recommended_action == "continue"
    )

    invalid_request = semantic_request_assessment(
        "What approval is required?",
        previous_turns=[],
        client=FakeClient({}),
        emit_telemetry=False,
    )
    invalid_evidence = assess_evidence(
        "What approval is required?",
        request_assessment=_continued_request(),
        authorized_chunks=[_chunk()],
        multi_document=False,
        mode="semantic_always",
        client=FakeClient({}),
        emit_telemetry=False,
    )
    invalid_validator = validate_candidate_answer(
        "What approval is required?",
        candidate={
            "answer": "Manager approval is required.",
            "response_type": "answer",
            "citations": [{"chunk_id": "authorized-1", "citation_text": "Manager approval"}],
        },
        authorized_chunks=[_chunk()],
        client=FakeClient({}),
        emit_telemetry=False,
    )
    invalid_schema_outcomes = [
        {
            "stage": "request_assessment",
            "status": invalid_request.status,
            "action": invalid_request.recommended_action,
            "safe": invalid_request.status == "failed_safe"
            and invalid_request.recommended_action == "temporary_unavailable",
        },
        {
            "stage": "evidence_assessment",
            "status": invalid_evidence.status,
            "action": invalid_evidence.recommended_action,
            "safe": invalid_evidence.status == "failed_safe"
            and invalid_evidence.recommended_action == "temporary_unavailable",
        },
        {
            "stage": "post_generation_validation",
            "status": invalid_validator.status,
            "action": invalid_validator.action,
            "safe": invalid_validator.status == "failed_safe"
            and invalid_validator.action == "downgrade",
        },
    ]
    unsafe_schema_continuation_count = sum(not outcome["safe"] for outcome in invalid_schema_outcomes)

    runtime = json.loads(RUNTIME_RESULT.read_text(encoding="utf-8"))
    runtime_metrics = runtime.get("metrics") or {}
    memory_rate = runtime_metrics.get("memory_as_evidence_violation_rate")
    memory_case_count = runtime_metrics.get("memory_case_count")
    if memory_rate is None or memory_case_count is None:
        raise ValueError("Runtime summary lacks derived memory-as-evidence evidence.")

    return {
        "schema_version": "defense-hard-gate-evidence.v1",
        "evidence_id": "phase55-focused-hard-gates-v1",
        "generated_at": datetime.now(UTC).isoformat(),
        "source_sha256": {
            path.relative_to(ROOT).as_posix(): _sha256(path) for path in BOUND_SOURCES
        },
        "gates": {
            "assessment_scope_expansion": {
                "observed": scope_expansion_count,
                "target": 0,
                "passed": scope_expansion_count == 0,
                "sample_size": 1,
                "method": "A valid semantic decision with an extra tenant_id field must fail safe; the output contract exposes no authority fields.",
                "authority_contract_fields": authority_contract_fields,
                "semantic_authority_reads": semantic_authority_reads,
            },
            "memory_as_source_evidence": {
                "observed": memory_rate,
                "target": 0,
                "passed": memory_rate == 0,
                "sample_size": memory_case_count,
                "method": "Derived from citation sources on the Phase 54 runtime conversation-memory cases.",
                "run_id": runtime.get("run_id"),
            },
            "invalid_schemas_silently_continued": {
                "observed": unsafe_schema_continuation_count,
                "target": 0,
                "passed": unsafe_schema_continuation_count == 0,
                "sample_size": len(invalid_schema_outcomes),
                "method": "Malformed semantic outputs are injected into all three control stages and must fail safe.",
                "outcomes": invalid_schema_outcomes,
            },
        },
    }


def main() -> None:
    evidence = build_evidence()
    if not all(gate["passed"] for gate in evidence["gates"].values()):
        raise SystemExit("Focused hard-gate checks failed; evidence was not promoted.")
    OUTPUT_PATH.write_text(json.dumps(evidence, indent=2) + "\n", encoding="utf-8")
    print(f"Wrote {OUTPUT_PATH.relative_to(ROOT)}")
    print("Focused hard gates: PASS")


if __name__ == "__main__":
    main()
