import hashlib
import time

from openai import OpenAI

from apps.api.app.core.config import get_settings
from apps.api.app.observability.auxiliary_telemetry import submit_auxiliary_telemetry

_EMBEDDING_CACHE: dict[tuple[str, str], list[float]] = {}


def _client() -> OpenAI:
    settings = get_settings()
    if not settings.openai_api_key:
        raise RuntimeError("OPENAI_API_KEY is required for embedding generation")
    return OpenAI(api_key=settings.openai_api_key)


def clear_embedding_cache() -> None:
    _EMBEDDING_CACHE.clear()


def _cache_key(model: str, text: str) -> tuple[str, str]:
    return model, hashlib.sha256(text.encode("utf-8")).hexdigest()


def embed_texts(texts: list[str]) -> list[list[float]]:
    if not texts:
        return []

    settings = get_settings()
    model = settings.openai_embedding_model
    uncached_texts: list[str] = []
    uncached_keys: list[tuple[str, str]] = []
    seen_uncached: set[tuple[str, str]] = set()
    for text in texts:
        key = _cache_key(model, text)
        if key in _EMBEDDING_CACHE or key in seen_uncached:
            continue
        uncached_texts.append(text)
        uncached_keys.append(key)
        seen_uncached.add(key)

    if uncached_texts:
        started_at = time.perf_counter()
        response = _client().embeddings.create(
            model=model,
            input=uncached_texts,
        )
        usage = getattr(response, "usage", None)
        input_tokens = getattr(usage, "prompt_tokens", None) if usage else None
        for key, item in zip(uncached_keys, response.data, strict=True):
            _EMBEDDING_CACHE[key] = list(item.embedding)
        submit_auxiliary_telemetry(
            operation_type="embedding_generation",
            model=model,
            input_tokens=input_tokens,
            pricing_status="unpriced" if input_tokens is not None else "unknown",
            latency_ms=int((time.perf_counter() - started_at) * 1000),
            metadata={
                "embedding_count": len(uncached_texts),
                "cache_hit": False,
            },
        )

    return [list(_EMBEDDING_CACHE[_cache_key(model, text)]) for text in texts]


def embed_text(text: str) -> list[float]:
    return embed_texts([text])[0]


def to_vector_literal(embedding: list[float]) -> str:
    return "[" + ",".join(f"{value:.10f}" for value in embedding) + "]"
