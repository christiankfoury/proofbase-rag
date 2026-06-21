from __future__ import annotations

from typing import Any


CITATION_FAILURE_LABELS = {
    "wrong_document_cited": "Wrong document cited",
    "right_document_wrong_chunk": "Right document but wrong chunk",
    "citation_missing": "Citation missing",
    "citation_attached_to_unsupported_claim": "Citation attached to unsupported claim",
    "citation_from_restricted_source": "Citation from restricted source",
}


def _document_ids(items: list[dict[str, Any]]) -> set[str]:
    return {str(item.get("document_id")) for item in items if item.get("document_id")}


def _expected_sections(question: dict[str, Any]) -> dict[str, set[str]]:
    sections: dict[str, set[str]] = {}
    for item in question.get("expected_source_section_or_quote") or []:
        document_id = item.get("document_id")
        section = item.get("section")
        if not document_id or not section:
            continue
        sections.setdefault(str(document_id), set()).add(str(section).strip().lower())
    return sections


def _role_has_access(user_role: str | None, allowed_roles: list[str]) -> bool:
    if not user_role:
        return False
    if user_role in allowed_roles:
        return True
    if user_role == "IT Admin" and "IT/Admin" in allowed_roles:
        return True
    if user_role == "IT/Admin" and "IT Admin" in allowed_roles:
        return True
    return False


def _value(item: Any, key: str, default: Any = None) -> Any:
    if isinstance(item, dict):
        return item.get(key, default)
    return getattr(item, key, default)


def _restricted_citation_documents(question: dict[str, Any], result: dict[str, Any]) -> set[str]:
    user_role = question.get("user_role")
    retrieved_chunks = result.get("retrieved_chunks") or result.get("retrieved_chunks_raw") or []
    retrieved_by_chunk = {
        str(_value(chunk, "chunk_id")): chunk
        for chunk in retrieved_chunks
        if _value(chunk, "chunk_id")
    }
    restricted_documents: set[str] = set()
    for citation in result.get("citations") or result.get("actual_citations") or []:
        chunk = retrieved_by_chunk.get(str(citation.get("chunk_id") or ""))
        if not chunk:
            continue
        if _value(chunk, "restricted") and not _role_has_access(user_role, list(_value(chunk, "access_roles", []) or [])):
            document_id = citation.get("document_id")
            if document_id:
                restricted_documents.add(str(document_id))
    return restricted_documents


def classify_citation_failure_categories(question: dict[str, Any], result: dict[str, Any]) -> list[str]:
    if question.get("expected_behavior") not in {"answer", "answer_with_memory"}:
        return []

    expected_docs = set(question.get("expected_source_document") or [])
    if not expected_docs:
        return []

    citations = result.get("citations") or result.get("actual_citations") or []
    cited_docs = _document_ids(citations)
    categories: set[str] = set()

    if not citations:
        categories.add("citation_missing")
    elif expected_docs - cited_docs:
        categories.add("citation_missing")

    unexpected_docs = cited_docs - expected_docs
    if unexpected_docs:
        categories.add("wrong_document_cited")

    restricted_citation_documents = _restricted_citation_documents(question, result)
    if restricted_citation_documents:
        categories.add("citation_from_restricted_source")

    expected_sections = _expected_sections(question)
    for citation in citations:
        confidence = citation.get("confidence")
        if isinstance(confidence, (int, float)) and confidence < 0.5:
            categories.add("citation_attached_to_unsupported_claim")
        document_id = str(citation.get("document_id") or "")
        if document_id not in expected_docs:
            continue
        section_heading = str(citation.get("section_heading") or "").strip().lower()
        section_options = expected_sections.get(document_id) or set()
        if section_options and section_heading and section_heading not in section_options:
            categories.add("right_document_wrong_chunk")

    if result.get("unsupported_claims") or result.get("hallucination_rate") == 1.0:
        categories.add("citation_attached_to_unsupported_claim")
    if (result.get("citation_confidence") or 0.0) < 0.5:
        categories.add("citation_attached_to_unsupported_claim")

    ordered = [
        "wrong_document_cited",
        "right_document_wrong_chunk",
        "citation_missing",
        "citation_attached_to_unsupported_claim",
        "citation_from_restricted_source",
    ]
    return [category for category in ordered if category in categories]


def citation_failure_summary(question: dict[str, Any], result: dict[str, Any]) -> dict[str, Any]:
    categories = classify_citation_failure_categories(question, result)
    expected_docs = list(question.get("expected_source_document") or [])
    citations = result.get("citations") or result.get("actual_citations") or []
    cited_docs = sorted(_document_ids(citations))
    return {
        "citation_failure_categories": categories,
        "citation_failure_labels": [CITATION_FAILURE_LABELS[category] for category in categories],
        "missing_citation_documents": [document_id for document_id in expected_docs if document_id not in cited_docs],
        "unexpected_citation_documents": [document_id for document_id in cited_docs if document_id not in expected_docs],
        "restricted_citation_documents": sorted(_restricted_citation_documents(question, result)),
    }
