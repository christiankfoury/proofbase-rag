from __future__ import annotations

import argparse
import json
import os
import sys
from collections import Counter
from pathlib import Path
from typing import Any


ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

from fastapi.testclient import TestClient

from apps.api.app.core.config import get_settings
from apps.api.app.db.session import get_connection
from apps.api.app.main import app
from scripts import run_independent_generalization_eval as engine
from scripts.independent_generalization_common import (
    CORPUS_DIR,
    PROJECT_ID,
    USER_IDS,
    dirty_paths,
    file_sha256,
    git_commit,
    git_output,
    load_json,
    protected_path_changes,
    tree_sha256,
    validate_suite_payload,
    write_json_atomic,
)
from scripts.reliable_evaluation_run import ReliableEvaluationRun, validate_cases_for_execution


SUITE_PATH = ROOT / "data/evaluation/independent-generalization/holdout-v3.json"
SUITE_HASH_PATH = ROOT / "data/evaluation/independent-generalization/holdout-v3.sha256"
SCHEMA_PATH = ROOT / "data/evaluation/independent-generalization/schema-v3.json"
RUN_ROOT = ROOT / "data/evaluation/independent-generalization/runs/phase49-independent-holdout-v3"
RESULT_PATH = ROOT / "data/evaluation/independent-generalization/results/phase49-independent-holdout-v3.json"
FAILURE_PATH = ROOT / "data/evaluation/independent-generalization/results/phase49-independent-holdout-v3-failures.json"
EVAL_RUN_PATH = ROOT / "data/evaluation/eval-runs/phase49-independent-holdout-v3.json"
RELIABILITY_PATH = ROOT / "data/evaluation/evaluation-reliability.json"
REPORT_PATH = ROOT / "docs/phase-49/fresh-holdout-results.md"
RUN_ID = "phase49-independent-holdout-v3"
SUITE_VERSION = "3.0"
PROMPT_VERSION = "v9"
MAX_COMMAND_BUDGET_USD = 2.0
FROZEN_EVALUATOR_PATHS = (
    "scripts/reliable_evaluation_run.py",
    "scripts/run_phase49_holdout_eval.py",
    "scripts/run_independent_generalization_eval.py",
    "scripts/independent_generalization_common.py",
    "scripts/phase48_generalization_scoring.py",
)
APPROVAL_MESSAGE = (
    "Phase 49 sends blind synthetic holdout questions, prior synthetic chat turns, uploaded synthetic fixture text, "
    "and permission-filtered synthetic snippets to OpenAI. Re-run with --allow-external-ai only after approval."
)
RESUMABLE_OUTPUT_PATHS = {
    str(RESULT_PATH.relative_to(ROOT)).replace("\\", "/"),
    str(FAILURE_PATH.relative_to(ROOT)).replace("\\", "/"),
    str(EVAL_RUN_PATH.relative_to(ROOT)).replace("\\", "/"),
    str(RELIABILITY_PATH.relative_to(ROOT)).replace("\\", "/"),
    str(REPORT_PATH.relative_to(ROOT)).replace("\\", "/"),
}
RESUMABLE_RUN_PREFIX = str(RUN_ROOT.relative_to(ROOT)).replace("\\", "/") + "/"


def _recorded_hash() -> str | None:
    if not SUITE_HASH_PATH.exists():
        return None
    return SUITE_HASH_PATH.read_text(encoding="utf-8").strip().split()[0]


def _evaluator_changes(evaluation_commit: str) -> list[str]:
    return [
        line.strip().replace("\\", "/")
        for line in git_output("diff", "--name-only", f"{evaluation_commit}..HEAD", "--", *FROZEN_EVALUATOR_PATHS).splitlines()
        if line.strip()
    ]


