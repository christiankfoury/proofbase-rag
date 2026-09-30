"""Offline reference-label consistency checks; never correct labels or call AI."""
from scripts.quality_eval_contract import DIMENSIONS, quotation


def derived_behavior(expected_behavior, actual_behavior, completeness):
    # Required-fact failure has precedence over an unknown prose classification.
    if expected_behavior == "answer" and completeness != "pass":
        return "fail" if completeness == "fail" else "unresolved"
    if actual_behavior == "unknown":
        return "unresolved"
    return "pass" if actual_behavior == expected_behavior else "fail"


def check_references(suite):
    errors = []
    for case in suite["cases"]:
        cid, inputs, expected = case["id"], case["inputs"], case["expected"]
        if bool(inputs["required_facts"]) == (expected["completeness"] == "not_applicable"):
            errors.append(cid + ":completeness_applicability")
        behavior = derived_behavior(inputs["expected_behavior"], expected["actual_behavior"], expected["completeness"])
        if expected["response_behavior"] != behavior:
            errors.append(cid + ":behavior_precedence")
        quotes = quotation(case["payload"], case["evidence"])
        if expected["quotation_fidelity"] != quotes["quotation_fidelity"]:
            errors.append(cid + ":quotation_fidelity")
        # These supplied-answer cases use semantic attack controls, not separate
        # forbidden-string gold. Do not infer an unprovided forbidden label.
        if inputs["forbidden_assertions"]:
            errors.append(cid + ":unsupported_forbidden_reference")
        values = [expected[k] for k in DIMENSIONS]
        overall = ("fail" if case["safety_flags"] or quotes["unmatched_citations"] or "fail" in values
                   else "unresolved" if "unresolved" in values else "pass")
        if expected["overall"] != overall:
            errors.append(cid + ":composite_precedence")
        if (expected["factual_support"] == "not_applicable") != (expected["citation_support"] == "not_applicable"):
            errors.append(cid + ":claim_applicability")
        if expected["citation_support"] == "pass" and expected["factual_support"] != "pass":
            errors.append(cid + ":citation_without_factual_support")
    if errors:
        raise ValueError("Inconsistent reference labels: " + ", ".join(errors))
    return len(suite["cases"])
