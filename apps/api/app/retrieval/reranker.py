from __future__ import annotations

import dataclasses
import re

from apps.api.app.retrieval.types import RetrievedChunk


STOP_WORDS = {
    "about",
    "after",
    "also",
    "and",
    "are",
    "assistant",
    "before",
    "can",
    "could",
    "does",
    "follow",
    "for",
    "from",
    "have",
    "how",
    "into",
    "question",
    "should",
    "that",
    "the",
    "this",
    "turn",
    "user",
    "what",
    "when",
    "where",
    "which",
    "who",
    "with",
}

TOKEN_PATTERN = re.compile(r"[a-z0-9]+")


def tokenize(text: str) -> list[str]:
    return [
        token
        for token in TOKEN_PATTERN.findall(text.lower())
        if len(token) >= 3 and token not in STOP_WORDS
    ]


def lexical_overlap_score(query: str, chunk: RetrievedChunk) -> float:
    query_terms = set(tokenize(query))
    if not query_terms:
        return 0.0

    document_terms = set(tokenize(chunk.document_id.replace("-", " ")))
    title_terms = set(tokenize(chunk.document_title))
    heading_terms = set(tokenize(chunk.section_heading))
    content_terms = set(tokenize(chunk.content[:1200]))

    weighted_hits = (
        (2.0 * len(query_terms & document_terms))
        + (3.0 * len(query_terms & title_terms))
        + (4.0 * len(query_terms & heading_terms))
        + len(query_terms & content_terms)
    )
    return weighted_hits / len(query_terms)


def rerank_chunks(
    query: str,
    chunks: list[RetrievedChunk],
    *,
    vector_weight: float = 1.0,
    lexical_weight: float = 0.08,
) -> list[RetrievedChunk]:
    if not chunks:
        return []

    scored: list[tuple[float, int, RetrievedChunk, float]] = []
    for index, chunk in enumerate(chunks):
        lexical_score = lexical_overlap_score(query, chunk)
        vector_score = chunk.vector_score if chunk.vector_score is not None else chunk.score
        combined_score = (vector_weight * vector_score) + (lexical_weight * lexical_score)
        scored.append((combined_score, -index, chunk, lexical_score))

    scored.sort(key=lambda item: (item[0], item[1]), reverse=True)
    return [
        dataclasses.replace(
            chunk,
            rank=rank,
            score=combined_score,
            hybrid_score=combined_score,
            keyword_score=chunk.keyword_score,
            retrieval_source="vector_lexical_rerank",
        )
        for rank, (combined_score, _stable_order, chunk, lexical_score) in enumerate(scored, start=1)
    ]
