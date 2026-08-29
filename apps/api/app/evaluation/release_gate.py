from __future__ import annotations

import hashlib
import json
from datetime import UTC, datetime
from pathlib import Path
from typing import Any

ROOT = Path(__file__).resolve().parents[4]


class ReleaseGateError(ValueError):
    pass


def sha256_file(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for chunk in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def corpus_sha256(root: Path) -> str:
    digest = hashlib.sha256()
    for path in sorted(root.rglob("*.md")):
        digest.update(path.relative_to(root).as_posix().encode())
        digest.update(b"\0")
        digest.update(path.read_bytes())
        digest.update(b"\0")
    return digest.hexdigest()


def load_json(path: Path) -> dict[str, Any]:
    try:
        value = json.loads(path.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError) as exc:
        raise ReleaseGateError(f"invalid_release_input:{path.name}") from exc
    if not isinstance(value, dict):
        raise ReleaseGateError(f"invalid_release_input:{path.name}")
    return value


def verify_sealed_custody(policy: dict[str, Any], *, suite_paths_used: list[str]) -> list[dict[str, Any]]:
    protected = policy.get("protected_sealed_suites")
    if not isinstance(protected, list) or not protected:
        raise ReleaseGateError("protected_sealed_suite_inventory_required")
    used = {Path(value).as_posix() for value in suite_paths_used}
    results: list[dict[str, Any]] = []
    for item in protected:
        suite_path = ROOT / str(item["suite_path"])
        seal_path = ROOT / str(item["seal_path"])
        if Path(str(item["suite_path"])).as_posix() in used:
            raise ReleaseGateError("protected_sealed_suite_used_by_development_gate")
        expected = seal_path.read_text(encoding="utf-8").strip().split()[0]
        observed = sha256_file(suite_path)
        if observed != expected:
            raise ReleaseGateError("protected_sealed_suite_hash_mismatch")
        results.append({
            "suite_path": str(item["suite_path"]),
            "seal_path": str(item["seal_path"]),
            "sha256": observed,
            "status": "sealed_unchanged_not_executed",
        })
    return results


def evaluate_release(
    *,
    policy: dict[str, Any],
    deterministic: dict[str, Any],
    readiness: dict[str, Any],
    findings: dict[str, Any],
    operational: dict[str, Any],
    provenance: dict[str, Any],
) -> dict[str, Any]:
    if policy.get("schema_version") != "phase63-release-policy.v1":
        raise ReleaseGateError("unsupported_release_policy_schema")
    if deterministic.get("schema_version") != "phase63-deterministic-checks.v1":
        raise ReleaseGateError("unsupported_deterministic_report_schema")
    if deterministic.get("runtime_commit") != provenance.get("runtime_commit"):
        raise ReleaseGateError("runtime_commit_provenance_mismatch")
    required = set(policy.get("deterministic_required_checks") or [])
    checks = {str(item.get("check_id")): item for item in deterministic.get("checks") or []}
    missing_checks = sorted(required - checks.keys())
    failed_checks = sorted(check_id for check_id in required if not checks.get(check_id, {}).get("passed"))
    deterministic_passed = not missing_checks and not failed_checks and bool(deterministic.get("all_passed"))
    if deterministic.get("sealed_suites_executed") is not False:
        raise ReleaseGateError("sealed_suite_execution_must_be_false_for_deterministic_gate")

    protected = verify_sealed_custody(
        policy,
        suite_paths_used=[str(path) for path in deterministic.get("suite_paths_used") or []],
    )
    hard_gate_records = readiness.get("hard_gates") or []
    hard_by_name = {str(gate.get("name")): gate for gate in hard_gate_records}
    required_hard = set(policy.get("hard_security_gates") or [])
    missing_hard = sorted(required_hard - hard_by_name.keys())
    hard_failures = [f"missing:{name}" for name in missing_hard]
    hard_failures.extend(gate["name"] for gate in hard_gate_records if not gate.get("passed"))
    quality_failures = [gate["name"] for gate in readiness.get("evidence_gates") or [] if not gate.get("passed")]
    if not readiness.get("stability", {}).get("passed"):
        quality_failures.append("Deterministic evidence stability")
    open_high = [
        item["id"] for item in findings.get("findings") or []
        if item.get("severity") in {"critical", "high"} and item.get("status") not in {"verified_closed", "false_positive"}
    ]
    hard_security_passed = not hard_failures and not open_high

    human = operational.get("human_review") or {}
    human_review_passed = bool(human.get("all_security_failures_reviewed")) and int(human.get("passes_reviewed", 0)) >= int(human.get("required_pass_sample", 0))
    monitoring_ready = bool((operational.get("monitoring") or {}).get("production_ready"))
    rollback_ready = bool((operational.get("rollback") or {}).get("verified"))
    availability_ready = bool((operational.get("availability") or {}).get("within_budget"))
    independent_status = str(operational.get("independent_validation_status") or "Independent validation required")

    blockers: list[str] = []
    if not deterministic_passed:
        blockers.append("deterministic_checks_failed_or_missing")
    if hard_failures:
        blockers.append("hard_security_gate_failed")
    if open_high:
        blockers.append("unresolved_critical_or_high_finding")
    if quality_failures:
        blockers.append("quality_budget_review_required")
    if not human_review_passed:
        blockers.append("human_review_required")
    if not monitoring_ready:
        blockers.append("production_monitoring_not_ready")
    if not rollback_ready:
        blockers.append("rollback_not_verified")
    if not availability_ready:
        blockers.append("hosted_availability_not_measured")
    if independent_status == "Independent validation required":
        blockers.append("independent_validation_required")

    return {
        "schema_version": "phase63-release-decision.v1",
        "decision_id": f"phase63-{str(provenance['runtime_commit'])[:12]}",
        "generated_at": datetime.now(UTC).isoformat(),
        "runtime_commit": provenance["runtime_commit"],
        "policy_id": policy["policy_id"],
        "policy_sha256": provenance["policy_sha256"],
        "corpus_sha256": provenance["corpus_sha256"],
        "development_manifest_sha256": provenance["development_manifest_sha256"],
        "provider_configuration": provenance["provider_configuration"],
        "development_evidence": {
            "manifest": readiness.get("manifest"),
            "stages": readiness.get("stages"),
            "runtime": readiness.get("runtime"),
            "permission": readiness.get("permission"),
            "hard_gates": hard_gate_records,
            "quality_latency_cost_gates": readiness.get("evidence_gates"),
            "stability": readiness.get("stability"),
        },
        "deterministic_checks": {
            "passed": deterministic_passed,
            "missing": missing_checks,
            "failed": failed_checks,
            "check_count": len(checks),
        },
        "hard_security_gates": {"passed": hard_security_passed, "failures": hard_failures, "missing": missing_hard, "open_critical_high_findings": open_high},
        "quality_gates": {"decision": "pass" if not quality_failures else "review_required", "failures": quality_failures},
        "human_review": {"passed": human_review_passed, **human},
        "operational_readiness": {
            "monitoring_ready": monitoring_ready,
            "rollback_ready": rollback_ready,
            "hosted_availability_within_budget": availability_ready,
            "independent_validation_status": independent_status,
        },
        "sealed_custody": protected,
        "portfolio_release_controls_ready": deterministic_passed and hard_security_passed and not quality_failures,
        "production_promotion_allowed": not blockers,
        "production_blockers": blockers,
        "claim_boundary": "A local portfolio gate result is not a production deployment, independent assessment, live monitoring test, or fresh holdout claim.",
    }
