from __future__ import annotations

import argparse
import json
import sys
from collections import Counter
from datetime import UTC, datetime
from pathlib import Path
from typing import Any


ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

from apps.api.app.core.config import get_settings
from scripts import run_independent_generalization_eval as engine
from scripts.independent_generalization_common import (
    CORPUS_DIR,
    DEVELOPMENT_PATH,
    dirty_paths,
    file_sha256,
    git_commit,
    load_json,
    protected_path_changes,
    tree_sha256,
    validate_suite_payload,
    write_json_atomic,
)


HOLDOUT_PATH = ROOT / "data/evaluation/independent-generalization/holdout-v2.json"
HOLDOUT_HASH_PATH = ROOT / "data/evaluation/independent-generalization/holdout-v2.sha256"
RESULTS_DIR = ROOT / "data/evaluation/independent-generalization/results"
EVAL_RUNS_DIR = ROOT / "data/evaluation/eval-runs"
PHASE_DOCS_DIR = ROOT / "docs/phase-48"
PROMPT_VERSION = "v9"
SUITE_VERSION = "2.0"
HOLDOUT_RESULT_PATH = RESULTS_DIR / "phase48-independent-holdout-v2.json"
APPROVAL_MESSAGE = (
    "Phase 48 sends authored synthetic questions, prior synthetic chat turns, uploaded synthetic fixture text, and "
    "permission-filtered synthetic document snippets to OpenAI. Re-run with --allow-external-ai only after approval."
)


def _now() -> str:
    return datetime.now(UTC).isoformat()


def _suite_path(split: str) -> Path:
    return DEVELOPMENT_PATH if split == "development" else HOLDOUT_PATH


def _validate(split: str) -> dict[str, Any]:
    path = _suite_path(split)
    if not path.exists():
        return {"valid": False, "errors": [f"missing suite file: {path}"]}
    version = "1.0" if split == "development" else SUITE_VERSION
    return validate_suite_payload(load_json(path), expected_split=split, expected_suite_version=version)


def _preflight(frozen_runtime_commit: str) -> dict[str, Any]:
    dirty = dirty_paths()
    protected = protected_path_changes(frozen_runtime_commit)
    actual_hash = file_sha256(HOLDOUT_PATH) if HOLDOUT_PATH.exists() else None
    recorded_hash = None
    if HOLDOUT_HASH_PATH.exists():
        recorded_hash = HOLDOUT_HASH_PATH.read_text(encoding="utf-8").strip().split()[0]
    validation = _validate("holdout")
    errors: list[str] = []
    if dirty:
        errors.append(f"working tree has non-ignored changes: {', '.join(dirty)}")
    if protected:
        errors.append(f"protected runtime/corpus paths changed since freeze: {', '.join(protected)}")
    if not validation["valid"]:
        errors.extend(validation["errors"])
    if not actual_hash or actual_hash != recorded_hash:
        errors.append("fresh holdout suite hash does not match holdout-v2.sha256")
    return {
        "valid": not errors,
        "errors": errors,
        "dirty_paths": dirty,
        "protected_path_changes": protected,
        "suite_hash": actual_hash,
        "recorded_suite_hash": recorded_hash,
        "corpus_hash": tree_sha256(CORPUS_DIR),
        "evaluation_commit": git_commit(),
        "frozen_runtime_commit": frozen_runtime_commit,
    }


def _select_cases(args: argparse.Namespace, suite: dict[str, Any]) -> list[dict[str, Any]]:
    cases = list(suite["cases"])
    if args.split == "holdout" and (args.case_id or args.category or args.limit or args.diagnostic):
        raise SystemExit("Partial or diagnostic fresh-holdout execution is prohibited.")
    if args.case_id:
        requested = set(args.case_id)
        cases = [case for case in cases if case["case_id"] in requested]
        missing = requested - {case["case_id"] for case in cases}
        if missing:
            raise SystemExit(f"Unknown case IDs: {', '.join(sorted(missing))}")
    if args.category:
        cases = [case for case in cases if case["category"] == args.category]
    if args.limit:
        cases = cases[: args.limit]
    if args.split == "development" and len(cases) != 70 and not args.diagnostic:
        raise SystemExit("Partial development runs require --diagnostic so they cannot be mistaken for the published 70-case result.")
    return cases


