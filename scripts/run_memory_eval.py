from __future__ import annotations

import json
import argparse
from datetime import UTC, datetime
from pathlib import Path
from statistics import mean
import sys
import time

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

from apps.api.app.evaluation.answer_metrics import score_answer
from apps.api.app.costing.estimator import estimate_chat_cost
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
DETAIL_PATH = Path("data/evaluation/phase36-memory-evaluation.json")
EVAL_RUN_PATH = Path("data/evaluation/eval-runs/phase36-memory-evaluation.json")
EXTERNAL_AI_APPROVAL_MESSAGE = (
    "The memory evaluation sends benchmark questions, previous turns, and retrieved source snippets to external "
    "OpenAI embeddings and chat-completion APIs. Re-run with --allow-external-ai only after explicit approval."
)


def _load_benchmark() -> dict:
    return json.loads(BENCHMARK_PATH.read_text(encoding="utf-8"))


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


def _number(value: str | float | int | None) -> float | int | str | None:
    if value is None:
        return None
    if isinstance(value, (int, float)):
        return value
    if value == "pending":
        return value
    try:
        parsed = float(value)
    except ValueError:
        return value
    return int(parsed) if parsed.is_integer() else parsed


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


def _write_results(summary: dict, rows: list[dict], results_path: Path) -> None:
    results_path.parent.mkdir(parents=True, exist_ok=True)
    title = "Phase 36 Memory Evaluation Results" if summary.get("phase") == "phase-36" else "Phase 9 Memory Evaluation Results"
    lines = [
        f"# {title}",
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
        f"- Input tokens: {summary['input_tokens']}",
        f"- Output tokens: {summary['output_tokens']}",
        f"- Estimated cost: {summary['estimated_cost']}",
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
    results_path.write_text("\n".join(lines) + "\n", encoding="utf-8")


def _write_failed(failed: list[dict], failed_path: Path) -> None:
    failed_path.parent.mkdir(parents=True, exist_ok=True)
    title = "Phase 36 Failed Memory Question Analysis" if "phase-36" in str(failed_path).replace("\\", "/") else "Phase 9 Failed Memory Question Analysis"
    lines = [
        f"# {title}",
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
    failed_path.write_text("\n".join(lines), encoding="utf-8")


def _dashboard_run(result: dict) -> dict:
    summary = result["summary"]
    failed_ids = [item["question_id"] for item in result.get("failed_questions", [])]
    return {
        "run_id": summary["run_id"],
        "run_name": summary["run_name"],
        "phase": summary["phase"],
        "run_type": "memory_eval",
        "timestamp": result["generated_at"],
        "retrieval_mode": summary["retrieval_mode"],
        "chunking_strategy": summary["chunking_strategy"],
        "top_k": summary["top_k"],
        "reranker": summary.get("reranker"),
        "rerank_candidate_limit": summary.get("rerank_candidate_limit"),
        "prompt_version": summary.get("prompt_version"),
        "model": summary.get("model"),
        "total_questions": summary["question_count"],
        "source_question_count": summary.get("source_question_count"),
        "question_filter": "conversation_memory",
        "metrics": {
            "followup_detection_accuracy": _number(summary["followup_detection_accuracy"]),
            "query_rewrite_quality": _number(summary["query_rewrite_quality"]),
            "memory_answer_accuracy": _number(summary["answer_accuracy"]),
            "memory_citation_accuracy": _number(summary["citation_accuracy"]),
            "memory_response_type_accuracy": _number(summary["memory_response_type_accuracy"]),
            "memory_permission_leakage": _number(summary["memory_permission_leakage"]),
            "hallucination_rate": _number(summary["hallucination_rate"]),
            "final_confidence": _number(summary["final_confidence"]),
            "input_tokens": _number(summary["input_tokens"]),
            "output_tokens": _number(summary["output_tokens"]),
            "estimated_cost": _number(summary["estimated_cost"]),
            "failed_question_count": len(failed_ids),
        },
        "failed_questions": failed_ids,
        "category_breakdown": {"conversation_memory": summary["question_count"]},
        "notes": (
            "Phase 36 expanded conversation-memory suite. Memory is used only for query rewriting; retrieved chunks "
            "and citations remain filtered by the current user role."
        ),
        "sample_size": summary["question_count"],
        "passed_count": summary["question_count"] - len(failed_ids),
        "failed_count": len(failed_ids),
        "benchmark_version": summary.get("benchmark_version"),
        "run_timestamp": result["generated_at"],
    }


def main() -> None:
    parser = argparse.ArgumentParser(description="Run the conversation-memory evaluation suite.")
    parser.add_argument("--phase", default="phase-9")
    parser.add_argument("--run-id", default=None)
    parser.add_argument("--run-name", default=None)
    parser.add_argument(
        "--retrieval-mode",
        default="vector_only",
        choices=["vector_only", "vector_lexical_rerank", "keyword_only", "hybrid"],
    )
    parser.add_argument("--chunking-strategy", default="section_based")
    parser.add_argument("--top-k", type=int, default=5)
    parser.add_argument("--rerank-candidate-limit", type=int, default=None)
    parser.add_argument("--prompt-version", default=None)
    parser.add_argument("--results-path", type=Path, default=None)
    parser.add_argument("--failed-path", type=Path, default=None)
    parser.add_argument("--detail-path", type=Path, default=None)
    parser.add_argument("--eval-run-path", type=Path, default=None)
    parser.add_argument("--budget-usd", type=float, default=None)
    parser.add_argument("--dry-run", action="store_true")
    parser.add_argument(
        "--allow-external-ai",
        action="store_true",
        help="Confirm explicit approval to send benchmark questions, previous turns, and retrieved snippets to external AI APIs.",
    )
    args = parser.parse_args()

    benchmark = _load_benchmark()
    questions = [
        question
        for question in benchmark["questions"]
        if question["question_type"] == "conversation_memory"
    ]
    run_id = args.run_id or ("phase36-memory-evaluation" if args.phase == "phase-36" else "phase9-memory")
    run_name = args.run_name or ("phase36-memory-evaluation" if args.phase == "phase-36" else "phase-9-memory")
    results_path = args.results_path or (Path("docs/phase-36/memory-evaluation-results.md") if args.phase == "phase-36" else RESULTS_PATH)
    failed_path = args.failed_path or (Path("docs/phase-36/failed-memory-question-analysis.md") if args.phase == "phase-36" else FAILED_PATH)
    detail_path = args.detail_path or (DETAIL_PATH if args.phase == "phase-36" else None)
    eval_run_path = args.eval_run_path or (EVAL_RUN_PATH if args.phase == "phase-36" else None)
    config = default_retrieval_config(
        run_name=run_name,
        retrieval_mode=args.retrieval_mode,
        chunking_strategy=args.chunking_strategy,
        top_k=args.top_k,
        rerank_candidate_limit=args.rerank_candidate_limit,
    )
    if args.dry_run:
        print(
            json.dumps(
                {
                    "run_id": run_id,
                    "phase": args.phase,
                    "question_count": len(questions),
                    "config": config.__dict__,
                    "prompt_version": args.prompt_version,
                    "would_write": [
                        str(results_path),
                        str(failed_path),
                        str(detail_path) if detail_path else None,
                        str(eval_run_path) if eval_run_path else None,
                    ],
                },
                indent=2,
            )
        )
        return
    if not args.allow_external_ai:
        raise SystemExit(EXTERNAL_AI_APPROVAL_MESSAGE)
    rows = []
    failed = []
    cumulative_cost = 0.0

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
            prompt_version=args.prompt_version,
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
            "input_tokens": answer["input_tokens"],
            "output_tokens": answer["output_tokens"],
            "input_cost_usd": answer.get("input_cost_usd"),
            "output_cost_usd": answer.get("output_cost_usd"),
            "estimated_cost_usd": answer.get("estimated_cost_usd"),
            "pricing_status": answer.get("pricing_status"),
            **scores,
        }
        rows.append(row)
        if row.get("estimated_cost_usd") is not None:
            cumulative_cost += float(row["estimated_cost_usd"])
        if args.budget_usd is not None and cumulative_cost >= args.budget_usd:
            raise RuntimeError(f"Memory evaluation budget stop reached: ${cumulative_cost:.6f} >= ${args.budget_usd:.2f}.")
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
        "run_id": run_id,
        "run_name": run_name,
        "phase": args.phase,
        "benchmark_version": benchmark.get("benchmark_version"),
        "source_question_count": benchmark.get("question_count"),
        "question_count": len(rows),
        "retrieval_mode": config.retrieval_mode,
        "chunking_strategy": config.chunking_strategy,
        "top_k": config.top_k,
        "reranker": config.reranker,
        "rerank_candidate_limit": config.rerank_candidate_limit,
        "prompt_version": args.prompt_version,
        "model": config.model,
        "followup_detection_accuracy": _average([row["followup_detection_accuracy"] for row in rows]),
        "query_rewrite_quality": _average([row["query_rewrite_quality"] for row in rows]),
        "answer_accuracy": _average([row["answer_accuracy"] for row in rows]),
        "citation_accuracy": _average([row["citation_accuracy"] for row in rows]),
        "memory_response_type_accuracy": _average([row["memory_response_type_accuracy"] for row in rows]),
        "memory_permission_leakage": _average([row["memory_permission_leakage"] for row in rows]),
        "hallucination_rate": _average([row["hallucination_rate"] for row in rows]),
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
    result = {
        "generated_at": datetime.now(UTC).isoformat(),
        "summary": summary,
        "rows": rows,
        "failed_questions": failed,
    }
    dashboard_run = _dashboard_run(result)
    result["dashboard_run"] = dashboard_run
    _write_results(summary, rows, results_path)
    _write_failed(failed, failed_path)
    if detail_path:
        detail_path.parent.mkdir(parents=True, exist_ok=True)
        detail_path.write_text(json.dumps(result, indent=2), encoding="utf-8")
    if eval_run_path:
        eval_run_path.parent.mkdir(parents=True, exist_ok=True)
        eval_run_path.write_text(json.dumps(dashboard_run, indent=2), encoding="utf-8")
    print(json.dumps(summary, indent=2))
    print(f"Wrote {results_path}")
    print(f"Wrote {failed_path}")
    if detail_path:
        print(f"Wrote {detail_path}")
    if eval_run_path:
        print(f"Wrote {eval_run_path}")


if __name__ == "__main__":
    main()
