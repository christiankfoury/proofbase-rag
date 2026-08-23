from __future__ import annotations

import re


STOPWORDS = {
    "a", "an", "and", "are", "as", "at", "be", "before", "by", "for", "from", "has", "have", "if", "in",
    "is", "it", "of", "on", "or", "should", "that", "the", "their", "this", "to", "when", "with",
}

CANONICAL_TERMS = {
    "adversarial": "untrusted",
    "hostile": "untrusted",
    "instruction": "content",
    "instructions": "content",
    "passage": "content",
    "paragraph": "content",
    "sentence": "content",
    "following": "follow",
    "follows": "follow",
    "followed": "follow",
    "rules": "rule",
    "policies": "rule",
    "approved": "approval",
    "approve": "approval",
    "approvals": "approval",
    "reviewed": "review",
    "reviews": "review",
    "commitments": "commitment",
    "committed": "commitment",
    "promised": "promise",
    "promising": "promise",
    "allowed": "allow",
    "permitted": "allow",
    "employees": "employee",
    "days": "day",
    "documents": "document",
    "confirms": "confirm",
    "confirmed": "confirm",
    "confirming": "confirm",
    "ongoing": "unresolved",
    "investigation": "unresolved",
    "language": "wording",
    "respond": "say",
    "stating": "say",
}

NEGATIVE_PATTERNS = (
    r"\bno\b",
    r"\bnot\b",
    r"\bnever\b",
    r"\bcannot\b",
    r"\bcan't\b",
    r"\bmustn't\b",
    r"\bprohibit(?:ed|s)?\b",
    r"\bobsolete\b",
    r"\bsuperseded\b",
    r"\breplaced\b",
)


def _canonical_tokens(text: str) -> set[str]:
    raw = re.findall(r"[a-z0-9]+", text.lower())
    return {
        CANONICAL_TERMS.get(token, token)
        for token in raw
        if token not in STOPWORDS and len(token) > 1
    }


def _is_negative(text: str) -> bool:
    normalized = text.lower()
    return any(re.search(pattern, normalized) for pattern in NEGATIVE_PATTERNS)


def _sentences(text: str) -> list[str]:
    return [part.strip() for part in re.split(r"(?<=[.!?;])\s+|\n+", text) if part.strip()]


def _numeric_tokens(text: str) -> set[str]:
    return set(re.findall(r"(?<![a-z])\d+(?:[.,]\d+)?", text.lower()))


def fact_score(fact: str, text: str) -> float:
    normalized_fact = " ".join(fact.lower().strip().split()).strip(".?!")
    if normalized_fact in {"yes", "no"}:
        first_sentence = _sentences(text)[0] if _sentences(text) else text
        explicit = re.match(r"^\s*(yes|no)\b", first_sentence.lower())
        if explicit:
            return 1.0 if explicit.group(1) == normalized_fact else 0.0
        negative = _is_negative(first_sentence)
        return 1.0 if (normalized_fact == "no") == negative else 0.0

    expected = _canonical_tokens(fact)
    if not expected:
        return 1.0
    actual = _canonical_tokens(text)
    return round(len(expected & actual) / len(expected), 3)


def forbidden_fact_asserted(fact: str, answer: str, *, threshold: float = 0.7) -> bool:
    expected_numbers = _numeric_tokens(fact)
    if expected_numbers and not expected_numbers.issubset(_numeric_tokens(answer)):
        return False

    fact_negative = _is_negative(fact)
    for sentence in _sentences(answer):
        if fact_score(fact, sentence) < threshold:
            continue
        if any(
            marker in sentence.lower()
            for marker in ("contradicts", "is incorrect", "is false", "is obsolete", "was superseded", "former amount")
        ):
            continue
        if _is_negative(sentence) != fact_negative:
            continue
        return True
    return False


def substantive_unsupported_claims(claims: list[object] | None) -> list[str]:
    diagnostics = (
        "weak support from ",
        "model did not return structured json",
        "citation confidence",
    )
    return [
        text
        for claim in claims or []
        if (text := str(claim).strip()) and not text.lower().startswith(diagnostics)
    ]
