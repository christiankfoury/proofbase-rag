from apps.api.app.evaluation.metrics import all_sources_hit, behavior_match
from apps.api.app.permissions.access_control import unauthorized_chunks_reached_generation
from apps.api.app.retrieval.types import RetrievedChunk


def followup_detection_accuracy(is_followup: bool) -> float:
    return 1.0 if is_followup else 0.0


def query_rewrite_quality(expected_documents: list[str], retrieved_chunks: list[RetrievedChunk]) -> float | None:
    return all_sources_hit(expected_documents, retrieved_chunks)


def memory_response_type_accuracy(expected_behavior: str, generated_behavior: str) -> float:
    if expected_behavior == "answer_with_memory" and generated_behavior == "answer":
        return 1.0
    return behavior_match(expected_behavior, generated_behavior)


def memory_permission_leakage(chunks: list[RetrievedChunk], user_role: str, citations: list[dict]) -> float:
    if unauthorized_chunks_reached_generation(chunks, user_role):
        return 1.0
    chunk_doc_ids = {chunk.document_id for chunk in chunks if chunk.restricted}
    cited_doc_ids = {citation.get("document_id") for citation in citations}
    return 1.0 if chunk_doc_ids & cited_doc_ids and unauthorized_chunks_reached_generation(chunks, user_role) else 0.0
