from __future__ import annotations

import argparse
import hashlib
import json
import os
import shutil
import subprocess
import sys
import time
from datetime import UTC, datetime
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
DEFAULT_OUTPUT = ROOT / "data" / "evaluation" / "release-gates" / "phase63-deterministic-checks.json"
ALLOWED_DIRTY = {"data/observability/request-logs.jsonl"}
NPM_EXECUTABLE = shutil.which("npm") or "npm"

CHECKS = (
    ("python_compile", [sys.executable, "-m", "py_compile", "apps/api/app/main.py", "apps/api/app/evaluation/release_gate.py", "scripts/run_phase63_release_gate.py"]),
    ("benchmark_schema", [sys.executable, "scripts/validate_benchmark.py"]),
    ("defense_manifest_schema", [sys.executable, "scripts/validate_defense_evaluation.py"]),
    ("phase52_request", [sys.executable, "scripts/test_phase52_request_assessment.py"]),
    ("phase53_evidence", [sys.executable, "scripts/test_phase53_evidence_assessment.py"]),
    ("phase54_validator", [sys.executable, "scripts/test_phase54_post_generation_validation.py"]),
    ("phase55_readiness", [sys.executable, "scripts/test_phase55_defense_readiness.py"]),
    ("phase56_identity", [sys.executable, "scripts/test_phase56_identity_tenancy.py"]),
    ("phase57_tenant_isolation", [sys.executable, "scripts/test_phase57_tenant_isolation.py"]),
    ("phase58_abuse", [sys.executable, "scripts/test_phase58_abuse_controls.py"]),
    ("phase59_files", [sys.executable, "scripts/test_phase59_secure_files.py"]),
    ("phase60_privacy", [sys.executable, "scripts/test_phase60_privacy_secrets.py"]),
    ("phase61_monitoring", [sys.executable, "scripts/test_phase61_security_monitoring.py"]),
    ("phase62_assessment", [sys.executable, "scripts/test_phase62_security_prechecks.py"]),
    ("phase63_release_gate", [sys.executable, "scripts/test_phase63_release_gates.py"]),
    ("repository_secret_scan", [sys.executable, "scripts/scan_phase60_secrets.py", "--scan-path", "."]),
    ("web_typecheck", [NPM_EXECUTABLE, "--prefix", "apps/web", "exec", "--", "tsc", "--noEmit", "--incremental", "false"]),
    ("compose_config", ["docker", "compose", "config", "--quiet"]),
)


def git(*args: str) -> str:
    return subprocess.check_output(["git", *args], cwd=ROOT, text=True).strip()


def main() -> None:
    parser = argparse.ArgumentParser(description="Run deterministic Phase 63 checks without external AI or sealed-suite execution.")
    parser.add_argument("--runtime-commit", required=True)
    parser.add_argument("--output", type=Path, default=DEFAULT_OUTPUT)
    args = parser.parse_args()
    if git("rev-parse", "HEAD") != args.runtime_commit:
        raise SystemExit("Runtime commit does not match HEAD.")
    dirty = {line.strip() for line in git("diff", "--name-only").splitlines() if line.strip()}
    unexpected = sorted(dirty - ALLOWED_DIRTY - {str(args.output.relative_to(ROOT)).replace("\\", "/")})
    if unexpected:
        raise SystemExit(f"Tracked runtime files are dirty: {', '.join(unexpected)}")

    environment = os.environ.copy()
    environment["PYTHONDONTWRITEBYTECODE"] = "1"
    results = []
    for check_id, command in CHECKS:
        started = time.perf_counter()
        completed = subprocess.run(command, cwd=ROOT, capture_output=True, text=True, check=False, env=environment)
        output = f"{completed.stdout}\n{completed.stderr}".encode()
        results.append({
            "check_id": check_id,
            "passed": completed.returncode == 0,
            "exit_code": completed.returncode,
            "duration_ms": round((time.perf_counter() - started) * 1000),
            "output_sha256": hashlib.sha256(output).hexdigest(),
        })
        print(f"{check_id}: {'PASS' if completed.returncode == 0 else 'FAIL'}")

    report = {
        "schema_version": "phase63-deterministic-checks.v1",
        "run_id": f"phase63-deterministic-{args.runtime_commit[:12]}",
        "generated_at": datetime.now(UTC).isoformat(),
        "runtime_commit": args.runtime_commit,
        "execution_mode": "local_no_external_ai",
        "all_passed": all(item["passed"] for item in results),
        "checks": results,
        "suite_paths_used": [
            "data/evaluation/benchmark-questions.json",
            "data/evaluation/defense/request-assessment-v1.json",
            "data/evaluation/defense/evidence-assessment-v1.json",
            "data/evaluation/defense/post-generation-validation-v1.json",
        ],
        "sealed_suites_executed": False,
    }
    args.output.parent.mkdir(parents=True, exist_ok=True)
    args.output.write_text(json.dumps(report, indent=2) + "\n", encoding="utf-8")
    if not report["all_passed"]:
        raise SystemExit("One or more deterministic release checks failed.")


if __name__ == "__main__":
    main()
