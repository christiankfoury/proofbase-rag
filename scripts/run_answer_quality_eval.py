from datetime import UTC, datetime
from pathlib import Path
from statistics import mean
import argparse
import json
import sys
import time

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

from apps.api.app.evaluation.answer_metrics import score_answer
from apps.api.app.costing.estimator import estimate_chat_cost
from apps.api.app.evaluation.failed_question_report import failed_question_item
from apps.api.app.evaluation.metrics import (
    all_sources_hit,
    any_source_hit,
    expected_source_recall,
    precision_at_k,
    reciprocal_rank,
)
from apps.api.app.generation.answer_generator import generate_answer, retrieved_chunks_payload
from apps.api.app.retrieval.config import default_retrieval_config
from apps.api.app.retrieval.retriever import retrieve_chunks


BENCHMARK_PATH = Path("data/evaluation/benchmark-questions.json")
RESULTS_PATH = Path("docs/phase-7/evaluation-results.md")
FAILED_PATH = Path("docs/phase-7/failed-question-analysis.md")
EXTERNAL_AI_APPROVAL_MESSAGE = (
    "The legacy answer-quality evaluation sends benchmark questions and retrieved synthetic source snippets to "
    "external OpenAI embeddings and chat-completion APIs. Re-run with --allow-external-ai only after explicit approval."
)


def _requires_external_ai_approval(*, dry_run: bool, allow_external_ai: bool) -> bool:
    return not dry_run and not allow_external_ai


def _load_benchmark() -> dict:
    return json.loads(BENCHMARK_PATH.read_text(encoding="utf-8"))


def _query_with_memory(question: dict) -> str:
    previous_turns = question.get("previous_turns") or []
    if not previous_turns:
        return question["question"]
    context = "\n".join(f"{turn['role']}: {turn['content']}" for turn in previous_turns)
    return f"Previous conversation:\n{context}\n\nFollow-up question:\n{question['question']}"


def _retrieval_expected_documents(question: dict) -> list[str]:
    if question["question_type"] in {"permission_restricted", "missing_information"}:
        return []
    return question.get("expected_source_document") or []


def _average(values: list[float | None]) -> str:
    real_values = [value for value in values if value is not None]
    if not real_values:
        return "pending"
    return f"{mean(real_values):.3f}"


def _sum(values: list[int | None]) -> int | str:
    real_values = [value for value in values if value is not None]
    if not real_values:
        return "pending"
    return sum(real_values)


def _sum_cost(values: list[float | None]) -> float | str:
    real_values = [value for value in values if value is not None]
    if not real_values:
        return "pending"
    return round(sum(real_values), 6)


def _write_results(summary: dict, rows: list[dict]) -> None:
    RESULTS_PATH.parent.mkdir(parents=True, exist_ok=True)
    lines = [
        "# Phase 7 Evaluation Results",
        "",
        f"Generated at: {datetime.now(UTC).isoformat()}",
        "",
        "## Run Summary",
        "",
        f"- Questions: {summary['question_count']}",
        f"- Retrieval mode: {summary['retrieval_mode']}",
        f"- Chunking strategy: {summary['chunking_strategy']}",
        f"- Top K: {summary['top_k']}",
        f"- Any-source hit: {summary['any_source_hit']}",
        f"- All-sources hit: {summary['all_sources_hit']}",
        f"- Precision@k: {summary['precision_at_k']}",
        f"- MRR: {summary['mrr']}",
        f"- Answer accuracy: {summary['answer_accuracy']}",
        f"- Citation accuracy: {summary['citation_accuracy']}",
        f"- Faithfulness/support score: {summary['faithfulness']}",
        f"- Hallucination rate: {summary['hallucination_rate']}",
        f"- Response type accuracy: {summary['response_type_accuracy']}",
        f"- Refusal accuracy: {summary['refusal_accuracy']}",
        f"- Not-found accuracy: {summary['not_found_accuracy']}",
        f"- Clarification accuracy: {summary['clarification_accuracy']}",
        f"- Average final confidence: {summary['final_confidence']}",
        f"- Input tokens: {summary['input_tokens']}",
        f"- Output tokens: {summary['output_tokens']}",
        f"- Estimated cost: {summary['estimated_cost']}",
        "",
        "## Question Results",
        "",
        "| Question ID | Expected | Actual | Answer Acc | Citation Acc | Faithfulness | Hallucination | Final Confidence |",
        "|---|---|---|---:|---:|---:|---:|---:|",
    ]
    for row in rows:
        lines.append(
            "| {question_id} | {expected_behavior} | {response_type} | {answer_accuracy} | {citation_accuracy} | {faithfulness} | {hallucination_rate} | {final_confidence} |".format(
                **row
            )
        )
    lines.extend(
        [
            "",
            "## Notes",
            "",
            "- Answer accuracy uses deterministic expected-answer term overlap and should be treated as a baseline signal, not a human-grade semantic judge.",
            "- Citation accuracy checks whether citations point to expected source documents.",
            "- Faithfulness is the heuristic citation confidence score.",
            "- Estimated cost uses configured chat model pricing and excludes embedding/ingestion cost.",
        ]
    )
    RESULTS_PATH.write_text("\n".join(lines) + "\n", encoding="utf-8")


