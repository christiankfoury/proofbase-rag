from __future__ import annotations

import argparse
import json
import sys
from datetime import UTC, datetime
from pathlib import Path
from statistics import mean
from typing import Any


ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

from apps.api.app.db.session import get_connection
from apps.api.app.evaluation.run_benchmark import run_benchmark
from apps.api.app.permissions.access_control import role_can_access
from apps.api.app.retrieval.config import default_retrieval_config


BENCHMARK_PATH = ROOT / "data/evaluation/benchmark-questions.json"
OUTPUT_PATH = ROOT / "data/evaluation/phase33-no-egress-candidates.json"
REPORT_PATH = ROOT / "docs/phase-33/no-egress-candidates.md"
TOP_K_VALUES = [1, 2, 3, 4, 5]


def _run_name(top_k: int) -> str:
    return f"phase33-no-egress-keyword-top{top_k}"


def _retrieval_run_name(top_k: int) -> str:
    return f"{_run_name(top_k)}-retrieval"


def _benchmark_questions_by_id() -> dict[str, dict[str, Any]]:
    benchmark = json.loads(BENCHMARK_PATH.read_text(encoding="utf-8"))
    return {str(question["question_id"]): question for question in benchmark["questions"]}


def _avg(values: list[float | int | None]) -> float | None:
    real = [float(value) for value in values if value is not None]
    return round(mean(real), 3) if real else None


def _load_latest_run_ids() -> dict[int, str]:
    latest: dict[int, str] = {}
    with get_connection() as conn:
        rows = conn.execute(
            """
            select id::text, run_name, top_k
            from evaluation_runs
            where run_name like 'phase33-no-egress-keyword-top%-retrieval'
            order by started_at
            """
        ).fetchall()
    for row in rows:
        latest[int(row["top_k"])] = str(row["id"])
    return latest


def _rows_for_run(run_id: str) -> list[dict[str, Any]]:
    with get_connection() as conn:
        rows = conn.execute(
            """
            select
              question_id,
              question_type,
              user_role,
              retrieval_hit_score,
              all_sources_hit_score,
              expected_source_recall,
              precision_at_k,
              mrr,
              latency_ms,
              retrieved_chunks_json
            from evaluation_results
            where evaluation_run_id = %s
            order by question_id
            """,
            (run_id,),
        ).fetchall()
    return [dict(row) for row in rows]


def _permission_boundary(rows: list[dict[str, Any]], questions: dict[str, dict[str, Any]]) -> dict[str, Any]:
    restricted_rows = [row for row in rows if row["question_type"] == "permission_restricted"]
    exposure_values: list[float] = []
    generation_values: list[float] = []
    exposed_questions: list[str] = []
    generation_questions: list[str] = []

    for row in restricted_rows:
        question = questions[row["question_id"]]
        expected_documents = set(question.get("expected_source_document") or [])
        chunks = row.get("retrieved_chunks_json") or []
        retrieved_documents = {chunk.get("document_id") for chunk in chunks if chunk.get("document_id")}
        exposed = bool(expected_documents.intersection(retrieved_documents))
        unauthorized = [
            chunk
            for chunk in chunks
            if not role_can_access(list(chunk.get("access_roles") or []), str(row["user_role"]))
        ]
        exposure_values.append(1.0 if exposed else 0.0)
        generation_values.append(1.0 if unauthorized else 0.0)
        if exposed:
            exposed_questions.append(str(row["question_id"]))
        if unauthorized:
            generation_questions.append(str(row["question_id"]))

    return {
        "restricted_question_count": len(restricted_rows),
        "unauthorized_chunk_exposure_rate": _avg(exposure_values),
        "unauthorized_chunks_reached_generation_rate": _avg(generation_values),
        "exposed_questions": exposed_questions,
        "unauthorized_generation_questions": generation_questions,
    }


def _summary_for_run(top_k: int, run_id: str, questions: dict[str, dict[str, Any]]) -> dict[str, Any]:
    rows = _rows_for_run(run_id)
    source_rows = [row for row in rows if row["all_sources_hit_score"] is not None]
    failed_questions = [
        str(row["question_id"])
        for row in source_rows
        if row["all_sources_hit_score"] is not None and float(row["all_sources_hit_score"]) < 1.0
    ]
    metrics = {
        "any_source_hit": _avg([row["retrieval_hit_score"] for row in source_rows]),
        "all_sources_hit": _avg([row["all_sources_hit_score"] for row in source_rows]),
        "expected_source_recall": _avg([row["expected_source_recall"] for row in source_rows]),
        "precision_at_k": _avg([row["precision_at_k"] for row in source_rows]),
        "mrr": _avg([row["mrr"] for row in source_rows]),
        "average_latency_ms": _avg([row["latency_ms"] for row in rows]),
        "failed_question_count": len(failed_questions),
    }
    return {
        "run_id": run_id,
        "run_name": _retrieval_run_name(top_k),
        "retrieval_mode": "keyword_only",
        "chunking_strategy": "section_based",
        "top_k": top_k,
        "total_questions": len(rows),
        "source_question_count": len(source_rows),
        "metrics": metrics,
        "failed_questions": failed_questions,
        "phase33_gate": {
            "precision_target_met": (metrics["precision_at_k"] or 0.0) >= 0.75,
            "recall_gate_met": (metrics["expected_source_recall"] or 0.0) >= 0.95,
            "mrr_gate_met": (metrics["mrr"] or 0.0) >= 0.95,
        },
        "permission_boundary": _permission_boundary(rows, questions),
    }


