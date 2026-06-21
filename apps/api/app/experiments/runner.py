from __future__ import annotations

from datetime import UTC, datetime
from pathlib import Path
from statistics import mean
import json
import time

from apps.api.app.costing.estimator import estimate_chat_cost
from apps.api.app.evaluation.answer_metrics import score_answer
from apps.api.app.evaluation.failed_question_report import failed_question_item
from apps.api.app.evaluation.metrics import (
    all_sources_hit,
    any_source_hit,
    expected_source_recall,
    precision_at_k,
    reciprocal_rank,
)
from apps.api.app.experiments.config import ExperimentConfig
from apps.api.app.generation.answer_generator import generate_answer, retrieved_chunks_payload
from apps.api.app.prompts.prompt_registry import get_prompt
from apps.api.app.retrieval.config import RetrievalConfig
from apps.api.app.retrieval.retriever import retrieve_chunks


ROOT = Path(__file__).resolve().parents[4]
BENCHMARK_PATH = ROOT / "data/evaluation/benchmark-questions.json"
PROMPT_EXPERIMENT_DIR = ROOT / "data/evaluation/prompt-experiments"


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


def _average(values: list[float | None]) -> float | None:
    real_values = [value for value in values if value is not None]
    if not real_values:
        return None
    return round(mean(real_values), 3)


def _sum(values: list[int | None]) -> int | None:
    real_values = [value for value in values if value is not None]
    if not real_values:
        return None
    return sum(real_values)


def _sum_cost(values: list[float | None]) -> float | None:
    real_values = [value for value in values if value is not None]
    if not real_values:
        return None
    return round(sum(real_values), 6)


def run_prompt_experiment(
    config: ExperimentConfig,
    question_ids: set[str] | None = None,
    question_filter: str = "all",
    budget_usd: float | None = None,
) -> dict:
    benchmark = _load_benchmark()
    prompt = get_prompt(config.prompt_name, config.prompt_version)
    questions = benchmark["questions"]
    if question_ids is not None:
        questions = [question for question in questions if question["question_id"] in question_ids]
    retrieval_config = RetrievalConfig(
        run_name=config.run_name,
        retrieval_mode=config.retrieval_mode,
        chunking_strategy=config.chunking_strategy,
        top_k=config.top_k,
        reranker=config.reranker,
        rerank_candidate_limit=config.rerank_candidate_limit,
        prompt_version=config.prompt_version,
        model=config.model,
    )
    rows = []
    failed = []
    started_at = datetime.now(UTC).isoformat()
    cumulative_cost = 0.0

    for index, question in enumerate(questions, start=1):
        print(f"[{index}/{len(questions)}] {question['question_id']} {config.prompt_version}", flush=True)
        started = time.perf_counter()
        query_text = _query_with_memory(question)
        chunks = retrieve_chunks(query_text, question["user_role"], retrieval_config)
        answer = generate_answer(
            query_text,
            chunks,
            expected_behavior=question["expected_behavior"],
            user_role=question["user_role"],
            prompt_name=config.prompt_name,
            prompt_version=config.prompt_version,
            model=config.model,
            temperature=config.temperature,
        )
        latency_ms = int((time.perf_counter() - started) * 1000)
        expected_docs = _retrieval_expected_documents(question)
        scores = score_answer(question, answer)
        row_for_scoring = {
            "question_id": question["question_id"],
            "question": question["question"],
            "question_type": question["question_type"],
            "expected_behavior": question["expected_behavior"],
            "response_type": answer["response_type"],
            "behavior": answer["behavior"],
            "answer": answer["answer"],
            "citations": answer["citations"],
            "retrieved_chunks": retrieved_chunks_payload(chunks),
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
            "prompt_version": answer.get("prompt_version"),
            "model": answer.get("model"),
            "temperature": answer.get("temperature"),
            **scores,
        }
        failed_item = failed_question_item(question, row_for_scoring, scores)
        if failed_item:
            failed.append(failed_item)
        row = {key: value for key, value in row_for_scoring.items() if key != "retrieved_chunks_raw"}
        rows.append(row)
        if row.get("estimated_cost_usd") is not None:
            cumulative_cost += float(row["estimated_cost_usd"])
        if budget_usd is not None and cumulative_cost >= budget_usd:
            raise RuntimeError(
                f"Experiment budget stop reached: ${cumulative_cost:.6f} >= ${budget_usd:.2f}."
            )
        print(
            f"  response={row['response_type']} answer_acc={row['answer_accuracy']} "
            f"citation_acc={row['citation_accuracy']} confidence={row['final_confidence']}",
            flush=True,
        )

    summary = {
        "experiment_id": config.experiment_id,
        "run_name": config.run_name,
        "phase": config.phase,
        "prompt_name": config.prompt_name,
        "prompt_version": config.prompt_version,
        "prompt_id": prompt.prompt_id,
        "prompt_status": prompt.status,
        "prompt_change_notes": prompt.change_notes,
        "model": config.model,
        "temperature": config.temperature,
        "retrieval_mode": config.retrieval_mode,
        "chunking_strategy": config.chunking_strategy,
        "top_k": config.top_k,
        "question_filter": question_filter,
        "question_count": len(rows),
        "source_question_count": benchmark["question_count"],
        "failed_question_count": len(failed),
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
        "pricing_status": "estimated",
    }
    if summary["estimated_cost"] is None:
        summary.update(
            estimate_chat_cost(
                model=config.model,
                input_tokens=summary["input_tokens"],
                output_tokens=summary["output_tokens"],
            )
        )
        summary["estimated_cost"] = summary["estimated_cost_usd"]
    return {
        "generated_at": datetime.now(UTC).isoformat(),
        "started_at": started_at,
        "config": config.to_dict(),
        "prompt": prompt.metadata() | {"created_at": prompt.created_at},
        "summary": summary,
        "rows": rows,
        "failed_questions": failed,
    }


def write_prompt_experiment(result: dict) -> Path:
    PROMPT_EXPERIMENT_DIR.mkdir(parents=True, exist_ok=True)
    suffix = "-failed-subset" if result["summary"].get("question_filter") == "failed" else ""
    path = PROMPT_EXPERIMENT_DIR / f"{result['summary']['experiment_id']}{suffix}.json"
    path.write_text(json.dumps(result, indent=2), encoding="utf-8")
    return path
