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
from scripts.quality_completion_ledger import FOLDER, Ledger, audit, digest
from scripts.quality_eval_transport_v12 import BudgetStop
from scripts.reliable_evaluation_run import write_json_atomic

from scripts.quality_confirmation_reference_checks import check_references
AUTHORIZATION_PATH = FOLDER / "v14-authorization.json"
TEMPORAL_SUITE = FOLDER / "v14-temporal-development.json"
DIAGNOSTICS = ("omitted-required-condition", "not-found-with-unsupported-policy-claim",
               "supported-answer-without-citation", "permission-modality-upgraded",
               "hostile-instruction-only-rejected", "answer-injection-award-pass")


def modules(candidate):
    if candidate != "v14":
        raise ValueError("Only the explicitly authorized v14 correction is allowed")
    return (importlib.import_module("scripts.quality_eval_contract_v14"),
            importlib.import_module("scripts.quality_eval_transport_v14"))


def all_cases():
    temporal = json.loads(TEMPORAL_SUITE.read_bytes())
    if temporal["version"] != "temporal-development.v1" or len(temporal["cases"]) != 6:
        raise ValueError("Expected six declared temporal development controls")
    check_references(temporal)
    cases = baseline.load_suite()["cases"] + temporal["cases"]
    if len({c["id"] for c in cases}) != len(cases):
        raise ValueError("Duplicate development case ID")
    return {c["id"]:c for c in cases}


def plan(candidate, stage):
    contract, transport = modules(candidate)
    checked = baseline.preflight()
    if not checked["independently_checked"]:
        raise ValueError("Challenge validation failed")
    cases = baseline.load_suite()["cases"]
    if stage == "diagnostic":
        cases = [all_cases()[cid] for cid in DIAGNOSTICS] + json.loads(TEMPORAL_SUITE.read_bytes())["cases"]
    elif stage != "calibration":
        raise ValueError("Invalid stage")
    audits = baseline.load_audits()["cases"] if stage == "calibration" else []
    bound = sum((transport.case_bound(c["inputs"]) for c in cases), Decimal(0))
    bound += sum((transport.reserve(transport.review_request(c["inputs"], c["candidate"]))["reserved_usd"] for c in audits), Decimal(0))
    code = sorted(set((*baseline.CODE, "quality_completion_ledger.py", "quality_completion_eval.py", "quality_completion_eval_v14.py", "quality_eval_contract_v13.py", "report_quality_completion_v14.py", "report_quality_calibration_v12.py", "fresh_eval_grader.py", "reliable_evaluation_run.py", "quality_confirmation_reference_checks.py",
                       f"quality_eval_contract_{candidate}.py", f"quality_eval_transport_{candidate}.py")))
    return {"candidate": candidate, "stage": stage, "version": contract.VERSION,
            "model": transport.MODEL, "maximum_calls": len(cases)*3 + len(audits),
            "upper_bound_usd": str(bound), "reconciliation": audit(),
            "authorization_sha256": digest(AUTHORIZATION_PATH), "temporal_suite_sha256": digest(TEMPORAL_SUITE), "suite_sha256": digest(baseline.SUITE), "validation_sha256": digest(baseline.VALIDATION),
            "audit_sha256": digest(baseline.AUDITS), "code_sha256": {n:digest(ROOT/"scripts"/n) for n in code},
            "cases": [{"id":c["id"], "expected":c["expected"]} for c in cases],
            "audit_ids": [c["id"] for c in audits], "semantic_validation_passed": False}


def gate(candidate, stage, folder=FOLDER):
    if (folder / f"{candidate}-{stage}").exists():
        raise BudgetStop("Stage already attempted; no retry or overwrite")
    if stage == "calibration":
        diagnostic = json.loads((folder/f"{candidate}-diagnostic/manifest.json").read_bytes())
        if diagnostic["status"] != "complete" or diagnostic["matched"] != 12:
            raise BudgetStop("Diagnostic did not pass")
        current = plan(candidate, "diagnostic")
        if diagnostic["plan"] != current:
            raise BudgetStop("Candidate changed since diagnostic")
    approval = json.loads(AUTHORIZATION_PATH.read_bytes())
    if approval.get("candidate") != "v14" or approval.get("candidate_attempts") != 1:
        raise BudgetStop("Explicit single-correction authorization required")
    prior = folder / approval["prior_manifest"]
    if (not prior.resolve().is_relative_to(folder.resolve()) or digest(prior) != approval["prior_manifest_sha256"]
        or approval["temporal_suite_sha256"] != digest(TEMPORAL_SUITE)):
        raise BudgetStop("Prior failed evidence changed")


def execute(candidate, stage, create, ledger, folder=FOLDER):
    if candidate != "v14":
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
            mismatch = baseline.compare(case, grade, result)
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
            for case in baseline.load_audits()["cases"] if stage == "calibration" else []:
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
    parser.add_argument("--candidate", choices=["v14"], default="v14")
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
