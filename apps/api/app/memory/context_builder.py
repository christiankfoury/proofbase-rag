from __future__ import annotations

import re

from apps.api.app.memory.followup_detector import is_followup_question


def _last_user_turn(previous_turns: list[dict]) -> str:
    for turn in reversed(previous_turns):
        if turn.get("role") == "user":
            return str(turn.get("content") or "")
    return ""


def _last_assistant_turn(previous_turns: list[dict]) -> dict:
    for turn in reversed(previous_turns):
        if turn.get("role") == "assistant":
            return turn
    return {}


TOPIC_RULES = [
        ("vacation days", "vacation days"),
        ("pto and leave policy", "PTO and Leave Policy"),
        ("remote work location", "remote work location change"),
        ("remote and hybrid work policy", "Remote and Hybrid Work Policy"),
        ("personal device", "personal device use"),
        ("device and byod security policy", "Device and BYOD Security Policy"),
        ("standard northstar implementation", "standard Northstar implementation"),
        ("product positioning and faq", "Product Positioning and FAQ"),
        ("formal performance review cycle", "formal performance review cycle"),
        ("performance review and promotion guide", "Performance Review and Promotion Guide"),
        ("promotion calibration", "promotion calibration"),
        ("privileged access incidents", "privileged access incidents"),
        ("acceptable use", "acceptable use"),
        ("discovery questions and objection handling", "discovery questions and objection handling"),
        ("employee-facing hr guidance", "employee-facing HR guidance"),
        ("work remotely and use a personal device", "remote work and personal device use"),
        ("parental leave", "parental leave policy"),
        ("expense above usd 25", "expense above USD 25"),
        ("approved expense report before payroll close", "approved expense report before payroll close"),
        ("booking business travel", "booking business travel"),
        ("customer contracts", "customer contracts"),
        ("production deployment", "production deployment"),
        ("enterprise support customer", "Enterprise support customer"),
        ("new-hire equipment", "new-hire equipment"),
        ("northstar standard mutual nda", "Northstar standard mutual NDA"),
        ("public api endpoint error shapes", "public API endpoint error shapes"),
        ("office supplies standard limit", "office supplies standard limit"),
]


def requires_full_context(text: str) -> bool:
    """Do not discard exclusions, corrections, or multiple named topics."""
    markers = {topic for marker, topic in TOPIC_RULES if marker in text.lower()}
    return bool(
        "\n" in text
        or len(markers) > 1
        or re.search(r"\b(?:not|no|never|rather|instead|actually|correction|ignore|except|but)\b|\bi (?:mean|meant)\b|n['’]t\b", text, re.I)
    )


def _known_topic(text: str) -> str | None:
    if requires_full_context(text):
        return None
    normalized = text.lower()
    for marker, topic in TOPIC_RULES:
        if marker in normalized:
            return topic
    return None


def extract_previous_topic(previous_turns: list[dict]) -> str:
    user_turns = [turn for turn in previous_turns if turn.get("role") == "user"]
    if user_turns:
        latest = str(user_turns[-1].get("content") or "")
        if topic := _known_topic(latest):
            return topic
        if not requires_full_context(latest) and is_followup_question(latest, user_turns[:-1]):
            # Retain a bounded chronological anchor for anaphoric follow-ups.
            # Assistant assertions are never copied into this user context.
            return "\n".join(str(turn.get("content") or "") for turn in user_turns[-4:])
        return latest
    assistant_content = str(_last_assistant_turn(previous_turns).get("content") or "")
    return _known_topic(assistant_content) or ""


def extract_referenced_topic(question: str, previous_turns: list[dict]) -> str:
    normalized = question.lower()
    user_turns = [str(turn.get("content") or "") for turn in previous_turns if turn.get("role") == "user"]

    if any(marker in normalized for marker in ("first topic", "original topic", "back to the original", "return to the first")):
        return (_known_topic(user_turns[0]) or user_turns[0]) if user_turns else ""

    return extract_previous_topic(previous_turns)


def build_memory_context(previous_turns: list[dict], limit: int = 4) -> dict:
    recent_turns = previous_turns[-limit:]
    assistant = _last_assistant_turn(previous_turns)
    citations = assistant.get("citations_json") or assistant.get("citations") or []
    cited_sources = [
        {
            "document_id": citation.get("document_id"),
            "section_heading": citation.get("section_heading"),
        }
        for citation in citations
        if isinstance(citation, dict)
    ]
    return {
        "previous_topic": extract_previous_topic(previous_turns),
        "recent_turns": [
            {
                "role": turn.get("role"),
                "content": turn.get("content"),
                "response_type": turn.get("response_type"),
            }
            for turn in recent_turns
        ],
        "previous_cited_sources": cited_sources,
    }


def memory_context_text(memory_context: dict) -> str:
    if not memory_context:
        return ""
    lines = [f"Previous topic: {memory_context.get('previous_topic') or 'unknown'}"]
    cited_sources = memory_context.get("previous_cited_sources") or []
    if cited_sources:
        lines.append("Previous cited sources:")
        for source in cited_sources:
            lines.append(f"- {source.get('document_id')} / {source.get('section_heading')}")
    return "\n".join(lines)
