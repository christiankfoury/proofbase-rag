"""Canonical preparation for future diagnostic executors; no network calls.

Historical runners and their recorded reservations remain frozen. A new executor
must call submit_prepared with its own fresh ledger and recheck current pricing.
"""
import json

from scripts.reliability_payload_budget import reservation


def prepare_request(body: dict, operation: str) -> tuple[dict, tuple]:
    # Same ordering for reservation, submission and sorted receipt persistence.
    # Reject NaN rather than serializing non-JSON input. Do not mutate the caller.
    canonical = json.loads(json.dumps(body, sort_keys=True, ensure_ascii=False, allow_nan=False))
    return canonical, reservation(canonical, operation)


def submit_prepared(ledger, create, body: dict, operation: str):
    canonical, _ = prepare_request(body, operation)
    return ledger.call(create, canonical, operation)
