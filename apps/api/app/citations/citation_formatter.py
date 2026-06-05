from apps.api.app.retrieval.types import RetrievedChunk


def citation_payload(
    chunk: RetrievedChunk,
    citation_type: str = "model",
    citation_text: str | None = None,
    confidence: float | None = None,
) -> dict:
    payload = {
        "document_id": chunk.document_id,
        "document_title": chunk.document_title,
        "section_heading": chunk.section_heading,
        "chunk_id": chunk.chunk_id,
        "citation_text": citation_text or chunk.content[:240],
        "source": f"Source: {chunk.document_id} {chunk.document_title}, Section: {chunk.section_heading}",
        "citation_type": citation_type,
    }
    if confidence is not None:
        payload["confidence"] = confidence
    return payload


def fallback_citation(chunk: RetrievedChunk) -> dict:
    return citation_payload(chunk, citation_type="fallback", confidence=0.0)
