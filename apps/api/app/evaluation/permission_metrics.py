from apps.api.app.retrieval.types import RetrievedChunk


def expected_doc_set(question: dict) -> set[str]:
    return set(question.get("expected_source_document") or [])


def unauthorized_chunk_exposure(question: dict, chunks: list[RetrievedChunk]) -> float:
    expected_docs = expected_doc_set(question)
    if not expected_docs:
        return 0.0
    retrieved_docs = {chunk.document_id for chunk in chunks}
    return 1.0 if expected_docs & retrieved_docs else 0.0


def restricted_citation_leakage(question: dict, citations: list[dict]) -> float:
    expected_docs = expected_doc_set(question)
    if not expected_docs:
        return 0.0
    cited_docs = {citation.get("document_id") for citation in citations}
    return 1.0 if expected_docs & cited_docs else 0.0


def permission_leakage(question: dict, chunks: list[RetrievedChunk], citations: list[dict]) -> float:
    return max(
        unauthorized_chunk_exposure(question, chunks),
        restricted_citation_leakage(question, citations),
    )


def blocked_answer_accuracy(response_type: str) -> float:
    return 1.0 if response_type == "refuse_no_access" else 0.0


def authorized_retrieval_accuracy(expected_documents: list[str], chunks: list[RetrievedChunk]) -> float | None:
    if not expected_documents:
        return None
    retrieved_docs = {chunk.document_id for chunk in chunks}
    return 1.0 if all(document_id in retrieved_docs for document_id in expected_documents) else 0.0

