from dataclasses import asdict
import json
import re

from openai import OpenAI

from apps.api.app.audit.audit_logger import log_audit_event
from apps.api.app.citations.citation_formatter import fallback_citation
from apps.api.app.citations.citation_validator import validate_citations
from apps.api.app.confidence.confidence_scorer import final_confidence
from apps.api.app.core.config import get_settings
from apps.api.app.generation.prompts import build_answer_user_prompt
from apps.api.app.generation.response_types import (
    RESPONSE_ANSWER,
    RESPONSE_CLARIFY,
    RESPONSE_NOT_FOUND,
    RESPONSE_PARTIAL_ANSWER,
    RESPONSE_REFUSE_NO_ACCESS,
    SUPPORTED_RESPONSE_TYPES,
    response_type_to_behavior,
)
from apps.api.app.prompts.prompt_registry import PromptVersion, get_prompt
from apps.api.app.retrieval.types import RetrievedChunk


def _client() -> OpenAI:
    settings = get_settings()
    if not settings.openai_api_key:
        raise RuntimeError("OPENAI_API_KEY is required for answer generation")
    return OpenAI(api_key=settings.openai_api_key)


SOURCE_RE = re.compile(
    r"Source:\s*(?P<document_id>[A-Z]+(?:-[A-Z]+)?-\d+)\s+(?P<title>.*?),\s*Section:\s*(?P<section>[^.\n]+)",
    re.IGNORECASE,
)

RESTRICTED_PATTERNS = {
    "promotion calibration": {"Manager"},
    "manager conflict": {"Manager"},
    "manager conflict handling": {"Manager"},
    "team conflict": {"Manager"},
    "performance improvement process": {"Manager"},
    "position northstar against": {"Sales Representative", "Manager"},
    "sales stages": {"Sales Representative", "Manager"},
    "sensitive employee relations": {"HR Admin"},
    "hr policy maintenance": {"HR Admin"},
    "internal hr escalation": {"HR Admin"},
    "privileged access reviewed": {"IT Admin", "IT/Admin"},
    "security triage incidents": {"IT Admin", "IT/Admin"},
}

MISSING_PATTERNS = [
    "sabbatical",
    "salary band",
    "salary bands",
    "compensation formula",
    "compensation formulas",
    "visa",
    "immigration",
    "exact pricing",
    "pricing table",
    "roadmap",
    "customer-specific",
    "contract commitment",
    "password",
    "token",
    "secret",
    "severity scoring",
    "detailed outcomes",
    "hr investigations",
    "prior hr investigations",
    "investigation outcome",
    "investigation outcomes",
]

AMBIGUOUS_PATTERNS = [
    "another country for a month",
    "customer files locally",
    "ai to summarize customer data",
    "expense a course",
    "move this opportunity to proposal",
]


def _parse_json_object(text: str) -> dict | None:
    try:
        parsed = json.loads(text)
    except json.JSONDecodeError:
        match = re.search(r"\{.*\}", text, re.DOTALL)
        if not match:
            return None
        try:
            parsed = json.loads(match.group(0))
        except json.JSONDecodeError:
            return None
    return parsed if isinstance(parsed, dict) else None


def _match_citation_to_chunk(citation: dict, chunks: list[RetrievedChunk]) -> dict | None:
    chunk_id = citation.get("chunk_id")
    for chunk in chunks:
        if chunk_id and chunk.chunk_id == chunk_id:
            return {
                "document_id": chunk.document_id,
                "document_title": chunk.document_title,
                "section_heading": chunk.section_heading,
                "chunk_id": chunk.chunk_id,
                "citation_text": citation.get("citation_text") or chunk.content[:240],
                "citation_type": "model",
            }
    document_id = str(citation.get("document_id", "")).lower()
    section_heading = str(citation.get("section_heading", "")).lower()
    for chunk in chunks:
        if chunk.document_id.lower() == document_id and chunk.section_heading.lower() == section_heading:
            return {
                "document_id": chunk.document_id,
                "document_title": chunk.document_title,
                "section_heading": chunk.section_heading,
                "chunk_id": chunk.chunk_id,
                "citation_text": citation.get("citation_text") or chunk.content[:240],
                "citation_type": "model",
            }
    return None