def _eval_run(result: dict[str, Any]) -> dict[str, Any]:
    summary = result["summary"]
    return {
        "run_id": result["run_id"],
        "run_name": result["run_name"],
        "phase": "phase-48",
        "run_type": "independent_generalization_eval",
        "timestamp": result["completed_at"],
        "benchmark_version": f"independent-generalization-{result['split']}-v{2 if result['split'] == 'holdout' else 1}",
        "split": result["split"],
        "total_questions": summary["sample_size"],
        "retrieval_mode": result["provenance"]["retrieval_profile"],
        "top_k": result["provenance"]["top_k"],
        "prompt_version": result["provenance"]["prompt_version"],
        "model": result["provenance"]["model"],
        "temperature": 0.0,
        "metrics": {**summary["metrics"], "failed_question_count": summary["failed_count"]},
        "failed_questions": summary["failed_case_ids"],
        "category_breakdown": summary["category_counts"],
        "provenance": result["provenance"],
        "hard_gates": summary["hard_gates"],
        "portfolio_claim_gates": summary["portfolio_claim_gates"],
        "notes": "Phase 48 evidence. The original Phase 47 holdout remains immutable historical evidence at 14/30.",
    }


def _report(result: dict[str, Any]) -> str:
    summary = result["summary"]
    metrics = summary["metrics"]
    lines = [
        f"# Phase 48 {result['split'].title()} Results",
        "",
        f"Generated at: {result['completed_at']}",
        "",
        f"- Run ID: `{result['run_id']}`",
        f"- Cases: `{summary['sample_size']}`; passed: `{summary['passed_count']}`; failed: `{summary['failed_count']}`",
        f"- Behavior accuracy: `{metrics['behavior_accuracy']}`",
        f"- Required-source recall: `{metrics['expected_source_recall']}`",
        f"- Required-fact completeness: `{metrics['required_fact_completeness']}`",
        f"- Citation document accuracy: `{metrics['citation_document_accuracy']}`",
        f"- Factual hallucination rate: `{metrics['hallucination_rate']}`",
        f"- Hard gates: `{'pass' if all(summary['hard_gates'].values()) else 'fail'}`",
        f"- Estimated OpenAI cost: `${metrics['estimated_cost']:.6f}`",
        "",
        "## Failed Cases",
        "",
    ]
    failed = [row for row in result["rows"] if not row["passed"]]
    if not failed:
        lines.append("- None.")
    else:
        for row in failed:
            lines.append(
                f"- `{row['case_id']}`: expected `{row['expected_behavior']}`, actual `{row['actual_behavior']}`, "
                f"facts `{row['required_fact_completeness']}`, citations `{row['citation_document_accuracy']}`."
            )
    lines.extend(
        [
            "",
            "## Interpretation",
            "",
            "- Factual hallucination excludes response-type mismatches and weak-support diagnostics; those remain separate failures.",
            "- Citation document accuracy remains strict requested-source completeness.",
            "- The Phase 47 holdout was not executed or rescored for this result.",
        ]
    )
    return "\n".join(lines) + "\n"


