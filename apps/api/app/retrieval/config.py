from dataclasses import dataclass

from apps.api.app.core.config import get_settings


@dataclass(frozen=True)
class RetrievalConfig:
    run_name: str = "baseline-vector-only"
    retrieval_mode: str = "vector_only"
    chunking_strategy: str = "section_based"
    top_k: int = 5
    vector_weight: float = 0.5
    keyword_weight: float = 0.5
    prompt_version: str = "answer_v1"
    model: str = "gpt-4.1-mini"


def default_retrieval_config(
    retrieval_mode: str = "vector_only",
    chunking_strategy: str = "section_based",
    top_k: int | None = None,
    vector_weight: float = 0.5,
    keyword_weight: float = 0.5,
    run_name: str | None = None,
) -> RetrievalConfig:
    settings = get_settings()
    mode = retrieval_mode
    strategy = chunking_strategy
    return RetrievalConfig(
        run_name=run_name or f"{mode}-{strategy}",
        retrieval_mode=mode,
        chunking_strategy=strategy,
        top_k=top_k or settings.default_top_k,
        vector_weight=vector_weight,
        keyword_weight=keyword_weight,
        model=settings.openai_chat_model,
    )