def _write_failed(failed: list[dict]) -> None:
    FAILED_PATH.parent.mkdir(parents=True, exist_ok=True)
    lines = [
        "# Phase 7 Failed Question Analysis",
        "",
        f"Generated at: {datetime.now(UTC).isoformat()}",
        "",
        f"Failed questions: {len(failed)}",
        "",
        "| Question ID | Expected Behavior | Actual Response | Failure Type | Citation Confidence | Answer Confidence | Recommended Fix |",
        "|---|---|---|---|---:|---:|---|",
    ]
    for item in failed:
        lines.append(
            "| {question_id} | {expected_behavior} | {actual_response_type} | {failure_type} | {citation_confidence} | {answer_confidence} | {recommended_fix} |".format(
                **item
            )
        )
    lines.extend(["", "## Detailed Items", ""])
    for item in failed:
        lines.extend(
            [
                f"### {item['question_id']}",
                "",
                f"- Question: {item['question']}",
                f"- Expected source document: {item['expected_source_document']}",
                f"- Actual citations: {item['actual_citations']}",
                f"- Retrieval success: {item['retrieval_success']}",
                f"- Failure type: {item['failure_type']}",
                f"- Recommended fix: {item['recommended_fix']}",
                "",
            ]
        )
    FAILED_PATH.write_text("\n".join(lines), encoding="utf-8")


