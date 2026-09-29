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
from scripts.quality_eval_contract_v13 import VERSION, BEHAVIORS, DIMENSIONS, dimensions
from scripts.quality_eval_transport_v13 import MODEL, case_bound, grade_case
from scripts.quality_completion_ledger import Ledger, FOLDER, AUTHORIZATION
from scripts.reliable_evaluation_run import write_json_atomic

SUITE = FOLDER / "confirmation-challenges-v2.json"
VALIDATION = FOLDER / "confirmation-validation-v2.json"
GATE = FOLDER / "calibration-v13-readiness.json"
CODE = (*calibration.CODE, "quality_eval_contract_v13.py", "quality_eval_transport_v13.py", "quality_completion_eval_v13.py", "quality_completion_ledger.py", "quality_completion_eval.py", "quality_completion_confirmation_v13.py", "report_quality_completion.py", "report_quality_confirmation_v13.py", "report_quality_calibration_v12.py", "fresh_eval_grader.py", "reliable_evaluation_run.py")
digest, compare = calibration.digest, calibration.compare


def load_suite(suite_path=SUITE):
    suite = json.loads(suite_path.read_text(encoding="utf-8"))
    cases = suite["cases"]
    if suite["version"] != "quality-confirmation.v1" or len(cases) != 16:
        raise ValueError("Expected all 16 independent confirmation challenges")
    seen = set()
    for case in cases:
        cid = case["id"]
        if not re.fullmatch(r"[a-zA-Z0-9_-]{1,80}", cid) or cid in seen:
            raise ValueError("Duplicate or unsafe challenge ID")
        seen.add(cid)
        inputs, payload = case["inputs"], case["payload"]
        if inputs["answer"] != payload["answer"] or not inputs["answer"].strip():
            raise ValueError("Challenge answer mismatch")
        if inputs["expected_behavior"] not in {"answer", "clarify", "not_found", "refuse_no_access"}:
            raise ValueError("Invalid expected behavior")
        if inputs["expected_behavior"] == "answer" and not inputs["required_facts"]:
            raise ValueError("Answer case has no required facts")
        ids = [fact["fact_id"] for fact in inputs["required_facts"]]
        if len(ids) != len(set(ids)):
            raise ValueError("Duplicate required fact")
        if set(case["expected"]) != set((*DIMENSIONS, "quotation_fidelity", "overall", "actual_behavior")):
            raise ValueError("Missing independent expectation dimension")
        if any(case["expected"][key] not in {"pass", "fail", "unresolved", "not_applicable"} for key in (*DIMENSIONS, "quotation_fidelity")):
            raise ValueError("Invalid dimension expectation")
        if case["expected"]["overall"] not in {"pass", "fail", "unresolved"} or case["expected"]["actual_behavior"] not in BEHAVIORS:
            raise ValueError("Invalid composite or behavior expectation")
        allowed = {str(row["chunk_id"]): (f"R{i}", row) for i, row in enumerate(case["evidence"], 1)}
        if len(allowed) != len(case["evidence"]):
            raise ValueError("Duplicate challenge chunk")
        for sid, row in allowed.values():
            if {"source_id": sid, "text": row["content"]} not in inputs["factual_sources"]:
                raise ValueError("Challenge retrieval/source mismatch")
        citations = []
        for i, citation in enumerate(payload["citations"], 1):
            sid, row = allowed[str(citation["chunk_id"])]
            if row["document_id"] != citation["document_id"]:
                raise ValueError("Challenge citation/document mismatch")
            citations.append({"citation_id": f"C{i}", "source_id": sid, "text": row["content"]})
        if citations != inputs["cited_sources"]:
            raise ValueError("Challenge cited-source mismatch")
    return suite


def readiness():
    from scripts.report_quality_completion import replay
    report = replay("v13", "calibration")
    if (report["matching_judgments"] != 24 or report["exact_review_probes"] != 3
        or any(row["grader_errors"] or row["disputed_dimensions"] for row in report["rows"])):
        raise ValueError("Development calibration has unresolved disagreements")
    gate = json.loads(GATE.read_bytes())
    review = ROOT / "docs/phase-71/calibration-v13-source-review.md"
    if (gate.get("status") != "approved" or gate.get("human_adjudication") is not False
        or gate.get("report_sha256") != digest(FOLDER / "v13-calibration-report.json")
        or gate.get("source_review_sha256") != digest(review)
        or gate.get("unresolved_semantic_findings") != 0
        or gate.get("code_sha256") != {name:digest(ROOT/"scripts"/name) for name in CODE}):
        raise ValueError("Source inspection readiness missing or invalid")
    return digest(GATE)


def preflight(ledger):
    freeze_path = FOLDER / "evaluator-freeze.json"
    freeze = json.loads(freeze_path.read_bytes())
    if (freeze.get("readiness_sha256") != digest(GATE)
        or freeze.get("code_sha256") != {name:digest(ROOT/"scripts"/name) for name in CODE}):
        raise ValueError("Evaluator freeze changed")
    suite = load_suite()
    if suite.get("authored_after_freeze") != freeze.get("commit") or not freeze.get("commit"):
        raise ValueError("Confirmation was not authored after the selected freeze")
    validation = json.loads(VALIDATION.read_bytes())
    reviews = validation.get("case_reviews", [])
    if (validation.get("status") != "approved" or validation.get("suite_sha256") != digest(SUITE)
        or validation.get("freeze_sha256") != digest(freeze_path)
        or validation.get("case_count") != 16 or validation.get("human_adjudication") is not False
        or len(reviews) != 16 or {r["id"] for r in reviews} != {c["id"] for c in suite["cases"]}
        or not all(r.get("accept") is True for r in reviews)):
        raise ValueError("Independent confirmation expectation validation failed")
    bounds = [{"id":case["id"], "upper_bound_usd":str(case_bound(case["inputs"]))} for case in suite["cases"]]
    bound = sum((Decimal(row["upper_bound_usd"]) for row in bounds),Decimal(0))
    return {"version":VERSION,"model":MODEL,"case_count":16,"suite_sha256":digest(SUITE),
            "validation_sha256":digest(VALIDATION),"freeze_sha256":digest(freeze_path),"upper_bound_usd":str(bound),
            "authorization":AUTHORIZATION,"maximum_calls":48,
            "code_sha256":{name:digest(ROOT/"scripts"/name) for name in CODE},"cases":bounds}


def execute(create, ledger, attempt="confirmation-v13-01"):
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
            manifest["matched"]+=int(not mismatch and not result["grader_errors"])
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
