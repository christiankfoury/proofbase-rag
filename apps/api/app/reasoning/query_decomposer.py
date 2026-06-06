from __future__ import annotations

import dataclasses
import json

from openai import OpenAI

from apps.api.app.core.config import get_settings
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
    try:
        response = _client().chat.completions.create(
            model=model,
            temperature=0,
            messages=[
                {"role": "system", "content": _DECOMPOSE_SYSTEM},
                {"role": "user", "content": question},
            ],
        )
        raw = response.choices[0].message.content or ""
        parsed = json.loads(raw)
        if isinstance(parsed, list) and all(isinstance(q, str) for q in parsed):
            return [q for q in parsed if q.strip()][:3]
    except Exception:
        pass
    return [question]


def retrieve_multi_doc(
    question: str,
    user_role: str,
    config: RetrievalConfig,
) -> list[RetrievedChunk]:
    subqueries = decompose_question(question, model=config.model)
    subquery_config = dataclasses.replace(config, top_k=4, run_name="multi-doc-subquery")

    seen: dict[str, RetrievedChunk] = {}
    for subquery in subqueries:
        for chunk in retrieve_chunks(subquery, user_role, subquery_config):
            if chunk.chunk_id not in seen:
                seen[chunk.chunk_id] = chunk

    merged = sorted(seen.values(), key=lambda c: c.score, reverse=True)[:10]
    return [
        dataclasses.replace(chunk, rank=rank)
        for rank, chunk in enumerate(merged, start=1)
    ]