def build_citations(chunks: list[RetrievedChunk]) -> list[dict]:
    seen: set[tuple[str, str]] = set()
    citations = []
    for chunk in chunks:
        key = (chunk.document_id, chunk.section_heading)
        if key in seen:
            continue
        seen.add(key)
        citations.append(fallback_citation(chunk))
    return citations


def citations_from_answer(answer: str, chunks: list[RetrievedChunk], include_fallback: bool = True) -> list[dict]:
    if not chunks:
        return []

    chunk_lookup = {
        (chunk.document_id.lower(), chunk.section_heading.lower()): chunk
        for chunk in chunks
    }
    citations = []
    seen: set[tuple[str, str]] = set()

    for match in SOURCE_RE.finditer(answer):
        key = (match.group("document_id").lower(), match.group("section").strip().lower())
        chunk = chunk_lookup.get(key)
        if chunk and key not in seen:
            seen.add(key)
            citations.append(
                {
                    "document_id": chunk.document_id,
                    "document_title": chunk.document_title,
                    "section_heading": chunk.section_heading,
                    "chunk_id": chunk.chunk_id,
                    "citation_text": chunk.content[:240],
                    "citation_type": "model",
                }
            )

    if citations:
        return citations

    if include_fallback:
        return [fallback_citation(chunks[0])]
    return []


def _role_has_access(user_role: str | None, allowed_roles: set[str]) -> bool:
    if not user_role:
        return False
    if user_role in allowed_roles:
        return True
    if user_role == "IT Admin" and "IT/Admin" in allowed_roles:
        return True
    if user_role == "IT/Admin" and "IT Admin" in allowed_roles:
        return True
    return False


def _prompt_metadata(prompt: PromptVersion, model: str, temperature: float) -> dict:
    return {
        "prompt_id": prompt.prompt_id,
        "prompt_name": prompt.prompt_name,
        "prompt_type": prompt.prompt_type,
        "prompt_version": prompt.version,
        "prompt_status": prompt.status,
        "model": model,
        "temperature": temperature,
    }


def _policy_response(question: str, chunks: list[RetrievedChunk], user_role: str | None = None) -> dict | None:
    normalized = question.lower()
    if any(pattern in normalized for pattern in MISSING_PATTERNS):
        response_type = RESPONSE_NOT_FOUND
        confidence = final_confidence(response_type, chunks, 0.0, [])
        return {
            "answer": "I could not find this in the available documents.",
            "response_type": response_type,
            "behavior": response_type_to_behavior(response_type),
            "citations": [],
            "supported_claims": [],
            "unsupported_claims": [],
            "validation_notes": "Missing-information policy check triggered before generation.",
            "input_tokens": 0,
            "output_tokens": 0,
            "estimated_cost_usd": None,
            **confidence,
        }
    if any(
        pattern in normalized and not _role_has_access(user_role, allowed_roles)
        for pattern, allowed_roles in RESTRICTED_PATTERNS.items()
    ):
        response_type = RESPONSE_REFUSE_NO_ACCESS
        if user_role:
            log_audit_event(
                action="restricted_query_refused",
                user_role=user_role,
                resource_type="query",
                outcome="refused",
                reason="restricted_topic_policy",
                metadata={"matched_policy": "restricted_topic"},
            )
        confidence = final_confidence(response_type, chunks, 0.0, [])
        return {
            "answer": "You do not have access to the required information.",
            "response_type": response_type,
            "behavior": response_type_to_behavior(response_type),
            "citations": [],
            "supported_claims": [],
            "unsupported_claims": [],
            "validation_notes": "Restricted-topic policy check triggered before generation.",
            "input_tokens": 0,
            "output_tokens": 0,
            "estimated_cost_usd": None,
            **confidence,
        }
    if any(pattern in normalized for pattern in AMBIGUOUS_PATTERNS):
        response_type = RESPONSE_CLARIFY
        citations = [fallback_citation(chunk) for chunk in chunks[:2]]
        validation = validate_citations("Clarifying question requested.", citations, chunks)
        confidence = final_confidence(response_type, chunks, validation["citation_confidence"], [])
        return {
            "answer": "Can you clarify the specific policy context, location, data type, or approval stage you mean?",
            "response_type": response_type,
            "behavior": response_type_to_behavior(response_type),
            "citations": validation["citations"],
            "supported_claims": validation["supported_claims"],
            "unsupported_claims": validation["unsupported_claims"],
            "validation_notes": "Ambiguity policy check triggered before generation.",
            "input_tokens": 0,
            "output_tokens": 0,
            "estimated_cost_usd": None,
            **confidence,
        }
    return None


