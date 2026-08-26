from __future__ import annotations

import argparse
import hashlib
import json
from pathlib import Path
from typing import Any


ROOT = Path(__file__).resolve().parents[1]
MANIFEST_PATH = ROOT / "data/evaluation/defense/defense-evaluation-manifest-v1.json"
ALLOWED_STAGES = {"request_assessment", "evidence_assessment", "post_generation_validation"}
ALLOWED_SCHEMAS = {
    "request-assessment-suite.v1",
    "evidence_assessment_suite.v1",
    "post_generation_validation_suite.v1",
}


def _load(path: Path) -> dict[str, Any]:
    return json.loads(path.read_text(encoding="utf-8"))


def _sha256(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def validate_manifest(path: Path = MANIFEST_PATH) -> dict[str, Any]:
    errors: list[str] = []
    try:
        manifest = _load(path)
    except Exception as exc:
        return {"valid": False, "errors": [f"manifest unreadable: {type(exc).__name__}"], "sample_size": 0}
    if manifest.get("schema_version") != "defense-evaluation-manifest.v1":
        errors.append("unsupported manifest schema")
    if manifest.get("sealed_holdout") is not False:
        errors.append("development manifest must not be labeled as a sealed holdout")
    suites = manifest.get("suites") or []
    if len(suites) != 3:
        errors.append("manifest must contain exactly three defense stages")
    stages: set[str] = set()
    case_ids: set[str] = set()
    sample_size = 0
    stage_summaries: list[dict[str, Any]] = []
    for entry in suites:
        stage = str(entry.get("stage") or "")
        if stage not in ALLOWED_STAGES or stage in stages:
            errors.append(f"invalid or duplicate stage: {stage}")
        stages.add(stage)
        suite_rel = str(entry.get("suite_path") or "")
        result_rel = str(entry.get("result_path") or "")
        if "independent-generalization" in suite_rel or any(f"phase-{number}" in suite_rel for number in (47, 48, 49)):
            errors.append(f"sealed holdout reference forbidden: {suite_rel}")
            continue
        suite_path = ROOT / suite_rel
        result_path = ROOT / result_rel
        for candidate, kind in ((suite_path, "suite"), (result_path, "result")):
            if not candidate.is_file() or ROOT not in candidate.resolve().parents:
                errors.append(f"{kind} path missing or outside repository: {candidate}")
        if not suite_path.is_file() or not result_path.is_file():
            continue
        if _sha256(suite_path) != entry.get("suite_sha256"):
            errors.append(f"suite hash drift: {suite_rel}")
        if _sha256(result_path) != entry.get("result_sha256"):
            errors.append(f"result hash drift: {result_rel}")
        suite = _load(suite_path)
        result = _load(result_path)
        schema = suite.get("schema_version")
        cases = suite.get("cases") or []
        ids = [str(case.get("id") or case.get("case_id") or "") for case in cases]
        if schema != entry.get("suite_schema_version") or schema not in ALLOWED_SCHEMAS:
            errors.append(f"suite schema mismatch: {suite_rel}")
        if len(cases) != entry.get("case_count") or len(cases) != suite.get("case_count"):
            errors.append(f"case count mismatch: {suite_rel}")
        if len(set(ids)) != len(ids) or any(not item for item in ids):
            errors.append(f"missing or duplicate IDs within {suite_rel}")
        duplicates = case_ids.intersection(ids)
        if duplicates:
            errors.append(f"case IDs collide across stages: {sorted(duplicates)}")
        case_ids.update(ids)
        result_count = int(result.get("sample_size") or result.get("metrics", {}).get("sample_size") or 0)
        if result_count != len(cases):
            errors.append(f"result sample mismatch: {result_rel}")
        sample_size += len(cases)
        stage_summaries.append({"stage": stage, "case_count": len(cases), "run_id": result.get("run_id")})
    if stages != ALLOWED_STAGES:
        errors.append("required defense stages are incomplete")
    return {
        "valid": not errors,
        "schema_version": manifest.get("schema_version"),
        "manifest_id": manifest.get("manifest_id"),
        "sample_size": sample_size,
        "stage_count": len(stages),
        "stages": stage_summaries,
        "errors": errors,
    }


def main() -> None:
    parser = argparse.ArgumentParser(description="Validate consolidated Phase 52-54 defense evidence.")
    parser.add_argument("--json", action="store_true")
    args = parser.parse_args()
    result = validate_manifest()
    if args.json:
        print(json.dumps(result, indent=2))
    else:
        print(f"{'PASS' if result['valid'] else 'FAIL'} defense manifest: {result['sample_size']} cases")
        for stage in result.get("stages") or []:
            print(f"  {stage['stage']}: {stage['case_count']} ({stage['run_id']})")
        for error in result["errors"]:
            print(f"  error: {error}")
    if not result["valid"]:
        raise SystemExit(1)


if __name__ == "__main__":
    main()
