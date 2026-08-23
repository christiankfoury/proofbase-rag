from __future__ import annotations

import dataclasses
import json
import re
import time

from openai import OpenAI

from apps.api.app.core.config import get_settings
from apps.api.app.costing.estimator import estimate_chat_cost
from apps.api.app.observability.auxiliary_telemetry import submit_auxiliary_telemetry
from apps.api.app.reasoning.source_planner import SourcePlanItem, plan_multi_document_sources
from apps.api.app.retrieval.config import RetrievalConfig
from apps.api.app.retrieval.retriever import retrieve_chunks
from apps.api.app.retrieval.types import RetrievedChunk

_DECOMPOSE_SYSTEM = (
    "You are a search query decomposer for an enterprise knowledge assistant. "
    "Given a question that requires information from multiple source documents, "
    "generate 2 to 3 specific search queries — one per required document domain. "
    "Return only a valid JSON array of query strings, nothing else. "
    "Example: [\"What is the remote work approval process?\", \"What device security rules apply to remote employees?\"]"
)


def _client() -> OpenAI:
    settings = get_settings()
    return OpenAI(api_key=settings.openai_api_key)


def decompose_question(question: str, model: str = "gpt-4.1-mini") -> list[str]:
    started_at = time.perf_counter()
    try:
        response = _client().chat.completions.create(
            model=model,
            temperature=0,
            messages=[
                {"role": "system", "content": _DECOMPOSE_SYSTEM},
                {"role": "user", "content": question},
            ],
        )
        usage = response.usage
        input_tokens = usage.prompt_tokens if usage else None
        output_tokens = usage.completion_tokens if usage else None
        cost = estimate_chat_cost(model=model, input_tokens=input_tokens, output_tokens=output_tokens)
        raw = response.choices[0].message.content or ""
        parsed = json.loads(raw)
        if isinstance(parsed, list) and all(isinstance(q, str) for q in parsed):
            subqueries = [q for q in parsed if q.strip()][:3]
            submit_auxiliary_telemetry(
                operation_type="query_decomposition",
                model=model,
                prompt_name="query_decomposition",
                input_tokens=input_tokens,
                output_tokens=output_tokens,
                estimated_cost_usd=cost["estimated_cost_usd"],
                pricing_status=cost["pricing_status"],
                latency_ms=int((time.perf_counter() - started_at) * 1000),
                question=question,
            )
            return subqueries
        submit_auxiliary_telemetry(
            operation_type="query_decomposition",
            model=model,
            status="failed",
            prompt_name="query_decomposition",
            input_tokens=input_tokens,
            output_tokens=output_tokens,
            estimated_cost_usd=cost["estimated_cost_usd"],
            pricing_status=cost["pricing_status"],
            latency_ms=int((time.perf_counter() - started_at) * 1000),
            question=question,
            error_category="invalid_provider_response",
            error_message_redacted="Query decomposition returned invalid JSON",
        )
    except Exception:
        submit_auxiliary_telemetry(
            operation_type="query_decomposition",
            model=model,
            status="failed",
            prompt_name="query_decomposition",
            pricing_status="unknown",
            latency_ms=int((time.perf_counter() - started_at) * 1000),
            question=question,
            error_category="provider_error",
            error_message_redacted="Query decomposition failed",
        )
        pass
    return [question]


def retrieve_multi_doc(
    question: str,
    user_role: str,
    config: RetrievalConfig,
) -> list[RetrievedChunk]:
    source_plan = plan_multi_document_sources(question)
    subqueries = [item.query for item in source_plan] or decompose_question(question, model=config.model)
    subquery_config = dataclasses.replace(config, top_k=8, run_name="multi-doc-subquery")

    seen: dict[str, RetrievedChunk] = {}
    per_query_results: list[tuple[SourcePlanItem | None, list[RetrievedChunk]]] = []
    for index, subquery in enumerate(subqueries):
        plan_item = source_plan[index] if source_plan else None
        chunks = retrieve_chunks(subquery, user_role, subquery_config)
        per_query_results.append((plan_item, chunks))
        for chunk in chunks:
            if chunk.chunk_id not in seen:
                seen[chunk.chunk_id] = chunk

    planned_first = _coverage_first_chunks(per_query_results)
    merged = planned_first + [
        chunk
        for chunk in sorted(seen.values(), key=lambda c: c.score, reverse=True)
        if chunk.chunk_id not in {planned.chunk_id for planned in planned_first}
    ]
    merged = merged[:10]
    return [
        dataclasses.replace(chunk, rank=rank)
        for rank, chunk in enumerate(merged, start=1)
    ]


def _coverage_first_chunks(
    per_query_results: list[tuple[SourcePlanItem | None, list[RetrievedChunk]]],
) -> list[RetrievedChunk]:
    selected: list[RetrievedChunk] = []
    selected_ids: set[str] = set()
    for plan_item, chunks in per_query_results:
        if not plan_item:
            continue
        for document_id in plan_item.target_document_ids:
            candidates = [chunk for chunk in chunks if chunk.document_id == document_id and chunk.chunk_id not in selected_ids]
            if not candidates:
                continue
            query_terms = set(re.findall(r"[a-z0-9]+", plan_item.query.lower()))
            best = sorted(
                candidates,
                key=lambda chunk: (
                    len(query_terms & set(re.findall(r"[a-z0-9]+", f"{chunk.section_heading} {chunk.content}".lower()))),
                    chunk.score,
                ),
                reverse=True,
            )[0]
            selected.append(best)
            selected_ids.add(best.chunk_id)
    return selected
