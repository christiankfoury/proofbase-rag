"""Bounded Phase 71 diagnostic/calibration workflow; dry-run unless explicitly enabled."""
import argparse
from decimal import Decimal
import importlib
import json
from pathlib import Path
import sys

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))
from scripts import quality_eval_calibration_v12 as baseline
from scripts.quality_completion_ledger import FOLDER, audit, digest
from scripts.quality_eval_transport_v12 import BudgetStop
from scripts.quality_completion_durable import Ledger, write_json_atomic

from scripts.quality_confirmation_reference_checks import check_references
from scripts import quality_completion_eval_v15 as previous
AUTHORIZATION_PATH = FOLDER / "autonomous-authorization.json"
DECLARATION = FOLDER / "v16-candidate-plan.json"
CONTROLS = FOLDER / "v16-agency-development.json"
TEMPORAL_SUITE = previous.TEMPORAL_SUITE
DIAGNOSTICS = ("omitted-required-condition", "not-found-with-unsupported-policy-claim",
               "supported-answer-without-citation", "permission-modality-upgraded",
               "hostile-instruction-only-rejected", "answer-injection-award-pass")


def modules(candidate):
    if candidate != "v16":
        raise ValueError("Only the explicitly authorized v16 correction is allowed")
    return (importlib.import_module("scripts.quality_eval_contract_v16"),
            importlib.import_module("scripts.quality_eval_transport_v16"))


def controls():
    value = json.loads(CONTROLS.read_bytes())
    if value["version"] != "agency-development.v1" or len(value["cases"]) != 4 or len(value["review_probes"]) != 1:
        raise ValueError("Expected four agency controls and one semantic reviewer probe")
    check_references(value)
    return value


def all_cases():
    cases = list(previous.all_cases().values()) + controls()["cases"]
    if len({c["id"] for c in cases}) != len(cases):
        raise ValueError("Duplicate development case ID")
    return {c["id"]:c for c in cases}


def audits(stage):
    return baseline.load_audits()["cases"] if stage == "calibration" else previous.controls()["review_probes"] + controls()["review_probes"]


def compare(case, grade, result):
    mismatch = previous.compare(case, grade, result)
    expected = controls()["fact_status_expectations"].get(case["id"])
    if expected is not None:
        actual = {f["fact_id"]:f["status"] for f in grade["facts"]} if grade else {}
        if actual != expected:
            mismatch["fact_statuses"] = {"expected":expected,"actual":actual}
    return mismatch


def plan(candidate, stage):
    contract, transport = modules(candidate)
    checked = baseline.preflight()
    if not checked["independently_checked"]:
        raise ValueError("Challenge validation failed")
    cases = baseline.load_suite()["cases"]
    if stage == "diagnostic":
        cases = controls()["cases"] + [all_cases()[cid] for cid in (*DIAGNOSTICS, "true-answer-wrong-topic")] + json.loads(TEMPORAL_SUITE.read_bytes())["cases"] + previous.controls()["cases"]
    elif stage != "calibration":
        raise ValueError("Invalid stage")
    review_cases = audits(stage)
    bound = sum((transport.case_bound(c["inputs"]) for c in cases), Decimal(0))
    bound += sum((transport.reserve(transport.review_request(c["inputs"], c["candidate"]))["reserved_usd"] for c in review_cases), Decimal(0))
    code = sorted(set((*previous.plan("v15", "diagnostic")["code_sha256"], "quality_completion_durable.py", "quality_completion_ledger.py", "quality_completion_eval.py", "quality_completion_eval_v16.py", "quality_eval_contract_v13.py", "report_quality_completion_v16.py", "report_quality_calibration_v12.py", "fresh_eval_grader.py", "reliable_evaluation_run.py", "quality_confirmation_reference_checks.py",
                       f"quality_eval_contract_{candidate}.py", f"quality_eval_transport_{candidate}.py")))
    return {"candidate": candidate, "stage": stage, "version": contract.VERSION,
            "model": transport.MODEL, "maximum_calls": len(cases)*3 + len(review_cases),
            "upper_bound_usd": str(bound), "reconciliation": audit(),
            "authorization_sha256": digest(AUTHORIZATION_PATH), "declaration_sha256": digest(DECLARATION), "controls_sha256": digest(CONTROLS), "coverage_controls_sha256": digest(previous.CONTROLS), "temporal_suite_sha256": digest(TEMPORAL_SUITE), "suite_sha256": digest(baseline.SUITE), "validation_sha256": digest(baseline.VALIDATION),
            "audit_sha256": digest(baseline.AUDITS), "code_sha256": {n:digest(ROOT/"scripts"/n) for n in code},
            "cases": [{"id":c["id"], "expected":c["expected"]} for c in cases],
            "audit_ids": [c["id"] for c in review_cases], "semantic_validation_passed": False}


