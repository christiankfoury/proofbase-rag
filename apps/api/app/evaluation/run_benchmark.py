from __future__ import annotations

import json
from datetime import UTC, datetime
from pathlib import Path
from statistics import mean
import time

from apps.api.app.core.config import get_settings
from apps.api.app.db.session import get_connection
from apps.api.app.evaluation.metrics import (
    all_sources_hit,
    any_source_hit,
    behavior_match,
    citation_source_match,
    expected_source_recall,
    precision_at_k,
    reciprocal_rank,
)
from apps.api.app.generation.answer_generator import citations_from_answer, generate_answer
from apps.api.app.retrieval.config import RetrievalConfig, default_retrieval_config
from apps.api.app.retrieval.retriever import retrieve_chunks


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


def _create_run(config: RetrievalConfig, retrieval_only: bool = False) -> str:
    config = {
        "run_name": f"{config.run_name}-retrieval" if retrieval_only else config.run_name,
        "retrieval_mode": config.retrieval_mode,
        "chunking_strategy": config.chunking_strategy,
        "top_k": config.top_k,
        "vector_weight": config.vector_weight,
        "keyword_weight": config.keyword_weight,
        "prompt_version": config.prompt_version,
        "model": config.model,
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
              retrieved_chunks_json,
              generated_answer,
              retrieval_hit_score,
              all_sources_hit_score,
              expected_source_recall,
              precision_at_k,
              mrr,
              citation_source_match,
              behavior_match,
              latency_ms,
              notes
            )
            values (%s, %s, %s, %s, %s, %s, %s, %s, %s::jsonb, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s)
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
                json.dumps(result["retrieved_chunks"]),
                result["answer"],
                result["any_source_hit"],
                result["all_sources_hit"],
                result["expected_source_recall"],
                result["precision_at_k"],
                result["mrr"],
                result["citation_source_match"],
                result["behavior_match"],
                result["latency_ms"],
                result["notes"],
            ),
        )


def _write_report(summary: dict, results: list[dict], report_path: Path = REPORT_PATH) -> None:
    report_path.parent.mkdir(parents=True, exist_ok=True)
    lines = [
        "# Baseline Evaluation Results",
        "",
        f"Generated at: {datetime.now(UTC).isoformat()}",
        "",
        "## Run Summary",
        "",
        f"- Questions: {summary['question_count']}",
        f"- Run name: {summary['run_name']}",
        f"- Retrieval mode: {summary['retrieval_mode']}",
        f"- Chunking strategy: {summary['chunking_strategy']}",
        f"- Top K: {summary['top_k']}",
        f"- Vector weight: {summary['vector_weight']}",
        f"- Keyword weight: {summary['keyword_weight']}",
        f"- Any-source retrieval hit: {summary['any_source_hit']}",
        f"- All-sources retrieval hit: {summary['all_sources_hit']}",
        f"- Expected-source recall: {summary['expected_source_recall']}",
        f"- Precision@k: {summary['precision_at_k']}",
        f"- MRR: {summary['mrr']}",
        f"- Average latency ms: {summary['average_latency_ms']}",
        f"- Citation source match: {summary['citation_source_match']}",
        f"- Behavior match: {summary['behavior_match']}",
        "",
        "Answer accuracy, faithfulness, and hallucination rate are pending because they require human review or an evaluation judge.",
        "",
        "## Question Results",
        "",
        "| Question ID | Type | Expected Behavior | Generated Behavior | Any Source | All Sources | Source Recall | Precision@k | MRR | Citation Match |",
        "|---|---|---|---|---:|---:|---:|---:|---:|---:|",
    ]
    for result in results:
        lines.append(
            "| {question_id} | {question_type} | {expected_behavior} | {generated_behavior} | {any_source_hit} | {all_sources_hit} | {expected_source_recall} | {precision_at_k} | {mrr} | {citation_source_match} |".format(
                **result
            )
        )
    report_path.write_text("\n".join(lines) + "\n", encoding="utf-8")


