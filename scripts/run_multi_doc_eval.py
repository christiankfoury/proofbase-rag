from __future__ import annotations

import json
import sys
import time
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

from apps.api.app.evaluation.answer_metrics import score_answer
from apps.api.app.evaluation.multi_doc_metrics import (
    all_required_sources_cited,
    multi_doc_summary,
    source_coverage_score,
)
from apps.api.app.evaluation.metrics import all_sources_hit, any_source_hit
from apps.api.app.generation.answer_generator import generate_answer
from apps.api.app.reasoning.evidence_grouper import group_chunks_by_document
from apps.api.app.reasoning.query_decomposer import retrieve_multi_doc
from apps.api.app.retrieval.config import default_retrieval_config
from apps.api.app.retrieval.retriever import retrieve_chunks

BENCHMARK_PATH = ROOT / "data/evaluation/benchmark-questions.json"
RESULTS_PATH = ROOT / "data/evaluation/multi-doc-eval.json"


def _load_benchmark() -> list[dict]:
    data = json.loads(BENCHMARK_PATH.read_text(encoding="utf-8"))
    return [q for q in data["questions"] if q["question_type"] == "multi_document"]


def _expected_docs(question: dict) -> list[str]:
    return question.get("expected_source_document") or []


def _run_pass(questions: list[dict], use_multi_doc: bool) -> list[dict]:
    config = default_retrieval_config(run_name="multi-doc-eval")
    rows = []
    label = "multi-doc" if use_multi_doc else "baseline"
    for index, question in enumerate(questions, start=1):
        print(f"[{label}] [{index}/{len(questions)}] {question['question_id']}", flush=True)
        started = time.perf_counter()
        query_text = question["question"]
        expected_docs = _expected_docs(question)

        if use_multi_doc:
            chunks = retrieve_multi_doc(query_text, question["user_role"], config)
            grouped_docs = group_chunks_by_document(chunks)
        else:
            chunks = retrieve_chunks(query_text, question["user_role"], config)
            grouped_docs = None

        answer = generate_answer(
            query_text,
            chunks,
            expected_behavior=question["expected_behavior"],
            user_role=question["user_role"],
            prompt_version="v4" if use_multi_doc else None,
            multi_doc=use_multi_doc,
            grouped_docs=grouped_docs,
        )
        latency_ms = int((time.perf_counter() - started) * 1000)
        scores = score_answer(question, answer)

        row = {
            "question_id": question["question_id"],
            "question": question["question"],
            "question_type": question["question_type"],
            "expected_behavior": question["expected_behavior"],
            "response_type": answer["response_type"],
            "answer": answer["answer"],
            "citations": answer["citations"],
            "any_source_hit": any_source_hit(expected_docs, chunks),
            "all_sources_hit": all_sources_hit(expected_docs, chunks),
            "source_coverage_score": source_coverage_score(expected_docs, chunks),
            "all_required_sources_cited": all_required_sources_cited(expected_docs, answer["citations"]),
            "final_confidence": answer["final_confidence"],
            "latency_ms": latency_ms,
            "mode": label,
            "input_tokens": answer["input_tokens"],
            "output_tokens": answer["output_tokens"],
            "input_cost_usd": answer.get("input_cost_usd"),
            "output_cost_usd": answer.get("output_cost_usd"),
            "estimated_cost_usd": answer.get("estimated_cost_usd"),
            "pricing_status": answer.get("pricing_status"),
            **scores,
        }
        rows.append(row)
        print(
            f"  response={row['response_type']} "
            f"answer_acc={row['answer_accuracy']} "
            f"citation_acc={row['citation_accuracy']} "
            f"all_sources_hit={row['all_sources_hit']}",
            flush=True,
        )
    return rows


def _print_comparison(baseline_rows: list[dict], multi_doc_rows: list[dict]) -> None:
    baseline = multi_doc_summary(baseline_rows)
    improved = multi_doc_summary(multi_doc_rows)

    print("\n=== Multi-Document Evaluation Results ===\n")
    print(f"{'Metric':<35} {'Baseline':>10} {'Multi-Doc':>10}")
    print("-" * 57)
    for key in [
        "answer_accuracy",
        "citation_accuracy",
        "all_sources_hit",
        "source_coverage_score",
        "hallucination_rate",
        "response_type_accuracy",
        "all_required_sources_cited_rate",
        "failed_question_count",
    ]:
        b = baseline.get(key)
        m = improved.get(key)
        b_str = f"{b:.3f}" if isinstance(b, float) else str(b) if b is not None else "-"
        m_str = f"{m:.3f}" if isinstance(m, float) else str(m) if m is not None else "-"
        print(f"{key:<35} {b_str:>10} {m_str:>10}")


def main() -> None:
    questions = _load_benchmark()
    print(f"Running multi-document evaluation on {len(questions)} MULTI questions.\n")

    baseline_rows = _run_pass(questions, use_multi_doc=False)
    multi_doc_rows = _run_pass(questions, use_multi_doc=True)

    _print_comparison(baseline_rows, multi_doc_rows)

    result = {
        "baseline": {
            "rows": baseline_rows,
            "summary": multi_doc_summary(baseline_rows),
        },
        "multi_doc": {
            "rows": multi_doc_rows,
            "summary": multi_doc_summary(multi_doc_rows),
        },
    }

    RESULTS_PATH.parent.mkdir(parents=True, exist_ok=True)
    RESULTS_PATH.write_text(json.dumps(result, indent=2), encoding="utf-8")
    print(f"\nWrote results to {RESULTS_PATH}")


if __name__ == "__main__":
    main()
