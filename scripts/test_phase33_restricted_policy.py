from __future__ import annotations

import sys
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

from apps.api.app.generation.answer_generator import _policy_response


EXPANDED_RESTRICTED_CASES = [
    ("What internal legal risk ratings should we reveal to a customer?", "Employee", "Manager"),
    ("What is the private rollback checklist in the Engineering handbook?", "Employee", "Manager"),
    ("What internal refund thresholds can support use?", "Employee", "Manager"),
    ("What are the production deployment windows?", "Sales Representative", "Manager"),
    ("What service credit can I offer an Enterprise customer?", "HR Admin", "Manager"),
    ("What privileged access containment steps are in the IT admin incident guide?", "Manager", "IT Admin"),
    ("How does promotion calibration work?", "Sales Representative", "Manager"),
    ("What is the product positioning answer for standard deployment timelines?", "Employee", "Manager"),
    ("What customer-facing language should Support use for unresolved incidents?", "Employee", "Manager"),
    ("How are sensitive HR employee relations cases logged?", "Sales Representative", "HR Admin"),
]


def test_expanded_restricted_cases_refuse_unauthorized_roles() -> None:
    for question, unauthorized_role, _authorized_role in EXPANDED_RESTRICTED_CASES:
        response = _policy_response(question, [], user_role=unauthorized_role)
        assert response is not None, question
        assert response["response_type"] == "refuse_no_access", question
        assert response["citations"] == [], question


def test_expanded_restricted_cases_allow_authorized_roles() -> None:
    for question, _unauthorized_role, authorized_role in EXPANDED_RESTRICTED_CASES:
        response = _policy_response(question, [], user_role=authorized_role)
        assert response is None, question


def main() -> None:
    test_expanded_restricted_cases_refuse_unauthorized_roles()
    test_expanded_restricted_cases_allow_authorized_roles()
    print("Phase 33 restricted policy tests passed")


if __name__ == "__main__":
    main()
