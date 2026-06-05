from apps.api.app.generation.response_types import RESPONSE_ANSWER, RESPONSE_PARTIAL_ANSWER
from apps.api.app.retrieval.types import RetrievedChunk


def retrieval_confidence(chunks: list[RetrievedChunk]) -> float:
    if not chunks:
        return 0.0
    top_score = min(max(chunks[0].score, 0.0), 1.0)
    rank_bonus = 1.0 if chunks[0].rank == 1 else 0.8
    supporting_documents = len({chunk.document_id for chunk in chunks[:3]})
    diversity_bonus = min(supporting_documents / 3, 1.0)
    return round((0.70 * top_score) + (0.20 * rank_bonus) + (0.10 * diversity_bonus), 3)


def answer_confidence(response_type: str, citation_confidence: float, unsupported_claims: list[str]) -> float:
    if response_type in {RESPONSE_ANSWER, RESPONSE_PARTIAL_ANSWER}:
        penalty = 0.15 if unsupported_claims else 0.0
        return round(max(citation_confidence - penalty, 0.0), 3)
    if response_type in {"not_found", "refuse_no_access", "clarify"}:
        return round(max(0.65, citation_confidence), 3)
    return citation_confidence


def final_confidence(
    response_type: str,
    chunks: list[RetrievedChunk],
    citation_confidence: float,
    unsupported_claims: list[str],
) -> dict:
    retrieval_score = retrieval_confidence(chunks)
    answer_score = answer_confidence(response_type, citation_confidence, unsupported_claims)
    if response_type in {RESPONSE_ANSWER, RESPONSE_PARTIAL_ANSWER}:
        final_score = (0.35 * retrieval_score) + (0.40 * citation_confidence) + (0.25 * answer_score)
    else:
        final_score = (0.55 * answer_score) + (0.45 * retrieval_score)
    return {
        "retrieval_confidence": round(retrieval_score, 3),
        "citation_confidence": round(citation_confidence, 3),
        "answer_confidence": round(answer_score, 3),
        "final_confidence": round(final_score, 3),
    }
