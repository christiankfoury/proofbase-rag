"""Reproduce public tables from saved evidence, without API or database imports.

This audits historical observations. It neither executes questions nor judges
answers anew. --check is read-only and detects drift in the published report.
"""
from __future__ import annotations

import argparse
from collections import Counter
import json
from pathlib import Path
from statistics import mean
import sys

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

from apps.api.app.evaluation.answer_metrics import answer_accuracy, citation_accuracy
from scripts.reliable_evaluation_run import payload_sha256

EVAL = "data/evaluation/"
HOLDOUT = EVAL + "independent-generalization/runs/phase49-independent-holdout-v3/"
REPORT = EVAL + "public-evidence.json"
METRICS = ("answer_accuracy", "citation_accuracy", "hallucination_rate", "response_type_accuracy")


def require(condition: bool, message: str) -> None:
    if not condition:
        raise ValueError(message)


def unique_rows(rows: list[dict], key: str) -> dict[str, dict]:
    indexed = {row[key]: row for row in rows}
    require(len(indexed) == len(rows), f"Duplicate {key}")
    return indexed


def metric(values: list[float | None]) -> dict:
    scored = [value for value in values if value is not None]
    require(all(type(v) in (int, float) and 0 <= v <= 1 for v in scored), "Invalid score")
    return {
        "scored_cases": len(scored),
        "excluded_cases": len(values) - len(scored),
        "score_sum": round(sum(scored), 6),
        "mean": round(mean(scored), 3) if scored else None,
    }


def regression(artifact: dict, questions: dict[str, dict]) -> dict:
    rows = artifact["rows"]
    indexed = unique_rows(rows, "question_id")
    require(indexed.keys() == questions.keys(), "Regression must cover the complete benchmark")
    summary = artifact["summary"]
    for qid, row in indexed.items():
        require(row["question"] == questions[qid]["question"], f"Question drift: {qid}")
        require(row["expected_behavior"] == questions[qid]["expected_behavior"], f"Behavior drift: {qid}")
        for key, scorer in (("answer_accuracy", answer_accuracy), ("citation_accuracy", citation_accuracy)):
            require(row[key] == scorer(questions[qid], row), f"Stored {key} disagrees with scorer: {qid}")
    scores = {key: metric([row[key] for row in rows]) for key in METRICS}
    for key, result in scores.items():
        require(result["mean"] == round(float(summary[key]), 3), f"Summary mismatch: {key}")
    failed = unique_rows(artifact["failed_questions"], "question_id")
    require(failed.keys() <= indexed.keys(), "Unknown failed question")
    require(len(failed) == summary["failed_question_count"], "Failure count mismatch")
    return {
        "run_id": summary["experiment_id"],
        "sample_size": len(rows),
        "recorded_failed_cases": len(failed),
        "recorded_failure_taxonomy": dict(sorted(Counter(row["failure_type"] for row in failed.values()).items())),
        "metrics": scores,
        "diagnostic_notes": summary.get("diagnostic_submetric_note_count"),
        "configuration": artifact["config"],
        "category_counts": dict(sorted(Counter(row["question_type"] for row in rows).items())),
    }


def verify_holdout(final: dict, manifest: dict, records: list[dict], events: list[dict]) -> None:
    ids = manifest["case_ids"]
    require(len(set(ids)) == len(ids) == manifest["case_count"], "Invalid case inventory")
    require(len(records) == len(ids), "Missing or extra case records")
    require(manifest["run_complete"] and final["status"] == "complete", "Incomplete run")
    previous = "GENESIS"
    for index, event in enumerate(events, start=1):
        require(event["sequence"] == index and event["previous_hash"] == previous, "Broken journal chain")
        unsigned = {k: v for k, v in event.items() if k != "event_hash"}
        require(event["event_hash"] == payload_sha256(unsigned), "Corrupt journal event")
        previous = event["event_hash"]
    require(events[0]["event"] == "run_started" and events[-1]["event"] == "run_completed", "Incomplete journal")
    for kind in ("case_started", "case_completed"):
        require([event["case_id"] for event in events if event["event"] == kind] == ids, f"Invalid {kind} sequence")
    for index, record in enumerate(records):
        require(record["case_id"] == ids[index] and record["case_index"] == index, "Case order mismatch")
        require(record["attempt_count"] == 1 and record["status"] == "completed", "Invalid attempt/status")
        unsigned = {k: v for k, v in record.items() if k != "record_hash"}
        require(record["record_hash"] == payload_sha256(unsigned), "Corrupt case record")
        for key in ("suite_hash", "runtime_commit", "evaluation_commit", "run_id"):
            require(record[key] == manifest[key], f"Case provenance mismatch: {key}")
        require(record["case_hash"] == manifest["case_hashes"][index], "Case hash mismatch")
        completed = next(e for e in events if e["event"] == "case_completed" and e["case_id"] == ids[index])
        require(completed["record_hash"] == record["record_hash"], "Journal/record mismatch")
    require(records == final["execution_records"], "Final records mismatch")
    require([record["row"] for record in records] == final["rows"], "Final rows mismatch")
    require(payload_sha256(final) == manifest["final_artifact_hash"] == events[-1]["final_hash"], "Final hash mismatch")


