from __future__ import annotations

from statistics import mean
from typing import Any

from apps.api.app.evaluation.metrics import expected_source_recall
from apps.api.app.retrieval.types import RetrievedChunk


def source_coverage_score(expected_docs: list[str], chunks: list[RetrievedChunk]) -> float:
    result = expected_source_recall(expected_docs, chunks)
    return result if result is not None else 0.0


def all_required_sources_cited(expected_docs: list[str], citations: list[dict]) -> bool:
    if not expected_docs:
        return True
    cited_doc_ids = {c.get("document_id", "") for c in citations}
    return all(doc_id in cited_doc_ids for doc_id in expected_docs)


def multi_doc_summary(rows: list[dict[str, Any]]) -> dict[str, Any]:
    multi_rows = [r for r in rows if r.get("question_type") == "multi_document"]
    if not multi_rows:
        return {"multi_doc_question_count": 0}

    def _avg(values: list) -> float | None:
        real = [v for v in values if v is not None]
        return round(mean(real), 3) if real else None

    def _sum(values: list) -> int | None:
        real = [v for v in values if v is not None]
        return sum(real) if real else None

    def _sum_cost(values: list) -> float | None:
        real = [v for v in values if v is not None]
        return round(sum(real), 6) if real else None

    return {
        "multi_doc_question_count": len(multi_rows),
        "answer_accuracy": _avg([r.get("answer_accuracy") for r in multi_rows]),
        "citation_accuracy": _avg([r.get("citation_accuracy") for r in multi_rows]),
        "all_sources_hit": _avg([r.get("all_sources_hit") for r in multi_rows]),
        "source_coverage_score": _avg([r.get("source_coverage_score") for r in multi_rows]),
        "hallucination_rate": _avg([r.get("hallucination_rate") for r in multi_rows]),
        "response_type_accuracy": _avg([r.get("response_type_accuracy") for r in multi_rows]),
        "all_required_sources_cited_rate": _avg([
            1.0 if r.get("all_required_sources_cited") else 0.0
            for r in multi_rows
        ]),
        "failed_question_count": sum(
            1 for r in multi_rows if r.get("answer_accuracy", 1.0) < 1.0
        ),
        "input_tokens": _sum([r.get("input_tokens") for r in multi_rows]),
        "output_tokens": _sum([r.get("output_tokens") for r in multi_rows]),
        "estimated_cost": _sum_cost([r.get("estimated_cost_usd") for r in multi_rows]),
    }
