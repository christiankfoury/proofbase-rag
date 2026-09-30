"""Resume only unissued requests after a proven local settlement-write failure."""
import argparse
from copy import deepcopy
from decimal import Decimal
import hashlib
import json
from pathlib import Path
import shutil
import sys
ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))
from scripts import quality_completion_eval_v15 as base
from scripts.quality_completion_durable import Ledger, write_json_atomic
from scripts.quality_completion_ledger import FOLDER, digest
from scripts.quality_eval_transport_v15 import BudgetStop

ORIGINAL = FOLDER / "v15-diagnostic"
RECOVERY = FOLDER / "v15-local-recovery"
DIAGNOSTIC = FOLDER / "v15-diagnostic-recovered"
TOOLING = ("quality_completion_durable.py", "quality_v15_local_recovery.py", "report_quality_v15_recovery.py")
modules, all_cases, audits, compare = base.modules, base.all_cases, base.audits, base.compare


def plan(candidate, stage):
    result = base.plan(candidate, stage)
    result["code_sha256"].update({n:digest(ROOT/"scripts"/n) for n in TOOLING})
    return result


def verify_record():
    record = json.loads((RECOVERY/"reconciliation.json").read_bytes())
    for name, expected in record["evidence_sha256"].items():
        path = (FOLDER/name).resolve()
        if not path.is_relative_to(FOLDER.resolve()) or digest(path) != expected:
            raise ValueError("Recovery custody changed")
    original = json.loads((ORIGINAL/"manifest.json").read_bytes())
    if original["plan"] != base.plan("v15", "diagnostic"):
        raise ValueError("Evaluator/input changed during local recovery")
    return record


