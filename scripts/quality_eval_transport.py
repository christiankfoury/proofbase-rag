"""Versioned candidate grader requests and durable no-retry API accounting."""
from __future__ import annotations

from contextlib import contextmanager
from copy import deepcopy
from decimal import Decimal
import hashlib
import json
from pathlib import Path

from scripts.fresh_eval_grader import matches_schema
from scripts.quality_eval_contract import request_parts, schema, review_schema, REVIEW_PROMPT
from scripts.quality_eval_preflight import LEDGER, HANDOFF_SPENT, CEILING, budget_audit
from scripts.reliable_evaluation_run import write_json_atomic

MODEL = "gpt-4.1-2025-04-14"
# Verified 2026-09-19: https://developers.openai.com/api/docs/models/gpt-4.1
INPUT_RATE, OUTPUT_RATE = Decimal("2"), Decimal("8")
CAPS = {"claims": 2048, "coverage": 1400, "review": 900}
MAX_CANDIDATE_BYTES = 12000


class BudgetStop(RuntimeError):
    pass


def request(purpose, prompt, data, contract):
    return {"model": MODEL, "temperature": 0, "max_completion_tokens": CAPS[purpose],
            "messages": [{"role": "system", "content": prompt},
                         {"role": "user", "content": json.dumps(data, ensure_ascii=False)}],
            "response_format": {"type": "json_schema", "json_schema": {
                "name": "quality_" + purpose, "strict": True, "schema": contract}}}


def initial_requests(inputs):
    full = schema()
    keys = {"claims": ("claims", "all_claims_assessed"),
            "coverage": ("facts", "actual_behavior", "behavior_span", "behavior_reason", "relevance", "forbidden_assertion")}
    result = []
    for part in request_parts(inputs):
        names = keys[part["purpose"]]
        contract = {"type": "object", "additionalProperties": False, "required": list(names),
                    "properties": {key: full["properties"][key] for key in names}}
        result.append((part["purpose"], request(part["purpose"], part["prompt"], part["input"], contract)))
    return result


def review_request(inputs, candidate):
    encoded = json.dumps(candidate, ensure_ascii=False).encode("utf-8")
    if len(encoded) > MAX_CANDIDATE_BYTES:
        raise ValueError("Candidate exceeds predeclared review size bound")
    # Candidate labels are audited against raw inputs, never fixture expectations.
    return request("review", REVIEW_PROMPT, {"inputs": inputs, "candidate": candidate}, review_schema())


def reserve(request_body):
    if request_body.get("model") != MODEL or request_body.get("stream") or request_body.get("tools"):
        raise BudgetStop("Unsupported unpriced request")
    cap = request_body.get("max_completion_tokens")
    if type(cap) is not int or not 0 < cap <= max(CAPS.values()):
        raise BudgetStop("Unbounded completion")
    # UTF-8 bytes conservatively bound input tokens; schema and framing included.
    input_bound = len(json.dumps(request_body, ensure_ascii=False).encode("utf-8")) + 2048
    return {"input_bound": input_bound, "output_cap": cap,
            "reserved_usd": (input_bound * INPUT_RATE + cap * OUTPUT_RATE) / 1_000_000}


def case_bound(inputs):
    total = sum((reserve(body)["reserved_usd"] for _, body in initial_requests(inputs)), Decimal(0))
    # Candidate output is not available yet. Bound its JSON encoding, including
    # escaping when nested in a user message, independently of tokenization.
    empty = review_request(inputs, {})
    # ensure_ascii=False already escapes controls in candidate JSON; the outer
    # JSON layer can at most double those existing bytes through quote escaping.
    review = reserve(empty)["reserved_usd"] + Decimal(MAX_CANDIDATE_BYTES * 2) * INPUT_RATE / 1_000_000
    return total + review


@contextmanager
def exclusive_lock(folder):
    lock = folder / ".api.lock"
    folder.mkdir(parents=True, exist_ok=True)
    with lock.open("x", encoding="utf-8") as handle:
        handle.write("Single writer; stale lock requires investigation, never automatic retry.\n")
    try:
        yield
    finally:
        lock.unlink()


