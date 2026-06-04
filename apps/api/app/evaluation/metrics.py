from apps.api.app.retrieval.vector_retriever import RetrievedChunk


def any_source_hit(expected_documents: list[str], retrieved_chunks: list[RetrievedChunk]) -> float | None:
    if not expected_documents:
        return None
    retrieved_docs = {chunk.document_id for chunk in retrieved_chunks}
    return 1.0 if any(document_id in retrieved_docs for document_id in expected_documents) else 0.0


def all_sources_hit(expected_documents: list[str], retrieved_chunks: list[RetrievedChunk]) -> float | None:
    if not expected_documents:
        return None
    retrieved_docs = {chunk.document_id for chunk in retrieved_chunks}
    return 1.0 if all(document_id in retrieved_docs for document_id in expected_documents) else 0.0


def expected_source_recall(expected_documents: list[str], retrieved_chunks: list[RetrievedChunk]) -> float | None:
    if not expected_documents:
        return None
    retrieved_docs = {chunk.document_id for chunk in retrieved_chunks}
    matched_documents = {document_id for document_id in expected_documents if document_id in retrieved_docs}
    return len(matched_documents) / len(set(expected_documents))


def retrieval_hit(expected_documents: list[str], retrieved_chunks: list[RetrievedChunk]) -> float | None:
    return any_source_hit(expected_documents, retrieved_chunks)


def reciprocal_rank(expected_documents: list[str], retrieved_chunks: list[RetrievedChunk]) -> float | None:
    if not expected_documents:
        return None
    expected = set(expected_documents)
    for chunk in retrieved_chunks:
        if chunk.document_id in expected:
            return 1.0 / chunk.rank
    return 0.0


def citation_source_match(expected_documents: list[str], citations: list[dict]) -> float | None:
    if not expected_documents:
        return None
    cited_docs = {citation["document_id"] for citation in citations}
    return 1.0 if any(document_id in cited_docs for document_id in expected_documents) else 0.0


def behavior_match(expected_behavior: str, generated_behavior: str) -> float:
    if expected_behavior == generated_behavior:
        return 1.0
    if expected_behavior == "answer_with_memory" and generated_behavior == "answer":
        return 0.5
    if expected_behavior == "ask_clarifying_question" and generated_behavior == "answer":
        return 0.0
    return 0.0