def main() -> None:
    parser = argparse.ArgumentParser(description="Run the legacy Phase 7 answer-quality evaluation.")
    parser.add_argument("--dry-run", action="store_true")
    parser.add_argument(
        "--allow-external-ai",
        action="store_true",
        help="Confirm explicit approval to send benchmark questions and retrieved snippets to external AI APIs.",
    )
    args = parser.parse_args()
    benchmark = _load_benchmark()
    config = default_retrieval_config(
        run_name="phase-7-answer-quality",
        retrieval_mode="vector_only",
        chunking_strategy="section_based",
        top_k=5,
    )
    if args.dry_run:
        print(
            json.dumps(
                {
                    "question_count": benchmark.get("question_count"),
                    "config": config.__dict__,
                    "would_write": [str(RESULTS_PATH), str(FAILED_PATH)],
                    "external_ai_required": True,
                },
                indent=2,
            )
        )
        return
    if _requires_external_ai_approval(dry_run=args.dry_run, allow_external_ai=args.allow_external_ai):
        raise SystemExit(EXTERNAL_AI_APPROVAL_MESSAGE)
    rows = []
    failed = []

    for index, question in enumerate(benchmark["questions"], start=1):
        print(f"[{index}/{benchmark['question_count']}] {question['question_id']} {question['question_type']}", flush=True)
        started = time.perf_counter()
        query_text = _query_with_memory(question)
        chunks = retrieve_chunks(query_text, question["user_role"], config)
        answer = generate_answer(
            query_text,
            chunks,
            expected_behavior=question["expected_behavior"],
            user_role=question["user_role"],
        )
        latency_ms = int((time.perf_counter() - started) * 1000)
        expected_docs = _retrieval_expected_documents(question)
        retrieval_chunks_payload = retrieved_chunks_payload(chunks)
        scores = score_answer(question, answer)
        row = {
            "question_id": question["question_id"],
            "question": question["question"],
            "question_type": question["question_type"],
            "expected_behavior": question["expected_behavior"],
            "response_type": answer["response_type"],
            "behavior": answer["behavior"],
            "answer": answer["answer"],
            "citations": answer["citations"],
            "retrieved_chunks": retrieval_chunks_payload,
            "retrieved_chunks_raw": chunks,
            "any_source_hit": any_source_hit(expected_docs, chunks),
            "all_sources_hit": all_sources_hit(expected_docs, chunks),
            "expected_source_recall": expected_source_recall(expected_docs, chunks),
            "precision_at_k": precision_at_k(expected_docs, chunks, config.top_k),
            "mrr": reciprocal_rank(expected_docs, chunks),
            "latency_ms": latency_ms,
            "citation_confidence": answer["citation_confidence"],
            "answer_confidence": answer["answer_confidence"],
            "final_confidence": answer["final_confidence"],
            "input_tokens": answer["input_tokens"],
            "output_tokens": answer["output_tokens"],
            "input_cost_usd": answer.get("input_cost_usd"),
            "output_cost_usd": answer.get("output_cost_usd"),
            "estimated_cost_usd": answer.get("estimated_cost_usd"),
            "pricing_status": answer.get("pricing_status"),
            **scores,
        }
        failed_item = failed_question_item(question, row, scores)
        if failed_item:
            failed.append(failed_item)
        rows.append(row)
        print(
            f"  response={row['response_type']} answer_acc={row['answer_accuracy']} "
            f"citation_acc={row['citation_accuracy']} confidence={row['final_confidence']}",
            flush=True,
        )

    summary = {
        "question_count": len(rows),
        "retrieval_mode": config.retrieval_mode,
        "chunking_strategy": config.chunking_strategy,
        "top_k": config.top_k,
        "any_source_hit": _average([row["any_source_hit"] for row in rows]),
        "all_sources_hit": _average([row["all_sources_hit"] for row in rows]),
        "precision_at_k": _average([row["precision_at_k"] for row in rows]),
        "mrr": _average([row["mrr"] for row in rows]),
        "answer_accuracy": _average([row["answer_accuracy"] for row in rows]),
        "citation_accuracy": _average([row["citation_accuracy"] for row in rows]),
        "faithfulness": _average([row["faithfulness"] for row in rows]),
        "hallucination_rate": _average([row["hallucination_rate"] for row in rows]),
        "response_type_accuracy": _average([row["response_type_accuracy"] for row in rows]),
        "refusal_accuracy": _average([row["refusal_accuracy"] for row in rows]),
        "not_found_accuracy": _average([row["not_found_accuracy"] for row in rows]),
        "clarification_accuracy": _average([row["clarification_accuracy"] for row in rows]),
        "final_confidence": _average([row["final_confidence"] for row in rows]),
        "input_tokens": _sum([row["input_tokens"] for row in rows]),
        "output_tokens": _sum([row["output_tokens"] for row in rows]),
        "estimated_cost": _sum_cost([row.get("estimated_cost_usd") for row in rows]),
    }
    if summary["estimated_cost"] == "pending":
        cost = estimate_chat_cost(
            model="gpt-4.1-mini",
            input_tokens=summary["input_tokens"],
            output_tokens=summary["output_tokens"],
        )
        summary["estimated_cost"] = cost["estimated_cost_usd"] if cost["estimated_cost_usd"] is not None else "pending"
    _write_results(summary, rows)
    _write_failed(failed)
    print(json.dumps(summary, indent=2))
    print(f"Wrote {RESULTS_PATH}")
    print(f"Wrote {FAILED_PATH}")


if __name__ == "__main__":
    main()
