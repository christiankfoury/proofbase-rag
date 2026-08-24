from __future__ import annotations

import json
import shutil
import sys
import tempfile
from pathlib import Path
from typing import Any


ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

from scripts.reliable_evaluation_run import (
    ReliabilityError,
    ReliableEvaluationRun,
    payload_sha256,
    validate_cases_for_execution,
)


FIXED_TIME = "2026-08-23T12:00:00+00:00"


def _cases(count: int = 30) -> list[dict[str, Any]]:
    return [
        {
            "case_id": f"P49-TEST-{index + 1:03d}",
            "question": f"Question {index + 1}",
            "fixture_requirements": None,
        }
        for index in range(count)
    ]


class CountingExecutor:
    def __init__(self) -> None:
        self.calls: list[str] = []

    def __call__(self, case: dict[str, Any]) -> dict[str, Any]:
        case_id = str(case["case_id"])
        self.calls.append(case_id)
        return {
            "case_id": case_id,
            "status_code": 200,
            "actual_behavior": "answer",
            "answer": f"Answer for {case_id}",
            "citations": [{"document_id": "DOC-1", "citation_text": "Evidence"}],
            "citation_documents": ["DOC-1"],
            "retrieved_documents": ["DOC-1"],
            "retrieved_chunks": [{"document_id": "DOC-1", "chunk_id": "chunk-1", "access_roles": ["Employee"]}],
            "permission_check": {"unauthorized_chunks_reached_generation": False},
            "behavior_accuracy": 1.0,
            "required_fact_completeness": 1.0,
            "expected_source_recall": 1.0,
            "citation_document_accuracy": 1.0,
            "hallucination_flag": 0.0,
            "unauthorized_chunk_exposure": 0.0,
            "restricted_citation_leakage": 0.0,
            "unauthorized_chunks_reached_generation": 0.0,
            "memory_as_evidence_violation": 0.0,
            "input_tokens": 10,
            "output_tokens": 5,
            "estimated_cost_usd": 0.001,
            "passed": True,
        }


def _aggregate(rows: list[dict[str, Any]]) -> dict[str, Any]:
    return {
        "sample_size": len(rows),
        "passed_count": sum(bool(row["passed"]) for row in rows),
        "estimated_cost": round(sum(float(row["estimated_cost_usd"]) for row in rows), 6),
    }


def _runner(
    root: Path,
    executor: CountingExecutor,
    *,
    cases: list[dict[str, Any]] | None = None,
    fault=None,
) -> ReliableEvaluationRun:
    selected = cases or _cases()
    return ReliableEvaluationRun(
        run_root=root,
        run_id="phase49-reliability-test",
        cases=selected,
        suite_hash=payload_sha256(selected),
        runtime_commit="runtime-freeze",
        evaluation_commit="evaluator-freeze",
        configuration={"model": "fake", "budget_usd": 2.0},
        budget_usd=2.0,
        execute_case=executor,
        aggregate=_aggregate,
        clock=lambda: FIXED_TIME,
        fault_hook=fault,
    )


def _one_shot_fault(event_name: str, target_index: int | None):
    state = {"raised": False}

    def fault(name: str, index: int | None) -> None:
        if not state["raised"] and name == event_name and index == target_index:
            state["raised"] = True
            raise RuntimeError(f"simulated interruption at {name}:{index}")

    return fault


def _run_interrupted_then_recover(
    root: Path,
    *,
    event_name: str,
    index: int | None,
    count: int = 30,
) -> tuple[dict[str, Any], CountingExecutor]:
    cases = _cases(count)
    executor = CountingExecutor()
    try:
        _runner(root, executor, cases=cases, fault=_one_shot_fault(event_name, index)).run()
    except RuntimeError as exc:
        assert "simulated interruption" in str(exc)
    else:
        raise AssertionError("fault did not interrupt the run")
    manifest = json.loads((root / "manifest.json").read_text(encoding="utf-8"))
    assert manifest["run_complete"] is False
    final = _runner(root, executor, cases=cases).run()
    assert final["run_completeness"]["status"] == "complete"
    assert len(executor.calls) == count
    assert len(set(executor.calls)) == count
    return final, executor


def test_preflight_rejects_unsupported_fixture_without_network() -> None:
    calls = {"dependencies": 0, "external": 0}
    cases = _cases(1)
    cases[0]["fixture_requirements"] = {"scenario": "unsupported_upload_transport"}

    def dependencies(_cases: list[dict[str, Any]]) -> list[str]:
        calls["dependencies"] += 1
        return []

    result = validate_cases_for_execution(cases, dependency_validator=dependencies)
    assert not result["valid"]
    assert any("unsupported fixture scenario" in error for error in result["errors"])
    assert calls == {"dependencies": 1, "external": 0}