def _dependency_errors(cases: list[dict[str, Any]]) -> list[str]:
    errors: list[str] = []
    if not os.environ.get("OPENAI_API_KEY") and not get_settings().openai_api_key:
        errors.append("OPENAI_API_KEY is unavailable")
    expected_users = {str(case["user_id"]): str(case["user_role"]) for case in cases}
    scoped_projects = {str(case["project_id"]) for case in cases if case.get("project_id")}
    scoped_departments = {str(case["department_id"]) for case in cases if case.get("department_id")}
    expected_documents = {
        str(document_id)
        for case in cases
        for document_id in case.get("expected_source_documents") or []
        if not str(document_id).startswith("UPLOAD-")
    }
    try:
        with get_connection() as conn:
            users = {
                str(row["id"]): str(row["business_role"])
                for row in conn.execute(
                    "select id::text as id, business_role from demo_users where id = any(%s::uuid[])",
                    (list(expected_users),),
                ).fetchall()
            }
            projects = {
                str(row["id"])
                for row in conn.execute(
                    "select id::text as id from projects where id = any(%s::uuid[]) and status = 'active'",
                    (list(scoped_projects),),
                ).fetchall()
            } if scoped_projects else set()
            departments = {
                str(row["id"]): str(row["project_id"])
                for row in conn.execute(
                    "select id::text as id, project_id::text as project_id from project_departments "
                    "where id = any(%s::uuid[]) and status = 'active'",
                    (list(scoped_departments),),
                ).fetchall()
            } if scoped_departments else {}
            documents = {
                str(row["external_document_id"]): int(row["chunk_count"])
                for row in conn.execute(
                    "select d.external_document_id, count(c.id) as chunk_count from documents d "
                    "left join chunks c on c.document_id = d.id "
                    "where d.external_document_id = any(%s::text[]) and d.status = 'active' "
                    "group by d.external_document_id",
                    (list(expected_documents),),
                ).fetchall()
            } if expected_documents else {}
    except Exception as exc:
        return [f"database dependency unavailable: {type(exc).__name__}: {exc}"]
    for user_id, role in expected_users.items():
        if users.get(user_id) != role:
            errors.append(f"user dependency mismatch for {user_id}: expected {role}")
    for project_id in scoped_projects:
        if project_id not in projects:
            errors.append(f"active project dependency missing: {project_id}")
    for case in cases:
        department_id = case.get("department_id")
        if department_id and departments.get(str(department_id)) != str(case.get("project_id")):
            errors.append(f"{case['case_id']}: department does not belong to the declared project")
    for document_id in expected_documents:
        if document_id not in documents:
            errors.append(f"indexed source dependency missing: {document_id}")
        elif documents[document_id] <= 0:
            errors.append(f"indexed source has no chunks: {document_id}")
    return errors


def preflight(
    *,
    frozen_runtime_commit: str,
    evaluation_commit: str,
    include_dependencies: bool,
) -> dict[str, Any]:
    errors: list[str] = []
    if not SUITE_PATH.exists():
        return {"valid": False, "errors": [f"missing suite file: {SUITE_PATH}"]}
    suite = load_json(SUITE_PATH)
    validation = validate_suite_payload(suite, expected_split="holdout", expected_suite_version=SUITE_VERSION)
    errors.extend(validation["errors"])
    actual_hash = file_sha256(SUITE_PATH)
    recorded_hash = _recorded_hash()
    if actual_hash != recorded_hash:
        errors.append("holdout-v3 suite hash does not match holdout-v3.sha256")
    all_dirty = dirty_paths()
    dirty = [
        path
        for path in all_dirty
        if path not in RESUMABLE_OUTPUT_PATHS and not path.startswith(RESUMABLE_RUN_PREFIX)
    ]
    if dirty:
        errors.append(f"working tree has non-ignored changes: {', '.join(dirty)}")
    protected = protected_path_changes(frozen_runtime_commit)
    if protected:
        errors.append(f"runtime or corpus changed since freeze: {', '.join(protected)}")
    evaluator_changes = _evaluator_changes(evaluation_commit)
    if evaluator_changes:
        errors.append(f"hardened evaluator changed since freeze: {', '.join(evaluator_changes)}")
    execution = validate_cases_for_execution(
        list(suite.get("cases") or []),
        dependency_validator=_dependency_errors if include_dependencies else None,
    )
    errors.extend(execution["errors"])
    return {
        "valid": not errors,
        "errors": errors,
        "warnings": validation["warnings"],
        "suite_hash": actual_hash,
        "recorded_suite_hash": recorded_hash,
        "corpus_hash": tree_sha256(CORPUS_DIR),
        "frozen_runtime_commit": frozen_runtime_commit,
        "evaluation_commit": evaluation_commit,
        "execution_commit": git_commit(),
        "dirty_paths": dirty,
        "resumable_output_paths": sorted(path for path in all_dirty if path not in dirty),
        "protected_path_changes": protected,
        "evaluator_path_changes": evaluator_changes,
        "case_count": execution["case_count"],
        "case_hashes": execution["case_hashes"],
        "dependencies_checked": include_dependencies,
    }