def _average(values: list[float | None]) -> str:
    real_values = [value for value in values if value is not None]
    if not real_values:
        return "pending"
    return f"{mean(real_values):.3f}"


def _retrieval_expected_documents(question: dict) -> list[str]:
    if question["question_type"] in {"permission_restricted", "missing_information"}:
        return []
    return question.get("expected_source_document") or []


def _retrieved_chunks_json(chunks) -> list[dict]:
    return [
        {
            "chunk_id": chunk.chunk_id,
            "document_id": chunk.document_id,
            "document_title": chunk.document_title,
            "section_heading": chunk.section_heading,
            "rank": chunk.rank,
            "score": chunk.score,
            "vector_score": chunk.vector_score,
            "keyword_score": chunk.keyword_score,
            "hybrid_score": chunk.hybrid_score,
            "retrieval_source": chunk.retrieval_source,
        }
        for chunk in chunks
    ]


def run_benchmark(
    retrieval_only: bool = False,
    config: RetrievalConfig | None = None,
    report_path: Path = REPORT_PATH,
    write_report: bool = True,
    include_results: bool = False,
) -> dict:
    benchmark = _load_benchmark()
    active_config = config or default_retrieval_config(
        run_name="baseline-vector-only-retrieval" if retrieval_only else "baseline-vector-only",
        retrieval_mode="vector_only",
        chunking_strategy="section_based",
    )
    run_id = _create_run(active_config, retrieval_only=retrieval_only)
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
        chunks = retrieve_chunks(query_text, question["user_role"], active_config)
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
        model_citations = [] if retrieval_only else citations_from_answer(generated["answer"], chunks, include_fallback=False)
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
            "retrieved_chunks": _retrieved_chunks_json(chunks),
            "any_source_hit": any_source_hit(expected_docs, chunks),
            "all_sources_hit": all_sources_hit(expected_docs, chunks),
            "expected_source_recall": expected_source_recall(expected_docs, chunks),
            "precision_at_k": precision_at_k(expected_docs, chunks, active_config.top_k),
            "mrr": reciprocal_rank(expected_docs, chunks),
            "citation_source_match": None if retrieval_only else citation_source_match(expected_docs, model_citations),
            "behavior_match": None if retrieval_only else behavior_match(question["expected_behavior"], generated["behavior"]),
            "latency_ms": latency_ms,
            "notes": notes,
        }
        _store_result(run_id, question, result)
        results.append(result)
        print(
            f"  retrieved={result['retrieved_source_documents']} "
            f"any={result['any_source_hit']} all={result['all_sources_hit']} "
            f"recall={result['expected_source_recall']} mrr={result['mrr']} elapsed_ms={latency_ms}",
            flush=True,
        )

    with get_connection() as conn:
        conn.execute(
            "update evaluation_runs set completed_at = now(), status = 'completed' where id = %s",
            (run_id,),
        )

    summary = {
        "run_id": run_id,
        "run_name": active_config.run_name,
        "question_count": len(results),
        "retrieval_mode": active_config.retrieval_mode,
        "chunking_strategy": active_config.chunking_strategy,
        "top_k": active_config.top_k,
        "vector_weight": active_config.vector_weight,
        "keyword_weight": active_config.keyword_weight,
        "any_source_hit": _average([result["any_source_hit"] for result in results]),
        "all_sources_hit": _average([result["all_sources_hit"] for result in results]),
        "expected_source_recall": _average([result["expected_source_recall"] for result in results]),
        "precision_at_k": _average([result["precision_at_k"] for result in results]),
        "mrr": _average([result["mrr"] for result in results]),
        "average_latency_ms": _average([result["latency_ms"] for result in results]),
        "citation_source_match": _average([result["citation_source_match"] for result in results]),
        "behavior_match": _average([result["behavior_match"] for result in results]),
    }
    if write_report:
        _write_report(summary, results, report_path=report_path)
    if include_results:
        summary["results"] = results
    return summary


if __name__ == "__main__":
    print(json.dumps(run_benchmark(), indent=2))
