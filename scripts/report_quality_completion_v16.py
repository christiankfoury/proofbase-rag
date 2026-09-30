"""Offline replay of Phase 71 development attempts, including early stops."""
import argparse
from decimal import Decimal
import hashlib
import json
from pathlib import Path
import sys

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))
from scripts.quality_completion_eval_v16 import modules, baseline, all_cases, TEMPORAL_SUITE, AUTHORIZATION_PATH, DECLARATION, CONTROLS, audits, compare
from scripts.quality_completion_ledger import FOLDER, Ledger, digest
from scripts.report_quality_calibration_v12 import replay_raw
from scripts.quality_completion_eval_v15 import CONTROLS as COVERAGE_CONTROLS


def replay(candidate, stage, folder=FOLDER):
    out = folder/f"{candidate}-{stage}"
    manifest = json.loads((out/"manifest.json").read_bytes())
    plan = manifest["plan"]
    if (plan["candidate"], plan["stage"]) != (candidate, stage):
        raise ValueError("Attempt identity changed")
    for key, path in (("declaration_sha256",DECLARATION),("controls_sha256",CONTROLS),("coverage_controls_sha256",COVERAGE_CONTROLS),("authorization_sha256",AUTHORIZATION_PATH), ("temporal_suite_sha256",TEMPORAL_SUITE), ("suite_sha256",baseline.SUITE), ("audit_sha256",baseline.AUDITS),
                      ("validation_sha256",baseline.VALIDATION)):
        if digest(path) != plan[key]:
            raise ValueError("Authored inputs changed")
    for name, expected in plan["code_sha256"].items():
        snapshot = out/"code"/name
        if digest(snapshot) != expected or snapshot.read_text(encoding="utf-8") != (ROOT/"scripts"/name).read_text(encoding="utf-8"):
            raise ValueError("Frozen evaluator source changed")
    contract, transport = modules(candidate)
    ledger = Ledger(out/"api-ledger.json")
    if str(ledger.spent) != manifest["cumulative_cost_usd"]:
        raise ValueError("Ledger cost mismatch")
    seen = set()
    for row in ledger.data["calls"][len(ledger.prefix["calls"]):]:
        path = (folder/row["raw_path"]).resolve()
        if not path.is_relative_to(folder.resolve()) or path in seen:
            raise ValueError("Duplicate or unsafe raw path")
        seen.add(path)
        raw = json.loads(path.read_bytes())
        request_hash = hashlib.sha256(json.dumps(raw["request"],ensure_ascii=False,sort_keys=True).encode()).hexdigest()
        if raw["status"] != "received" or digest(path) != row["raw_sha256"] or request_hash != row["request_sha256"]:
            raise ValueError("Raw ledger binding mismatch")
        usage = raw["response"]["usage"]
        if raw["response"]["model"] != transport.MODEL or raw["request"]["model"] != transport.MODEL:
            raise ValueError("Model mismatch")
        charge = (usage["prompt_tokens"]*transport.INPUT_RATE + usage["completion_tokens"]*transport.OUTPUT_RATE)/1_000_000
        if charge != Decimal(row["charged_usd"]):
            raise ValueError("Token accounting mismatch")
    cases = all_cases()
    rows = []
    for item in plan["cases"][:manifest["completed"]]:
        case = cases[item["id"]]
        if case["expected"] != item["expected"]:
            raise ValueError("Predeclared expectations changed")
        path = out/(case["id"]+".json")
        if digest(path) != manifest["rows"][case["id"]]:
            raise ValueError("Result changed")
        saved = json.loads(path.read_bytes())
        grade, review, error = None, None, None
        try:
            parts = {}
            for purpose, body in transport.initial_requests(case["inputs"]):
                parts.update(replay_raw(out/case["id"]/(purpose+".json"),body))
            body = transport.review_request(case["inputs"],parts)
            review = replay_raw(out/case["id"]/"review.json",body)
            grade = parts
        except (ValueError, IndexError) as exc:
            error = type(exc).__name__
        result = contract.dimensions(case["inputs"],grade,case["payload"],case["evidence"],case["safety_flags"],review)
        mismatch = compare(case,grade,result)
        matched = not mismatch and not result["grader_errors"] and not result["disputed_dimensions"]
        rebuilt = {"case_id":case["id"],"grade":grade,"review":review,"dimensions":result,
                   "mismatches":mismatch,"grading_error":error,"matched":matched}
        if rebuilt != saved:
            raise ValueError("Judgment reconstruction mismatch")
        rows.append({"id":case["id"],"matched":matched,"mismatches":mismatch,
                     "grader_errors":result["grader_errors"],"disputed_dimensions":result["disputed_dimensions"]})
    exact_probes = 0
    for case in audits(stage) if manifest["status"] == "complete" else []:
        path = out/(case["id"]+"-review.json")
        if digest(path) != manifest["review_rows"][case["id"]]["sha256"]:
            raise ValueError("Probe changed")
        review, error = None, None
        try:
            review = replay_raw(out/(case["id"]+"-raw.json"),transport.review_request(case["inputs"],case["candidate"]))
        except (ValueError, IndexError) as exc:
            error = type(exc).__name__
        exact = bool(review and all(review[k] == ("dispute" if k in case["expected_disputes"] else "agree")
                                   for k in (*contract.DIMENSIONS,"forbidden_assertion")))
        if {"review":review,"grading_error":error,"exact_match":exact} != json.loads(path.read_bytes()):
            raise ValueError("Probe reconstruction mismatch")
        exact_probes += int(exact)
    if manifest["status"] not in {"complete","early_stopped"} or manifest["matched"] != sum(r["matched"] for r in rows):
        raise ValueError("Incomplete or inconsistent attempt")
    if manifest["status"] == "complete" and len(rows) != len(plan["cases"]):
        raise ValueError("Missing cases")
    return {"candidate":candidate,"stage":stage,"status":manifest["status"],"completed":len(rows),
            "matching_judgments":manifest["matched"],"exact_review_probes":exact_probes,
            "cumulative_cost_usd":str(ledger.spent),"semantic_validation_passed":False,"rows":rows}


if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("--candidate", choices=["v16"], default="v16")
    parser.add_argument("--stage", choices=["diagnostic","calibration"], default="diagnostic")
    args = parser.parse_args()
    print(json.dumps(replay(args.candidate,args.stage),indent=2))
