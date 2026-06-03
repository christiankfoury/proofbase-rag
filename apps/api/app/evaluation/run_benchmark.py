from __future__ import annotations

import json
from datetime import UTC, datetime
from pathlib import Path
from statistics import mean
import time

from apps.api.app.core.config import get_settings
from apps.api.app.db.session import get_connection
from apps.api.app.evaluation.metrics import (
    behavior_match,
    citation_source_match,
    reciprocal_rank,
    retrieval_hit,
)
from apps.api.app.generation.answer_generator import generate_answer
from apps.api.app.retrieval.vector_retriever import retrieve_chunks


BENCHMARK_PATH = Path("data/evaluation/benchmark-questions.json")
REPORT_PATH = Path("docs/phase-5/baseline-evaluation-results.md")


def _load_benchmark() -> dict:
    return json.loads(BENCHMARK_PATH.read_text(encoding="utf-8"))


def _query_with_memory(question: dict) -> str:
    previous_turns = question.get("previous_turns") or []
    if not previous_turns:
        return question["question"]
    context = "\n".join(f"{turn['role']}: {turn['content']}" for turn in previous_turns)
    return f"Previous conversation:\n{context}\n\nFollow-up question:\n{question['question']}"


def _create_run(retrieval_only: bool = False) -> str:
    settings = get_settings()
    config = {
        "run_name": "baseline-vector-only-retrieval" if retrieval_only else "baseline-vector-only",
        "retrieval_mode": "vector_only",
        "chunking_strategy": "section_based",
        "top_k": settings.default_top_k,
        "prompt_version": "answer_v1",
        "model": settings.openai_chat_model,
        "retrieval_only": retrieval_only,
    }
    with get_connection() as conn:
        row = conn.execute(
            """
            insert into evaluation_runs (run_name, config_json, retrieval_mode, chunking_strategy, top_k, model)
            values (%s, %s::jsonb, %s, %s, %s, %s)
            returning id::text
            """,
            (
                config["run_name"],
                json.dumps(config),
                config["retrieval_mode"],
                config["chunking_strategy"],
                config["top_k"],
                config["model"],
            ),
        ).fetchone()
    return row["id"]


def _store_result(run_id: str, question: dict, result: dict) -> None:
    with get_connection() as conn:
        conn.execute(
            """
            insert into evaluation_results (
              evaluation_run_id,
              question_id,
              question_type,
              user_role,
              expected_behavior,
              generated_behavior,
              expected_source_documents,
              retrieved_source_documents,
              generated_answer,
              retrieval_hit_score,
              mrr,
              citation_source_match,
              behavior_match,
              latency_ms,
              notes
            )
            values (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s)
            """,
            (
                run_id,
                question["question_id"],
                question["question_type"],
                question["user_role"],
                question["expected_behavior"],
                result["generated_behavior"],
                question.get("expected_source_document") or [],
                result["retrieved_source_documents"],
                result["answer"],
                result["retrieval_hit"],
                result["mrr"],
                result["citation_source_match"],
                result["behavior_match"],
                result["latency_ms"],
                result["notes"],
            ),
        )


def _write_report(summary: dict, results: list[dict]) -> None:
    REPORT_PATH.parent.mkdir(parents=True, exist_ok=True)
    lines = [
        "# Baseline Evaluation Results",
        "",
        f"Generated at: {datetime.now(UTC).isoformat()}",
        "",
        "## Run Summary",
        "",
        f"- Questions: {summary['question_count']}",
        f"- Retrieval mode: vector_only",
        f"- Chunking strategy: section_based",
        f"- Top K: {summary['top_k']}",
        f"- Retrieval hit rate: {summary['retrieval_hit_rate']}",
        f"- MRR: {summary['mrr']}",
        f"- Citation source match: {summary['citation_source_match']}",
        f"- Behavior match: {summary['behavior_match']}",
        "",
        "Answer accuracy, faithfulness, and hallucination rate are pending because they require human review or an evaluation judge.",
        "",
        "## Question Results",
        "",
        "| Question ID | Type | Expected Behavior | Generated Behavior | Retrieval Hit | MRR | Citation Match |",
        "|---|---|---|---|---:|---:|---:|",
    ]
    for result in results:
        lines.append(
            "| {question_id} | {question_type} | {expected_behavior} | {generated_behavior} | {retrieval_hit} | {mrr} | {citation_source_match} |".format(
                **result
            )
        )
    REPORT_PATH.write_text("\n".join(lines) + "\n", encoding="utf-8")


