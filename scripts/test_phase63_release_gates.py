from __future__ import annotations

import copy
import json
import os
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from apps.api.app.evaluation.release_gate import ReleaseGateError, evaluate_release, load_json, sha256_file
from scripts.run_phase63_deterministic_checks import CHECKS, NPM_EXECUTABLE

POLICY_PATH = ROOT / "data" / "evaluation" / "release-gates" / "phase63-policy.json"
READINESS_PATH = ROOT / "data" / "evaluation" / "defense" / "phase55-defense-readiness.json"
FINDINGS_PATH = ROOT / "data" / "evaluation" / "release-gates" / "phase63-findings.json"
OPERATIONAL_PATH = ROOT / "data" / "evaluation" / "release-gates" / "phase63-operational-readiness.json"


def deterministic(policy: dict, *, passed: bool = True) -> dict:
    return {
        "schema_version": "phase63-deterministic-checks.v1",
        "runtime_commit": "a" * 40,
        "all_passed": passed,
        "checks": [{"check_id": check_id, "passed": passed} for check_id in policy["deterministic_required_checks"]],
        "suite_paths_used": ["data/evaluation/defense/request-assessment-v1.json"],
        "sealed_suites_executed": False,
    }


def provenance() -> dict:
    return {
        "runtime_commit": "a" * 40,
        "policy_sha256": sha256_file(POLICY_PATH),
        "corpus_sha256": "b" * 64,
        "development_manifest_sha256": "c" * 64,
        "provider_configuration": {"external_calls_performed_by_this_gate": False},
    }


def evaluate(**overrides: dict) -> dict:
    policy = overrides.get("policy") or load_json(POLICY_PATH)
    return evaluate_release(
        policy=policy,
        deterministic=overrides.get("deterministic") or deterministic(policy),
        readiness=overrides.get("readiness") or load_json(READINESS_PATH),
        findings=overrides.get("findings") or load_json(FINDINGS_PATH),
        operational=overrides.get("operational") or load_json(OPERATIONAL_PATH),
        provenance=overrides.get("provenance") or provenance(),
    )


def test_current_local_evidence_passes_controls_but_blocks_production() -> None:
    result = evaluate()
    assert result["portfolio_release_controls_ready"] is True
    assert result["hard_security_gates"]["passed"] is True
    assert result["production_promotion_allowed"] is False
    assert {"human_review_required", "production_monitoring_not_ready", "hosted_availability_not_measured", "independent_validation_required"}.issubset(result["production_blockers"])
    assert all(item["status"] == "sealed_unchanged_not_executed" for item in result["sealed_custody"])


def test_hard_failure_and_open_high_block() -> None:
    readiness = copy.deepcopy(load_json(READINESS_PATH))
    readiness["hard_gates"][0]["passed"] = False
    result = evaluate(readiness=readiness)
    assert result["portfolio_release_controls_ready"] is False
    assert "hard_security_gate_failed" in result["production_blockers"]

    findings = copy.deepcopy(load_json(FINDINGS_PATH))
    findings["findings"].append({"id": "SYNTHETIC-HIGH", "severity": "high", "status": "open"})
    result = evaluate(findings=findings)
    assert result["hard_security_gates"]["passed"] is False
    assert "SYNTHETIC-HIGH" in result["hard_security_gates"]["open_critical_high_findings"]

    readiness = copy.deepcopy(load_json(READINESS_PATH))
    readiness["hard_gates"].pop()
    result = evaluate(readiness=readiness)
    assert result["hard_security_gates"]["passed"] is False
    assert result["hard_security_gates"]["missing"]


def test_quality_miss_requires_review() -> None:
    readiness = copy.deepcopy(load_json(READINESS_PATH))
    readiness["evidence_gates"][0]["passed"] = False
    result = evaluate(readiness=readiness)
    assert result["quality_gates"]["decision"] == "review_required"
    assert "quality_budget_review_required" in result["production_blockers"]


def test_sealed_suite_cannot_be_development_input() -> None:
    policy = load_json(POLICY_PATH)
    report = deterministic(policy)
    report["suite_paths_used"].append(policy["protected_sealed_suites"][0]["suite_path"])
    try:
        evaluate(policy=policy, deterministic=report)
    except ReleaseGateError as exc:
        assert str(exc) == "protected_sealed_suite_used_by_development_gate"
    else:
        raise AssertionError("Protected sealed suite was accepted as development evidence")


def test_missing_check_and_provenance_mismatch_fail_closed() -> None:
    policy = load_json(POLICY_PATH)
    report = deterministic(policy)
    report["checks"].pop()
    result = evaluate(policy=policy, deterministic=report)
    assert result["deterministic_checks"]["passed"] is False
    assert result["deterministic_checks"]["missing"]

    report = deterministic(policy)
    report["sealed_suites_executed"] = True
    try:
        evaluate(policy=policy, deterministic=report)
    except ReleaseGateError as exc:
        assert str(exc) == "sealed_suite_execution_must_be_false_for_deterministic_gate"
    else:
        raise AssertionError("A deterministic report claiming sealed-suite execution was accepted")

    bad_provenance = provenance()
    bad_provenance["runtime_commit"] = "d" * 40
    try:
        evaluate(policy=policy, provenance=bad_provenance)
    except ReleaseGateError as exc:
        assert str(exc) == "runtime_commit_provenance_mismatch"
    else:
        raise AssertionError("Mismatched runtime provenance was accepted")


def test_drift_inputs_require_reviewed_sources() -> None:
    policy_text = json.dumps(load_json(POLICY_PATH))
    assert "automatic benchmark truth" not in policy_text.lower()
    docs = (ROOT / "docs" / "phase-63" / "drift-and-case-lifecycle.md").read_text(encoding="utf-8")
    assert "never automatic benchmark truth" in docs
    assert "reviewed incidents" in docs and "reviewed feedback" in docs


def test_platform_executables_are_resolved() -> None:
    if os.name == "nt":
        assert NPM_EXECUTABLE.lower().endswith(("npm.cmd", "npm.exe"))
    web_command = next(command for check_id, command in CHECKS if check_id == "web_typecheck")
    assert web_command[web_command.index("--project") + 1] == "apps/web/tsconfig.json"


def main() -> None:
    test_current_local_evidence_passes_controls_but_blocks_production()
    test_hard_failure_and_open_high_block()
    test_quality_miss_requires_review()
    test_sealed_suite_cannot_be_development_input()
    test_missing_check_and_provenance_mismatch_fail_closed()
    test_drift_inputs_require_reviewed_sources()
    test_platform_executables_are_resolved()
    print("Phase 63 adversarial release-gate checks passed.")


if __name__ == "__main__":
    main()