def holdout_summary(final: dict) -> dict:
    rows = final["rows"]
    unique_rows(rows, "case_id")
    passed = sum(row["passed"] is True for row in rows)
    require(passed == final["summary"]["passed_count"], "Holdout pass count mismatch")
    require(len(rows) == final["summary"]["sample_size"], "Holdout sample mismatch")
    failed = [row["case_id"] for row in rows if not row["passed"]]
    require(failed == final["summary"]["failed_case_ids"], "Holdout failures mismatch")
    answer_rows = [row for row in rows if row["expected_behavior"] == "answer"]
    keys = {"behavior_accuracy": (rows, "behavior_accuracy"),
            "required_fact_completeness": (answer_rows, "required_fact_completeness"),
            "citation_document_accuracy": (answer_rows, "citation_document_accuracy"),
            "expected_source_recall": (answer_rows, "expected_source_recall"),
            "hallucination_rate": (rows, "hallucination_flag")}
    scores = {name: metric([row[key] for row in subset]) for name, (subset, key) in keys.items()}
    for key, result in scores.items():
        require(result["mean"] == final["summary"]["metrics"][key], f"Holdout metric mismatch: {key}")
    return {
        "run_id": final["run_id"], "sample_size": len(rows), "automated_passes": passed,
        "automated_pass_rate": round(passed / len(rows), 4), "failed_case_ids": failed,
        "metrics": scores, "provenance": final["provenance"],
        "categories": {category: {"sample_size": len(group), "passed": sum(row["passed"] for row in group)}
                       for category in sorted({row["category"] for row in rows})
                       for group in [[row for row in rows if row["category"] == category]]},
        "safety_violations_all_rows": {key: sum(row[key] > 0 for row in rows) for key in (
            "unauthorized_chunk_exposure", "restricted_citation_leakage",
            "unauthorized_chunks_reached_generation", "memory_as_evidence_violation")},
        "dedicated_safety_denominators": final["summary"]["numerators_denominators"],
    }


def build_report(root: Path = ROOT) -> dict:
    hashes: dict[str, str] = {}

    def read(path: str) -> dict:
        payload = json.loads((root / path).read_text(encoding="utf-8"))
        hashes[path] = payload_sha256(payload)
        return payload

    benchmark = read(EVAL + "benchmark-questions.json")
    questions = unique_rows(benchmark["questions"], "question_id")
    require(len(questions) == benchmark["question_count"], "Benchmark count mismatch")
    runs = [regression(read(EVAL + f"expanded-baseline/{name}.json"), questions) for name in (
        "phase32-expanded-answer-generation-v5", "phase50-manual-findings-regression")]
    final, manifest = read(HOLDOUT + "final.json"), read(HOLDOUT + "manifest.json")
    records = [read(path.relative_to(root).as_posix()) for path in sorted((root / HOLDOUT / "cases").glob("*.json"))]
    events = [json.loads(line) for line in (root / HOLDOUT / "journal.jsonl").read_text(encoding="utf-8").splitlines()]
    hashes[HOLDOUT + "journal.jsonl"] = payload_sha256(events)
    verify_holdout(final, manifest, records, events)
    permission = read(EVAL + "phase46-permission-evaluation.json")
    unauthorized, authorized = permission["unauthorized_rows"], permission["authorized_rows"]
    expected_permission_ids = {qid for qid, q in questions.items() if q["question_type"] == "permission_restricted"}
    require(unique_rows(unauthorized, "question_id").keys() == expected_permission_ids, "Permission coverage mismatch")
    require(unique_rows(authorized, "question_id").keys() == expected_permission_ids, "Authorized coverage mismatch")
    permission_scores = {key: metric([row[key] for row in unauthorized]) for key in (
        "permission_leakage", "unauthorized_chunk_exposure", "restricted_citation_leakage", "unauthorized_chunks_reached_generation")}
    for key, result in permission_scores.items():
        require(result["mean"] == float(permission["summary"][key + "_rate"]), "Permission summary mismatch")
    return {
        "schema_version": "public-evidence.v1",
        "method": "Offline aggregation of saved scores; answer/citation rescoring; durable holdout integrity checks. No new inference or human adjudication.",
        "benchmark": {"version": benchmark["benchmark_version"], "sample_size": len(questions),
                      "difficulty_counts": dict(sorted(Counter(q["difficulty"] for q in questions.values()).items())),
                      "expected_behavior_counts": dict(sorted(Counter(q["expected_behavior"] for q in questions.values()).items()))},
        "historical_regressions": runs,
        "historical_holdout": holdout_summary(final),
        "focused_permission": {"run_id": permission["summary"]["run_id"], "unauthorized_cases": len(unauthorized),
                               "authorized_controls": len(authorized), "metrics": permission_scores,
                               "authorized_answer_quality": "not measured"},
        "source_hash_format": "SHA-256 of canonical JSON (journal parsed as array); portable across checkout line endings; not a replacement for original raw-byte seals.",
        "source_hashes": dict(sorted(hashes.items())),
    }


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--check", action="store_true", help="Fail if the committed report differs; write nothing.")
    args = parser.parse_args()
    report = build_report()
    path = ROOT / REPORT
    if args.check:
        require(path.exists() and json.loads(path.read_text(encoding="utf-8")) == report, "Public report drift; regenerate and review it")
        print("Public evidence verified: 130-case regressions, 30 durable holdout rows, 20 permission pairs; no external calls.")
    else:
        path.write_text(json.dumps(report, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")
        print(f"Wrote {REPORT}")


if __name__ == "__main__":
    main()
