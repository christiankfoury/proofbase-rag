"""V8 requests; reuse frozen budget enforcement, never alter v7 evidence."""
from decimal import Decimal
import json

from scripts import quality_eval_transport as v7
from scripts.quality_eval_contract_v8 import schema, request_parts, review_schema, REVIEW_PROMPT, candidate_judgments

MODEL, APPROVED_CEILING, AUTHORIZATION = v7.MODEL, v7.APPROVED_CEILING, v7.AUTHORIZATION
Ledger, BudgetStop, reserve, parsed = v7.Ledger, v7.BudgetStop, v7.reserve, v7.parsed


def initial_requests(inputs):
    full = schema()
    keysets = [("claims", "all_claims_assessed"),
               ("facts", "actual_behavior", "behavior_span", "behavior_reason", "relevance", "forbidden_assertion")]
    return [(part["purpose"], v7.request(part["purpose"], part["prompt"], part["input"],
             {"type": "object", "additionalProperties": False, "required": list(keys),
              "properties": {key: full["properties"][key] for key in keys}}))
            for part, keys in zip(request_parts(inputs), keysets)]


def review_request(inputs, candidate):
    if len(json.dumps(candidate, ensure_ascii=False).encode("utf-8")) > v7.MAX_CANDIDATE_BYTES:
        raise ValueError("Candidate exceeds predeclared review size bound")
    return v7.request("review", REVIEW_PROMPT, {"inputs": inputs, "candidate": candidate,
                      "candidate_judgments": candidate_judgments(inputs, candidate)}, review_schema())


def case_bound(inputs):
    total = sum((reserve(body)["reserved_usd"] for _, body in initial_requests(inputs)), Decimal(0))
    # Fixed projection has six short labels; reserve 1024 extra bytes for it.
    empty = v7.request("review", REVIEW_PROMPT, {"inputs": inputs, "candidate": {}, "candidate_judgments": {}}, review_schema())
    return total + reserve(empty)["reserved_usd"] + Decimal(v7.MAX_CANDIDATE_BYTES * 2 + 1024) * v7.INPUT_RATE / 1_000_000


def grade_case(create, inputs, ledger, folder):
    grade = {}
    for purpose, body in initial_requests(inputs):
        response = ledger.call(create, body, folder / (purpose + ".json"))
        grade.update(parsed(response, body["response_format"]["json_schema"]["schema"]))
    body = review_request(inputs, grade)
    return grade, parsed(ledger.call(create, body, folder / "review.json"), review_schema())
