from apps.api.app.evaluation.citation_failures import citation_failure_summary
from apps.api.app.evaluation.metrics import all_sources_hit


def failure_type(question: dict, result: dict, scores: dict) -> str | None:
    expected_sources = question.get("expected_source_document") or []
    retrieval_success = all_sources_hit(expected_sources, result["retrieved_chunks_raw"])
    expects_answer = question["expected_behavior"] in {"answer", "answer_with_memory"}

    if question["expected_behavior"] == "refuse_no_access":
        return None if result["response_type"] == "refuse_no_access" else "missed_refusal"
    if question["expected_behavior"] == "say_not_found":
        return None if result["response_type"] == "not_found" else "not_found_failure"
    if question["expected_behavior"] == "ask_clarifying_question":
        return None if result["response_type"] == "clarify" else "ambiguity_failure"
    if expected_sources and retrieval_success != 1.0:
        return "multi_document_failure" if len(expected_sources) > 1 else "retrieval_miss"
    if expects_answer and result["response_type"] not in {"answer", "partial_answer"}:
        return "answer_not_generated"
    if scores["citation_accuracy"] is not None and scores["citation_accuracy"] < 1.0:
        return "wrong_citation"
    if scores["hallucination_rate"] == 1.0:
        return "unsupported_answer"
    if scores["answer_accuracy"] == 0.5:
        return "incomplete_answer"
    if scores["answer_accuracy"] == 0.0:
        return "unsupported_answer"
    return None


def recommended_fix(failure: str | None) -> str:
    recommendations = {
        "retrieval_miss": "Improve retrieval query handling, chunking, or metadata filters for the expected source.",
        "wrong_citation": "Improve citation formatting and require the model to cite the exact supporting chunk.",
        "unsupported_answer": "Tighten answer prompt and lower confidence when citation validation is weak.",
        "hallucination": "Add stricter not-found behavior and claim validation.",
        "incorrect_refusal": "Tune refusal policy to avoid refusing answerable questions.",
        "missed_refusal": "Add restricted-topic detection or access-aware no-access classification.",
        "not_found_failure": "Improve not-found thresholding for missing-information questions.",
        "ambiguity_failure": "Add ambiguity detection before generation or clearer prompt examples.",
        "multi_document_failure": "Add query decomposition or multi-document retrieval logic.",
        "answer_not_generated": "Adjust confidence thresholds or prompting so answerable questions do not downgrade to not-found when supporting sources were retrieved.",
        "incomplete_answer": "Improve answer completeness scoring or prompt the model to include all required expected-answer facts.",
    }
    return recommendations.get(failure or "", "No fix required.")


def failed_question_item(question: dict, result: dict, scores: dict) -> dict | None:
    failure = failure_type(question, result, scores)
    if not failure:
        return None
    citation_summary = citation_failure_summary(question, result)
    return {
        "question_id": question["question_id"],
        "question": question["question"],
        "expected_behavior": question["expected_behavior"],
        "actual_response_type": result["response_type"],
        "expected_source_document": question.get("expected_source_document") or [],
        "actual_citations": [
            {
                "document_id": citation["document_id"],
                "section_heading": citation["section_heading"],
                "confidence": citation.get("confidence"),
            }
            for citation in result["citations"]
        ],
        "retrieval_success": all_sources_hit(question.get("expected_source_document") or [], result["retrieved_chunks_raw"]),
        "citation_confidence": result["citation_confidence"],
        "answer_confidence": result["answer_confidence"],
        "failure_type": failure,
        **citation_summary,
        "recommended_fix": recommended_fix(failure),
    }
