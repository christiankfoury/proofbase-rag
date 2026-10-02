"""Provider output contract and local fail-closed shape validation."""
from apps.api.app.generation.response_types import SUPPORTED_RESPONSE_TYPES


def response_format() -> dict:
    citation_fields = {name: {"type": "string"} for name in
                       ("document_id", "document_title", "section_heading", "chunk_id", "citation_text")}
    properties = {
        "answer": {"type": "string"},
        "response_type": {"type": "string", "enum": sorted(SUPPORTED_RESPONSE_TYPES)},
        "citations": {"type": "array", "items": {
            "type": "object", "properties": citation_fields,
            "required": list(citation_fields), "additionalProperties": False}},
        "supported_claims": {"type": "array", "items": {"type": "string"}},
        "unsupported_claims": {"type": "array", "items": {"type": "string"}},
        "validation_notes": {"type": "string"},
    }
    return {"type": "json_schema", "json_schema": {
        "name": "generated_answer_v1", "strict": True,
        "schema": {"type": "object", "properties": properties,
                   "required": list(properties), "additionalProperties": False}}}


def valid_answer_shape(value) -> bool:
    # Legacy minimal structured answers remain readable. No raw-text fallback,
    # coerced object/list answers, invalid enums, or malformed citation objects.
    if not isinstance(value, dict) or not isinstance(value.get("answer"), str) or not value["answer"].strip():
        return False
    if not isinstance(value.get("response_type"), str) or value["response_type"] not in SUPPORTED_RESPONSE_TYPES:
        return False
    if not isinstance(value.get("citations"), list):
        return False
    if any(not isinstance(c, dict) or any(not isinstance(v, str) for v in c.values()) for c in value["citations"]):
        return False
    return all(isinstance(value.get(k, []), list) and all(isinstance(v, str) for v in value.get(k, []))
               for k in ("supported_claims", "unsupported_claims")) and isinstance(value.get("validation_notes", ""), str)
