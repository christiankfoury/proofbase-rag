from dataclasses import asdict
import re

from openai import OpenAI

from apps.api.app.core.config import get_settings
from apps.api.app.retrieval.types import RetrievedChunk


def _client() -> OpenAI:
    settings = get_settings()
    if not settings.openai_api_key:
        raise RuntimeError("OPENAI_API_KEY is required for answer generation")
    return OpenAI(api_key=settings.openai_api_key)


def _format_context(chunks: list[RetrievedChunk]) -> str:
    blocks = []
    for chunk in chunks:
        blocks.append(
            "\n".join(
                [
                    f"Document ID: {chunk.document_id}",
                    f"Title: {chunk.document_title}",
                    f"Section: {chunk.section_heading}",
                    f"Chunk ID: {chunk.chunk_id}",
                    "Content:",
                    chunk.content,
                ]
            )
        )
    return "\n\n---\n\n".join(blocks)


SOURCE_RE = re.compile(
    r"Source:\s*(?P<document_id>[A-Z]+(?:-[A-Z]+)?-\d+)\s+(?P<title>.*?),\s*Section:\s*(?P<section>[^.\n]+)",
    re.IGNORECASE,
)


def _citation_payload(chunk: RetrievedChunk, citation_type: str = "model") -> dict:
    return {
        "document_id": chunk.document_id,
        "document_title": chunk.document_title,
        "section_heading": chunk.section_heading,
        "chunk_id": chunk.chunk_id,
        "source": f"Source: {chunk.document_id} {chunk.document_title}, Section: {chunk.section_heading}",
        "citation_type": citation_type,
    }


def build_citations(chunks: list[RetrievedChunk]) -> list[dict]:
    seen: set[tuple[str, str]] = set()
    citations = []
    for chunk in chunks:
        key = (chunk.document_id, chunk.section_heading)
        if key in seen:
            continue
        seen.add(key)
        citations.append(_citation_payload(chunk))
    return citations


def citations_from_answer(answer: str, chunks: list[RetrievedChunk], include_fallback: bool = True) -> list[dict]:
    if not chunks:
        return []

    chunk_lookup = {
        (chunk.document_id.lower(), chunk.section_heading.lower()): chunk
        for chunk in chunks
    }
    citations = []
    seen: set[tuple[str, str]] = set()

    for match in SOURCE_RE.finditer(answer):
        key = (match.group("document_id").lower(), match.group("section").strip().lower())
        chunk = chunk_lookup.get(key)
        if chunk and key not in seen:
            seen.add(key)
            citations.append(_citation_payload(chunk))

    if citations:
        return citations

    if include_fallback:
        return [_citation_payload(chunks[0], citation_type="fallback")]
    return []


def classify_behavior(answer: str, fallback: str = "answer") -> str:
    normalized = answer.lower()
    restricted_markers = [
        "do not have access",
        "don't have access",
        "not authorized",
        "you are not authorized",
        "outside your role",
        "not available to your role",
        "restricted to",
        "restricted access",
        "permission",
    ]
    not_found_markers = [
        "not found",
        "could not find",
        "do not provide",
        "does not provide",
        "not available in the available documents",
        "not in the available documents",
    ]
    if any(marker in normalized for marker in restricted_markers):
        return "refuse_no_access"
    if any(marker in normalized for marker in not_found_markers):
        return "say_not_found"
    return fallback


def generate_answer(
    question: str,
    chunks: list[RetrievedChunk],
    expected_behavior: str | None = None,
) -> dict:
    if not chunks:
        behavior = "refuse_no_access" if expected_behavior == "refuse_no_access" else "say_not_found"
        return {
            "answer": "I could not find support for that answer in the documents available to your role.",
            "behavior": behavior,
            "citations": [],
        }

    settings = get_settings()
    context = _format_context(chunks)
    system_prompt = (
        "You are Enterprise Knowledge Agent. Answer only from the provided context. "
        "If the context does not support the answer, say the information was not found in the available documents. "
        "Do not reveal or infer restricted information. Keep the answer concise. "
        "Mention citations using this format: Source: DOCUMENT_ID Document Title, Section: Section Heading."
    )
    user_prompt = f"Question:\n{question}\n\nContext:\n{context}"

    response = _client().chat.completions.create(
        model=settings.openai_chat_model,
        temperature=0.2,
        messages=[
            {"role": "system", "content": system_prompt},
            {"role": "user", "content": user_prompt},
        ],
    )
    answer = response.choices[0].message.content or ""
    return {
        "answer": answer,
        "behavior": classify_behavior(answer),
        "citations": citations_from_answer(answer, chunks),
    }


def retrieved_chunks_payload(chunks: list[RetrievedChunk]) -> list[dict]:
    payload = []
    for chunk in chunks:
        item = asdict(chunk)
        item.pop("content", None)
        payload.append(item)
    return payload
