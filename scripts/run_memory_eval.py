from __future__ import annotations

import json
from datetime import UTC, datetime
from pathlib import Path
from statistics import mean
import sys
import time

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

from apps.api.app.evaluation.answer_metrics import score_answer
from apps.api.app.evaluation.memory_metrics import (
    followup_detection_accuracy,
    memory_permission_leakage,
    memory_response_type_accuracy,
    query_rewrite_quality,
)
from apps.api.app.evaluation.metrics import precision_at_k, reciprocal_rank
from apps.api.app.generation.answer_generator import generate_answer, retrieved_chunks_payload
from apps.api.app.memory.context_builder import build_memory_context, memory_context_text
from apps.api.app.memory.query_rewriter import rewrite_followup_question
from apps.api.app.retrieval.config import default_retrieval_config
from apps.api.app.retrieval.retriever import retrieve_chunks


BENCHMARK_PATH = Path("data/evaluation/benchmark-questions.json")
RESULTS_PATH = Path("docs/phase-9/memory-evaluation-results.md")
FAILED_PATH = Path("docs/phase-9/failed-memory-question-analysis.md")


def _load_benchmark() -> dict:
    return json.loads(BENCHMARK_PATH.read_text(encoding="utf-8"))


def _average(values: list[float | None]) -> str:
    real_values = [value for value in values if value is not None]
    if not real_values:
        return "pending"
    return f"{mean(real_values):.3f}"


def _failure_type(question: dict, row: dict) -> str | None:
    if row["followup_detection_accuracy"] != 1.0:
        return "followup_not_detected"
    if row["query_rewrite_quality"] != 1.0:
        return "bad_query_rewrite"
    if row["memory_permission_leakage"] == 1.0:
        return "permission_memory_leak"
    if row["memory_response_type_accuracy"] != 1.0:
        return "wrong_memory_response_type"
    if row["answer_accuracy"] is not None and row["answer_accuracy"] < 1.0:
        return "unsupported_answer"
    if row["citation_accuracy"] is not None and row["citation_accuracy"] < 1.0:
        return "wrong_citation"
    if row["hallucination_rate"] == 1.0:
        return "unsupported_answer"
    return None


def _recommended_fix(failure_type: str | None) -> str:
    fixes = {
        "followup_not_detected": "Expand follow-up detection markers for this phrasing.",
        "bad_query_rewrite": "Improve query rewriting so the standalone query retrieves the expected source.",
        "permission_memory_leak": "Ensure prior context is used only for rewriting and retrieval still filters by current role.",
        "wrong_memory_response_type": "Tune memory-aware prompting so answerable follow-ups do not downgrade incorrectly.",
        "unsupported_answer": "Improve memory-aware answer generation or citation support thresholds.",
        "wrong_citation": "Require citations from the exact expected document section.",
    }
    return fixes.get(failure_type or "", "No fix required.")


def _write_results(summary: dict, rows: list[dict]) -> None:
    RESULTS_PATH.parent.mkdir(parents=True, exist_ok=True)
    lines = [
        "# Phase 9 Memory Evaluation Results",
        "",
        f"Generated at: {datetime.now(UTC).isoformat()}",
        "",
        "## Run Summary",
        "",
        f"- Memory benchmark questions: {summary['question_count']}",
        f"- Retrieval mode: {summary['retrieval_mode']}",
        f"- Chunking strategy: {summary['chunking_strategy']}",
        f"- Top K: {summary['top_k']}",
        f"- Follow-up detection accuracy: {summary['followup_detection_accuracy']}",
        f"- Query rewrite quality: {summary['query_rewrite_quality']}",
        f"- Memory answer accuracy: {summary['answer_accuracy']}",
        f"- Memory citation accuracy: {summary['citation_accuracy']}",
        f"- Memory response type accuracy: {summary['memory_response_type_accuracy']}",
        f"- Memory permission leakage: {summary['memory_permission_leakage']}",
        f"- Hallucination rate on follow-ups: {summary['hallucination_rate']}",
        f"- Average final confidence: {summary['final_confidence']}",
        "",
        "## Question Results",
        "",
        "| Question ID | Follow-up | Rewritten Question | Detection | Rewrite Quality | Answer Acc | Citation Acc | Response Type | Leakage |",
        "|---|---|---|---:|---:|---:|---:|---:|---:|",
    ]
    for row in rows:
        lines.append(
            "| {question_id} | {question} | {rewritten_question} | {followup_detection_accuracy} | {query_rewrite_quality} | {answer_accuracy} | {citation_accuracy} | {memory_response_type_accuracy} | {memory_permission_leakage} |".format(
                **row
            )
        )
    lines.extend(
        [
            "",
            "## Notes",
            "",
            "- Memory is used only to rewrite/clarify the current query.",
            "- Prior assistant answers are not treated as source evidence.",
            "- Retrieval still applies current-role permission filtering before generation.",
            "- Semantic rewrite quality is approximated by expected-source retrieval success.",
        ]
    )
    RESULTS_PATH.write_text("\n".join(lines) + "\n", encoding="utf-8")