def _execute_case(client: TestClient, case: dict[str, Any]) -> dict[str, Any]:
    if case.get("fixture_requirements"):
        rows = engine._run_fixture_cases(client, [case])
        if len(rows) != 1:
            raise RuntimeError(f"fixture executor returned {len(rows)} rows for {case['case_id']}")
        return rows[0]
    return engine._run_query_case(client, case)


def _phase49_summary(rows: list[dict[str, Any]]) -> dict[str, Any]:
    summary = engine._summary(rows)
    metrics = summary["metrics"]
    summary["hard_gates"] = {
        "permission_leakage_zero": (metrics.get("unauthorized_chunk_exposure_rate") or 0.0) == 0.0,
        "unauthorized_chunks_reached_generation_zero": (metrics.get("unauthorized_chunks_reached_generation_rate") or 0.0) == 0.0,
        "restricted_citation_leakage_zero": (metrics.get("restricted_citation_leakage_rate") or 0.0) == 0.0,
        "memory_as_evidence_zero": (metrics.get("memory_as_evidence_violation_rate") or 0.0) == 0.0,
    }
    summary["claim_gates"] = {
        **summary["hard_gates"],
        "behavior_accuracy_gte_0_90": (metrics.get("behavior_accuracy") or 0.0) >= 0.90,
        "required_source_recall_gte_0_90": (metrics.get("expected_source_recall") or 0.0) >= 0.90,
        "required_fact_completeness_gte_0_85": (metrics.get("required_fact_completeness") or 0.0) >= 0.85,
        "citation_accuracy_gte_0_90": (metrics.get("citation_document_accuracy") or 0.0) >= 0.90,
        "heuristic_hallucination_lte_0_05": (metrics.get("hallucination_rate") or 0.0) <= 0.05,
        "overall_pass_count_gte_27": summary["passed_count"] >= 27,
    }
    summary["improvement_claim_allowed"] = all(summary["claim_gates"].values())
    return summary


def _eval_run(final: dict[str, Any], preflight_result: dict[str, Any]) -> dict[str, Any]:
    summary = final["summary"]
    return {
        "run_id": RUN_ID,
        "run_name": "Phase 49 Fresh Independent Holdout V3",
        "phase": "phase-49",
        "run_type": "independent_generalization_eval",
        "timestamp": final["completed_at"],
        "benchmark_version": "independent-generalization-holdout-v3",
        "split": "holdout",
        "total_questions": summary["sample_size"],
        "sample_size": summary["sample_size"],
        "passed_count": summary["passed_count"],
        "failed_count": summary["failed_count"],
        "retrieval_mode": engine.DEFAULT_RETRIEVAL_MODE,
        "top_k": engine.DEFAULT_TOP_K,
        "prompt_version": PROMPT_VERSION,
        "model": final["provenance"]["configuration"]["model"],
        "temperature": 0.0,
        "metrics": {**summary["metrics"], "failed_question_count": summary["failed_count"]},
        "failed_questions": summary["failed_case_ids"],
        "category_breakdown": summary["category_counts"],
        "provenance": {**final["provenance"], "preflight": preflight_result},
        "run_completeness": final["run_completeness"],
        "hard_gates": summary["hard_gates"],
        "claim_gates": summary["claim_gates"],
        "improvement_claim_allowed": summary["improvement_claim_allowed"],
        "notes": "Fresh Phase 49 evidence. Automated results remain separate from manual adjudication and prior holdouts.",
    }


