"""Reconstruct saved automated verdicts offline; never invokes the model grader."""
from __future__ import annotations
import argparse
from collections import Counter
import json
from pathlib import Path
import sys
ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))
from scripts.fresh_eval_protocol import FOLDER, digest, verify_custody
from scripts.fresh_eval_grader import verdict
from scripts.run_fresh_eval import summarize
from scripts.reliable_evaluation_run import write_json_atomic


def reconstruct():
    freeze = json.loads((FOLDER / "freeze.json").read_text())
    base = {"runtime_commit": freeze["commit"], "run_id": "fresh-current-run-v1", "suite_version": "fresh-current-1",
            "human_review": "pending", "status": "not_started", "expected_cases": 60, "completed_cases": 0,
            "full_response": {"passed": 0, "total": 0, "rate": None},
            "answer_expected": {"passed": 0, "total": 0, "rate": None},
            "non_answer_expected": {"passed": 0, "total": 0, "rate": None},
            "categories": {}, "difficulty": {}, "safety_flags": {}, "failure_taxonomy": {},
            "cost_usd_including_calibration": None, "record_hashes": {}}
    run = FOLDER / "run-v1"
    if not run.exists():
        return base
    _, suite = verify_custody()
    rows = []
    for case in suite["cases"]:
        path = run / (case["case_id"] + ".json")
        if not path.exists():
            continue
        base["record_hashes"][path.name] = digest(path)
        row = json.loads(path.read_text())
        if row["case_id"] != case["case_id"]:
            raise ValueError("Mismatched durable row identity")
        if row["status"] != "complete":
            continue
        payload = dict(row["raw_response"])
        payload["citations"] = [dict(c, citation_id=f"C{i}") for i, c in enumerate(payload.get("citations", []), 1)]
        replay = verdict(case, payload, row["authorized_evidence"], row["grade"], row["safety_flags"])
        if any(row[k] != v for k, v in replay.items()):
            raise ValueError("Stored verdict differs from deterministic replay")
        rows.append(row)
    summary = summarize(suite["cases"], rows)
    saved = json.loads((FOLDER / "summary.json").read_text())
    if any(saved[k] != v for k, v in summary.items()):
        raise ValueError("Saved aggregate differs from durable rows")
    ledger = json.loads((FOLDER / "api-ledger.json").read_text())
    cost = sum(c["charged_usd"] for c in ledger["calls"])
    if abs(cost - saved["cost_usd_including_calibration"]) > 1e-10:
        raise ValueError("Saved cost differs from ledger")
    base.update(summary, cost_usd_including_calibration=cost)
    base["categories"] = {category: {"passed": sum(r["passed"] for r in rows if r["category"] == category),
                                     "completed": sum(r["category"] == category for r in rows),
                                     "planned": sum(c["category"] == category for c in suite["cases"])}
                          for category in sorted({c["category"] for c in suite["cases"]})}
    base["difficulty"] = dict(Counter(c["difficulty"] for c in suite["cases"]))
    base["safety_flags"] = dict(Counter(f for r in rows for f in r["safety_flags"]))
    hard_reasons = {"forbidden_assertion", "citation_not_in_authorized_retrieval",
                    "unauthorized_returned_evidence", "runtime_reports_unauthorized_generation",
                    "unknown_returned_chunk", "returned_identity_mismatch"}
    base["hard_failure_reasons"] = dict(Counter(f for r in rows for f in r["failure_reasons"] if f in hard_reasons))
    base["safety_gate_met"] = (summary["status"] == "complete" and not base["hard_failure_reasons"]
                               and all(r["grader_valid"] for r in rows))
    base["combined_gate_met"] = summary["target_met"] and base["safety_gate_met"]
    base["suite_sha256"] = digest(FOLDER / "holdout.json")
    return base


def human_packet():
    _, suite = verify_custody()
    lines = ["# Fresh holdout: human review packet", "",
             "Status: **pending**. This packet is prepared by an agent; it is not evidence of human review.", "",
             "For every case, a named person must inspect the question, history, expected facts, complete response and exact cited passages. Record correctness, completeness, source support and permission issues in `data/evaluation/fresh-current/human-review.json`, with name and UTC timestamp. Preserve disagreements with the automated rubric. Do not modify sealed labels or original responses.", "",
             "Source documents and response files are linked below. Missing responses are incomplete, not passes. In the automated grade, C1 means the first citation in raw_response.citations, C2 the second, and so on. Make your own decision before comparing the automated verdict.", ""]
    for case in suite["cases"]:
        path = FOLDER / "run-v1" / (case["case_id"] + ".json")
        row = json.loads(path.read_text()) if path.exists() else {}
        lines.extend([f"## {case['case_id']} — {case['category']}", "", f"Role: {case['user_role']}; expected: {case['expected_behavior']}; difficulty: {case['difficulty']}", "",
                      f"Question: {case['question']}", "", f"Label rationale: {case['rationale']}", ""])
        for turn in case.get("previous_turns", []):
            lines.extend([f"Prior {turn['role']}: {turn['content']}", ""])
        for fact in case["required_facts"]:
            lines.extend([f"- {fact['fact_id']}: {fact['text']} — [source](../../{fact['source_path']})", f"  Source quote: {fact['source_quote']}", ""])
        lines.extend(["Forbidden assertions: " + json.dumps(case.get("forbidden_assertions", []), ensure_ascii=False), "",
                      "Response: " + row.get("raw_response", {}).get("answer", "No saved answer"), "",
                      f"[Full response, citations and automated grading](../../data/evaluation/fresh-current/run-v1/{case['case_id']}.json)", "",
                      "Human decision: pending. Reviewer: pending. Reviewed at: pending. Notes: pending.", ""])
    return "\n".join(lines)


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--check", action="store_true")
    parser.add_argument("--human-packet", action="store_true")
    args = parser.parse_args()
    report = reconstruct()
    path = FOLDER / "public-report.json"
    if args.check:
        if not path.exists() or json.loads(path.read_text()) != report:
            raise SystemExit("Fresh public report is stale")
        print("Fresh saved verdicts, denominators and hashes verified offline; semantic judgments are not revalidated")
    else:
        write_json_atomic(path, report)
        print(report["status"], report["completed_cases"], "completed cases")
    if args.human_packet:
        (ROOT / "docs/phase-65/human-review-packet.md").write_text(human_packet(), encoding="utf-8")


if __name__ == "__main__":
    main()
