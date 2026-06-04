from apps.api.app.retrieval.config import RetrievalConfig, default_retrieval_config


def phase6_retrieval_configs() -> list[RetrievalConfig]:
    return [
        default_retrieval_config(
            run_name="vector-section",
            retrieval_mode="vector_only",
            chunking_strategy="section_based",
        ),
        default_retrieval_config(
            run_name="keyword-section",
            retrieval_mode="keyword_only",
            chunking_strategy="section_based",
        ),
        default_retrieval_config(
            run_name="hybrid-section-0.5",
            retrieval_mode="hybrid",
            chunking_strategy="section_based",
            vector_weight=0.5,
            keyword_weight=0.5,
        ),
        default_retrieval_config(
            run_name="vector-fixed-size",
            retrieval_mode="vector_only",
            chunking_strategy="fixed_size",
        ),
        default_retrieval_config(
            run_name="hybrid-fixed-size-0.5",
            retrieval_mode="hybrid",
            chunking_strategy="fixed_size",
            vector_weight=0.5,
            keyword_weight=0.5,
        ),
    ]
