from __future__ import annotations

import json
import sys
import tempfile
import unittest
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

from apps.api.app.reasoning.defense_trace import build_defense_trace  # noqa: E402
from apps.api.app.reasoning.request_assessment import RequestAssessment  # noqa: E402
from apps.api.app.retrieval.types import RetrievedChunk  # noqa: E402
from scripts.export_defense_readiness import build_summary  # noqa: E402
from scripts import export_defense_readiness  # noqa: E402
from scripts.author_phase55_defense_holdout import _response_schema  # noqa: E402
from scripts.validate_defense_evaluation import MANIFEST_PATH, validate_manifest  # noqa: E402


class Phase55DefenseReadinessTests(unittest.TestCase):
    def _request_assessment(self) -> RequestAssessment:
        return RequestAssessment(
            intent="question",
            topic="security",
            topic_description=None,
            referents="not_applicable",
            missing_referents=[],
            decision_variables=[],
            ambiguity="none",
            injection_risk="none",
            recommended_action="continue",
            reason_codes=["no_risk"],
            assessment_confidence=0.98,
            schema_version="request_assessment.v1",
            route="semantic_assessment",
            status="succeeded",
            response_reason=None,
            model="test-model",
            prompt_version="v4",
            latency_ms=12,
            input_tokens=20,
            output_tokens=5,
            input_cost_usd=0.00001,
            output_cost_usd=0.00001,
            estimated_cost_usd=0.00002,
            pricing_status="estimated",
        )

    def _chunk(self, *, roles: list[str] | None = None) -> RetrievedChunk:
        return RetrievedChunk(
            chunk_id="safe-chunk-id",
            document_id="safe-document-id",
            document_title="Sensitive title must not enter trace",
            section_heading="Sensitive section must not enter trace",
            content="Sensitive source text and embedded instructions must not enter trace.",
            access_roles=roles or ["employee"],
            restricted=False,
            sensitivity="internal",
            rank=1,
            score=0.9,
        )

    def test_manifest_is_valid_and_consolidates_all_three_stages(self) -> None:
        result = validate_manifest()
        self.assertTrue(result["valid"], result["errors"])
        self.assertEqual(result["sample_size"], 102)
        self.assertEqual(result["stage_count"], 3)

    def test_manifest_hash_drift_fails_closed(self) -> None:
        manifest = json.loads(MANIFEST_PATH.read_text(encoding="utf-8"))
        manifest["suites"][0]["suite_sha256"] = "0" * 64
        with tempfile.TemporaryDirectory() as directory:
            path = Path(directory) / "manifest.json"
            path.write_text(json.dumps(manifest), encoding="utf-8")
            result = validate_manifest(path)
        self.assertFalse(result["valid"])
        self.assertTrue(any("hash drift" in error for error in result["errors"]))

    def test_generated_evidence_passes_predeclared_gates(self) -> None:
        summary = build_summary()
        self.assertTrue(summary["hard_gates_passed"])
        self.assertTrue(summary["evidence_gates_passed"])
        self.assertEqual(summary["manifest"]["sample_size"], 102)
        self.assertFalse(summary["independent_security_assessment"])
        self.assertFalse(summary["holdout"]["supports_current_claims"])
        self.assertTrue(summary["stability"]["passed"])
        self.assertEqual(summary["stability"]["passes"], 3)
        self.assertEqual(
            {gate["source"] for gate in summary["hard_gates"] if gate["name"] in {
                "Assessment-caused tenant or scope expansion",
                "Memory used as source evidence",
                "Invalid assessment schemas silently continued",
            }},
            {"phase55-focused-hard-gates-v1"},
        )

    def test_generated_evidence_rejects_stale_source_binding(self) -> None:
        evidence = json.loads(export_defense_readiness.HARD_GATE_RESULT.read_text(encoding="utf-8"))
        evidence["source_sha256"]["apps/api/app/main.py"] = "0" * 64
        with tempfile.TemporaryDirectory() as directory:
            path = Path(directory) / "stale-hard-gates.json"
            path.write_text(json.dumps(evidence), encoding="utf-8")
            original = export_defense_readiness.HARD_GATE_RESULT
            try:
                export_defense_readiness.HARD_GATE_RESULT = path
                with self.assertRaisesRegex(ValueError, "stale"):
                    export_defense_readiness.build_summary()
            finally:
                export_defense_readiness.HARD_GATE_RESULT = original

    def test_trace_has_seven_bounded_stages_without_content_or_identity(self) -> None:
        trace = build_defense_trace(
            request_assessment=self._request_assessment(),
            evidence_assessment=None,
            post_generation_validation=None,
            answer={"response_type": "clarification", "estimated_cost_usd": 0.0},
            authorized_chunks=[self._chunk()],
            effective_role="employee",
            generation_latency_ms=0,
        )
        payload = trace.model_dump(mode="json")
        serialized = json.dumps(payload)
        self.assertEqual(payload["schema_version"], "defense_trace.v1")
        self.assertEqual(len(payload["stages"]), 7)
        for forbidden in (
            "Sensitive title",
            "Sensitive source text",
            "safe-chunk-id",
            "safe-document-id",
            "employee",
            "test-model",
        ):
            self.assertNotIn(forbidden, serialized)
        self.assertTrue(all(stage.get("memory_used_as_evidence") is not True for stage in payload["stages"]))

    def test_permission_stage_cannot_silently_mark_unauthorized_input_safe(self) -> None:
        trace = build_defense_trace(
            request_assessment=self._request_assessment(),
            evidence_assessment=None,
            post_generation_validation=None,
            answer={"response_type": "not_found"},
            authorized_chunks=[self._chunk(roles=["it_admin"])],
            effective_role="employee",
            generation_latency_ms=0,
        )
        permission = next(stage for stage in trace.stages if stage.name == "permission_filter")
        self.assertEqual(permission.status, "failed_safe")
        self.assertEqual(permission.action, "security_invariant_failed")
        self.assertEqual(permission.unauthorized_chunk_count, 1)
        self.assertEqual(permission.authorized_chunk_count, 0)

    def test_trace_builder_has_no_scope_or_content_authority_inputs(self) -> None:
        import inspect

        parameters = set(inspect.signature(build_defense_trace).parameters)
        self.assertFalse({"project_id", "department_id", "tenant_id", "question", "memory_text", "source_text"} & parameters)

    def test_holdout_authoring_schema_enforces_ten_cases_per_stage(self) -> None:
        schema = _response_schema()
        properties = schema["properties"]
        self.assertEqual(set(properties), {"request_cases", "evidence_cases", "validation_cases"})
        expected = {
            "request_cases": "request_assessment",
            "evidence_cases": "evidence_assessment",
            "validation_cases": "post_generation_validation",
        }
        for name, stage in expected.items():
            self.assertEqual(properties[name]["minItems"], 10)
            self.assertEqual(properties[name]["maxItems"], 10)
            self.assertEqual(properties[name]["items"]["properties"]["stage"]["type"], "string")
            self.assertEqual(properties[name]["items"]["properties"]["stage"]["const"], stage)

    def test_default_holdout_authoring_model_has_budget_pricing(self) -> None:
        from apps.api.app.costing.estimator import estimate_chat_cost
        from scripts.author_phase55_defense_holdout import (
            DEFAULT_MODEL,
            MAX_COMPLETION_TOKENS,
            MAX_INPUT_BUDGET_TOKENS,
        )

        estimate = estimate_chat_cost(
            model=DEFAULT_MODEL,
            input_tokens=MAX_INPUT_BUDGET_TOKENS,
            output_tokens=MAX_COMPLETION_TOKENS,
        )
        self.assertEqual(estimate["pricing_status"], "estimated")
        self.assertLessEqual(float(estimate["estimated_cost_usd"] or 1.0), 0.15)


if __name__ == "__main__":
    unittest.main()
