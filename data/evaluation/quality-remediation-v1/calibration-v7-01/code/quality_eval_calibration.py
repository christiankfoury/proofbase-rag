"""Independent development calibration, with immutable attempts and no app calls."""
from __future__ import annotations

import argparse
from decimal import Decimal
import hashlib
import json
from pathlib import Path
import re
import sys

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))
from scripts.quality_eval_contract import BEHAVIORS, DIMENSIONS, VERSION, dimensions
from scripts.quality_eval_preflight import budget_audit
from scripts.quality_eval_transport import MODEL, APPROVED_CEILING, AUTHORIZATION, Ledger, case_bound, grade_case, review_request, reserve, parsed, BudgetStop
from scripts.quality_eval_contract import schema, review_schema
from scripts.fresh_eval_grader import matches_schema
from scripts.reliable_evaluation_run import write_json_atomic

FOLDER = ROOT / "data/evaluation/quality-remediation-v1"
SUITE = FOLDER / "challenges-v2.json"
VALIDATION = FOLDER / "challenge-validation-v2.json"
AUDITS = FOLDER / "review-challenges-v1.json"
CODE = ("quality_eval_contract.py", "quality_eval_transport.py", "quality_eval_calibration.py", "quality_eval_preflight.py")


def digest(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()


def code_hashes():
    return {name: digest(ROOT / "scripts" / name) for name in CODE}


def load_suite(suite_path=SUITE):
    suite = json.loads(suite_path.read_text(encoding="utf-8"))
    cases = suite["cases"]
    if suite["version"] != "quality-challenges.v2" or len(cases) != 24:
        raise ValueError("Expected all 24 independent challenges")
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


def load_audits(audit_path=AUDITS):
    audits = json.loads(audit_path.read_text(encoding="utf-8"))
    if audits["version"] != "quality-review-challenges.v1" or len(audits["cases"]) != 3:
        raise ValueError("Expected three independent reviewer challenges")
    ids = set()
    for case in audits["cases"]:
        if not re.fullmatch(r"[a-zA-Z0-9_-]{1,80}", case["id"]) or case["id"] in ids:
            raise ValueError("Unsafe or duplicate audit challenge ID")
        ids.add(case["id"])
        if not matches_schema(case["candidate"], schema()):
            raise ValueError("Audit candidate schema mismatch")
        if not case["expected_disputes"] or not set(case["expected_disputes"]) <= set((*DIMENSIONS, "forbidden_assertion")):
            raise ValueError("Audit must predeclare specific semantic disputes")
        if case["inputs"]["answer"] != case["payload"]["answer"]:
            raise ValueError("Audit answer mismatch")
    return audits


def preflight(suite_path=SUITE, validation_path=VALIDATION, audit_path=AUDITS):
    suite = load_suite(suite_path)
    audits = load_audits(audit_path)
    validation = json.loads(validation_path.read_text(encoding="utf-8")) if validation_path.exists() else None
    independently_checked = bool(validation and validation.get("status") == "approved"
                                 and validation.get("suite_sha256") == digest(suite_path)
                                 and validation.get("case_count") == len(suite["cases"])
                                 and validation.get("human_adjudication") is False
                                 and validation.get("review_suite_sha256") == digest(audit_path)
                                 and validation.get("review_case_count") == 3
                                 and len(validation.get("case_reviews", [])) == len(suite["cases"])
                                 and {r["id"] for r in validation["case_reviews"]} == {c["id"] for c in suite["cases"]}
                                 and all(r.get("accept") is True for r in validation["case_reviews"])
                                 and len(validation.get("review_case_reviews", [])) == len(audits["cases"])
                                 and {r["id"] for r in validation["review_case_reviews"]} == {c["id"] for c in audits["cases"]}
                                 and all(r.get("accept") is True for r in validation["review_case_reviews"]))
    costs = [{"id": case["id"], "upper_bound_usd": str(case_bound(case["inputs"]))} for case in suite["cases"]]
    costs += [{"id": case["id"], "upper_bound_usd": str(reserve(review_request(case["inputs"], case["candidate"]))["reserved_usd"])}
              for case in audits["cases"]]
    total = sum((Decimal(row["upper_bound_usd"]) for row in costs), Decimal(0))
    budget = budget_audit()
    ledger_path = FOLDER / "api-ledger.json"
    if ledger_path.exists():
        ledger = Ledger(ledger_path)
        available = APPROVED_CEILING - ledger.spent
    else:
        available = APPROVED_CEILING - max(Decimal(budget["ledger_sum_usd"]), Decimal(budget["handoff_spent_usd"]))
    return {"version": VERSION, "model": MODEL, "suite_sha256": digest(suite_path),
            "validation_sha256": digest(validation_path) if validation_path.exists() else None,
            "review_suite_sha256": digest(audit_path), "review_case_count": len(audits["cases"]),
            "independently_checked": independently_checked, "case_count": len(suite["cases"]),
            "upper_bound_usd": str(total), "available_usd": str(available),
            "authorization": AUTHORIZATION,
            "headroom_passed": total <= available, "cases": costs, "code_sha256": code_hashes(),
            "semantic_validation_passed": False, "external_calls": 0}


def compare(case, grade, result):
    actual = dict(result, actual_behavior=grade.get("actual_behavior") if grade else "unknown")
    return {key: {"expected": expected, "actual": actual[key]}
            for key, expected in case["expected"].items() if actual[key] != expected}


def execute(attempt, create, ledger, *, suite_path=SUITE, validation_path=VALIDATION, audit_path=AUDITS, folder=FOLDER):
    if not re.fullmatch(r"[a-zA-Z0-9_-]{1,60}", attempt):
        raise ValueError("Invalid attempt name")
    plan = preflight(suite_path, validation_path, audit_path)
    if not plan["independently_checked"]:
        raise ValueError("Independent challenge judgment validation is pending")
    suite = load_suite(suite_path)
    ledger.require_headroom(Decimal(plan["upper_bound_usd"]))
    out = folder / ("calibration-" + attempt)
    out.mkdir()  # Existing attempt is always immutable, including failed attempts.
    manifest = {"status": "running", "plan": plan, "completed": 0, "matched": 0,
                "semantic_validation_passed": False, "human_adjudication": False, "rows": {}, "review_rows": {}}
    # Freeze exact code bytes with every attempt, including failed ones.
    code_dir = out / "code"
    code_dir.mkdir()
    for name in CODE:
        (code_dir / name).write_bytes((ROOT / "scripts" / name).read_bytes())
    write_json_atomic(out / "manifest.json", manifest)
    try:
        for case in suite["cases"]:
            row_path = out / (case["id"] + ".json")
            grade, review, error = None, None, None
            try:
                grade, review = grade_case(create, case["inputs"], ledger, out / case["id"])
            except (ValueError, IndexError) as exc:
                # Raw output remains durable; malformed grades are unresolved.
                error = type(exc).__name__
            result = dimensions(case["inputs"], grade, case["payload"], case["evidence"], case["safety_flags"], review)
            mismatches = compare(case, grade, result)
            row = {"case_id": case["id"], "grade": grade, "review": review, "dimensions": result,
                   "mismatches": mismatches, "grading_error": error, "cost_usd": str(ledger.spent)}
            write_json_atomic(row_path, row)
            manifest["completed"] += 1
            manifest["matched"] += int(not mismatches and not result["grader_errors"])
            manifest["rows"][case["id"]] = digest(row_path)
            write_json_atomic(out / "manifest.json", manifest)
            print(f"{case['id']}: {'matches' if not mismatches else 'disagreement'}; cumulative USD {ledger.spent}", flush=True)
        for case in load_audits(audit_path)["cases"]:
            body = review_request(case["inputs"], case["candidate"])
            review, error = None, None
            try:
                raw = ledger.call(create, body, out / (case["id"] + "-raw.json"))
                review = parsed(raw, review_schema())
            except (ValueError, IndexError) as exc:
                error = type(exc).__name__
            matched = bool(review and all(review[key] == "dispute" for key in case["expected_disputes"]))
            path = out / (case["id"] + "-review.json")
            write_json_atomic(path, {"case_id": case["id"], "review": review, "matched": matched, "grading_error": error})
            manifest["review_rows"][case["id"]] = {"sha256": digest(path), "matched": matched}
            write_json_atomic(out / "manifest.json", manifest)
        manifest["status"] = "complete"
        # Completion only establishes agreement with these independent labels.
        # A later source review and explicit readiness artifact are still needed.
    except BaseException as exc:
        manifest.update(status="interrupted", exception_type=type(exc).__name__)
        raise
    finally:
        manifest["cumulative_cost_usd"] = str(ledger.spent)
        write_json_atomic(out / "manifest.json", manifest)
    return manifest


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--allow-external-ai", action="store_true")
    parser.add_argument("--attempt")
    args = parser.parse_args()
    plan = preflight()
    if not args.allow_external_ai:
        print(json.dumps(plan, indent=2))
        return
    if not args.attempt or not plan["independently_checked"] or not plan["headroom_passed"]:
        raise BudgetStop("Attempt, independent validation and conservative whole-attempt headroom required")
    if (FOLDER / ("calibration-" + args.attempt)).exists():
        raise ValueError("Attempt exists; preserve it")
    # Key reuse is authorized by the handoff. Resolve using normal settings;
    # callers can supply the existing environment without writing a secret.
    from apps.api.app.core.config import get_settings
    from openai import OpenAI
    key = get_settings().openai_api_key
    if not key:
        raise ValueError("Configured credential unavailable")
    path = FOLDER / "api-ledger.json"
    ledger = Ledger(path) if path.exists() else Ledger.initialize(path)
    client = OpenAI(api_key=key, max_retries=0, timeout=60)
    execute(args.attempt, client.chat.completions.create, ledger)


if __name__ == "__main__":
    main()
