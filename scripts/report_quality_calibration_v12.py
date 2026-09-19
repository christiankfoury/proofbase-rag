"""Replay frozen v12 calibration from saved requests and responses; no API calls."""
import argparse
from decimal import Decimal
import hashlib
import json
from pathlib import Path
import sys
from types import SimpleNamespace

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))
from scripts.quality_eval_calibration_v12 import FOLDER, SUITE, AUDITS, VALIDATION, digest, compare, CODE
from scripts.quality_eval_contract_v12 import dimensions, review_schema, DIMENSIONS
from scripts.quality_eval_transport_v12 import initial_requests, review_request, parsed, Ledger
from scripts.quality_eval_transport_v12 import INPUT_RATE, OUTPUT_RATE, MODEL
from scripts.reliable_evaluation_run import write_json_atomic


def read(path):
    return json.loads(path.read_text(encoding="utf-8"))


def replay_raw(path, expected):
    raw = read(path)
    if raw["status"] != "received" or raw["request"] != expected:
        raise ValueError("Raw request mismatch or unsettled outcome")
    response = raw["response"]
    choices = [SimpleNamespace(finish_reason=choice["finish_reason"], message=SimpleNamespace(**choice["message"]))
               for choice in response["choices"]]
    return parsed(SimpleNamespace(choices=choices), expected["response_format"]["json_schema"]["schema"])


def replay(attempt="v12-01"):
    if attempt != "v12-01":
        raise ValueError("This frozen reporter handles only v12-01")
    folder = FOLDER / ("calibration-" + attempt)
    manifest = read(folder / "manifest.json")
    for key, path in (("suite_sha256", SUITE), ("review_suite_sha256", AUDITS), ("validation_sha256", VALIDATION)):
        if manifest["plan"][key] != digest(path):
            raise ValueError("Calibration input changed")
    for name in CODE:
        expected = manifest["plan"]["code_sha256"][name]
        if digest(folder / "code" / name) != expected:
            raise ValueError("Frozen source snapshot changed")
        # Imports used for reconstruction must match the recorded implementation.
        # Python normalizes source newlines; Git CRLF checkouts must replay the
        # same program while raw frozen snapshot hashes remain exact above.
        if (ROOT / "scripts" / name).read_text(encoding="utf-8") != (folder / "code" / name).read_text(encoding="utf-8"):
            raise ValueError("Replay requires the frozen v12 evaluator source")
    ledger = Ledger(folder / "api-ledger.json")
    if str(ledger.spent) != manifest["cumulative_cost_usd"]:
        raise ValueError("Frozen ledger/manifest cost mismatch")
    linked = set()
    for row in ledger.data["calls"][len(ledger.prefix["calls"]):]:
        relative = row["raw_path"]
        path = (FOLDER / relative).resolve()
        if not path.is_relative_to(FOLDER.resolve()) or relative in linked:
            raise ValueError("Duplicate or invalid ledger raw path")
        linked.add(relative)
        raw = read(path)
        request_hash = hashlib.sha256(json.dumps(raw["request"], ensure_ascii=False, sort_keys=True).encode()).hexdigest()
        if digest(path) != row["raw_sha256"] or request_hash != row["request_sha256"]:
            raise ValueError("Raw ledger binding changed")
        usage = raw["response"]["usage"]
        rates = {"gpt-4.1-2025-04-14": (Decimal("2"), Decimal("8")), "gpt-5.4-mini-2026-03-17": (Decimal("0.75"), Decimal("4.50")), MODEL: (INPUT_RATE, OUTPUT_RATE)}
        input_rate, output_rate = rates[row["model"]]
        if raw["response"]["model"] != row["model"] or raw["request"]["model"] != row["model"]:
            raise ValueError("Recorded model mismatch")
        cost = (usage["prompt_tokens"] * input_rate + usage["completion_tokens"] * output_rate) / 1_000_000
        if cost != Decimal(row["charged_usd"]):
            raise ValueError("Recorded token cost mismatch")
    rows = []
    for case in read(SUITE)["cases"]:
        path = folder / (case["id"] + ".json")
        if manifest["rows"].get(case["id"]) != digest(path):
            raise ValueError("Result row changed")
        saved = read(path)
        grade = {}
        for purpose, body in initial_requests(case["inputs"]):
            grade.update(replay_raw(folder / case["id"] / (purpose + ".json"), body))
        body = review_request(case["inputs"], grade)
        review = replay_raw(folder / case["id"] / "review.json", body)
        result = dimensions(case["inputs"], grade, case["payload"], case["evidence"], case["safety_flags"], review)
        mismatch = compare(case, grade, result)
        if (grade, review, result, mismatch) != (saved["grade"], saved["review"], saved["dimensions"], saved["mismatches"]):
            raise ValueError("Saved judgment reconstruction mismatch")
        rows.append({"id": case["id"], "matched": not mismatch, "mismatches": mismatch,
                     "grader_errors": result["grader_errors"], "disputed_dimensions": result["disputed_dimensions"]})
    audit_rows = []
    for case in read(AUDITS)["cases"]:
        path = folder / (case["id"] + "-review.json")
        if digest(path) != manifest["review_rows"][case["id"]]["sha256"]:
            raise ValueError("Audit row changed")
        review = replay_raw(folder / (case["id"] + "-raw.json"), review_request(case["inputs"], case["candidate"]))
        saved = read(path)
        matched = all(review[key] == "dispute" for key in case["expected_disputes"])
        exact = all(review[key] == ("dispute" if key in case["expected_disputes"] else "agree") for key in (*DIMENSIONS, "forbidden_assertion"))
        if review != saved["review"] or matched != saved["matched"] or exact != saved["exact_match"]:
            raise ValueError("Audit replay mismatch")
        audit_rows.append({"id": case["id"], "matched": matched, "exact_match": exact, "review": review})
    if manifest["status"] != "complete" or manifest["completed"] != len(rows) or manifest["matched"] != sum(r["matched"] for r in rows):
        raise ValueError("Incomplete or inconsistent calibration manifest")
    return {"attempt": attempt, "status": "complete", "case_count": len(rows), "matching_judgments": sum(r["matched"] for r in rows),
            "review_probe_count": len(audit_rows), "matching_review_probes": sum(r["matched"] for r in audit_rows),
            "exact_review_probes": sum(r["exact_match"] for r in audit_rows),
            "cumulative_cost_usd": str(ledger.spent), "semantic_validation_passed": False,
            "human_adjudication": False, "rows": rows, "review_rows": audit_rows}


if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("--write", action="store_true")
    args = parser.parse_args()
    result = replay()
    path = FOLDER / "calibration-v12-report.json"
    if args.write:
        if path.exists():
            raise ValueError("Report exists; preserve it")
        write_json_atomic(path, result)
    elif path.exists() and read(path) != result:
        raise ValueError("Saved report changed")
    print(json.dumps({k: v for k, v in result.items() if k not in {"rows", "review_rows"}}, indent=2))
