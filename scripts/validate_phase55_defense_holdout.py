from __future__ import annotations

import hashlib
import json
from collections import Counter
from pathlib import Path
from typing import Any


ROOT = Path(__file__).resolve().parents[1]
HOLDOUT_PATH = ROOT / "data/evaluation/defense/phase55-defense-holdout-v1.json"
HASH_PATH = ROOT / "data/evaluation/defense/phase55-defense-holdout-v1.sha256"
STAGES = {"request_assessment", "evidence_assessment", "post_generation_validation"}
ACTIONS = {
    "request_assessment": {"continue", "clarify", "block", "temporary_unavailable"},
    "evidence_assessment": {"answer", "partial_answer", "clarify", "not_found", "temporary_unavailable"},
    "post_generation_validation": {"accept", "repair", "downgrade"},
}


def file_sha256(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def validate_holdout(*, require_hash: bool = True) -> dict[str, Any]:
    errors: list[str] = []
    if not HOLDOUT_PATH.is_file():
        return {"valid": False, "errors": ["sealed holdout file is missing"], "case_count": 0}
    try:
        payload = json.loads(HOLDOUT_PATH.read_text(encoding="utf-8"))
    except Exception as exc:
        return {"valid": False, "errors": [f"holdout unreadable: {type(exc).__name__}"], "case_count": 0}
    cases = payload.get("cases") or []
    if payload.get("schema_version") != "phase55-defense-holdout.v1":
        errors.append("schema version mismatch")
    if payload.get("suite_id") != "phase55-defense-holdout-v1" or payload.get("split") != "holdout" or payload.get("sealed") is not True:
        errors.append("holdout identity or sealed state mismatch")
    if len(cases) != 30 or payload.get("case_count") != 30:
        errors.append("holdout must contain exactly 30 cases")
    ids = [str(case.get("case_id") or "") for case in cases]
    if len(set(ids)) != len(ids) or any(not item for item in ids):
        errors.append("case IDs must be present and unique")
    stages = Counter(str(case.get("stage") or "") for case in cases)
    if stages != Counter({stage: 10 for stage in STAGES}):
        errors.append("holdout must contain exactly 10 cases per defense stage")
    for case in cases:
        stage = str(case.get("stage") or "")
        if stage not in STAGES:
            errors.append("case contains unknown stage")
            continue
        if case.get("expected_action") not in ACTIONS[stage]:
            errors.append(f"{case.get('case_id')}: invalid expected action")
        if not str(case.get("question") or "").strip() or not str(case.get("category") or "").strip():
            errors.append(f"{case.get('case_id')}: missing bounded input metadata")
        if stage != "request_assessment" and not case.get("authorized_evidence"):
            errors.append(f"{case.get('case_id')}: evidence-stage case has no evidence")
        if stage == "post_generation_validation" and not case.get("candidate"):
            errors.append(f"{case.get('case_id')}: validator case has no candidate")
    digest = file_sha256(HOLDOUT_PATH)
    recorded = HASH_PATH.read_text(encoding="utf-8").strip().split()[0] if HASH_PATH.is_file() else None
    if require_hash and digest != recorded:
        errors.append("holdout hash is missing or does not match")
    return {
        "valid": not errors,
        "case_count": len(cases),
        "stage_counts": dict(sorted(stages.items())),
        "suite_sha256": digest,
        "recorded_sha256": recorded,
        "frozen_runtime_commit": (payload.get("frozen_runtime") or {}).get("commit"),
        "executed": False,
        "errors": errors,
    }


def main() -> None:
    result = validate_holdout()
    print(f"{'PASS' if result['valid'] else 'FAIL'} sealed Phase 55 holdout: {result['case_count']} cases")
    if result.get("stage_counts"):
        print("  stage counts: " + ", ".join(f"{key}={value}" for key, value in result["stage_counts"].items()))
    print(f"  executed: {result['executed']}")
    for error in result["errors"]:
        print(f"  error: {error}")
    if not result["valid"]:
        raise SystemExit(1)


if __name__ == "__main__":
    main()
