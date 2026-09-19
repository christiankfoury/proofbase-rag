from copy import deepcopy
from decimal import Decimal
import json
from pathlib import Path
import tempfile
from types import SimpleNamespace
import unittest

from scripts.quality_eval_challenges import fixtures
from scripts.quality_eval_transport import (Ledger, BudgetStop, MODEL, MAX_CANDIDATE_BYTES,
    initial_requests, review_request, case_bound, reserve, parsed, grade_case)


def response(value, *, usage=None, finish="stop", refusal=None):
    data = {"model": MODEL, "usage": usage or {"prompt_tokens": 100, "completion_tokens": 50},
            "choices": [{"finish_reason": finish, "message": {"content": json.dumps(value), "refusal": refusal}}]}
    return SimpleNamespace(model=MODEL, usage=SimpleNamespace(**data["usage"]),
                           choices=[SimpleNamespace(finish_reason=finish, message=SimpleNamespace(**data["choices"][0]["message"]))],
                           model_dump=lambda **kwargs: deepcopy(data))


class QualityTransportTests(unittest.TestCase):
    def test_independent_calls_do_not_receive_expected_labels(self):
        inputs = fixtures()[0]["inputs"]
        requests = initial_requests(inputs)
        self.assertEqual(len(requests), 2)
        for _, body in requests:
            data = json.loads(body["messages"][1]["content"])
            self.assertNotIn("expected_behavior", data)
            self.assertNotIn("response_type", data)
        self.assertNotIn("required_facts", json.loads(requests[0][1]["messages"][1]["content"]))
        self.assertNotIn("factual_sources", json.loads(requests[1][1]["messages"][1]["content"]))

    def test_maximum_review_encoding_fits_predeclared_bound(self):
        inputs = fixtures()[0]["inputs"]
        candidate = {"text": "\\\"" * 2500}
        body = review_request(inputs, candidate)
        actual = sum((reserve(b)["reserved_usd"] for _, b in initial_requests(inputs)), Decimal(0)) + reserve(body)["reserved_usd"]
        self.assertLessEqual(actual, case_bound(inputs))
        with self.assertRaises(ValueError):
            review_request(inputs, {"text": "x" * MAX_CANDIDATE_BYTES})

    def test_full_attempt_reservation_rejected_before_any_call(self):
        with tempfile.TemporaryDirectory() as temp:
            ledger = Ledger.initialize(Path(temp) / "ledger.json")
            before = ledger.path.read_bytes()
            with self.assertRaises(BudgetStop):
                ledger.require_headroom(Decimal("6"))
            self.assertEqual(before, ledger.path.read_bytes())

    def test_raw_response_saved_and_cost_settled_before_parse_error(self):
        with tempfile.TemporaryDirectory() as temp:
            ledger = Ledger.initialize(Path(temp) / "ledger.json")
            before = ledger.spent
            _, body = initial_requests(fixtures()[0]["inputs"])[0]
            raw = Path(temp) / "raw.json"
            result = ledger.call(lambda **kwargs: response({"invalid": True}), body, raw)
            with self.assertRaises(ValueError):
                parsed(result, body["response_format"]["json_schema"]["schema"])
            saved = json.loads(raw.read_bytes())
            self.assertEqual(saved["status"], "received")
            self.assertEqual(saved["request"], body)
            self.assertEqual(ledger.spent - before, Decimal("0.0006"))
            self.assertEqual(ledger.data["calls"][-1]["status"], "completed")

    def test_unknown_outcome_charged_and_blocks_retry(self):
        with tempfile.TemporaryDirectory() as temp:
            ledger = Ledger.initialize(Path(temp) / "ledger.json")
            before = ledger.spent
            _, body = initial_requests(fixtures()[0]["inputs"])[0]
            def fail(**kwargs):
                raise TimeoutError("sensitive exception message must not be persisted")
            with self.assertRaises(TimeoutError):
                ledger.call(fail, body, Path(temp) / "raw.json")
            self.assertEqual(ledger.spent - before, reserve(body)["reserved_usd"])
            self.assertNotIn("sensitive", (Path(temp) / "raw.json").read_text())
            with self.assertRaises(BudgetStop):
                Ledger(ledger.path)

    def test_preserves_full_phase68_prefix_and_rejects_tampering(self):
        with tempfile.TemporaryDirectory() as temp:
            path = Path(temp) / "ledger.json"
            ledger = Ledger.initialize(path)
            self.assertEqual(len(ledger.data["calls"]), 1321)
            ledger.data["calls"][-1]["charged_usd"] = 0
            path.write_text(json.dumps(ledger.data))
            with self.assertRaises(BudgetStop):
                Ledger(path)

    def test_existing_request_or_ledger_never_overwritten(self):
        with tempfile.TemporaryDirectory() as temp:
            ledger = Ledger.initialize(Path(temp) / "ledger.json")
            with self.assertRaises(FileExistsError):
                Ledger.initialize(ledger.path)
            raw = Path(temp) / "raw.json"
            raw.write_text("old evidence")
            with self.assertRaises(BudgetStop):
                ledger.call(lambda **kwargs: self.fail("No call allowed"), initial_requests(fixtures()[0]["inputs"])[0][1], raw)
            self.assertEqual(raw.read_text(), "old evidence")

    def test_three_calls_are_recorded_with_bounded_output(self):
        with tempfile.TemporaryDirectory() as temp:
            item = fixtures()[0]
            ledger = Ledger.initialize(Path(temp) / "ledger.json")
            bodies = []
            def create(**body):
                bodies.append(body)
                keys = body["response_format"]["json_schema"]["schema"]["required"]
                full = item["review"] if "reason" in keys else item["grade"]
                return response({key: full[key] for key in keys})
            grade, review = grade_case(create, item["inputs"], ledger, Path(temp) / "case")
            self.assertEqual((grade, review), (item["grade"], item["review"]))
            self.assertEqual(len(bodies), 3)
            review_input = json.loads(bodies[2]["messages"][1]["content"])
            self.assertEqual(review_input["candidate"], grade)
            self.assertEqual(len(list((Path(temp) / "case").glob("*.json"))), 3)
            self.assertEqual([row["raw_path"] for row in ledger.data["calls"][-3:]],
                             ["case/claims.json", "case/coverage.json", "case/review.json"])
            self.assertTrue(all(len(row["raw_sha256"]) == 64 and len(row["request_sha256"]) == 64
                                for row in ledger.data["calls"][-3:]))

    def test_refusal_or_truncation_is_not_schema_success(self):
        contract = initial_requests(fixtures()[0]["inputs"])[0][1]["response_format"]["json_schema"]["schema"]
        for candidate in (response({}, finish="length"), response({}, refusal="No")):
            with self.assertRaises(ValueError):
                parsed(candidate, contract)

    def test_unpriced_or_unbounded_requests_fail(self):
        body = initial_requests(fixtures()[0]["inputs"])[0][1]
        for key, value in (("model", "unpriced"), ("max_completion_tokens", 99999), ("stream", True), ("tools", ["tool"])):
            changed = dict(body, **{key: value})
            with self.subTest(key=key), self.assertRaises(BudgetStop):
                reserve(changed)


if __name__ == "__main__":
    unittest.main()