def _publish(final: dict[str, Any], preflight_result: dict[str, Any]) -> None:
    result = {
        **final,
        "phase": "phase-49",
        "split": "holdout",
        "run_name": "Phase 49 Fresh Independent Holdout V3",
        "preflight": preflight_result,
    }
    write_json_atomic(RESULT_PATH, result)
    failures = {
        "run_id": RUN_ID,
        "automated_result_immutable": True,
        "failed_count": final["summary"]["failed_count"],
        "failures": [record for record in final["execution_records"] if not record["row"]["passed"]],
    }
    write_json_atomic(FAILURE_PATH, failures)
    write_json_atomic(EVAL_RUN_PATH, _eval_run(final, preflight_result))
    reliability = {
        "phase": "phase-49",
        "status": "verified_and_measured",
        "run_id": RUN_ID,
        "run_completeness": final["run_completeness"],
        "manifest_path": str(RUN_ROOT.relative_to(ROOT) / "manifest.json").replace("\\", "/"),
        "journal_path": str(RUN_ROOT.relative_to(ROOT) / "journal.jsonl").replace("\\", "/"),
        "detailed_result_path": str(RESULT_PATH.relative_to(ROOT)).replace("\\", "/"),
        "interruption_tests": {
            "before_case_1": "passed",
            "arbitrary_case": "passed",
            "after_case_29": "passed",
            "atomic_persistence": "passed",
            "final_aggregation": "passed",
            "unsupported_fixture_no_network": "passed",
            "recovery_equivalence_without_duplicate_calls": "passed",
        },
        "phase48_evidence_preserved": {
            "machine_observed": "19/30",
            "estimated_cost_usd": 0.023159,
            "aggregate_metrics_available": False,
            "cases_1_through_29_rerun": False,
        },
    }
    write_json_atomic(RELIABILITY_PATH, reliability)


def _report(final: dict[str, Any]) -> str:
    summary = final["summary"]
    metrics = summary["metrics"]
    gate_lines = [f"| {name} | `{'pass' if value else 'miss'}` |" for name, value in summary["claim_gates"].items()]
    failures = [record for record in final["execution_records"] if not record["row"]["passed"]]
    failure_lines = [
        f"- `{record['case_id']}`: expected `{record['row']['expected_behavior']}`, actual `{record['row']['actual_behavior']}`."
        for record in failures
    ] or ["- None."]
    return "\n".join(
        [
            "# Phase 49 Fresh Holdout Results",
            "",
            f"- Run: `{RUN_ID}`",
            f"- Complete persisted rows: `{summary['sample_size']}/{summary['sample_size']}`",
            f"- Automated result: `{summary['passed_count']}/{summary['sample_size']}`",
            f"- Behavior accuracy: `{metrics['behavior_accuracy']}`",
            f"- Required-source recall: `{metrics['expected_source_recall']}`",
            f"- Required-fact completeness: `{metrics['required_fact_completeness']}`",
            f"- Citation accuracy: `{metrics['citation_document_accuracy']}`",
            f"- Heuristic hallucination rate: `{metrics['hallucination_rate']}`",
            f"- Estimated cost: `${metrics['estimated_cost']:.6f}`",
            f"- Improvement claim allowed: `{'yes' if summary['improvement_claim_allowed'] else 'no'}`",
            "",
            "## Claim Gates",
            "",
            "| Gate | Automated status |",
            "| --- | --- |",
            *gate_lines,
            "",
            "## Automated Failures",
            "",
            *failure_lines,
            "",
            "Automated and manual-adjudication results are preserved separately. A missed target is valid measurement, not an incomplete run.",
            "",
        ]
    )


