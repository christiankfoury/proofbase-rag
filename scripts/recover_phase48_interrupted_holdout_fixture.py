from __future__ import annotations

import argparse
import json
import sys
from datetime import UTC, datetime
from pathlib import Path

from fastapi.testclient import TestClient


ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

from apps.api.app.main import app
from scripts import run_independent_generalization_eval as engine
from scripts.independent_generalization_common import file_sha256, git_commit, load_json, tree_sha256, write_json_atomic
from scripts.run_phase48_generalization_eval import CORPUS_DIR, HOLDOUT_PATH, _preflight


RESULT_PATH = ROOT / "data/evaluation/independent-generalization/results/phase48-independent-holdout-v2.json"
RECOVERY_PATH = ROOT / "data/evaluation/independent-generalization/results/phase48-independent-holdout-v2-fixture-recovery.json"


def main() -> None:
    parser = argparse.ArgumentParser(
        description="Execute only the untouched fixture case after the Phase 48 run stopped before fixture setup."
    )
    parser.add_argument("--frozen-runtime-commit", required=True)
    parser.add_argument("--allow-external-ai", action="store_true")
    parser.add_argument("--budget-usd", type=float, default=0.25)
    args = parser.parse_args()

    if not args.allow_external_ai:
        raise SystemExit("Recovery fixture setup may call OpenAI embeddings and answer generation; explicit approval is required.")
    if RESULT_PATH.exists() or RECOVERY_PATH.exists():
        raise SystemExit("A Phase 48 complete or fixture-recovery artifact already exists; another execution is prohibited.")
    preflight = _preflight(args.frozen_runtime_commit)
    if not preflight["valid"]:
        raise SystemExit("Recovery preflight failed:\n- " + "\n- ".join(preflight["errors"]))

    suite = load_json(HOLDOUT_PATH)
    fixtures = [case for case in suite["cases"] if case.get("fixture_requirements")]
    if len(fixtures) != 1:
        raise SystemExit(f"Expected exactly one untouched fixture case, found {len(fixtures)}.")

    engine.DEFAULT_PROMPT_VERSION = "v9"
    started_at = datetime.now(UTC).isoformat()
    rows = engine._run_fixture_cases(TestClient(app), fixtures)
    completed_at = datetime.now(UTC).isoformat()
    if len(rows) != 1:
        raise SystemExit(f"Expected exactly one fixture result, found {len(rows)}.")
    cost = float(rows[0].get("estimated_cost_usd") or 0.0)
    if cost > args.budget_usd:
        raise SystemExit(f"Fixture cost ${cost:.6f} exceeded recovery budget ${args.budget_usd:.6f}.")

    result = {
        "run_id": "phase48-independent-holdout-v2-fixture-recovery",
        "status": "completed_after_interruption",
        "started_at": started_at,
        "completed_at": completed_at,
        "reason": "The sealed complete run stopped before fixture setup because the evaluator lacked generic fixture support.",
        "scope": "Only the previously untouched uploaded-document fixture case was executed; cases 1-29 were not rerun.",
        "provenance": {
            "evaluation_commit": git_commit(),
            "frozen_runtime_commit": args.frozen_runtime_commit,
            "suite_hash": file_sha256(HOLDOUT_PATH),
            "corpus_hash": tree_sha256(CORPUS_DIR),
            "prompt_version": "v9",
            "preflight": preflight,
        },
        "estimated_cost_usd": cost,
        "row": rows[0],
    }
    write_json_atomic(RECOVERY_PATH, result)
    print(json.dumps({"case_id": rows[0]["case_id"], "passed": rows[0]["passed"], "estimated_cost_usd": cost}, indent=2))


if __name__ == "__main__":
    main()