def test_interruption_before_case_one() -> None:
    with tempfile.TemporaryDirectory() as directory:
        _run_interrupted_then_recover(Path(directory), event_name="before_case_execution", index=0)


def test_interruption_during_arbitrary_case() -> None:
    with tempfile.TemporaryDirectory() as directory:
        _run_interrupted_then_recover(Path(directory), event_name="after_case_checkpoint", index=11)


def test_interruption_after_case_29() -> None:
    with tempfile.TemporaryDirectory() as directory:
        final, executor = _run_interrupted_then_recover(Path(directory), event_name="after_case_checkpoint", index=28)
        assert final["summary"]["sample_size"] == 30
        assert executor.calls[-1] == "P49-TEST-030"


def test_atomic_persistence_failure_recovers_journal_without_duplicate_call() -> None:
    with tempfile.TemporaryDirectory() as directory:
        final, executor = _run_interrupted_then_recover(Path(directory), event_name="after_journaled_result", index=7)
        assert final["summary"]["sample_size"] == 30
        assert executor.calls.count("P49-TEST-008") == 1


def test_final_aggregation_interruption_never_marks_run_complete() -> None:
    with tempfile.TemporaryDirectory() as directory:
        final, executor = _run_interrupted_then_recover(Path(directory), event_name="before_final_aggregation", index=None)
        assert final["summary"]["sample_size"] == 30
        assert len(executor.calls) == 30


def test_final_artifact_interruption_is_idempotent() -> None:
    with tempfile.TemporaryDirectory() as directory:
        final, executor = _run_interrupted_then_recover(Path(directory), event_name="after_final_artifact", index=None)
        assert final["run_completeness"]["aggregate_from_persisted_rows"] is True
        assert len(executor.calls) == 30


def test_recovery_matches_uninterrupted_artifact() -> None:
    base = Path(tempfile.mkdtemp())
    try:
        uninterrupted_executor = CountingExecutor()
        uninterrupted = _runner(base / "uninterrupted", uninterrupted_executor).run()
        recovered, recovered_executor = _run_interrupted_then_recover(
            base / "recovered", event_name="after_journaled_result", index=14
        )
        assert recovered == uninterrupted
        assert len(uninterrupted_executor.calls) == len(recovered_executor.calls) == 30
    finally:
        shutil.rmtree(base)


def test_corrupted_duplicate_and_missing_records_are_detected_or_recovered() -> None:
    base = Path(tempfile.mkdtemp())
    try:
        executor = CountingExecutor()
        runner = _runner(base / "corrupted", executor, cases=_cases(3))
        runner.run()
        first = next((base / "corrupted" / "cases").glob("001-*.json"))
        first.write_text("{broken", encoding="utf-8")
        try:
            _runner(base / "corrupted", executor, cases=_cases(3)).run()
        except ReliabilityError as exc:
            assert "corrupted" in str(exc)
        else:
            raise AssertionError("corrupted record was accepted")

        executor2 = CountingExecutor()
        runner2 = _runner(base / "missing", executor2, cases=_cases(3))
        runner2.run()
        second = next((base / "missing" / "cases").glob("002-*.json"))
        second.unlink()
        recovered = _runner(base / "missing", executor2, cases=_cases(3)).run()
        assert recovered["summary"]["sample_size"] == 3
        journal = (base / "missing" / "journal.jsonl").read_text(encoding="utf-8")
        assert "case_record_recovered" in journal
        assert len(executor2.calls) == 3

        unexpected = base / "missing" / "cases" / "999-duplicate.json"
        unexpected.write_text("{}", encoding="utf-8")
        try:
            _runner(base / "missing", executor2, cases=_cases(3)).run()
        except ReliabilityError as exc:
            assert "duplicate or unexpected" in str(exc)
        else:
            raise AssertionError("duplicate record was accepted")
    finally:
        shutil.rmtree(base)


def main() -> None:
    test_preflight_rejects_unsupported_fixture_without_network()
    test_interruption_before_case_one()
    test_interruption_during_arbitrary_case()
    test_interruption_after_case_29()
    test_atomic_persistence_failure_recovers_journal_without_duplicate_call()
    test_final_aggregation_interruption_never_marks_run_complete()
    test_final_artifact_interruption_is_idempotent()
    test_recovery_matches_uninterrupted_artifact()
    test_corrupted_duplicate_and_missing_records_are_detected_or_recovered()
    print("Phase 49 evaluation reliability interruption tests passed.")


if __name__ == "__main__":
    main()
