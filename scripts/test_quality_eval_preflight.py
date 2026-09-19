from copy import deepcopy
from decimal import Decimal
import json
from pathlib import Path
import tempfile
import unittest

from scripts.quality_eval_preflight import budget_audit, report


class QualityPreflightTests(unittest.TestCase):
    def test_actual_ledger_and_conservative_handoff_allowance(self):
        result = budget_audit()
        self.assertEqual(result["calls"], 1321)
        self.assertEqual(Decimal(result["conservative_remaining_usd"]), Decimal("0.80310608"))
        self.assertFalse(result["external_calls_authorized_by_this_check"])

    def test_contract_report_cannot_claim_semantic_validation(self):
        result = report()
        self.assertEqual(result["contracts_matched"], 22)
        self.assertFalse(result["semantic_validation_passed"])
        self.assertEqual(result["human_adjudication"], "not_performed")

    def test_invalid_budget_or_prefix_cannot_pass(self):
        historical = {"calls": [{"call_index": 0, "charged_usd": 0.5, "status": "completed"}]}
        original = {"calls": deepcopy(historical["calls"]), "unknown_outcome": False,
                    "limit_usd": 2, "budget_authorization": "User approved USD 2 cumulative ceiling on 2026-09-14"}
        with tempfile.TemporaryDirectory() as folder:
            prefix = Path(folder) / "prefix.json"
            current = Path(folder) / "ledger.json"
            prefix.write_text(json.dumps(historical))
            for field, value in (("unknown_outcome", True), ("limit_usd", 3), ("budget_exhausted", True), ("calls", [])):
                ledger = deepcopy(original)
                ledger[field] = value
                current.write_text(json.dumps(ledger))
                with self.subTest(field=field), self.assertRaises(ValueError):
                    budget_audit(current, prefix)
            for charge, status in ((-1, "completed"), (0.1, "started"), (2, "completed")):
                ledger = deepcopy(original)
                ledger["calls"].append({"call_index": 1, "charged_usd": charge, "status": status})
                current.write_text(json.dumps(ledger))
                with self.subTest(charge=charge, status=status), self.assertRaises(ValueError):
                    budget_audit(current, prefix)


if __name__ == "__main__":
    unittest.main()
