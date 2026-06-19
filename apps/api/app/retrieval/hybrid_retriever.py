from apps.api.app.core.config import get_settings
from apps.api.app.retrieval import keyword_retriever, vector_retriever
from apps.api.app.retrieval.types import RetrievedChunk


def _normalize_scores(values: list[float]) -> list[float]:
    if not values:
        return []
    minimum = min(values)
    maximum = max(values)
    if maximum == minimum:
        return [1.0 for _ in values]
    return [(value - minimum) / (maximum - minimum) for value in values]


def retrieve_chunks(
    question: str,
    user_role: str,
    top_k: int | None = None,
    chunking_strategy: str = "section_based",
    vector_weight: float = 0.5,
    keyword_weight: float = 0.5,
    project_id: str | None = None,
    department_id: str | None = None,
) -> list[RetrievedChunk]:
    settings = get_settings()
    limit = top_k or settings.default_top_k
    candidate_k = max(limit * 4, 20)

    vector_chunks = vector_retriever.retrieve_chunks(
        question,
        user_role,
        top_k=candidate_k,
        chunking_strategy=chunking_strategy,
        project_id=project_id,
        department_id=department_id,
    )
    keyword_chunks = keyword_retriever.retrieve_chunks(
        question,
        user_role,
        top_k=candidate_k,
        chunking_strategy=chunking_strategy,
        project_id=project_id,
        department_id=department_id,
    )

    vector_scores = {chunk.chunk_id: score for chunk, score in zip(vector_chunks, _normalize_scores([c.score for c in vector_chunks]), strict=True)}
    keyword_scores = {chunk.chunk_id: score for chunk, score in zip(keyword_chunks, _normalize_scores([c.score for c in keyword_chunks]), strict=True)}

    merged: dict[str, RetrievedChunk] = {}
    for chunk in vector_chunks + keyword_chunks:
        merged.setdefault(chunk.chunk_id, chunk)

    ranked = []
    for chunk_id, chunk in merged.items():
        normalized_vector = vector_scores.get(chunk_id, 0.0)
        normalized_keyword = keyword_scores.get(chunk_id, 0.0)
        hybrid_score = (vector_weight * normalized_vector) + (keyword_weight * normalized_keyword)
        if chunk_id in vector_scores and chunk_id in keyword_scores:
            source = "both"
        elif chunk_id in vector_scores:
            source = "vector"
        else:
            source = "keyword"
        ranked.append(
            RetrievedChunk(
                chunk_id=chunk.chunk_id,
                document_id=chunk.document_id,
                document_title=chunk.document_title,
                project_id=chunk.project_id,
                department_id=chunk.department_id,
                section_heading=chunk.section_heading,
                content=chunk.content,
                access_roles=chunk.access_roles,
                restricted=chunk.restricted,
                sensitivity=chunk.sensitivity,
                rank=0,
                score=hybrid_score,
                vector_score=normalized_vector if chunk_id in vector_scores else None,
                keyword_score=normalized_keyword if chunk_id in keyword_scores else None,
                hybrid_score=hybrid_score,
                retrieval_source=source,
            )
        )

    ranked.sort(key=lambda chunk: chunk.hybrid_score or 0.0, reverse=True)
    return [
        RetrievedChunk(
            chunk_id=chunk.chunk_id,
            document_id=chunk.document_id,
            document_title=chunk.document_title,
            project_id=chunk.project_id,
            department_id=chunk.department_id,
            section_heading=chunk.section_heading,
            content=chunk.content,
            access_roles=chunk.access_roles,
            restricted=chunk.restricted,
            sensitivity=chunk.sensitivity,
            rank=index + 1,
            score=chunk.hybrid_score or 0.0,
            vector_score=chunk.vector_score,
            keyword_score=chunk.keyword_score,
            hybrid_score=chunk.hybrid_score,
            retrieval_source=chunk.retrieval_source,
        )
        for index, chunk in enumerate(ranked[:limit])
    ]