def main() -> None:
    parser = argparse.ArgumentParser(description="Run the Phase 48 development suite or one-time fresh holdout.")
    parser.add_argument("--split", choices=("development", "holdout"), required=True)
    parser.add_argument("--dry-run", action="store_true")
    parser.add_argument("--diagnostic", action="store_true")
    parser.add_argument("--allow-external-ai", action="store_true")
    parser.add_argument("--budget-usd", type=float, default=2.0)
    parser.add_argument("--frozen-runtime-commit")
    parser.add_argument("--case-id", action="append")
    parser.add_argument("--category")
    parser.add_argument("--limit", type=int)
    args = parser.parse_args()

    validation = _validate(args.split)
    if not validation["valid"]:
        raise SystemExit("Suite validation failed:\n- " + "\n- ".join(validation["errors"]))
    suite = load_json(_suite_path(args.split))
    cases = _select_cases(args, suite)
    if args.dry_run:
        print(
            json.dumps(
                {
                    "phase": "phase-48",
                    "split": args.split,
                    "suite_version": suite["suite_version"],
                    "case_count": len(cases),
                    "category_counts": dict(sorted(Counter(case["category"] for case in cases).items())),
                    "prompt_version": PROMPT_VERSION,
                    "estimated_maximum_cost_usd": round(len(cases) * engine.MAX_ESTIMATED_CASE_COST_USD, 2),
                    "would_call_external_ai": False,
                    "diagnostic": args.diagnostic,
                },
                indent=2,
            )
        )
        return
    if not args.allow_external_ai:
        raise SystemExit(APPROVAL_MESSAGE)
    if args.budget_usd <= 0:
        raise SystemExit("--budget-usd must be positive")

    preflight = None
    if args.split == "holdout":
        if not args.frozen_runtime_commit:
            raise SystemExit("Fresh holdout execution requires --frozen-runtime-commit.")
        if HOLDOUT_RESULT_PATH.exists():
            raise SystemExit("The complete Phase 48 fresh-holdout artifact already exists; reruns are prohibited.")
        preflight = _preflight(args.frozen_runtime_commit)
        if not preflight["valid"]:
            raise SystemExit("Fresh holdout preflight failed:\n- " + "\n- ".join(preflight["errors"]))

    engine.DEFAULT_PROMPT_VERSION = PROMPT_VERSION
    settings = get_settings()
    started_at = _now()
    rows = engine._run_once(cases, budget_usd=args.budget_usd)
    completed_at = _now()
    summary = engine._summary(rows)

    if args.diagnostic:
        print(json.dumps({"diagnostic": True, **summary}, indent=2))
        return

    run_id = "phase48-generalization-development" if args.split == "development" else "phase48-independent-holdout-v2"
    suite_path = _suite_path(args.split)
    result = {
        "run_id": run_id,
        "run_name": f"Phase 48 Generalization {args.split.title()}",
        "phase": "phase-48",
        "split": args.split,
        "started_at": started_at,
        "completed_at": completed_at,
        "provenance": {
            "evaluation_commit": git_commit(),
            "frozen_runtime_commit": args.frozen_runtime_commit,
            "corpus_hash": tree_sha256(CORPUS_DIR),
            "suite_hash": file_sha256(suite_path),
            "original_phase47_holdout_hash": file_sha256(ROOT / "data/evaluation/independent-generalization/holdout-v1.json"),
            "model": settings.openai_chat_model,
            "embedding_model": settings.openai_embedding_model,
            "prompt_version": PROMPT_VERSION,
            "retrieval_profile": engine.DEFAULT_RETRIEVAL_MODE,
            "top_k": engine.DEFAULT_TOP_K,
            "rerank_candidate_limit": engine.DEFAULT_RERANK_CANDIDATE_LIMIT,
            "temperature": 0.0,
            "platform_telemetry_enabled": settings.proofbase_telemetry_enabled,
            "preflight": preflight,
        },
        "summary": summary,
        "rows": rows,
    }
    write_json_atomic(RESULTS_DIR / f"{run_id}.json", result)
    write_json_atomic(EVAL_RUNS_DIR / f"{run_id}.json", _eval_run(result))
    write_json_atomic(RESULTS_DIR / f"{run_id}-failures.json", engine._failure_matrix(result))
    report_path = PHASE_DOCS_DIR / f"{args.split}-results.md"
    report_path.parent.mkdir(parents=True, exist_ok=True)
    report_path.write_text(_report(result), encoding="utf-8")
    print(json.dumps({"run_id": run_id, **summary["metrics"], "passed_count": summary["passed_count"], "failed_count": summary["failed_count"]}, indent=2))


if __name__ == "__main__":
    main()
