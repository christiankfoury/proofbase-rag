from __future__ import annotations


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


def extract_previous_topic(previous_turns: list[dict]) -> str:
    text = " ".join(str(turn.get("content") or "") for turn in previous_turns).lower()
    topic_rules = [
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
    for marker, topic in topic_rules:
        if marker in text:
            return topic
    return _last_user_turn(previous_turns)


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
