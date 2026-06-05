import re

from apps.api.app.evaluation.metrics import behavior_match


STOP_WORDS = {
    "about",
    "also",
    "and",
    "are",
    "available",
    "because",
    "but",
    "can",
    "could",
    "does",
    "for",
    "from",
    "has",
    "have",
    "into",
    "may",
    "must",
    "not",
    "per",
    "should",
    "that",
    "the",
    "their",
    "this",
    "with",
    "within",
    "would",
}


def _terms(text: str) -> set[str]:
    return {
        token
        for token in re.findall(r"[a-zA-Z0-9]+", text.lower())
        if len(token) >= 3 and token not in STOP_WORDS
    }


def expected_answer_overlap(expected_answer: str, actual_answer: str) -> float | None:
    expected_terms = _terms(expected_answer)
    if not expected_terms:
        return None
    actual_terms = _terms(actual_answer)
    return len(expected_terms & actual_terms) / len(expected_terms)


def answer_accuracy(question: dict, result: dict) -> float | None:
    expected_behavior = question["expected_behavior"]
    if expected_behavior not in {"answer", "answer_with_memory"}:
        return None
    if result["response_type"] not in {"answer", "partial_answer"}:
        return 0.0
    overlap = expected_answer_overlap(question.get("expected_answer", ""), result["answer"])
    if overlap is None:
        return None
    if overlap >= 0.65:
        return 1.0
    if overlap >= 0.4:
        return 0.5
    return 0.0


def citation_accuracy(question: dict, result: dict) -> float | None:
    if question["expected_behavior"] not in {"answer", "answer_with_memory"}:
        return None
    expected_sources = question.get("expected_source_document") or []
    if not expected_sources:
        return None
    if result["response_type"] not in {"answer", "partial_answer"}:
        return 0.0
    cited_sources = {citation["document_id"] for citation in result["citations"]}
    if all(source in cited_sources for source in expected_sources):
        return 1.0
    if any(source in cited_sources for source in expected_sources):
        return 0.5
    return 0.0


def faithfulness_score(result: dict) -> float | None:
    if result["response_type"] not in {"answer", "partial_answer"}:
        return None
    return float(result.get("citation_confidence") or 0.0)


def hallucination_flag(result: dict) -> float | None:
    if result["response_type"] not in {"answer", "partial_answer"}:
        return None
    if result.get("unsupported_claims"):
        return 1.0
    if result["response_type"] in {"answer", "partial_answer"} and result.get("citation_confidence", 0.0) < 0.5:
        return 1.0
    return 0.0


def response_type_accuracy(question: dict, result: dict) -> float:
    return behavior_match(question["expected_behavior"], result["behavior"])


def refusal_accuracy(question: dict, result: dict) -> float | None:
    if question["expected_behavior"] != "refuse_no_access":
        return None
    return 1.0 if result["response_type"] == "refuse_no_access" else 0.0


def not_found_accuracy(question: dict, result: dict) -> float | None:
    if question["expected_behavior"] != "say_not_found":
        return None
    return 1.0 if result["response_type"] == "not_found" else 0.0


def clarification_accuracy(question: dict, result: dict) -> float | None:
    if question["expected_behavior"] != "ask_clarifying_question":
        return None
    return 1.0 if result["response_type"] == "clarify" else 0.0


def score_answer(question: dict, result: dict) -> dict:
    return {
        "answer_accuracy": answer_accuracy(question, result),
        "citation_accuracy": citation_accuracy(question, result),
        "faithfulness": faithfulness_score(result),
        "hallucination_rate": hallucination_flag(result),
        "response_type_accuracy": response_type_accuracy(question, result),
        "refusal_accuracy": refusal_accuracy(question, result),
        "not_found_accuracy": not_found_accuracy(question, result),
        "clarification_accuracy": clarification_accuracy(question, result),
    }