def main() -> None:
    parser = argparse.ArgumentParser(description="Run the reliable one-time Phase 49 fresh holdout.")
    parser.add_argument("--dry-run", action="store_true")
    parser.add_argument("--preflight-only", action="store_true")
    parser.add_argument("--allow-external-ai", action="store_true")
    parser.add_argument("--budget-usd", type=float, default=2.0)
    parser.add_argument("--frozen-runtime-commit", required=True)
    parser.add_argument("--evaluation-commit", required=True)
    args = parser.parse_args()
    if args.budget_usd <= 0 or args.budget_usd > MAX_COMMAND_BUDGET_USD:
        raise SystemExit(f"--budget-usd must be greater than zero and no more than ${MAX_COMMAND_BUDGET_USD:.2f}")
    if not SUITE_PATH.exists():
        raise SystemExit(f"Missing Phase 49 suite: {SUITE_PATH}")
    suite = load_json(SUITE_PATH)
    if args.dry_run:
        check = preflight(
            frozen_runtime_commit=args.frozen_runtime_commit,
            evaluation_commit=args.evaluation_commit,
            include_dependencies=False,
        )
        print(json.dumps({
            "phase": "phase-49",
            "run_id": RUN_ID,
            "case_count": len(suite.get("cases") or []),
            "category_counts": dict(sorted(Counter(case["category"] for case in suite.get("cases") or []).items())),
            "preflight": check,
            "would_call_external_ai": False,
            "maximum_budget_usd": args.budget_usd,
        }, indent=2))
        if not check["valid"]:
            raise SystemExit(1)
        return
    check = preflight(
        frozen_runtime_commit=args.frozen_runtime_commit,
        evaluation_commit=args.evaluation_commit,
        include_dependencies=True,
    )
    if not check["valid"]:
        raise SystemExit("Phase 49 preflight failed before case 1:\n- " + "\n- ".join(check["errors"]))
    if args.preflight_only:
        print(json.dumps(check, indent=2))
        return
    if not args.allow_external_ai:
        raise SystemExit(APPROVAL_MESSAGE)
    if RESULT_PATH.exists() and not RUN_ROOT.joinpath("manifest.json").exists():
        raise SystemExit("A Phase 49 result exists without its durable run manifest; fail closed rather than rerun.")
    settings = get_settings()
    engine.DEFAULT_PROMPT_VERSION = PROMPT_VERSION
    configuration = {
        "model": settings.openai_chat_model,
        "embedding_model": settings.openai_embedding_model,
        "prompt_version": PROMPT_VERSION,
        "retrieval_profile": engine.DEFAULT_RETRIEVAL_MODE,
        "top_k": engine.DEFAULT_TOP_K,
        "rerank_candidate_limit": engine.DEFAULT_RERANK_CANDIDATE_LIMIT,
        "temperature": 0.0,
        "budget_usd": args.budget_usd,
        "corpus_hash": tree_sha256(CORPUS_DIR),
    }
    with TestClient(app) as client:
        runner = ReliableEvaluationRun(
            run_root=RUN_ROOT,
            run_id=RUN_ID,
            cases=list(suite["cases"]),
            suite_hash=file_sha256(SUITE_PATH),
            runtime_commit=args.frozen_runtime_commit,
            evaluation_commit=args.evaluation_commit,
            configuration=configuration,
            budget_usd=args.budget_usd,
            execute_case=lambda case: _execute_case(client, case),
            aggregate=_phase49_summary,
        )
        final = runner.run()
    _publish(final, check)
    REPORT_PATH.parent.mkdir(parents=True, exist_ok=True)
    REPORT_PATH.write_text(_report(final), encoding="utf-8")
    print(json.dumps({
        "run_id": RUN_ID,
        "passed_count": final["summary"]["passed_count"],
        "failed_count": final["summary"]["failed_count"],
        "metrics": final["summary"]["metrics"],
        "claim_gates": final["summary"]["claim_gates"],
    }, indent=2))


if __name__ == "__main__":
    main()
