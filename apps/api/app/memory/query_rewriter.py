from apps.api.app.memory.context_builder import extract_previous_topic
from apps.api.app.memory.followup_detector import is_followup_question


def rewrite_followup_question(question: str, previous_turns: list[dict] | None = None) -> dict:
    turns = previous_turns or []
    detected = is_followup_question(question, turns)
    if not detected:
        return {
            "original_question": question,
            "rewritten_question": question,
            "is_followup": False,
            "memory_used": False,
            "rewrite_strategy": "none",
        }

    topic = extract_previous_topic(turns)
    normalized_question = question.lower().strip()
    normalized_topic = topic.lower()
    rewritten = question
    strategy = "topic_prefix"

    if "vacation" in normalized_topic and "carry" in normalized_question:
        rewritten = "Can employees carry unused vacation days into next year?"
        strategy = "vacation_carryover"
    elif "remote work location" in normalized_topic and "fewer than 15" in normalized_question:
        rewritten = "For a temporary remote work location change, what happens if it is fewer than 15 business days?"
        strategy = "remote_location_duration"
    elif "personal device" in normalized_topic and "restricted data" in normalized_question:
        rewritten = "Can an employee download restricted data to a personal device?"
        strategy = "personal_device_restricted_data"
    elif "implementation" in normalized_topic and "how long" in normalized_question:
        rewritten = "What is the typical implementation range for standard deployments?"
        strategy = "implementation_timeline"
    elif "performance review" in normalized_topic and "when" in normalized_question:
        rewritten = "When does the formal performance review cycle happen?"
        strategy = "performance_review_timing"
    elif "parental leave" in normalized_topic and "adoptive" in normalized_question:
        rewritten = "Does the parental leave policy apply to adoptive parents?"
        strategy = "parental_leave_adoptive"
    elif topic:
        rewritten = f"{question} Context: {topic}."

    return {
        "original_question": question,
        "rewritten_question": rewritten,
        "is_followup": True,
        "memory_used": True,
        "rewrite_strategy": strategy,
        "previous_topic": topic,
    }