def _write_failed(failed: list[dict]) -> None:
    FAILED_PATH.parent.mkdir(parents=True, exist_ok=True)
    lines = [
        "# Phase 9 Failed Memory Question Analysis",
        "",
        f"Generated at: {datetime.now(UTC).isoformat()}",
        "",
        f"Failed memory questions: {len(failed)}",
        "",
        "| Question ID | Failure Type | Rewritten Question | Expected Source | Actual Citations | Recommended Fix |",
        "|---|---|---|---|---|---|",
    ]
    for item in failed:
        lines.append(
            "| {question_id} | {failure_type} | {rewritten_question} | {expected_source_document} | {actual_citations} | {recommended_fix} |".format(
                **item
            )
        )
    lines.extend(["", "## Detailed Items", ""])
    for item in failed:
        lines.extend(
            [
                f"### {item['question_id']}",
                "",
                f"- Prior turns: {item['prior_turns']}",
                f"- Follow-up question: {item['follow_up_question']}",
                f"- Rewritten question: {item['rewritten_question']}",
                f"- Expected answer: {item['expected_answer']}",
                f"- Actual answer: {item['actual_answer']}",
                f"- Expected source document: {item['expected_source_document']}",
                f"- Actual citations: {item['actual_citations']}",
                f"- Failure type: {item['failure_type']}",
                f"- Recommended fix: {item['recommended_fix']}",
                "",
            ]
        )
    FAILED_PATH.write_text("\n".join(lines), encoding="utf-8")


def main() -> None:
    benchmark = _load_benchmark()
    questions = [
        question
        for question in benchmark["questions"]
        if question["question_type"] == "conversation_memory"
    ]
    config = default_retrieval_config(
        run_name="phase-9-memory",
        retrieval_mode="vector_only",
        chunking_strategy="section_based",
        top_k=5,
    )
    rows = []
    failed = []

    for index, question in enumerate(questions, start=1):
        print(f"[{index}/{len(questions)}] {question['question_id']} memory", flush=True)
        previous_turns = question.get("previous_turns") or []
        rewrite = rewrite_followup_question(question["question"], previous_turns)
        memory_context = build_memory_context(previous_turns)
        memory_text = memory_context_text(memory_context)
        chunks = retrieve_chunks(rewrite["rewritten_question"], question["user_role"], config)
        started = time.perf_counter()
        answer = generate_answer(
            rewrite["rewritten_question"],
            chunks,
            expected_behavior=question["expected_behavior"],
            user_role=question["user_role"],
            memory_context=memory_text,
            original_question=question["question"],
        )
        latency_ms = int((time.perf_counter() - started) * 1000)
        scores = score_answer(question, answer)
        expected_docs = question.get("expected_source_document") or []
        row = {
            "question_id": question["question_id"],
            "question": question["question"],
            "prior_turns": previous_turns,
            "rewritten_question": rewrite["rewritten_question"],
            "is_followup": rewrite["is_followup"],
            "memory_used": rewrite["memory_used"],
            "followup_detection_accuracy": followup_detection_accuracy(rewrite["is_followup"]),
            "query_rewrite_quality": query_rewrite_quality(expected_docs, chunks),
            "precision_at_k": precision_at_k(expected_docs, chunks, config.top_k),
            "mrr": reciprocal_rank(expected_docs, chunks),
            "answer": answer["answer"],
            "response_type": answer["response_type"],
            "behavior": answer["behavior"],
            "citations": answer["citations"],
            "retrieved_chunks": retrieved_chunks_payload(chunks),
            "memory_response_type_accuracy": memory_response_type_accuracy(question["expected_behavior"], answer["behavior"]),
            "memory_permission_leakage": memory_permission_leakage(chunks, question["user_role"], answer["citations"]),
            "latency_ms": latency_ms,
            "final_confidence": answer["final_confidence"],
            **scores,
        }
        rows.append(row)
        failure = _failure_type(question, row)
        if failure:
            failed.append(
                {
                    "question_id": question["question_id"],
                    "prior_turns": previous_turns,
                    "follow_up_question": question["question"],
                    "rewritten_question": rewrite["rewritten_question"],
                    "expected_answer": question["expected_answer"],
                    "actual_answer": answer["answer"],
                    "expected_source_document": question.get("expected_source_document") or [],
                    "actual_citations": [
                        {
                            "document_id": citation["document_id"],
                            "section_heading": citation["section_heading"],
                            "confidence": citation.get("confidence"),
                        }
                        for citation in answer["citations"]
                    ],
                    "failure_type": failure,
                    "recommended_fix": _recommended_fix(failure),
                }
            )
        print(
            f"  rewritten='{rewrite['rewritten_question']}' response={answer['response_type']} "
            f"rewrite_quality={row['query_rewrite_quality']} answer_acc={row['answer_accuracy']}",
            flush=True,
        )

    summary = {
        "question_count": len(rows),
        "retrieval_mode": config.retrieval_mode,
        "chunking_strategy": config.chunking_strategy,
        "top_k": config.top_k,
        "followup_detection_accuracy": _average([row["followup_detection_accuracy"] for row in rows]),
        "query_rewrite_quality": _average([row["query_rewrite_quality"] for row in rows]),
        "answer_accuracy": _average([row["answer_accuracy"] for row in rows]),
        "citation_accuracy": _average([row["citation_accuracy"] for row in rows]),
        "memory_response_type_accuracy": _average([row["memory_response_type_accuracy"] for row in rows]),
        "memory_permission_leakage": _average([row["memory_permission_leakage"] for row in rows]),
        "hallucination_rate": _average([row["hallucination_rate"] for row in rows]),
        "final_confidence": _average([row["final_confidence"] for row in rows]),
    }
    _write_results(summary, rows)
    _write_failed(failed)
    print(json.dumps(summary, indent=2))
    print(f"Wrote {RESULTS_PATH}")
    print(f"Wrote {FAILED_PATH}")


if __name__ == "__main__":
    main()

