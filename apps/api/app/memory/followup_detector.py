FOLLOWUP_MARKERS = {
    "that",
    "it",
    "this",
    "those",
    "same",
    "also",
}

FOLLOWUP_PHRASES = [
    "what about",
    "does that",
    "is that",
    "can i",
    "can you summarize",
    "who approves",
    "what section",
    "how long",
    "when does",
    "what if",
]


def is_followup_question(question: str, previous_turns: list[dict] | None = None) -> bool:
    if not previous_turns:
        return False
    normalized = question.lower().strip()
    if any(normalized.startswith(phrase) for phrase in FOLLOWUP_PHRASES):
        return True
    words = {word.strip(".,?!:;") for word in normalized.split()}
    return bool(words & FOLLOWUP_MARKERS)