def reconcile():
    # No provider client is created in this operation.
    original = json.loads((ORIGINAL/"manifest.json").read_bytes())
    if original["status"] != "interrupted" or original.get("exception_type") != "PermissionError":
        raise ValueError("Not the known local file-write interruption")
    if original["plan"] != base.plan("v15", "diagnostic"):
        raise ValueError("Original evaluator/input changed")
    ledger_path = FOLDER/"api-ledger.json"
    before = ledger_path.read_bytes()
    data = json.loads(before)
    stage = data["stage"]
    if stage["name"] != "v15-diagnostic" or not data["unknown_outcome"]:
        raise ValueError("Unexpected settlement state")
    rows = data["calls"]
    if any(r["status"] != "completed" for r in rows[:-1]) or rows[-1]["status"] != "unknown":
        raise ValueError("More than one unsettled call")
    if len(rows)-stage["start_calls"] != original["completed"]*3+1:
        raise ValueError("Interruption is not after the next single claims response")
    row = rows[-1]
    source = (FOLDER/row["raw_path"]).resolve()
    if not source.is_relative_to(ORIGINAL.resolve()):
        raise ValueError("Unsafe interrupted response path")
    raw = json.loads(source.read_bytes())
    if raw["status"] != "unknown" or raw.get("exception_type") != "PermissionError" or not raw.get("response"):
        raise ValueError("No proven saved provider response; do not retry")
    restored = deepcopy(raw)
    restored["status"] = "received"
    del restored["exception_type"]
    received_bytes = (json.dumps(restored,indent=2,ensure_ascii=False,sort_keys=True)+"\n").encode()
    if hashlib.sha256(received_bytes).hexdigest() != row["raw_sha256"]:
        raise ValueError("Saved response differs from the received hash recorded before settlement")
    transport = modules("v15")[1]
    case_id = original["plan"]["cases"][original["completed"]]["id"]
    body = transport.initial_requests(all_cases()[case_id]["inputs"])[0][1]
    request_hash = hashlib.sha256(json.dumps(body,ensure_ascii=False,sort_keys=True).encode()).hexdigest()
    if raw["request"] != body or request_hash != row["request_sha256"]:
        raise ValueError("Interrupted request differs from declared next request")
    response = raw["response"]
    usage = response["usage"]
    charge = (usage["prompt_tokens"]*transport.INPUT_RATE+usage["completion_tokens"]*transport.OUTPUT_RATE)/1_000_000
    if (response["model"] != transport.MODEL or charge != Decimal(row["charged_usd"])
        or usage["prompt_tokens"] != row["input_tokens"] or usage["completion_tokens"] != row["output_tokens"]
        or not 0 <= usage["prompt_tokens"] <= row["input_bound"] or not 0 <= usage["completion_tokens"] <= row["output_cap"]):
        raise ValueError("Provider usage/model/settlement is unverified")
    if RECOVERY.exists() or DIAGNOSTIC.exists():
        raise ValueError("Recovery already prepared; no overwrite")
    RECOVERY.mkdir(); DIAGNOSTIC.mkdir(); (DIAGNOSTIC/"code").mkdir()
    (RECOVERY/"ledger-before.json").write_bytes(before)
    for cid in original["rows"]:
        shutil.copytree(ORIGINAL/cid, DIAGNOSTIC/cid)
        shutil.copyfile(ORIGINAL/(cid+".json"), DIAGNOSTIC/(cid+".json"))
    destination = DIAGNOSTIC/case_id/"claims.json"
    write_json_atomic(destination, restored)
    current_plan = plan("v15", "diagnostic")
    for name in current_plan["code_sha256"]:
        (DIAGNOSTIC/"code"/name).write_bytes((ROOT/"scripts"/name).read_bytes())
    record = {"version":"local-settlement-reconciliation.v1","reason":"Windows denied ledger replacement after complete response/usage were saved",
              "provider_requests_retried":0,"call_index":row["call_index"],"response_id":response["id"],
              "charged_usd":str(charge),"old_raw_path":row["raw_path"],"settled_raw_path":destination.relative_to(FOLDER).as_posix(),
              "evidence_sha256":{path.relative_to(FOLDER).as_posix():digest(path) for path in [ORIGINAL/"manifest.json",ORIGINAL/"api-ledger.json",source,RECOVERY/"ledger-before.json",destination]}}
    write_json_atomic(RECOVERY/"reconciliation.json",record)
    row.update(status="completed",raw_path=destination.relative_to(FOLDER).as_posix(),raw_sha256=digest(destination))
    data["unknown_outcome"] = False
    data.setdefault("local_reconciliation_records",[]).append({"path":"v15-local-recovery/reconciliation.json","sha256":digest(RECOVERY/"reconciliation.json")})
    write_json_atomic(ledger_path,data)
    manifest=deepcopy(original)
    manifest.update(status="recovery_prepared",plan=current_plan,local_recovery_sha256=digest(RECOVERY/"reconciliation.json"))
    manifest.pop("exception_type",None)
    write_json_atomic(DIAGNOSTIC/"manifest.json",manifest)
    write_json_atomic(DIAGNOSTIC/"api-ledger.json",data)
    print("Local settlement reconciled from exact received-response hash; zero provider requests retried.")


def saved_or_call(transport, create, ledger, body, path):
    if path.exists():
        raw=json.loads(path.read_bytes())
        if raw["status"] != "received" or raw["request"] != body:
            raise ValueError("Saved request is not reusable")
        from openai.types.chat import ChatCompletion
        response=ChatCompletion.model_validate(raw["response"])
    else:
        response=ledger.call(create,body,path)
    return transport.parsed(response,body["response_format"]["json_schema"]["schema"])


