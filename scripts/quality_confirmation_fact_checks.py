"""Pre-execution consistency for independently authored intermediate fact labels."""
from scripts.quality_confirmation_reference_checks import check_references

def check_fact_references(suite):
    check_references(suite)
    for case in suite["cases"]:
        labels = case["expected_fact_statuses"]
        ids = {f["fact_id"] for f in case["inputs"]["required_facts"]}
        if set(labels) != ids or any(s not in {"covered", "missing", "contradicted", "unknown"} for s in labels.values()):
            raise ValueError("Invalid fact-status reference: " + case["id"])
        values = list(labels.values())
        expected = ("not_applicable" if not values else "fail" if any(s in {"missing", "contradicted"} for s in values)
                    else "unresolved" if "unknown" in values else "pass")
        if expected != case["expected"]["completeness"]:
            raise ValueError("Fact-status/completeness mismatch: " + case["id"])
    return len(suite["cases"])
