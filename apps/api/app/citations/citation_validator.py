import re

from apps.api.app.citations.citation_formatter import citation_payload
from apps.api.app.retrieval.types import RetrievedChunk


STOP_WORDS = {
    "about",
    "after",
    "also",
    "and",
    "are",
    "available",
    "because",
    "been",
    "but",
    "can",
    "could",
    "does",
    "for",
    "from",
    "has",
    "have",
    "how",
    "into",
    "may",
    "must",
    "not",
    "per",
    "should",
    "that",
    "the",
    "their",
    "this",
    "through",
    "with",
    "within",
    "would",
    "you",
}


def _terms(text: str) -> set[str]:
    return {
        token
        for token in re.findall(r"[a-zA-Z0-9]+", text.lower())
        if len(token) >= 3 and token not in STOP_WORDS
    }


def _chunk_lookup(chunks: list[RetrievedChunk]) -> dict[str, RetrievedChunk]:
    return {chunk.chunk_id: chunk for chunk in chunks}


def _confidence_from_overlap(answer: str, citation_text: str, chunk: RetrievedChunk) -> float:
    answer_terms = _terms(answer)
    evidence_terms = _terms(f"{citation_text} {chunk.content}")
    if not answer_terms:
        overlap_score = 0.0
    else:
        overlap_score = len(answer_terms & evidence_terms) / len(answer_terms)
    rank_score = max(0.0, 1.0 - ((chunk.rank - 1) * 0.12))
    retrieval_score = min(max(chunk.score, 0.0), 1.0)
    return round((0.55 * overlap_score) + (0.25 * rank_score) + (0.20 * retrieval_score), 3)


def validate_citations(answer: str, citations: list[dict], chunks: list[RetrievedChunk]) -> dict:
    chunks_by_id = _chunk_lookup(chunks)
    validated = []
    supported_claims = []
    unsupported_claims = []

    for citation in citations:
        chunk = chunks_by_id.get(citation.get("chunk_id", ""))
        if not chunk:
            unsupported_claims.append(f"Citation does not match retrieved chunk: {citation.get('chunk_id')}")
            continue
        citation_text = citation.get("citation_text") or citation.get("source") or ""
        confidence = _confidence_from_overlap(answer, citation_text, chunk)
        validated.append(
            citation_payload(
                chunk,
                citation_type=citation.get("citation_type", "model"),
                citation_text=citation_text,
                confidence=confidence,
            )
        )
        if confidence >= 0.7:
            supported_claims.append(f"{chunk.document_id}: {chunk.section_heading}")
        elif confidence < 0.5:
            unsupported_claims.append(f"Weak support from {chunk.document_id}: {chunk.section_heading}")

    if validated:
        citation_confidence = round(sum(item["confidence"] for item in validated) / len(validated), 3)
    else:
        citation_confidence = 0.0

    if citation_confidence >= 0.85:
        validation_notes = "Strong citation support."
    elif citation_confidence >= 0.7:
        validation_notes = "Acceptable citation support."
    elif citation_confidence >= 0.5:
        validation_notes = "Weak citation support; answer should be treated cautiously."
    else:
        validation_notes = "Not enough citation support."

    return {
        "citations": validated,
        "citation_confidence": citation_confidence,
        "supported_claims": supported_claims,
        "unsupported_claims": unsupported_claims,
        "validation_notes": validation_notes,
    }
