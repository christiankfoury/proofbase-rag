import re

from apps.api.app.retrieval.types import RetrievedChunk


def citation_payload(
    chunk: RetrievedChunk,
    citation_type: str = "model",
    citation_text: str | None = None,
    confidence: float | None = None,
    answer: str = "",
) -> dict:
    # The UI renders citation_text as an excerpt. A model paraphrase or a join
    # across source passages must never be presented as a contiguous quotation.
    # Replacing the display excerpt does not establish support for answer claims.
    if not citation_text or citation_text not in chunk.content:
        citation_text = select_source_excerpt(chunk.content, answer or citation_text or "")
        citation_type = "fallback"
    payload = {
        "document_id": chunk.document_id,
        "document_title": chunk.document_title,
        "section_heading": chunk.section_heading,
        "chunk_id": chunk.chunk_id,
        "citation_text": citation_text,
        "source": f"Source: {chunk.document_id} {chunk.document_title}, Section: {chunk.section_heading}",
        "citation_type": citation_type,
    }
    if confidence is not None:
        payload["confidence"] = confidence
    return payload


def fallback_citation(chunk: RetrievedChunk) -> dict:
    return citation_payload(chunk, citation_type="fallback", confidence=0.0)


def select_source_excerpt(content: str, context: str, limit: int = 480) -> str:
    """Rank contiguous source spans without manufacturing a quotation."""
    stop = {"the", "and", "for", "with", "what", "does", "this", "that", "are", "from", "need", "must"}
    terms = {w.casefold() for w in re.findall(r"\w{3,}", context)} - stop
    starts = [0] + [m.end() for m in re.finditer(r"(?<=[.!?])\s+|\n+", content)]
    candidates = []
    for start in starts:
        tail = content[start:start + limit]
        ends = list(re.finditer(r"[.!?](?=\s|$)|\n", tail))
        if start + limit < len(content):
            end = ends[-1].end() if ends else tail.rfind(" ")
            tail = tail[:end] if end > 0 else tail
        text = tail.strip()
        if text:
            words = {w.casefold() for w in re.findall(r"\w{3,}", text)}
            candidates.append((len(terms & words), -start, text))
    return max(candidates)[2] if candidates else content[:limit]
