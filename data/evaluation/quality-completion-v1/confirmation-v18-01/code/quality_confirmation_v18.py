"""One-shot separate-context confirmation of the frozen evaluator; no app calls."""
import argparse
from decimal import Decimal
import json
from pathlib import Path
import re
import sys

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0,str(ROOT))
from scripts import quality_eval_calibration_v12 as calibration
from scripts.quality_eval_contract_v18 import VERSION, BEHAVIORS, DIMENSIONS, dimensions
from scripts.quality_eval_transport_v18 import MODEL, case_bound, grade_case
from scripts.quality_completion_ledger import FOLDER, AUTHORIZATION
from scripts.quality_completion_durable import Ledger
from scripts.quality_completion_durable import write_json_atomic

SUITE = FOLDER / "confirmation-challenges-v7.json"
VALIDATION = FOLDER / "confirmation-validation-v7.json"
GATE = FOLDER / "calibration-v18-readiness.json"
from scripts import quality_completion_confirmation_v13 as original
from scripts.quality_confirmation_fact_checks import check_fact_references
from scripts.quality_completion_eval_v18 import plan as development_plan
CODE = tuple(sorted(set((*original.CODE, *development_plan("v18", "diagnostic")["code_sha256"], "quality_confirmation_fact_checks.py", "quality_confirmation_v18.py", "report_quality_confirmation_v18.py"))))
digest = calibration.digest

def compare(case, grade, result):
    mismatch = calibration.compare(case, grade, result)
    actual = {f["fact_id"]:f["status"] for f in grade["facts"]} if grade else {}
    if actual != case["expected_fact_statuses"]:
        mismatch["fact_statuses"] = {"expected":case["expected_fact_statuses"], "actual":actual}
    return mismatch

def readiness():
    from scripts.report_quality_completion_v18 import replay
    diagnostic, report = replay("v18", "diagnostic"), replay("v18", "calibration")
    if (diagnostic["matching_judgments"] != 29 or diagnostic["exact_review_probes"] != 4
        or report["matching_judgments"] != 24 or report["exact_review_probes"] != 3
        or any(r["grader_errors"] or r["disputed_dimensions"] for r in diagnostic["rows"] + report["rows"])):
        raise ValueError("Development calibration has unresolved disagreements")
    gate = json.loads(GATE.read_bytes())
    review = ROOT / "docs/phase-71/confirmation-v18-development-source-review.md"
    if (gate.get("status") != "approved" or gate.get("human_adjudication") is not False
        or gate.get("diagnostic_report_sha256") != digest(FOLDER / "v18-diagnostic-report.json")
        or gate.get("report_sha256") != digest(FOLDER / "v18-calibration-report.json")
        or gate.get("source_review_sha256") != digest(review)
        or gate.get("unresolved_semantic_findings") != 0
        or gate.get("code_sha256") != {name:digest(ROOT/"scripts"/name) for name in CODE}):
        raise ValueError("Source inspection readiness missing or invalid")
    return digest(GATE)

FREEZE = FOLDER / "v18-freeze.json"
SEAL = FOLDER / "v18-seal.json"
APPROVAL = FOLDER / "autonomous-authorization.json"


def load_suite():
    suite = original.load_suite(SUITE)
    check_fact_references(suite)
    return suite