def gate(candidate, stage, folder=FOLDER):
    if (folder / f"{candidate}-{stage}").exists():
        raise BudgetStop("Stage already attempted; no retry or overwrite")
    if stage == "calibration":
        diagnostic = json.loads((folder/f"{candidate}-diagnostic/manifest.json").read_bytes())
        if diagnostic["status"] != "complete" or diagnostic["matched"] != 21 or len(diagnostic["review_rows"]) != 2 or not all(r["exact_match"] for r in diagnostic["review_rows"].values()):
            raise BudgetStop("Diagnostic did not pass")
        current = plan(candidate, "diagnostic")
        if diagnostic["plan"] != current:
            raise BudgetStop("Candidate changed since diagnostic")
    approval = json.loads(AUTHORIZATION_PATH.read_bytes())
    declaration = json.loads(DECLARATION.read_bytes())
    if not approval.get("successive_evaluator_repairs_authorized") or not approval.get("unchanged_scoring_and_readiness_gates"):
        raise BudgetStop("Standing authorization missing")
    if (declaration["candidate"] != "v16" or declaration["single_execution_per_stage"] is not True
        or declaration["standing_authorization_sha256"] != digest(AUTHORIZATION_PATH)
        or declaration["prior_readiness_sha256"] != digest(FOLDER/"confirmation-v15-readiness.json")
        or declaration["controls_sha256"] != digest(CONTROLS)):
        raise BudgetStop("Candidate declaration or prior evidence changed")


def execute(candidate, stage, create, ledger, folder=FOLDER):
    if candidate != "v16":
        raise BudgetStop("Runner is restricted to the authorized correction")
    gate(candidate, stage, folder)
    preflight = plan(candidate, stage)
    contract, transport = modules(candidate)
    out = folder / f"{candidate}-{stage}"
    out.mkdir()
    (out/"code").mkdir()
    for name in preflight["code_sha256"]:
        (out/"code"/name).write_bytes((ROOT/"scripts"/name).read_bytes())
    manifest = {"status":"running", "plan":preflight, "completed":0, "matched":0,
                "rows":{}, "review_rows":{}, "semantic_validation_passed":False, "human_adjudication":False}
    write_json_atomic(out/"manifest.json", manifest)
    ledger.begin_stage(f"{candidate}-{stage}", preflight["maximum_calls"], Decimal(preflight["upper_bound_usd"]))
    try:
        cases = all_cases()
        for item in preflight["cases"]:
            case = cases[item["id"]]
            grade, review, error = None, None, None
            try:
                grade, review = transport.grade_case(create, case["inputs"], ledger, out/case["id"])
            except (ValueError, IndexError) as exc:
                error = type(exc).__name__
            result = contract.dimensions(case["inputs"], grade, case["payload"], case["evidence"], case["safety_flags"], review)
            mismatch = compare(case, grade, result)
            matched = not mismatch and not result["grader_errors"] and not result["disputed_dimensions"]
            path = out/(case["id"]+".json")
            write_json_atomic(path, {"case_id":case["id"], "grade":grade, "review":review, "dimensions":result,
                                     "mismatches":mismatch, "grading_error":error, "matched":matched})
            manifest["rows"][case["id"]] = digest(path)
            manifest["completed"] += 1
            manifest["matched"] += int(matched)
            write_json_atomic(out/"manifest.json", manifest)
            print(f"{candidate}/{stage}/{case['id']}: {'matches' if matched else 'disagreement'}; cumulative USD {ledger.spent}", flush=True)
            if stage == "diagnostic" and not matched:
                manifest["status"] = "early_stopped"
                break
        else:
            for case in audits(stage):
                body = transport.review_request(case["inputs"], case["candidate"])
                review, error = None, None
                try:
                    review = transport.parsed(ledger.call(create, body, out/(case["id"]+"-raw.json")), contract.review_schema())
                except (ValueError, IndexError) as exc:
                    error = type(exc).__name__
                exact = bool(review and all(review[k] == ("dispute" if k in case["expected_disputes"] else "agree")
                                           for k in (*contract.DIMENSIONS, "forbidden_assertion")))
                path = out/(case["id"]+"-review.json")
                write_json_atomic(path, {"review":review, "exact_match":exact, "grading_error":error})
                manifest["review_rows"][case["id"]] = {"sha256":digest(path), "exact_match":exact}
            manifest["status"] = "complete"
        ledger.finish_stage()
    except BaseException as exc:
        manifest.update(status="interrupted", exception_type=type(exc).__name__)
        raise
    finally:
        manifest["cumulative_cost_usd"] = str(ledger.spent)
        write_json_atomic(out/"api-ledger.json", ledger.data)
        write_json_atomic(out/"manifest.json", manifest)
    return manifest


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--candidate", choices=["v16"], default="v16")
    parser.add_argument("--stage", choices=["diagnostic", "calibration"], default="diagnostic")
    parser.add_argument("--allow-external-ai", action="store_true")
    args = parser.parse_args()
    preflight = plan(args.candidate, args.stage)
    if not args.allow_external_ai:
        print(json.dumps(preflight, indent=2))
        return
    gate(args.candidate, args.stage)
    from apps.api.app.core.config import get_settings
    from openai import OpenAI
    key = get_settings().openai_api_key
    if not key:
        raise ValueError("Configured credential unavailable")
    path = FOLDER/"api-ledger.json"
    ledger = Ledger(path) if path.exists() else Ledger.initialize(path)
    client = OpenAI(api_key=key, max_retries=0, timeout=60)
    execute(args.candidate, args.stage, client.chat.completions.create, ledger)


if __name__ == "__main__":
    main()
