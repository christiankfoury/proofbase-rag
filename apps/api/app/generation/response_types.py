RESPONSE_ANSWER = "answer"
RESPONSE_NOT_FOUND = "not_found"
RESPONSE_REFUSE_NO_ACCESS = "refuse_no_access"
RESPONSE_CLARIFY = "clarify"
RESPONSE_PARTIAL_ANSWER = "partial_answer"

SUPPORTED_RESPONSE_TYPES = {
    RESPONSE_ANSWER,
    RESPONSE_NOT_FOUND,
    RESPONSE_REFUSE_NO_ACCESS,
    RESPONSE_CLARIFY,
    RESPONSE_PARTIAL_ANSWER,
}


def response_type_to_behavior(response_type: str) -> str:
    if response_type == RESPONSE_NOT_FOUND:
        return "say_not_found"
    if response_type == RESPONSE_CLARIFY:
        return "ask_clarifying_question"
    if response_type == RESPONSE_REFUSE_NO_ACCESS:
        return "refuse_no_access"
    if response_type == RESPONSE_PARTIAL_ANSWER:
        return "answer"
    return "answer"
