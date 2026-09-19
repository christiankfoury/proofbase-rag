"""Read-only budget and visible contract challenge report. Never calls a provider."""
from decimal import Decimal
import hashlib
import json
from pathlib import Path
import sys

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))
from scripts.quality_eval_challenges import fixtures
from scripts.quality_eval_contract import VERSION, dimensions

CEILING = Decimal("2.00")
HANDOFF_SPENT = Decimal("1.19689392")
LEDGER = ROOT / "data/evaluation/current-runtime-v3/api-ledger.json"
PREFIX = ROOT / "data/evaluation/dimension-reanalysis-v1/api-ledger.json"


def budget_audit(ledger_path=LEDGER, prefix_path=PREFIX):
    raw = ledger_path.read_bytes()
    ledger = json.loads(raw, parse_float=Decimal)
    prior = json.loads(prefix_path.read_bytes(), parse_float=Decimal)
    if ledger["calls"][:len(prior["calls"])] != prior["calls"]:
        raise ValueError("Historical cost prefix changed")
    if ledger.get("limit_usd") != CEILING or ledger.get("budget_authorization") != "User approved USD 2 cumulative ceiling on 2026-09-14":
        raise ValueError("Unexpected budget authorization")
    if ledger.get("unknown_outcome") is not False or ledger.get("budget_exhausted"):
        raise ValueError("Ledger is stopped")
    spent = Decimal(0)
    for index, call in enumerate(ledger["calls"]):
        if call.get("call_index") != index or call.get("status") != "completed":
            raise ValueError("Unsettled or unordered ledger")
        charge = Decimal(str(call["charged_usd"]))
        if not charge.is_finite() or charge < 0:
            raise ValueError("Invalid ledger charge")
        spent += charge
    remaining = CEILING - max(spent, HANDOFF_SPENT)
    if remaining < 0:
        raise ValueError("Cumulative ceiling exceeded")
    return {"historical_ledger_sha256": hashlib.sha256(raw).hexdigest(), "calls": len(ledger["calls"]),
            "ledger_sum_usd": str(spent), "handoff_spent_usd": str(HANDOFF_SPENT),
            "conservative_remaining_usd": str(remaining), "ceiling_usd": str(CEILING),
            "external_calls_authorized_by_this_check": False}


def report():
    results = []
    for item in fixtures():
        output = dimensions(item["inputs"], item["grade"], item["payload"], item["evidence"], item["safety_flags"], item["review"])
        mismatches = {key: {"expected": value, "actual": output[key]}
                      for key, value in item["expected"].items() if output[key] != value}
        results.append({"id": item["id"], "matches_authored_expectations": not mismatches,
                        "mismatches": mismatches, "dimensions": output})
    return {"version": VERSION, "kind": "offline_contract_challenges_with_supplied_judgments",
            "semantic_validation_passed": False, "human_adjudication": "not_performed",
            "challenge_count": len(results), "contracts_matched": sum(r["matches_authored_expectations"] for r in results),
            "budget": budget_audit(), "results": results}


if __name__ == "__main__":
    result = report()
    print(json.dumps(result, indent=2))
    raise SystemExit(0 if result["challenge_count"] == result["contracts_matched"] else 1)