def resume(create, ledger):
    verify_record()
    manifest=json.loads((DIAGNOSTIC/"manifest.json").read_bytes())
    if manifest["status"] != "recovery_prepared" or manifest["plan"] != plan("v15","diagnostic"):
        raise ValueError("Recovery already executed or source changed")
    contract,transport=modules("v15")
    manifest["status"]="running"
    write_json_atomic(DIAGNOSTIC/"manifest.json",manifest)
    try:
        cases=all_cases()
        for item in manifest["plan"]["cases"][manifest["completed"]:]:
            case=cases[item["id"]]; grade,review,error=None,None,None
            try:
                parts={}
                for purpose,body in transport.initial_requests(case["inputs"]):
                    parts.update(saved_or_call(transport,create,ledger,body,DIAGNOSTIC/case["id"]/(purpose+".json")))
                review=saved_or_call(transport,create,ledger,transport.review_request(case["inputs"],parts),DIAGNOSTIC/case["id"]/"review.json")
                grade=parts
            except (ValueError,IndexError) as exc:
                error=type(exc).__name__
            result=contract.dimensions(case["inputs"],grade,case["payload"],case["evidence"],case["safety_flags"],review)
            mismatch=compare(case,grade,result)
            matched=not mismatch and not result["grader_errors"] and not result["disputed_dimensions"]
            path=DIAGNOSTIC/(case["id"]+".json")
            write_json_atomic(path,{"case_id":case["id"],"grade":grade,"review":review,"dimensions":result,"mismatches":mismatch,"grading_error":error,"matched":matched})
            manifest["rows"][case["id"]]=digest(path);manifest["completed"]+=1;manifest["matched"]+=int(matched)
            write_json_atomic(DIAGNOSTIC/"manifest.json",manifest)
            print(f"v15/diagnostic/{case['id']}: {'matches' if matched else 'disagreement'}; cumulative USD {ledger.spent}",flush=True)
            if not matched:
                manifest["status"]="early_stopped";break
        else:
            for case in audits("diagnostic"):
                review,error=None,None
                try:
                    review=saved_or_call(transport,create,ledger,transport.review_request(case["inputs"],case["candidate"]),DIAGNOSTIC/(case["id"]+"-raw.json"))
                except (ValueError,IndexError) as exc:
                    error=type(exc).__name__
                exact=bool(review and all(review[k]==("dispute" if k in case["expected_disputes"] else "agree") for k in (*contract.DIMENSIONS,"forbidden_assertion")))
                path=DIAGNOSTIC/(case["id"]+"-review.json")
                write_json_atomic(path,{"review":review,"exact_match":exact,"grading_error":error})
                manifest["review_rows"][case["id"]]={"sha256":digest(path),"exact_match":exact}
            manifest["status"]="complete"
        ledger.finish_stage()
    except BaseException as exc:
        manifest.update(status="interrupted",exception_type=type(exc).__name__);raise
    finally:
        manifest["cumulative_cost_usd"]=str(ledger.spent)
        write_json_atomic(DIAGNOSTIC/"api-ledger.json",ledger.data)
        write_json_atomic(DIAGNOSTIC/"manifest.json",manifest)
    return manifest


def gate(candidate, stage, folder=FOLDER):
    if candidate != "v15" or stage != "calibration" or (folder/"v15-calibration").exists():
        raise BudgetStop("Only the unexecuted calibration stage is allowed")
    verify_record()
    from scripts.report_quality_v15_recovery import replay
    report=replay("v15","diagnostic")
    if report["matching_judgments"] != 17 or report["exact_review_probes"] != 1:
        raise BudgetStop("Recovered diagnostic did not pass")
    manifest=json.loads((DIAGNOSTIC/"manifest.json").read_bytes())
    if manifest["plan"] != plan(candidate,"diagnostic"):
        raise BudgetStop("Candidate changed since diagnostic")


def execute(candidate, stage, create, ledger, folder=FOLDER):
    if candidate != "v15":
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
    parser=argparse.ArgumentParser()
    parser.add_argument("--reconcile",action="store_true")
    parser.add_argument("--stage",choices=["diagnostic","calibration"],default="diagnostic")
    parser.add_argument("--allow-external-ai",action="store_true")
    args=parser.parse_args()
    if args.reconcile:
        reconcile();return
    verify_record()
    if not args.allow_external_ai:
        print(json.dumps(plan("v15",args.stage),indent=2));return
    if args.stage=="calibration":gate("v15","calibration")
    from apps.api.app.core.config import get_settings
    from openai import OpenAI
    key=get_settings().openai_api_key
    if not key:raise ValueError("Configured credential unavailable")
    client=OpenAI(api_key=key,max_retries=0,timeout=60)
    ledger=Ledger(FOLDER/"api-ledger.json")
    if args.stage=="diagnostic":resume(client.chat.completions.create,ledger)
    else:execute("v15","calibration",client.chat.completions.create,ledger)


if __name__=="__main__":main()