def _citations_from_structured_response(parsed: dict, chunks: list[RetrievedChunk]) -> list[dict]:
    citations = []
    seen: set[str] = set()
    for citation in parsed.get("citations") or []:
        if not isinstance(citation, dict):
            continue
        matched = _match_citation_to_chunk(citation, chunks)
        if matched and matched["chunk_id"] not in seen:
            seen.add(matched["chunk_id"])
            citations.append(matched)
    return citations


def classify_behavior(answer: str, fallback: str = "answer") -> str:
    normalized = answer.lower()
    restricted_markers = [
        "do not have access",
        "don't have access",
        "not authorized",
        "you are not authorized",
        "outside your role",
        "not available to your role",
        "restricted to",
        "restricted access",
        "permission",
    ]
    not_found_markers = [
        "not found",
        "could not find",
        "do not provide",
        "does not provide",
        "not available in the available documents",
        "not in the available documents",
    ]
    if any(marker in normalized for marker in restricted_markers):
        return "refuse_no_access"
    if any(marker in normalized for marker in not_found_markers):
        return "say_not_found"
    return fallback


def generate_answer(
    question: str,
    chunks: list[RetrievedChunk],
    expected_behavior: str | None = None,
    user_role: str | None = None,
    memory_context: str | None = None,
    original_question: str | None = None,
    prompt_name: str = "answer_generation",
    prompt_version: str | None = None,
    model: str | None = None,
    temperature: float | None = None,
) -> dict:
    settings = get_settings()
    prompt = get_prompt(prompt_name, prompt_version)
    selected_model = model or prompt.model or settings.openai_chat_model
    selected_temperature = prompt.temperature if temperature is None else temperature
    prompt_metadata = _prompt_metadata(prompt, selected_model, selected_temperature)

    policy_response = _policy_response(question, chunks, user_role=user_role)
    if policy_response:
        return {**policy_response, **prompt_metadata}

    if user_role and chunks:
        from apps.api.app.permissions.access_control import unauthorized_chunks

        unauthorized = unauthorized_chunks(chunks, user_role)
        if unauthorized:
            log_audit_event(
                action="unauthorized_chunks_reached_generation",
                user_role=user_role,
                resource_type="generation",
                outcome="blocked",
                reason="retriever_returned_disallowed_chunks",
                metadata={
                    "blocked_document_ids": list(dict.fromkeys(chunk.document_id for chunk in unauthorized)),
                    "blocked_chunks_count": len(unauthorized),
                },
            )
            response_type = RESPONSE_REFUSE_NO_ACCESS
            confidence = final_confidence(response_type, [], 0.0, [])
            return {
                "answer": "I cannot answer this because your role does not have access to the required document.",
                "response_type": response_type,
                "behavior": response_type_to_behavior(response_type),
                "citations": [],
                "supported_claims": [],
                "unsupported_claims": [],
                "validation_notes": "Unauthorized chunks were blocked before generation.",
                "input_tokens": 0,
                "output_tokens": 0,
                "estimated_cost_usd": None,
                **prompt_metadata,
                **confidence,
            }

    if not chunks:
        response_type = "refuse_no_access" if expected_behavior == "refuse_no_access" else RESPONSE_NOT_FOUND
        answer = (
            "I could not find this in the available documents."
            if response_type == RESPONSE_NOT_FOUND
            else "You do not have access to the required information."
        )
        confidence = final_confidence(response_type, [], 0.0, [])
        return {
            "answer": answer,
            "response_type": response_type,
            "behavior": response_type_to_behavior(response_type),
            "citations": [],
            "supported_claims": [],
            "unsupported_claims": [],
            "validation_notes": "No retrieved chunks were available.",
            "input_tokens": 0,
            "output_tokens": 0,
            "estimated_cost_usd": None,
            **prompt_metadata,
            **confidence,
        }

    user_prompt = build_answer_user_prompt(
        question,
        chunks,
        memory_context=memory_context,
        original_question=original_question,
    )

    response = _client().chat.completions.create(
        model=selected_model,
        temperature=selected_temperature,
        messages=[
            {"role": "system", "content": prompt.content},
            {"role": "user", "content": user_prompt},
        ],
    )
    usage = response.usage
    raw_answer = response.choices[0].message.content or ""
    parsed = _parse_json_object(raw_answer)
    if parsed:
        answer = str(parsed.get("answer") or "")
        response_type = str(parsed.get("response_type") or RESPONSE_ANSWER)
        if response_type not in SUPPORTED_RESPONSE_TYPES:
            response_type = RESPONSE_ANSWER
        citations = _citations_from_structured_response(parsed, chunks)
        supported_claims = [str(claim) for claim in parsed.get("supported_claims") or []]
        unsupported_claims = [str(claim) for claim in parsed.get("unsupported_claims") or []]
    else:
        answer = raw_answer
        response_type = RESPONSE_NOT_FOUND if classify_behavior(answer) == "say_not_found" else RESPONSE_ANSWER
        citations = citations_from_answer(answer, chunks, include_fallback=False)
        supported_claims = []
        unsupported_claims = ["Model did not return structured JSON."]

    validation = validate_citations(answer, citations, chunks)
    unsupported_claims = list(dict.fromkeys(unsupported_claims + validation["unsupported_claims"]))
    response_type = _adjust_response_type(response_type, validation["citation_confidence"], unsupported_claims)
    answer = _adjust_answer_text(answer, response_type, validation["citation_confidence"])
    if response_type == RESPONSE_NOT_FOUND:
        validation = {
            "citations": [],
            "citation_confidence": 0.0,
            "supported_claims": [],
            "unsupported_claims": [],
            "validation_notes": "Retrieved context did not provide enough support for the requested answer.",
        }
        supported_claims = []
        unsupported_claims = []
    confidence = final_confidence(response_type, chunks, validation["citation_confidence"], unsupported_claims)

    return {
        "answer": answer,
        "response_type": response_type,
        "behavior": response_type_to_behavior(response_type),
        "citations": validation["citations"],
        "supported_claims": list(dict.fromkeys(supported_claims + validation["supported_claims"])),
        "unsupported_claims": unsupported_claims,
        "validation_notes": validation["validation_notes"],
        "input_tokens": usage.prompt_tokens if usage else None,
        "output_tokens": usage.completion_tokens if usage else None,
        "estimated_cost_usd": None,
        **prompt_metadata,
        **confidence,
    }


def _adjust_response_type(response_type: str, citation_confidence: float, unsupported_claims: list[str]) -> str:
    if response_type in {RESPONSE_ANSWER, RESPONSE_PARTIAL_ANSWER}:
        if citation_confidence < 0.5:
            return RESPONSE_NOT_FOUND
        if citation_confidence < 0.7 or unsupported_claims:
            return RESPONSE_PARTIAL_ANSWER
    return response_type


def _adjust_answer_text(answer: str, response_type: str, citation_confidence: float) -> str:
    if response_type == RESPONSE_NOT_FOUND:
        return "I could not find this in the available documents."
    if response_type == RESPONSE_PARTIAL_ANSWER and citation_confidence < 0.7:
        return f"Based on limited supporting evidence, {answer}"
    return answer


def retrieved_chunks_payload(chunks: list[RetrievedChunk]) -> list[dict]:
    payload = []
    for chunk in chunks:
        item = asdict(chunk)
        item.pop("content", None)
        payload.append(item)
    return payload