def _run_missing_candidates(existing: dict[int, str]) -> None:
    for top_k in TOP_K_VALUES:
        if top_k in existing:
            continue
        config = default_retrieval_config(
            run_name=_run_name(top_k),
            retrieval_mode="keyword_only",
            chunking_strategy="section_based",
            top_k=top_k,
        )
        run_benchmark(retrieval_only=True, config=config, write_report=False, include_results=False)


def _write_report(payload: dict[str, Any]) -> None:
    REPORT_PATH.parent.mkdir(parents=True, exist_ok=True)
    lines = [
        "# Phase 33 No-Egress Retrieval Candidates",
        "",
        f"Generated at: {payload['generated_at']}",
        "",
        "## Scope",
        "",
        "- Method: local Postgres full-text retrieval using `keyword_only` mode.",
        "- Network/API use: none.",
        "- Answer generation: skipped.",
        "- This is safe negative/triage evidence; it does not replace the OpenAI-backed vector rerank live gate.",
        "",
        "## Candidate Results",
        "",
        "| Top K | Precision@k | Source Recall | MRR | Failed Source Questions | Unauthorized Chunk Exposure | Unauthorized Chunks Reached Generation | Precision Gate | Recall Gate | MRR Gate |",
        "| ---: | ---: | ---: | ---: | ---: | ---: | ---: | --- | --- | --- |",
    ]
    for candidate in payload["candidates"]:
        metrics = candidate["metrics"]
        gate = candidate["phase33_gate"]
        permission = candidate["permission_boundary"]
        lines.append(
            "| {top_k} | {precision:.3f} | {recall:.3f} | {mrr:.3f} | {failed} | {exposure:.3f} | {generation:.3f} | {precision_gate} | {recall_gate} | {mrr_gate} |".format(
                top_k=candidate["top_k"],
                precision=metrics["precision_at_k"] or 0.0,
                recall=metrics["expected_source_recall"] or 0.0,
                mrr=metrics["mrr"] or 0.0,
                failed=metrics["failed_question_count"],
                exposure=permission["unauthorized_chunk_exposure_rate"] or 0.0,
                generation=permission["unauthorized_chunks_reached_generation_rate"] or 0.0,
                precision_gate="pass" if gate["precision_target_met"] else "fail",
                recall_gate="pass" if gate["recall_gate_met"] else "fail",
                mrr_gate="pass" if gate["mrr_gate_met"] else "fail",
            )
        )
    lines.extend(
        [
            "",
            "## Findings",
            "",
            "- No keyword-only no-egress candidate satisfies all Phase 33 retrieval gates.",
            "- Top-1 passes the precision target but fails recall and MRR.",
            "- Top-4 and top-5 preserve recall but miss the precision target and MRR gate.",
            "- Permission-boundary retrieval checks show zero unauthorized chunks reaching the retrieved context for these keyword-only runs.",
            "- The vector lexical rerank live run remains the next required gate, but it requires explicit approval for external embedding API data egress.",
            "",
        ]
    )
    REPORT_PATH.write_text("\n".join(lines), encoding="utf-8")


def main() -> None:
    parser = argparse.ArgumentParser(description="Summarize Phase 33 no-egress keyword retrieval candidates.")
    parser.add_argument(
        "--run-missing",
        action="store_true",
        help="Run any missing keyword-only retrieval sweeps before writing artifacts.",
    )
    args = parser.parse_args()

    existing = _load_latest_run_ids()
    if args.run_missing:
        _run_missing_candidates(existing)
        existing = _load_latest_run_ids()

    missing = [top_k for top_k in TOP_K_VALUES if top_k not in existing]
    if missing:
        missing_list = ", ".join(str(top_k) for top_k in missing)
        raise SystemExit(f"Missing no-egress keyword runs for top-k: {missing_list}. Re-run with --run-missing.")

    questions = _benchmark_questions_by_id()
    candidates = [_summary_for_run(top_k, existing[top_k], questions) for top_k in TOP_K_VALUES]
    payload = {
        "generated_at": datetime.now(UTC).isoformat(),
        "benchmark_version": json.loads(BENCHMARK_PATH.read_text(encoding="utf-8")).get("benchmark_version"),
        "method": "keyword_only_top_k_sweep",
        "network_api_use": "none",
        "answer_generation": "skipped",
        "candidates": candidates,
        "notes": [
            "Keyword-only retrieval is a no-egress local baseline and does not call OpenAI embeddings.",
            "No candidate satisfies precision, recall, and MRR gates together.",
            "Permission-boundary metrics are retrieval-only and do not measure answer refusal or citation leakage.",
        ],
    }
    OUTPUT_PATH.write_text(json.dumps(payload, indent=2), encoding="utf-8")
    _write_report(payload)
    print(json.dumps({"candidates": len(candidates), "output": str(OUTPUT_PATH), "report": str(REPORT_PATH)}, indent=2))


if __name__ == "__main__":
    main()
