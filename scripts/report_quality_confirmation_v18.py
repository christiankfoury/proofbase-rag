"""Offline reconstruction of the separate-context v18 confirmation; never calls AI."""
from decimal import Decimal
import hashlib
import json
from pathlib import Path
import sys

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0,str(ROOT))
from scripts import quality_confirmation_v18 as confirmation
from scripts import quality_eval_transport_v18 as transport
from scripts.quality_completion_ledger import FOLDER, Ledger, digest
from scripts.report_quality_calibration_v12 import replay_raw


def replay():
    out=FOLDER/"confirmation-v18-01"
    manifest=json.loads((out/"manifest.json").read_bytes())
    plan=manifest["plan"]
    if manifest["status"]!="complete" or manifest["completed"]!=16:
        raise ValueError("Confirmation incomplete")
    for key,path in (("seal_sha256",confirmation.SEAL),("authorization_sha256",confirmation.APPROVAL),("suite_sha256",confirmation.SUITE),("validation_sha256",confirmation.VALIDATION),
                     ("readiness_sha256",confirmation.GATE),("freeze_sha256",confirmation.FREEZE)):
        if digest(path)!=plan[key]:
            raise ValueError("Confirmation custody changed")
    for name,expected in plan["code_sha256"].items():
        snapshot=out/"code"/name
        if digest(snapshot)!=expected or snapshot.read_text(encoding="utf-8")!=(ROOT/"scripts"/name).read_text(encoding="utf-8"):
            raise ValueError("Frozen confirmation code changed")
    ledger=Ledger(out/"api-ledger.json")
    if str(ledger.spent)!=manifest["cumulative_cost_usd"]:
        raise ValueError("Cost mismatch")
    raw_paths=set()
    for row in ledger.data["calls"][len(ledger.prefix["calls"]):]:
        path=(FOLDER/row["raw_path"]).resolve()
        if not path.is_relative_to(FOLDER.resolve()) or path in raw_paths:
            raise ValueError("Unsafe/duplicate raw path")
        raw_paths.add(path)
        raw=json.loads(path.read_bytes())
        request_hash=hashlib.sha256(json.dumps(raw["request"],ensure_ascii=False,sort_keys=True).encode()).hexdigest()
        if digest(path)!=row["raw_sha256"] or request_hash!=row["request_sha256"] or raw["status"]!="received":
            raise ValueError("Raw request/response changed")
        usage=raw["response"]["usage"]
        if raw["response"]["model"]!=transport.MODEL or raw["request"]["model"]!=transport.MODEL:
            raise ValueError("Unpriced model")
        cost=(usage["prompt_tokens"]*transport.INPUT_RATE+usage["completion_tokens"]*transport.OUTPUT_RATE)/1_000_000
        if cost!=Decimal(row["charged_usd"]):
            raise ValueError("Token charge mismatch")
    rows=[]
    for case in confirmation.load_suite()["cases"]:
        path=out/(case["id"]+".json")
        if digest(path)!=manifest["rows"][case["id"]]:
            raise ValueError("Row changed")
        saved=json.loads(path.read_bytes())
        grade,review,error=None,None,None
        try:
            parts={}
            for purpose,body in transport.initial_requests(case["inputs"]):
                parts.update(replay_raw(out/case["id"]/(purpose+".json"),body))
            review=replay_raw(out/case["id"]/"review.json",transport.review_request(case["inputs"],parts))
            grade=parts
        except (ValueError,IndexError) as exc:
            error=type(exc).__name__
        result=confirmation.dimensions(case["inputs"],grade,case["payload"],case["evidence"],case["safety_flags"],review)
        mismatch=confirmation.compare(case,grade,result)
        if (grade,review,error,result,mismatch)!=(saved["grade"],saved["review"],saved["grading_error"],saved["dimensions"],saved["mismatches"]):
            raise ValueError("Reconstructed confirmation differs")
        rows.append({"id":case["id"],"matched":not mismatch and not result["grader_errors"] and not result["disputed_dimensions"],
                     "mismatches":mismatch,"grader_errors":result["grader_errors"],
                     "disputed_dimensions":result["disputed_dimensions"]})
    if manifest["matched"]!=sum(r["matched"] for r in rows):
        raise ValueError("Matched count differs")
    return {"version":confirmation.VERSION,"status":"complete","count":16,"matched":manifest["matched"],
            "cumulative_cost_usd":str(ledger.spent),"semantic_validation_passed":False,
            "human_adjudication":False,"rows":rows}


if __name__=="__main__":
    print(json.dumps(replay(),indent=2))