class Ledger:
    """Continuation with the COMPLETE Phase 68 prefix; unknown calls stop work."""
    def __init__(self, path, *, historical=LEDGER):
        self.path, self.historical = Path(path), Path(historical)
        if self.path.resolve() == self.historical.resolve():
            raise ValueError("Historical ledger is immutable")
        self.prefix = json.loads(self.historical.read_bytes())
        self.prefix_hash = hashlib.sha256(self.historical.read_bytes()).hexdigest()
        self.reload()

    @classmethod
    def initialize(cls, path):
        budget_audit()
        path = Path(path)
        data = json.loads(LEDGER.read_bytes())
        data["continuation"] = {"historical_sha256": hashlib.sha256(LEDGER.read_bytes()).hexdigest(),
                                "historical_calls": len(data["calls"]), "handoff_spent_floor_usd": str(HANDOFF_SPENT)}
        path.parent.mkdir(parents=True, exist_ok=True)
        # Exclusive creation prevents accidentally replacing a prior attempt.
        with path.open("x", encoding="utf-8", newline="\n") as handle:
            json.dump(data, handle, indent=2, ensure_ascii=False)
            handle.write("\n")
        return cls(path)

    def reload(self):
        self.data = json.loads(self.path.read_bytes())
        old = self.prefix["calls"]
        if self.data["calls"][:len(old)] != old:
            raise BudgetStop("Complete historical prefix changed")
        if self.data.get("continuation") != {"historical_sha256": self.prefix_hash, "historical_calls": len(old), "handoff_spent_floor_usd": str(HANDOFF_SPENT)}:
            raise BudgetStop("Historical provenance changed")
        if Decimal(str(self.data["limit_usd"])) != CEILING or self.data.get("budget_authorization") != self.prefix.get("budget_authorization"):
            raise BudgetStop("Budget authorization changed")
        for index, row in enumerate(self.data["calls"]):
            charge = Decimal(str(row["charged_usd"]))
            if row["call_index"] != index or not charge.is_finite() or charge < 0:
                raise BudgetStop("Invalid cost history")
        if self.data.get("unknown_outcome") or any(row["status"] != "completed" for row in self.data["calls"]):
            raise BudgetStop("Unsettled external outcome; no retry")

    @property
    def spent(self):
        old_count = len(self.prefix["calls"])
        old = sum((Decimal(str(row["charged_usd"])) for row in self.prefix["calls"]), Decimal(0))
        new = sum((Decimal(str(row["charged_usd"])) for row in self.data["calls"][old_count:]), Decimal(0))
        return max(old, HANDOFF_SPENT) + new

    def require_headroom(self, amount):
        if self.spent + amount > CEILING:
            raise BudgetStop(f"Conservative preflight needs USD {amount}; only USD {CEILING - self.spent} remains")

    def call(self, create, body, raw_path):
        with exclusive_lock(self.path.parent):
            self.reload()
            bound = reserve(body)
            self.require_headroom(bound["reserved_usd"])
            raw_path = Path(raw_path)
            if raw_path.exists():
                raise BudgetStop("Request already attempted; preserve prior evidence")
            entry = {"request": deepcopy(body), "status": "started", "response": None}
            write_json_atomic(raw_path, entry)
            row = {"call_index": len(self.data["calls"]), "operation": "chat", "model": MODEL,
                   "status": "started", **{k: str(v) if isinstance(v, Decimal) else v for k, v in bound.items()},
                   "charged_usd": str(bound["reserved_usd"]), "raw_path": raw_path.name}
            self.data["calls"].append(row)
            write_json_atomic(self.path, self.data)
            try:
                response = create(**body)
                entry.update(status="received", response=response.model_dump(mode="json"))
                # Preserve raw malformed/refused/truncated responses before parsing.
                write_json_atomic(raw_path, entry)
                if response.model != MODEL:
                    raise BudgetStop("Provider returned an unpriced model snapshot")
                usage = response.usage
                prompt_tokens, completion_tokens = usage.prompt_tokens, usage.completion_tokens
                if type(prompt_tokens) is not int or type(completion_tokens) is not int or not 0 <= prompt_tokens <= bound["input_bound"] or not 0 <= completion_tokens <= bound["output_cap"]:
                    raise BudgetStop("Provider usage outside reservation")
                cost = (prompt_tokens * INPUT_RATE + completion_tokens * OUTPUT_RATE) / 1_000_000
                row.update(status="completed", input_tokens=prompt_tokens, output_tokens=completion_tokens,
                           charged_usd=str(cost), response_model=response.model,
                           system_fingerprint=getattr(response, "system_fingerprint", None))
                write_json_atomic(self.path, self.data)
                return response
            except BaseException as exc:
                row["status"] = "unknown"
                self.data["unknown_outcome"] = True
                entry.update(status="unknown", exception_type=type(exc).__name__)
                write_json_atomic(self.path, self.data)
                write_json_atomic(raw_path, entry)
                raise


def parsed(response, contract):
    choice = response.choices[0]
    if choice.finish_reason != "stop" or choice.message.refusal:
        raise ValueError("Incomplete or refused grade")
    value = json.loads(choice.message.content)
    if not matches_schema(value, contract):
        raise ValueError("Grade schema mismatch")
    return value


def grade_case(create, inputs, ledger, folder):
    grade = {}
    for purpose, body in initial_requests(inputs):
        response = ledger.call(create, body, folder / (purpose + ".json"))
        grade.update(parsed(response, body["response_format"]["json_schema"]["schema"]))
    body = review_request(inputs, grade)
    response = ledger.call(create, body, folder / "review.json")
    return grade, parsed(response, review_schema())
