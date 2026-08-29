from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from apps.api.app.evaluation.release_gate import corpus_sha256, evaluate_release, load_json, sha256_file

DEFAULT_POLICY = ROOT / "data" / "evaluation" / "release-gates" / "phase63-policy.json"
DEFAULT_CHECKS = ROOT / "data" / "evaluation" / "release-gates" / "phase63-deterministic-checks.json"
DEFAULT_FINDINGS = ROOT / "data" / "evaluation" / "release-gates" / "phase63-findings.json"
DEFAULT_OPERATIONAL = ROOT / "data" / "evaluation" / "release-gates" / "phase63-operational-readiness.json"
DEFAULT_READINESS = ROOT / "data" / "evaluation" / "defense" / "phase55-defense-readiness.json"
DEVELOPMENT_MANIFEST = ROOT / "data" / "evaluation" / "defense" / "defense-evaluation-manifest-v1.json"
DEFAULT_OUTPUT = ROOT / "data" / "evaluation" / "release-gates" / "phase63-release-decision.json"


def provider_configuration() -> dict:
    stages = []
    manifest = load_json(DEVELOPMENT_MANIFEST)
    for suite in manifest["suites"]:
        result = load_json(ROOT / suite["result_path"])
        stages.append({
            "stage": suite["stage"],
            "run_id": suite["promoted_run_id"],
            "mode": result.get("mode"),
            "model": result.get("model") or "not_recorded_in_source_artifact",
            "prompt_version": result.get("prompt_version") or "not_recorded_in_source_artifact",
            "sample_size": suite["case_count"],
            "estimated_cost_usd": result.get("estimated_cost_usd") or result.get("metrics", {}).get("estimated_cost_usd"),
        })
    return {"source": "historical_visible_development_artifacts", "external_calls_performed_by_this_gate": False, "stages": stages}


def main() -> None:
    parser = argparse.ArgumentParser(description="Evaluate the Phase 63 release policy without executing semantic or sealed suites.")
    parser.add_argument("--runtime-commit", required=True)
    parser.add_argument("--policy", type=Path, default=DEFAULT_POLICY)
    parser.add_argument("--checks", type=Path, default=DEFAULT_CHECKS)
    parser.add_argument("--findings", type=Path, default=DEFAULT_FINDINGS)
    parser.add_argument("--operational", type=Path, default=DEFAULT_OPERATIONAL)
    parser.add_argument("--readiness", type=Path, default=DEFAULT_READINESS)
    parser.add_argument("--output", type=Path, default=DEFAULT_OUTPUT)
    parser.add_argument("--check-only", action="store_true")
    args = parser.parse_args()

    policy = load_json(args.policy.resolve())
    decision = evaluate_release(
        policy=policy,
        deterministic=load_json(args.checks.resolve()),
        readiness=load_json(args.readiness.resolve()),
        findings=load_json(args.findings.resolve()),
        operational=load_json(args.operational.resolve()),
        provenance={
            "runtime_commit": args.runtime_commit,
            "policy_sha256": sha256_file(args.policy.resolve()),
            "corpus_sha256": corpus_sha256(ROOT / "data" / "synthetic-documents"),
            "development_manifest_sha256": sha256_file(DEVELOPMENT_MANIFEST),
            "provider_configuration": provider_configuration(),
        },
    )
    if not args.check_only:
        args.output.parent.mkdir(parents=True, exist_ok=True)
        args.output.write_text(json.dumps(decision, indent=2) + "\n", encoding="utf-8")
        print(f"Wrote {args.output.relative_to(ROOT)}")
    print(json.dumps({
        "portfolio_release_controls_ready": decision["portfolio_release_controls_ready"],
        "production_promotion_allowed": decision["production_promotion_allowed"],
        "production_blockers": decision["production_blockers"],
    }, indent=2))


if __name__ == "__main__":
    main()
