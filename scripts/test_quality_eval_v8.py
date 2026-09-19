from copy import deepcopy
from decimal import Decimal
import json
from pathlib import Path
import tempfile
import unittest

from scripts.quality_eval_challenges import fixtures
from scripts.quality_eval_contract_v8 import candidate_judgments, dimensions, validate
from scripts.quality_eval_transport_v8 import initial_requests, review_request, case_bound, reserve, grade_case, Ledger
from scripts.test_quality_eval_transport import response


def typed(grade):
    result = deepcopy(grade)
    if result:
        for claim in result["claims"]:
            claim["kind"] = "factual"
    return result


class V8Tests(unittest.TestCase):
    def test_visible_contract_expectations_preserved(self):
        for item in fixtures():
            with self.subTest(case=item["id"]):
                result = dimensions(item["inputs"], typed(item["grade"]), item["payload"], item["evidence"], item["safety_flags"], item["review"])
                for key, expected in item["expected"].items():
                    self.assertEqual(result[key], expected)

    def test_explicit_speech_act_has_no_factual_or_citation_denominator(self):
        item = fixtures()[4]
        grade = typed(item["grade"])
        grade["claims"] = [{"text": item["inputs"]["answer"], "kind": "speech_act", "factual_status": "unknown", "source_spans": [],
                            "citation_status": "unknown", "citation_spans": [], "reason": "Pure access-refusal speech act."}]
        result = dimensions(item["inputs"], grade, item["payload"], item["evidence"], [], item["review"])
        self.assertEqual(result["overall"], "pass")
        self.assertEqual(result["factual_support"], "not_applicable")
        grade["claims"][0]["factual_status"] = "supported"
        self.assertIn("speech_act_contract", validate(grade, item["inputs"]))

    def test_reviewer_receives_negative_judgment_not_only_bad_answer(self):
        item = fixtures()[1]
        body = review_request(item["inputs"], typed(item["grade"]))
        data = json.loads(body["messages"][1]["content"])
        self.assertEqual(data["candidate_judgments"]["completeness"], "fail")
        self.assertEqual(data["candidate_judgments"]["response_behavior"], "fail")
        self.assertEqual(data["candidate_judgments"]["factual_support"], "pass")
        self.assertNotIn("expected", data)

    def test_projection_matches_reducer_before_review(self):
        for item in fixtures()[:17]:
            grade = typed(item["grade"])
            projected = candidate_judgments(item["inputs"], grade)
            result = dimensions(item["inputs"], grade, item["payload"], item["evidence"], [], item["review"])
            with self.subTest(case=item["id"]):
                for key, value in projected.items():
                    self.assertEqual(result[key], value)

    def test_reservation_bounds_actual_three_calls(self):
        item = fixtures()[0]
        grade = typed(item["grade"])
        actual = sum((reserve(body)["reserved_usd"] for _, body in initial_requests(item["inputs"])), Decimal(0))
        actual += reserve(review_request(item["inputs"], grade))["reserved_usd"]
        self.assertLessEqual(actual, case_bound(item["inputs"]))

    def test_typed_response_and_explicit_review_roundtrip(self):
        item = fixtures()[0]
        grade = typed(item["grade"])
        with tempfile.TemporaryDirectory() as temp:
            ledger = Ledger.initialize(Path(temp) / "ledger.json")
            def create(**body):
                keys = body["response_format"]["json_schema"]["schema"]["required"]
                full = item["review"] if "reason" in keys else grade
                return response({key: full[key] for key in keys})
            self.assertEqual(grade_case(create, item["inputs"], ledger, Path(temp) / "case"), (grade, item["review"]))


if __name__ == "__main__":
    unittest.main()
