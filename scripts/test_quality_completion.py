from copy import deepcopy
from decimal import Decimal
import json
from pathlib import Path
import tempfile
from types import SimpleNamespace
import unittest
from unittest.mock import patch

from scripts import quality_completion_ledger as accounting
from scripts import quality_completion_eval as runner
from scripts import quality_eval_transport_v12 as transport
from scripts.quality_eval_challenges import fixtures


class CompletionTests(unittest.TestCase):
    def test_reconciliation_keeps_complete_branches_and_floor(self):
        audit = accounting.audit()
        self.assertEqual(audit["historical_calls"], 1707)
        self.assertEqual(audit["phase70_additional_calls"], 11)
        self.assertEqual(audit["conservative_spent_usd"], "2.14328077")
        self.assertIsNone(audit["authorization"]["local_cumulative_ceiling_usd"])

    def response(self):
        data = {"model":transport.MODEL, "usage":{"prompt_tokens":100,"completion_tokens":2500}, "choices":[]}
        return SimpleNamespace(model=transport.MODEL, usage=SimpleNamespace(**data["usage"]),
                               model_dump=lambda **kwargs:deepcopy(data))

    def test_new_authorization_allows_old_cap_exceeding_preflight_but_bounds_calls(self):
        with tempfile.TemporaryDirectory() as temp:
            ledger = accounting.Ledger.initialize(Path(temp)/"ledger.json")
            with self.assertRaises(accounting.BudgetStop):
                ledger.require_headroom(Decimal("0.1"))
            ledger.begin_stage("test", 1, Decimal("8"))
            ledger.require_headroom(Decimal("8"))
            body = transport.initial_requests(fixtures()[0]["inputs"])[0][1]
            before = ledger.spent
            ledger.call(lambda **kw:self.response(), body, Path(temp)/"raw.json")
            self.assertEqual(ledger.spent-before, Decimal("0.03775"))
            with self.assertRaises(accounting.BudgetStop):
                ledger.call(lambda **kw:self.fail("No second call"), body, Path(temp)/"second.json")

    def test_unknown_outcome_blocks_continuation_and_keeps_reserved_cost(self):
        with tempfile.TemporaryDirectory() as temp:
            ledger = accounting.Ledger.initialize(Path(temp)/"ledger.json")
            ledger.begin_stage("test", 2, Decimal("1"))
            body = transport.initial_requests(fixtures()[0]["inputs"])[0][1]
            before = ledger.spent
            def fail(**kw):
                raise TimeoutError("private failure text")
            with self.assertRaises(TimeoutError):
                ledger.call(fail, body, Path(temp)/"raw.json")
            self.assertEqual(ledger.spent-before, transport.reserve(body)["reserved_usd"])
            with self.assertRaises(accounting.BudgetStop):
                accounting.Ledger(ledger.path)
            self.assertNotIn("private", (Path(temp)/"raw.json").read_text())

    def test_prefix_and_authorization_tamper_rejected(self):
        for field in ("calls", "authorization"):
            with tempfile.TemporaryDirectory() as temp:
                ledger = accounting.Ledger.initialize(Path(temp)/"ledger.json")
                if field == "calls":
                    ledger.data[field][-1]["charged_usd"] = "0"
                else:
                    ledger.data[field]["local_cumulative_ceiling_usd"] = "5"
                ledger.path.write_text(json.dumps(ledger.data))
                with self.assertRaises(accounting.BudgetStop):
                    accounting.Ledger(ledger.path)

    def test_diagnostic_plan_is_predeclared_and_bounded(self):
        plan = runner.plan("v12", "diagnostic")
        self.assertEqual([c["id"] for c in plan["cases"]], list(runner.DIAGNOSTICS))
        self.assertEqual(plan["maximum_calls"], 12)
        self.assertEqual(runner.plan("v12", "calibration")["maximum_calls"], 75)

    def test_failed_diagnostic_stops_before_second_case_and_consumes_attempt(self):
        with tempfile.TemporaryDirectory() as temp:
            folder = Path(temp)
            ledger = accounting.Ledger.initialize(folder/"api-ledger.json")
            with patch.object(transport, "grade_case", side_effect=ValueError("bad contract")) as grade:
                result = runner.execute("v12", "diagnostic", None, ledger, folder)
            self.assertEqual(result["status"], "early_stopped")
            self.assertEqual(result["completed"], 1)
            self.assertEqual(grade.call_count, 1)
            with self.assertRaises(accounting.BudgetStop):
                runner.gate("v12", "diagnostic", folder)
            with self.assertRaises(accounting.BudgetStop):
                runner.gate("v12", "calibration", folder)
            with self.assertRaises(ValueError):
                runner.modules("v14")

    def test_confirmation_cannot_load_cases_or_call_before_readiness(self):
        from scripts import quality_completion_confirmation_v12 as confirmation
        with patch.object(confirmation, "readiness", side_effect=ValueError("not ready")), \
             patch.object(confirmation, "preflight") as preflight:
            with self.assertRaisesRegex(ValueError, "not ready"):
                confirmation.execute(lambda **kw:self.fail("No call"), None)
            preflight.assert_not_called()

    def test_diagnostic_replays_from_raw_responses(self):
        from scripts.report_quality_completion import replay
        if not (accounting.FOLDER/"v12-diagnostic/manifest.json").exists():
            self.skipTest("Live diagnostic not yet recorded")
        result = replay("v12", "diagnostic")
        self.assertEqual(result["completed"], 4)
        self.assertEqual(result["matching_judgments"], 4)
        self.assertFalse(result["semantic_validation_passed"])

    def test_repair_preserves_reducers_and_separates_context_from_gold(self):
        from scripts import quality_eval_contract_v13 as contract
        from scripts import quality_eval_transport_v13 as repair
        from scripts import quality_completion_eval_v13 as repair_runner
        from scripts.quality_eval_contract_v12 import dimensions
        self.assertIs(contract.dimensions, dimensions)
        self.assertEqual(repair_runner.plan("v13", "diagnostic")["maximum_calls"], 18)
        item = fixtures()[0]
        claims = json.loads(repair.initial_requests(item["inputs"])[0][1]["messages"][1]["content"])
        self.assertNotIn("required_facts", claims)
        self.assertNotIn("expected_behavior", claims)
        self.assertEqual(claims["question"], item["inputs"]["question"])

    def test_repair_cannot_run_without_bound_hypothesis(self):
        from scripts import quality_completion_eval_v13 as repair
        with tempfile.TemporaryDirectory() as temp:
            with self.assertRaises(FileNotFoundError):
                repair.gate("v13", "diagnostic", Path(temp))

    def test_selected_confirmation_rejects_less_than_exact_full_gate(self):
        from scripts import quality_completion_confirmation_v13 as confirmation
        report={"matching_judgments":23,"exact_review_probes":3,"rows":[]}
        with patch("scripts.report_quality_completion.replay",return_value=report), \
             patch.object(confirmation,"preflight") as preflight:
            with self.assertRaisesRegex(ValueError,"unresolved disagreements"):
                confirmation.execute(lambda **kw:self.fail("No confirmation call"),None)
            preflight.assert_not_called()


if __name__ == "__main__":
    unittest.main()