def preflight(ledger):
    freeze_path = FREEZE
    freeze = json.loads(freeze_path.read_bytes())
    if (freeze.get("readiness_sha256") != digest(GATE)
        or freeze.get("code_sha256") != {name:digest(ROOT/"scripts"/name) for name in CODE}):
        raise ValueError("Evaluator freeze changed")
    approval = json.loads(APPROVAL.read_bytes())
    if (not approval.get("successive_evaluator_repairs_authorized") or not approval.get("fresh_post_freeze_holdouts_only")
        or freeze.get("authorization_sha256") != digest(APPROVAL)):
        raise ValueError("Standing authorization changed")
    for name, expected in freeze["briefs_sha256"].items():
        path = (ROOT / name).resolve()
        if not path.is_relative_to(ROOT) or digest(path) != expected:
            raise ValueError("Authoring specification changed")
    seal = json.loads(SEAL.read_bytes())
    for name, expected in seal["files_sha256"].items():
        path = (ROOT / name).resolve()
        if not path.is_relative_to(ROOT) or digest(path) != expected:
            raise ValueError("Confirmation seal changed")
    required = [FREEZE, APPROVAL, SUITE, VALIDATION]
    if not all(str(p.relative_to(ROOT)).replace("\\", "/") in seal["files_sha256"] for p in required):
        raise ValueError("Confirmation seal incomplete")
    suite = load_suite()
    if suite.get("authored_after_freeze") != freeze.get("commit") or not freeze.get("commit"):
        raise ValueError("Confirmation was not authored after the selected freeze")
    validation = json.loads(VALIDATION.read_bytes())
    reviews = validation.get("case_reviews", [])
    if (validation.get("status") != "approved" or validation.get("suite_sha256") != digest(SUITE)
        or validation.get("freeze_sha256") != digest(freeze_path)
        or validation.get("case_count") != 16 or validation.get("human_adjudication") is not False
        or validation.get("unresolved_findings") != []
        or len(reviews) != 16 or {r["id"] for r in reviews} != {c["id"] for c in suite["cases"]}
        or not all(r.get("accept") is True for r in reviews)
        or {r["id"]:r.get("independently_derived_expected") for r in reviews} != {c["id"]:c["expected"] for c in suite["cases"]}
        or {r["id"]:r.get("independently_derived_fact_statuses") for r in reviews} != {c["id"]:c["expected_fact_statuses"] for c in suite["cases"]}):
        raise ValueError("Independent confirmation expectation validation failed")
    bounds = [{"id":case["id"], "upper_bound_usd":str(case_bound(case["inputs"]))} for case in suite["cases"]]
    bound = sum((Decimal(row["upper_bound_usd"]) for row in bounds),Decimal(0))
    return {"version":VERSION,"model":MODEL,"case_count":16,"suite_sha256":digest(SUITE),
            "seal_sha256":digest(SEAL),"authorization_sha256":digest(APPROVAL),"validation_sha256":digest(VALIDATION),"freeze_sha256":digest(freeze_path),"upper_bound_usd":str(bound),
            "authorization":AUTHORIZATION,"maximum_calls":48,
            "code_sha256":{name:digest(ROOT/"scripts"/name) for name in CODE},"cases":bounds}


def execute(create, ledger):
    attempt = "confirmation-v18-01"  # Single authorized path; no retry-name override.
    gate_hash = readiness()
    plan = preflight(ledger)
    plan["readiness_sha256"] = gate_hash
    if not re.fullmatch(r"[a-zA-Z0-9_-]{1,60}",attempt):
        raise ValueError("Unsafe attempt name")
    out = FOLDER/attempt
    out.mkdir()
    (out/"code").mkdir()
    for name in CODE:
        (out/"code"/name).write_bytes((ROOT/"scripts"/name).read_bytes())
    manifest={"status":"running","plan":plan,"completed":0,"matched":0,"rows":{},
              "semantic_validation_passed":False,"human_adjudication":False}
    write_json_atomic(out/"manifest.json",manifest)
    ledger.begin_stage(attempt, 48, Decimal(plan["upper_bound_usd"]))
    try:
        for case in load_suite()["cases"]:
            grade, review, error = None,None,None
            try:
                grade,review=grade_case(create,case["inputs"],ledger,out/case["id"])
            except (ValueError,IndexError) as exc:
                error=type(exc).__name__
            result=dimensions(case["inputs"],grade,case["payload"],case["evidence"],case["safety_flags"],review)
            mismatch=compare(case,grade,result)
            path=out/(case["id"]+".json")
            write_json_atomic(path,{"case_id":case["id"],"grade":grade,"review":review,"dimensions":result,
                                    "mismatches":mismatch,"grading_error":error,"cost_usd":str(ledger.spent)})
            manifest["completed"]+=1
            manifest["matched"]+=int(not mismatch and not result["grader_errors"] and not result["disputed_dimensions"])
            manifest["rows"][case["id"]]=digest(path)
            write_json_atomic(out/"manifest.json",manifest)
            print(f"{case['id']}: {'matches' if not mismatch else 'disagreement'}; cumulative USD {ledger.spent}",flush=True)
        manifest["status"]="complete"
        ledger.finish_stage()
    except BaseException as exc:
        manifest.update(status="interrupted",exception_type=type(exc).__name__)
        raise
    finally:
        manifest["cumulative_cost_usd"]=str(ledger.spent)
        write_json_atomic(out/"api-ledger.json",ledger.data)
        write_json_atomic(out/"manifest.json",manifest)
    return manifest


if __name__ == "__main__":
    parser=argparse.ArgumentParser()
    parser.add_argument("--allow-external-ai",action="store_true")
    args=parser.parse_args()
    ledger=Ledger(FOLDER/"api-ledger.json")
    readiness()  # Do not even load confirmation content before development readiness.
    plan=preflight(ledger)
    if not args.allow_external_ai:
        print(json.dumps(plan,indent=2))
    else:
        # Check readiness and budget before resolving a client, no retries.
        readiness()
        from apps.api.app.core.config import get_settings
        from openai import OpenAI
        key=get_settings().openai_api_key
        if not key:
            raise ValueError("Configured credential unavailable")
        client=OpenAI(api_key=key,max_retries=0,timeout=60)
        execute(client.chat.completions.create,ledger)