def _average(values: list[float | None]) -> str:
    real_values = [value for value in values if value is not None]
    if not real_values:
        return "pending"
    return f"{mean(real_values):.3f}"


def _retrieval_expected_documents(question: dict) -> list[str]:
    if question["question_type"] in {"permission_restricted", "missing_information"}:
        return []
    return question.get("expected_source_document") or []


def run_benchmark(retrieval_only: bool = False) -> dict:
    benchmark = _load_benchmark()
    settings = get_settings()
    run_id = _create_run(retrieval_only=retrieval_only)
    results: list[dict] = []
    questions = benchmark["questions"]

    for index, question in enumerate(questions, start=1):
        print(
            f"[{index}/{len(questions)}] {question['question_id']} "
            f"{question['question_type']} as {question['user_role']}",
            flush=True,
        )
        started = time.perf_counter()
        query_text = _query_with_memory(question)
        chunks = retrieve_chunks(query_text, question["user_role"], settings.default_top_k)
        if retrieval_only:
            generated = {
                "answer": "[retrieval-only run: answer generation skipped]",
                "behavior": "pending",
                "citations": [],
            }
        else:
            generated = generate_answer(query_text, chunks, expected_behavior=question["expected_behavior"])
        latency_ms = int((time.perf_counter() - started) * 1000)

        expected_docs = _retrieval_expected_documents(question)
        citations = generated["citations"]
        if question["question_type"] == "permission_restricted":
            notes = "Permission-restricted question: expected source should not be retrieved for this role."
        elif question["question_type"] == "missing_information":
            notes = "Missing-information question: no expected source document."
        else:
            notes = "Answer accuracy, faithfulness, and hallucination metrics pending review."
        result = {
            "question_id": question["question_id"],
            "question_type": question["question_type"],
            "expected_behavior": question["expected_behavior"],
            "generated_behavior": generated["behavior"],
            "answer": generated["answer"],
            "retrieved_source_documents": list(dict.fromkeys(chunk.document_id for chunk in chunks)),
            "retrieval_hit": retrieval_hit(expected_docs, chunks),
            "mrr": reciprocal_rank(expected_docs, chunks),
            "citation_source_match": None if retrieval_only else citation_source_match(expected_docs, citations),
            "behavior_match": None if retrieval_only else behavior_match(question["expected_behavior"], generated["behavior"]),
            "latency_ms": latency_ms,
            "notes": notes,
        }
        _store_result(run_id, question, result)
        results.append(result)
        print(
            f"  retrieved={result['retrieved_source_documents']} "
            f"hit={result['retrieval_hit']} mrr={result['mrr']} elapsed_ms={latency_ms}",
            flush=True,
        )

    with get_connection() as conn:
        conn.execute(
            "update evaluation_runs set completed_at = now(), status = 'completed' where id = %s",
            (run_id,),
        )

    summary = {
        "run_id": run_id,
        "question_count": len(results),
        "top_k": settings.default_top_k,
        "retrieval_hit_rate": _average([result["retrieval_hit"] for result in results]),
        "mrr": _average([result["mrr"] for result in results]),
        "citation_source_match": _average([result["citation_source_match"] for result in results]),
        "behavior_match": _average([result["behavior_match"] for result in results]),
    }
    _write_report(summary, results)
    return summary


if __name__ == "__main__":
    print(json.dumps(run_benchmark(), indent=2))
