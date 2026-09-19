from copy import deepcopy
from decimal import Decimal
import json
from pathlib import Path
import shutil
import tempfile
from types import SimpleNamespace
import unittest

from scripts.quality_eval_challenges import fixtures
from scripts.quality_eval_contract_v9 import dimensions
from scripts import quality_eval_transport_v9 as transport


class V9Tests(unittest.TestCase):
    def ledger(self, folder):
        path = Path(folder) / "ledger.json"
        source = Path(__file__).resolve().parents[1] / "data/evaluation/quality-remediation-v1/calibration-v8-01/api-ledger.json"
        shutil.copyfile(source, path)
        return transport.Ledger(path)

    def test_existing_rubric_and_challenges_unchanged(self):
        for item in fixtures():
            result = dimensions(item["inputs"], item["grade"], item["payload"], item["evidence"], item["safety_flags"], item["review"])
            for key, expected in item["expected"].items():
                with self.subTest(case=item["id"], dimension=key):
                    self.assertEqual(result[key], expected)

    def test_reasoning_completion_is_priced_including_hidden_tokens(self):
        item = fixtures()[0]
        body = transport.initial_requests(item["inputs"])[0][1]
        self.assertEqual(body["reasoning_effort"], "low")
        self.assertNotIn("temperature", body)
        with tempfile.TemporaryDirectory() as temp:
            ledger = self.ledger(temp)
            before = ledger.spent
            data = {"model": transport.MODEL, "usage": {"prompt_tokens": 100, "completion_tokens": 2500,
                    "completion_tokens_details": {"reasoning_tokens": 2200}}, "choices": []}
            response = SimpleNamespace(model=transport.MODEL, usage=SimpleNamespace(**data["usage"]),
                                       model_dump=lambda **kwargs: deepcopy(data))
            ledger.call(lambda **kwargs: response, body, Path(temp) / "raw.json")
            self.assertEqual(ledger.spent - before, Decimal("0.011325"))
            self.assertEqual(ledger.data["calls"][-1]["model"], transport.MODEL)

    def test_preserves_v7_and_v8_history(self):
        with tempfile.TemporaryDirectory() as temp:
            ledger = self.ledger(temp)
            self.assertEqual(len(ledger.data["calls"]), 1471)
            ledger.data["calls"][-1]["charged_usd"] = "0"
            ledger.path.write_text(json.dumps(ledger.data))
            with self.assertRaisesRegex(transport.BudgetStop, "v8 continuation prefix"):
                transport.Ledger(ledger.path)

    def test_unknown_outcome_reserves_all_cost_and_blocks_retry(self):
        with tempfile.TemporaryDirectory() as temp:
            ledger = self.ledger(temp)
            body = transport.initial_requests(fixtures()[0]["inputs"])[0][1]
            before = ledger.spent
            def fail(**kwargs):
                raise TimeoutError("do not persist sensitive exception text")
            with self.assertRaises(TimeoutError):
                ledger.call(fail, body, Path(temp) / "raw.json")
            self.assertEqual(ledger.spent - before, transport.reserve(body)["reserved_usd"])
            with self.assertRaises(transport.BudgetStop):
                transport.Ledger(ledger.path)
            self.assertNotIn("sensitive", (Path(temp) / "raw.json").read_text())

    def test_whole_case_bounds_actual_review(self):
        item = fixtures()[0]
        actual = sum((transport.reserve(body)["reserved_usd"] for _, body in transport.initial_requests(item["inputs"])), Decimal(0))
        actual += transport.reserve(transport.review_request(item["inputs"], item["grade"]))["reserved_usd"]
        self.assertLessEqual(actual, transport.case_bound(item["inputs"]))
        for _, body in transport.initial_requests(item["inputs"]):
            data = json.loads(body["messages"][1]["content"])
            self.assertNotIn("expected_behavior", data)
            self.assertNotIn("response_type", data)


if __name__ == "__main__":
    unittest.main()
