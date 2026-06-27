from apps.api.app.retrieval.config import RetrievalConfig, default_retrieval_config
from apps.api.app.retrieval import hybrid_retriever, keyword_retriever, vector_retriever
from apps.api.app.retrieval.types import RetrievedChunk


def retrieve_chunks(
    question: str,
    user_role: str,
    config: RetrievalConfig | None = None,
) -> list[RetrievedChunk]:
    active_config = config or default_retrieval_config()

    if active_config.retrieval_mode in {"vector_only", "vector_lexical_rerank"}:
        return vector_retriever.retrieve_chunks(
            question,
            user_role,
            top_k=active_config.top_k,
            chunking_strategy=active_config.chunking_strategy,
            project_id=active_config.project_id,
            department_id=active_config.department_id,
            excluded_document_prefixes=active_config.excluded_document_prefixes,
            reranker="lexical" if active_config.retrieval_mode == "vector_lexical_rerank" else active_config.reranker,
            rerank_candidate_limit=active_config.rerank_candidate_limit,
        )
    if active_config.retrieval_mode == "keyword_only":
        return keyword_retriever.retrieve_chunks(
            question,
            user_role,
            top_k=active_config.top_k,
            chunking_strategy=active_config.chunking_strategy,
            project_id=active_config.project_id,
            department_id=active_config.department_id,
            excluded_document_prefixes=active_config.excluded_document_prefixes,
        )
    if active_config.retrieval_mode == "hybrid":
        return hybrid_retriever.retrieve_chunks(
            question,
            user_role,
            top_k=active_config.top_k,
            chunking_strategy=active_config.chunking_strategy,
            vector_weight=active_config.vector_weight,
            keyword_weight=active_config.keyword_weight,
            project_id=active_config.project_id,
            department_id=active_config.department_id,
            excluded_document_prefixes=active_config.excluded_document_prefixes,
        )

    raise ValueError(f"Unsupported retrieval mode: {active_config.retrieval_mode}")
