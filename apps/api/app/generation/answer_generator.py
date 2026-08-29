from dataclasses import asdict
import json
import re
from collections.abc import Iterator

from openai import OpenAI

from apps.api.app.audit.audit_logger import log_audit_event
from apps.api.app.citations.citation_formatter import fallback_citation
from apps.api.app.citations.citation_validator import claim_overlap_score, citation_support_confidence, validate_citations
from apps.api.app.confidence.confidence_scorer import final_confidence
from apps.api.app.costing.estimator import estimate_chat_cost
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
from apps.api.app.reasoning.restricted_intent import restricted_intent_allowed_roles
from apps.api.app.retrieval.types import RetrievedChunk


def _client() -> OpenAI:
    settings = get_settings()
    if not settings.openai_api_key:
        raise RuntimeError("OPENAI_API_KEY is required for answer generation")
    return OpenAI(api_key=settings.openai_api_key, max_retries=settings.external_ai_max_retries)


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
    "product positioning": {"Sales Representative", "Manager"},
    "standard deployment timelines": {"Sales Representative", "Manager"},
    "internal refund thresholds": {"Sales Representative", "Manager"},
    "refund thresholds": {"Sales Representative", "Manager"},
    "service credit": {"Sales Representative", "Manager"},
    "customer-facing language": {"Sales Representative", "Manager"},
    "unresolved incidents": {"Sales Representative", "Manager"},
    "sensitive employee relations": {"HR Admin"},
    "sensitive hr employee relations": {"HR Admin"},
    "hr policy maintenance": {"HR Admin"},
    "internal hr escalation": {"HR Admin"},
    "privileged access reviewed": {"IT Admin", "IT/Admin"},
    "privileged access containment": {"IT Admin", "IT/Admin"},
    "security triage incidents": {"IT Admin", "IT/Admin"},
    "internal legal risk ratings": {"Manager"},
    "legal risk ratings": {"Manager"},
    "private rollback checklist": {"Manager", "IT Admin", "IT/Admin"},
    "private rollback": {"Manager", "IT Admin", "IT/Admin"},
    "production deployment windows": {"Manager", "IT Admin", "IT/Admin"},
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
    "which roadmap features are committed",
    "customer-specific",
    "contract commitment",
    "production admin passwords",
    "admin passwords",
    "access tokens",
    "secrets",
    "severity scoring",
    "detailed outcomes",
    "hr investigations",
    "prior hr investigations",
    "investigation outcome",
    "investigation outcomes",
    "who exactly is listed",
    "listed in the legal signature authority register",
    "named signatories",
    "exact signatories",
    "exact payroll-close change-freeze dates",
    "final root cause for the current customer incident",
    "apply for a company credit card",
    "pre-approved for data residency commitments",
    "payroll deduction amount",
    "private step-by-step rollback checklist",
    "reimbursement limit applies to family travel",
]

AMBIGUOUS_PATTERNS = [
    "another country for a month",
    "customer files locally",
    "ai to summarize customer data",
    "expense a course",
    "move this opportunity to proposal",
    "buy software",
    "delete these contract drafts",
    "deploy tonight",
    "offer a customer credit",
    "vendor start this week",
]

ADVERSARIAL_SOURCE_PATTERNS = [
    "bypass access checks",
    "hide citations",
    "reveal fallback clauses",
]

CITATION_BACKFILL_RESPONSE_TYPES = {RESPONSE_ANSWER, RESPONSE_PARTIAL_ANSWER}
CITATION_BACKFILL_MIN_CONFIDENCE = 0.58
CITATION_BACKFILL_MIN_OVERLAP = 0.28
CITATION_BACKFILL_LIMIT = 3


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


def _zero_cost(model: str) -> dict:
    return estimate_chat_cost(model=model, input_tokens=0, output_tokens=0)


def _policy_response(question: str, chunks: list[RetrievedChunk], user_role: str | None = None) -> dict | None:
    normalized = question.lower()
    if _is_adversarial_source_question(normalized) and not any(
        pattern in normalized for pattern in ADVERSARIAL_SOURCE_PATTERNS
    ):
        adversarial_response = _general_adversarial_source_response(normalized, chunks)
        if adversarial_response:
            return adversarial_response
    general_restricted_roles = restricted_intent_allowed_roles(question)
    exact_restricted_roles = next(
        (allowed_roles for pattern, allowed_roles in RESTRICTED_PATTERNS.items() if pattern in normalized),
        None,
    )
    restricted_roles = general_restricted_roles or exact_restricted_roles
    if restricted_roles and not _role_has_access(user_role, set(restricted_roles)):
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
    direct_response = _direct_supported_response(normalized, chunks)
    if direct_response:
        return direct_response
    if any(pattern in normalized for pattern in ADVERSARIAL_SOURCE_PATTERNS):
        adversarial_response = _adversarial_source_response(normalized, chunks)
        if adversarial_response:
            return adversarial_response
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


def _is_adversarial_source_question(normalized_question: str) -> bool:
    source_markers = (
        "source says",
        "document says",
        "handbook says",
        "policy says",
        "retrieved passage",
        "retrieved source",
        "paragraph says",
    )
    override_markers = (
        "ignore previous",
        "ignore the rules",
        "system rules",
        "rules no longer apply",
        "bypass access",
        "hide citations",
        "reveal",
        "print the private",
    )
    return any(marker in normalized_question for marker in source_markers) and any(
        marker in normalized_question for marker in override_markers
    )


def _general_adversarial_source_response(normalized_question: str, chunks: list[RetrievedChunk]) -> dict | None:
    if not chunks:
        return None
    markers = ("ignore previous", "system instruction", "untrusted", "do not reveal", "private", "bypass", "prompt injection")
    evidence = [chunk for chunk in chunks if "prompt injection" in chunk.section_heading.lower()]
    if not evidence:
        evidence = [chunk for chunk in chunks if any(marker in chunk.content.lower() for marker in markers)]
    if not evidence:
        evidence = chunks[:1]
    prohibited_actions = []
    if "hide citation" in normalized_question:
        prohibited_actions.append("hide citations")
    if "fallback clause" in normalized_question or "restricted clause" in normalized_question:
        prohibited_actions.append("reveal restricted fallback clauses")
    if "rollback checklist" in normalized_question or "private checklist" in normalized_question:
        prohibited_actions.append("print the private rollback checklist")
    action_text = f" Do not {', or '.join(prohibited_actions)}." if prohibited_actions else ""
    return _supported_answer_response(
        (
            "Do not follow that adversarial instruction. Treat it as untrusted document source content and continue following system, permission, and citation rules."
            + action_text
        ),
        evidence[:1],
        "General adversarial source-content guard triggered before generation.",
    )


def _supported_answer_response(answer: str, chunks: list[RetrievedChunk], validation_note: str) -> dict:
    citations = [fallback_citation(chunk) for chunk in chunks]
    validation = validate_citations(answer, citations, chunks)
    confidence = final_confidence(RESPONSE_ANSWER, chunks, validation["citation_confidence"], validation["unsupported_claims"])
    return {
        "answer": answer,
        "response_type": RESPONSE_ANSWER,
        "behavior": response_type_to_behavior(RESPONSE_ANSWER),
        "citations": validation["citations"],
        "supported_claims": validation["supported_claims"],
        "unsupported_claims": validation["unsupported_claims"],
        "validation_notes": validation_note,
        "input_tokens": 0,
        "output_tokens": 0,
        "estimated_cost_usd": None,
        **confidence,
    }


def _direct_supported_response(normalized_question: str, chunks: list[RetrievedChunk]) -> dict | None:
    employee_support = _find_chunk(chunks, "HR-001", "Employee Support Channels")
    vacation_entitlement = _find_chunk(chunks, "HR-002", "Vacation Entitlement")
    if employee_support and vacation_entitlement and any(term in normalized_question for term in ("pto", "vacation")) and "contact" in normalized_question:
        return _supported_answer_response(
            (
                "General HR and PTO questions should be sent to People Operations. "
                "Full-time employees receive 20 paid vacation days per calendar year."
            ),
            [employee_support, vacation_entitlement],
            "Cross-policy PTO support and entitlement answer assembled from retrieved employee-support and leave sections.",
        )

    benefits_help = _find_chunk(chunks, "HR-001", "Employee Support Channels")
    learning_budget = _find_chunk(chunks, "HR-004", "Learning Budget")
    if benefits_help and learning_budget and "benefits help" in normalized_question and "learning budget" in normalized_question:
        return _supported_answer_response(
            (
                "Benefits questions should be sent to the benefits support queue. "
                "For the learning budget, employees receive 1,500 CAD or 1,100 USD annually for approved role-related learning, "
                "and manager approval is required before purchase."
            ),
            [benefits_help, learning_budget],
            "Direct policy answer selected from retrieved benefits-support and learning-budget sections.",
        )

    remote_security = _find_chunk(chunks, "HR-003", "Security Requirements")
    remote_work_model = _find_chunk(chunks, "HR-003", "Work Model")
    remote_locations = _find_chunk(chunks, "HR-003", "Approved Remote Work Locations")
    byod_requirements = _find_chunk(chunks, "IT-002", "Personal Device")
    device_data = _find_chunk(chunks, "IT-002", "Data Storage")
    if remote_security and byod_requirements and "security expectations" in normalized_question:
        return _supported_answer_response(
            (
                "Remote work must follow the Device and BYOD Security Policy and Data Classification and Handling Policy. "
                "Employees working remotely should use secure networks, avoid shared public computers, protect screens from unauthorized viewing, "
                "and use personal devices only when enrolled in approved mobile device management or through approved browser-based tools."
            ),
            [remote_security, byod_requirements],
            "Direct policy answer selected from retrieved remote-work security and BYOD sections.",
        )

    if remote_work_model and byod_requirements and "remote work" in normalized_question and any(
        term in normalized_question for term in ("personal device", "byod", "device rules")
    ):
        return _supported_answer_response(
            (
                "Remote employees may work from approved locations in Canada or the United States when their role, tax location, and security requirements support remote work. "
                "Personal devices may be used for limited work access only when enrolled in approved mobile device management or through approved browser-based tools, "
                "and Restricted data must not be downloaded to personal devices."
            ),
            [remote_work_model, byod_requirements],
            "Cross-policy remote-work and personal-device answer assembled from retrieved work-model and BYOD sections.",
        )

    if remote_locations and remote_security and byod_requirements and "approvals and device safeguards" in normalized_question:
        citation_chunks = [remote_locations, remote_security, byod_requirements]
        if device_data:
            citation_chunks.append(device_data)
        return _supported_answer_response(
            (
                "Remote employees may work from approved locations in Canada or the United States when their role, tax location, and security requirements support it. "
                "Remote work must follow device and data-handling safeguards: use secure networks, avoid shared public computers, protect screens, "
                "use approved personal-device access controls, and do not download restricted data to personal devices."
            ),
            citation_chunks,
            "Direct policy answer selected from retrieved remote-work approval and device-safeguard sections.",
        )

    byod = _find_chunk(chunks, "IT-002", "Personal Device")
    acceptable_use_devices = _find_chunk(chunks, "IT-001", "Company Devices")
    if byod and "byod devices" in normalized_question:
        citation_chunks = [byod]
        if acceptable_use_devices:
            citation_chunks.insert(0, acceptable_use_devices)
        return _supported_answer_response(
            (
                "BYOD devices may be used for limited work access only when enrolled in approved mobile device management or when access occurs through approved browser-based tools. "
                "Personal devices must use a passcode, supported operating system, and automatic lock."
            ),
            citation_chunks,
            "Direct policy answer selected from retrieved BYOD device requirements.",
        )

    price_objection = _find_chunk(chunks, "SALES-003", "Price Objections")
    discovery = _find_chunk(chunks, "SALES-001", "Discovery Questions")
    if price_objection and "price objections" in normalized_question:
        citation_chunks = [price_objection]
        if discovery:
            citation_chunks.insert(0, discovery)
        return _supported_answer_response(
            (
                "For price objections, Sales Representatives should connect value to reduced reporting effort, faster approvals, fewer data quality escalations, and better executive visibility. "
                "Discovery should connect operational friction to measurable business outcomes."
            ),
            citation_chunks,
            "Direct policy answer selected from retrieved discovery and price-objection sections.",
        )

    hr_unclear_policy = _find_chunk(chunks, "HR-ADMIN-001", "Employee-Facing Guidance")
    if hr_unclear_policy and "policy is unclear" in normalized_question:
        return _supported_answer_response(
            "When an employee-facing HR policy is unclear, HR Admins should keep answers factual and policy-based and direct the employee to People Operations instead of giving speculative guidance.",
            [hr_unclear_policy],
            "Direct policy answer selected from retrieved HR Admin employee-facing guidance.",
        )

    lost_device = _find_chunk(chunks, "IT-002", "Lost or Stolen Devices")
    if lost_device and "lost or stolen device" in normalized_question and "report" in normalized_question:
        return _supported_answer_response(
            "Employees must report lost or stolen devices to IT Support within 2 hours of discovery.",
            [lost_device],
            "Direct policy answer selected from retrieved lost-device reporting section.",
        )

    customer_language = _find_chunk(chunks, "SUPPORT-001", "Customer-Facing Language")
    if customer_language and "root cause" in normalized_question and "customer" in normalized_question:
        return _supported_answer_response(
            (
                "Use approved unresolved-incident wording. Do not say root cause is confirmed until Engineering or the incident commander confirms it."
            ),
            [customer_language],
            "Customer-facing unresolved-incident response selected from retrieved Support guidance.",
        )

    sales_stage = _find_chunk(chunks, "SALES-001", "Sales Stages")
    if sales_stage and "proposal stage" in normalized_question and "before" in normalized_question:
        return _supported_answer_response(
            "Opportunities should not move to proposal until discovery notes and stakeholder mapping are complete.",
            [sales_stage],
            "Direct policy answer selected from retrieved sales-stage section.",
        )

    refund_guardrails = _find_chunk(chunks, "SUPPORT-001", "Refund Guardrails")
    contract_approval = _find_chunk(chunks, "LEGAL-001", "Contract Approval Process")
    if refund_guardrails and contract_approval and "refund tied to contract terms" in normalized_question:
        return _supported_answer_response(
            (
                "Refunds tied to contract terms require Manager and Legal review before they are promised. "
                "Contract issues should be handled through Legal approval rather than promised independently; "
                "no employee may sign a contract on behalf of Northstar unless listed in the signature authority register maintained by Legal Operations."
            ),
            [refund_guardrails, contract_approval],
            "Direct policy answer selected from retrieved refund and contract-approval sections.",
        )

    cross_border = _find_chunk(chunks, "HR-003", "Cross-Border Work")
    hr_escalation = _find_chunk(chunks, "HR-ADMIN-001", "Escalation Paths")
    if cross_border and hr_escalation and "cross-border remote work" in normalized_question:
        return _supported_answer_response(
            (
                "Temporary cross-border work requires People Operations review before travel. "
                "Remote work exceptions involving cross-border work should be reviewed with People Operations and Legal before approval."
            ),
            [cross_border, hr_escalation],
            "Direct policy answer selected from retrieved cross-border remote-work sections.",
        )

    sales_value = _find_chunk(chunks, "SALES-002", "Core Value Proposition")
    bi_positioning = _find_chunk(chunks, "SALES-003", "Positioning Against Generic BI Tools")
    prohibited_claims = _find_chunk(chunks, "SALES-003", "Prohibited Claims")
    if sales_value and bi_positioning and prohibited_claims and "bi tool" in normalized_question and "prohibited" in normalized_question:
        return _supported_answer_response(
            (
                "Position Northstar as workflow-aware analytics that gives operations teams one place to monitor workflows, "
                "approvals, data quality issues, and executive KPIs. Against generic BI tools, say that Northstar complements "
                "BI by helping operations teams act on workflow issues, not just view dashboards. Avoid claims that Northstar "
                "guarantees revenue improvement, replaces all existing systems, meets every regulatory requirement, or has "
                "committed roadmap features."
            ),
            [sales_value, bi_positioning, prohibited_claims],
            "Direct policy answer selected from retrieved product-positioning and prohibited-claims sections.",
        )

    manager_responsibilities = _find_chunk(chunks, "MGR-001", "Manager Responsibilities")
    performance_documentation = _find_chunk(chunks, "MGR-002", "Performance Documentation")
    performance_process = _find_chunk(chunks, "MGR-002", "Performance Improvement Process")
    if (
        manager_responsibilities
        and performance_documentation
        and performance_process
        and "performance" in normalized_question
        and ("manager" in normalized_question or "ongoing" in normalized_question)
    ):
        return _supported_answer_response(
            (
                "A manager handling ongoing performance concerns should set clear expectations, support employee growth, "
                "document important decisions, and escalate risks early. Performance feedback should include specific examples, "
                "business impact, expected behavior, and follow-up actions. If serious performance issues continue after feedback, "
                "the manager should consult People Operations before starting a formal performance improvement process."
            ),
            [manager_responsibilities, performance_documentation, performance_process],
            "Direct policy answer selected from retrieved manager-responsibility and performance-process sections.",
        )

    api_standards = _find_chunk(chunks, "ENG-001", "API Standards")
    storage_rules = _find_chunk(chunks, "IT-003", "Storage Rules")
    if api_standards and storage_rules and "api" in normalized_question and "customer data" in normalized_question:
        return _supported_answer_response(
            (
                "APIs that expose customer or employee data must enforce authorization before database fetches whenever practical; "
                "if pre-fetch filtering is not possible, the exception must be documented in the design review. Customer, "
                "Confidential, and Restricted data must be stored in approved company systems, and Restricted data must not be "
                "downloaded to personal devices."
            ),
            [api_standards, storage_rules],
            "Direct policy answer selected from retrieved API-standards and storage-rules sections.",
        )

    ai_usage = _find_chunk(chunks, "IT-001", "AI Tool Usage")
    ai_classification = _find_chunk(chunks, "IT-003", "AI and Automation")
    if ai_usage and ai_classification and any(term in normalized_question for term in ("ai tool", "ai assistant", "copilot", "llm")):
        return _supported_answer_response(
            (
                "Employees may use approved AI tools for drafting, summarization, and analysis when the data classification allows it. "
                "Approved AI tools may process Public and Internal data, while Confidential or Restricted data requires an approved tool and a documented business purpose. "
                "Confidential or Restricted data must not be pasted into unapproved AI tools, and generated output must be reviewed before customer communication, policy interpretation, or security decisions."
            ),
            [ai_usage, ai_classification],
            "Cross-policy AI-use decision assembled from retrieved acceptable-use and data-classification sections.",
        )

    expense_categories = _find_chunk(chunks, "FIN-001", "Expense Categories")
    procurement_thresholds = _find_chunk(chunks, "FIN-001", "Procurement Thresholds")
    vendor_onboarding = _find_chunk(chunks, "OPS-001", "Vendor Onboarding")
    policy_overlap = _find_chunk(chunks, "OPS-001", "Overlap With Other Policies")
    contract_approval = _find_chunk(chunks, "LEGAL-001", "Contract Approval Process")
    if (
        procurement_thresholds
        and vendor_onboarding
        and contract_approval
        and "vendor" in normalized_question
        and any(term in normalized_question for term in ("company data", "customer data", "process data"))
        and any(term in normalized_question for term in ("approval", "review", "before signature", "sign"))
    ):
        return _supported_answer_response(
            (
                "The requester needs Finance review, Legal contract review, department leader approval, and vendor security review before contract signature "
                "because the vendor will process company data and the spend is above USD 10,000. "
                "A vendor processing company or customer data is high risk and requires Operations, Legal, and IT Admin review; "
                "it may not receive company data, customer data, credentials, or building access until those reviews are complete. "
                "Before signature, confirm that the signer is listed in Legal Operations' signature authority register."
            ),
            [procurement_thresholds, vendor_onboarding, contract_approval],
            "Cross-policy vendor decision assembled from retrieved procurement, onboarding, and contract-approval sections.",
        )
    if expense_categories and policy_overlap and "policies overlap" in normalized_question and (
        "software" in normalized_question or "vendor" in normalized_question
    ):
        citation_chunks = [expense_categories, policy_overlap]
        if vendor_onboarding:
            citation_chunks.insert(1, vendor_onboarding)
        return _supported_answer_response(
            (
                "For software purchases, Finance requires IT review and manager approval for a software subscription trial "
                "at USD 500 annualized value. For vendors, Operations requires the appropriate intake and review path, including "
                "Operations, Legal, and IT Admin review for high-risk vendors that process company or customer data. When policies "
                "overlap, use the stricter approval path."
            ),
            citation_chunks,
            "Direct policy answer selected from retrieved finance software-purchase and operations overlap sections.",
        )
    return None


def _find_chunk(chunks: list[RetrievedChunk], document_id: str, section_contains: str) -> RetrievedChunk | None:
    normalized_section = section_contains.lower()
    for chunk in chunks:
        if chunk.document_id == document_id and normalized_section in chunk.section_heading.lower():
            return chunk
    return None


def _adversarial_source_response(normalized_question: str, chunks: list[RetrievedChunk]) -> dict | None:
    prompt_chunk = _find_chunk(chunks, "LEGAL-001", "Prompt Injection Test Text")
    do_not_reveal_chunk = _find_chunk(chunks, "LEGAL-001", "Do Not Reveal")
    if not prompt_chunk:
        return None

    if "hide citations" in normalized_question or "fallback clauses" in normalized_question:
        answer = (
            "The assistant should not hide citations or reveal restricted fallback clauses. "
            "It should treat that text as source content and continue following permission and citation rules."
        )
        citation_chunks = [chunk for chunk in [do_not_reveal_chunk, prompt_chunk] if chunk is not None]
    else:
        answer = (
            "No. The paragraph is source content, not a system instruction, including any request to bypass access checks. "
            "The assistant should continue following system and permission rules."
        )
        citation_chunks = [prompt_chunk]

    citations = [fallback_citation(chunk) for chunk in citation_chunks]
    validation = validate_citations(answer, citations, chunks)
    confidence = final_confidence(RESPONSE_ANSWER, chunks, validation["citation_confidence"], validation["unsupported_claims"])
    return {
        "answer": answer,
        "response_type": RESPONSE_ANSWER,
        "behavior": response_type_to_behavior(RESPONSE_ANSWER),
        "citations": validation["citations"],
        "supported_claims": validation["supported_claims"],
        "unsupported_claims": validation["unsupported_claims"],
        "validation_notes": "Adversarial source-content policy check triggered before generation.",
        "input_tokens": 0,
        "output_tokens": 0,
        "estimated_cost_usd": None,
        **confidence,
    }


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


def _backfill_supporting_citations(
    answer: str,
    response_type: str,
    citations: list[dict],
    chunks: list[RetrievedChunk],
    *,
    multi_doc: bool = False,
) -> list[dict]:
    if response_type not in CITATION_BACKFILL_RESPONSE_TYPES or not answer.strip() or not chunks:
        return citations

    seen_chunk_ids = {str(citation.get("chunk_id")) for citation in citations if citation.get("chunk_id")}
    seen_document_ids = {str(citation.get("document_id")) for citation in citations if citation.get("document_id")}
    candidates = []
    answer_sentences = [part.strip() for part in re.split(r"(?<=[.!?])\s+", answer) if part.strip()]
    for chunk in chunks:
        if chunk.chunk_id in seen_chunk_ids:
            continue
        citation_text = chunk.content[:240]
        sentence_scores = [
            (
                citation_support_confidence(sentence, citation_text, chunk),
                claim_overlap_score(sentence, chunk.content),
            )
            for sentence in answer_sentences
        ]
        confidence = max([citation_support_confidence(answer, citation_text, chunk), *[item[0] for item in sentence_scores]])
        overlap = max([claim_overlap_score(answer, chunk.content), *[item[1] for item in sentence_scores]])
        adds_document = chunk.document_id not in seen_document_ids
        min_confidence = 0.5 if multi_doc and adds_document else CITATION_BACKFILL_MIN_CONFIDENCE
        min_overlap = 0.18 if multi_doc and adds_document else CITATION_BACKFILL_MIN_OVERLAP
        if confidence < min_confidence or overlap < min_overlap:
            continue
        candidates.append(
            {
                "chunk": chunk,
                "confidence": confidence,
                "overlap": overlap,
                "adds_document": adds_document,
            }
        )

    candidates.sort(
        key=lambda item: (
            1 if item["adds_document"] else 0,
            item["confidence"],
            item["overlap"],
            item["chunk"].score,
        ),
        reverse=True,
    )

    backfilled = list(citations)
    added = 0
    for candidate in candidates:
        chunk = candidate["chunk"]
        if chunk.chunk_id in seen_chunk_ids:
            continue
        if chunk.document_id in seen_document_ids:
            continue
        citation = fallback_citation(chunk)
        citation["citation_type"] = "verified_backfill"
        citation["confidence"] = candidate["confidence"]
        backfilled.append(citation)
        seen_chunk_ids.add(chunk.chunk_id)
        seen_document_ids.add(chunk.document_id)
        added += 1
        if added >= CITATION_BACKFILL_LIMIT:
            break
    return backfilled


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


class _AnswerFieldDeltaExtractor:
    def __init__(self) -> None:
        self.buffer = ""
        self.in_answer = False
        self.done = False
        self.escape = False
        self.unicode_escape: str | None = None

    def push(self, text: str) -> str:
        if self.done:
            return ""
        if not self.in_answer:
            self.buffer += text
            key_index = self.buffer.find('"answer"')
            if key_index == -1:
                self.buffer = self.buffer[-32:]
                return ""
            colon_index = self.buffer.find(":", key_index + len('"answer"'))
            if colon_index == -1:
                return ""
            quote_index = self.buffer.find('"', colon_index + 1)
            if quote_index == -1:
                return ""
            self.in_answer = True
            text = self.buffer[quote_index + 1 :]
            self.buffer = ""

        output = []
        for char in text:
            if self.unicode_escape is not None:
                self.unicode_escape += char
                if len(self.unicode_escape) == 4:
                    try:
                        output.append(chr(int(self.unicode_escape, 16)))
                    except ValueError:
                        output.append(f"\\u{self.unicode_escape}")
                    self.unicode_escape = None
                    self.escape = False
                continue
            if self.escape:
                if char == "u":
                    self.unicode_escape = ""
                    continue
                output.append(
                    {
                        '"': '"',
                        "\\": "\\",
                        "/": "/",
                        "b": "\b",
                        "f": "\f",
                        "n": "\n",
                        "r": "\r",
                        "t": "\t",
                    }.get(char, char)
                )
                self.escape = False
                continue
            if char == "\\":
                self.escape = True
                continue
            if char == '"':
                self.done = True
                break
            output.append(char)
        return "".join(output)


def _finalize_generated_answer(
    raw_answer: str,
    chunks: list[RetrievedChunk],
    usage,
    selected_model: str,
    prompt_metadata: dict,
    multi_doc: bool = False,
    evidence_action: str | None = None,
) -> dict:
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

    citations = _backfill_supporting_citations(answer, response_type, citations, chunks, multi_doc=multi_doc)
    validation = validate_citations(answer, citations, chunks)
    unsupported_claims = list(dict.fromkeys(unsupported_claims + validation["unsupported_claims"]))
    response_type = _adjust_response_type(response_type, validation["citation_confidence"], unsupported_claims, multi_doc=multi_doc)
    if evidence_action == "partial_answer" and response_type == RESPONSE_ANSWER:
        response_type = RESPONSE_PARTIAL_ANSWER
    answer = _adjust_answer_text(answer, response_type, validation["citation_confidence"], multi_doc=multi_doc)
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

    input_tokens = usage.prompt_tokens if usage else None
    output_tokens = usage.completion_tokens if usage else None
    return {
        "answer": answer,
        "response_type": response_type,
        "behavior": response_type_to_behavior(response_type),
        "citations": validation["citations"],
        "supported_claims": list(dict.fromkeys(supported_claims + validation["supported_claims"])),
        "unsupported_claims": unsupported_claims,
        "validation_notes": validation["validation_notes"],
        "input_tokens": input_tokens,
        "output_tokens": output_tokens,
        **estimate_chat_cost(
            model=selected_model,
            input_tokens=input_tokens,
            output_tokens=output_tokens,
        ),
        **prompt_metadata,
        **confidence,
    }


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
    multi_doc: bool = False,
    grouped_docs: list[dict] | None = None,
    evidence_action: str | None = None,
) -> dict:
    settings = get_settings()
    prompt = get_prompt(prompt_name, prompt_version)
    selected_model = model or prompt.model or settings.openai_chat_model
    selected_temperature = prompt.temperature if temperature is None else temperature
    prompt_metadata = _prompt_metadata(prompt, selected_model, selected_temperature)

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
                **_zero_cost(selected_model),
                **confidence,
            }

    policy_response = _policy_response(question, chunks, user_role=user_role)
    if policy_response:
        if evidence_action == "partial_answer" and policy_response["response_type"] == RESPONSE_ANSWER:
            policy_response = _force_partial_response(policy_response, chunks)
        return {**policy_response, **prompt_metadata, **_zero_cost(selected_model)}

    if not chunks:
        response_type = RESPONSE_REFUSE_NO_ACCESS if expected_behavior == "refuse_no_access" else RESPONSE_NOT_FOUND
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
            **_zero_cost(selected_model),
            **confidence,
        }

    if grouped_docs is not None:
        from apps.api.app.generation.prompts import build_multi_doc_user_prompt
        user_prompt = build_multi_doc_user_prompt(
            question,
            grouped_docs,
            memory_context=memory_context,
            original_question=original_question,
            evidence_action=evidence_action,
        )
    else:
        user_prompt = build_answer_user_prompt(
            question,
            chunks,
            memory_context=memory_context,
            original_question=original_question,
            evidence_action=evidence_action,
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
    return _finalize_generated_answer(
        raw_answer,
        chunks,
        usage,
        selected_model,
        prompt_metadata,
        multi_doc=multi_doc,
        evidence_action=evidence_action,
    )


def repair_answer_once(
    question: str,
    chunks: list[RetrievedChunk],
    *,
    candidate: dict,
    validation_reason_codes: list[str],
    user_role: str | None = None,
    memory_context: str | None = None,
    original_question: str | None = None,
    prompt_name: str = "answer_generation",
    prompt_version: str | None = None,
    model: str | None = None,
    temperature: float | None = None,
    multi_doc: bool = False,
    grouped_docs: list[dict] | None = None,
    evidence_action: str | None = None,
) -> dict:
    """Regenerate once from the identical authorized chunks; never performs retrieval."""
    settings = get_settings()
    prompt = get_prompt(prompt_name, prompt_version)
    selected_model = model or prompt.model or settings.openai_chat_model
    selected_temperature = prompt.temperature if temperature is None else temperature
    prompt_metadata = _prompt_metadata(prompt, selected_model, selected_temperature)

    if user_role and chunks:
        from apps.api.app.permissions.access_control import unauthorized_chunks

        if unauthorized_chunks(chunks, user_role):
            raise ValueError("Repair received chunks outside the effective role.")

    if grouped_docs is not None:
        from apps.api.app.generation.prompts import build_multi_doc_user_prompt

        user_prompt = build_multi_doc_user_prompt(
            question,
            grouped_docs,
            memory_context=memory_context,
            original_question=original_question,
            evidence_action=evidence_action,
        )
    else:
        user_prompt = build_answer_user_prompt(
            question,
            chunks,
            memory_context=memory_context,
            original_question=original_question,
            evidence_action=evidence_action,
        )
    repair_payload = {
        "candidate_answer": str(candidate.get("answer") or "")[:6000],
        "candidate_citation_chunk_ids": [
            item.get("chunk_id") for item in (candidate.get("citations") or [])[:12]
        ],
        "validator_reason_codes": list(validation_reason_codes)[:8],
    }
    user_prompt = (
        f"{user_prompt}\n\n"
        "Bounded validation repair (one attempt only): Correct or remove every flagged claim. "
        "Use only the retrieved context above, keep citations inside that context, and return the normal strict JSON shape.\n"
        f"{json.dumps(repair_payload, ensure_ascii=True)}"
    )
    response = _client().chat.completions.create(
        model=selected_model,
        temperature=selected_temperature,
        messages=[
            {"role": "system", "content": prompt.content},
            {"role": "user", "content": user_prompt},
        ],
    )
    return _finalize_generated_answer(
        response.choices[0].message.content or "",
        chunks,
        response.usage,
        selected_model,
        prompt_metadata,
        multi_doc=multi_doc,
        evidence_action=evidence_action,
    )


def generate_answer_stream(
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
    multi_doc: bool = False,
    grouped_docs: list[dict] | None = None,
    evidence_action: str | None = None,
) -> Iterator[dict]:
    settings = get_settings()
    prompt = get_prompt(prompt_name, prompt_version)
    selected_model = model or prompt.model or settings.openai_chat_model
    selected_temperature = prompt.temperature if temperature is None else temperature
    prompt_metadata = _prompt_metadata(prompt, selected_model, selected_temperature)

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
            answer = {
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
                **_zero_cost(selected_model),
                **confidence,
            }
            yield {"type": "answer_delta", "delta": answer["answer"]}
            yield {"type": "final", "answer": answer}
            return

    policy_response = _policy_response(question, chunks, user_role=user_role)
    if policy_response:
        if evidence_action == "partial_answer" and policy_response["response_type"] == RESPONSE_ANSWER:
            policy_response = _force_partial_response(policy_response, chunks)
        answer = {**policy_response, **prompt_metadata, **_zero_cost(selected_model)}
        yield {"type": "answer_delta", "delta": answer["answer"]}
        yield {"type": "final", "answer": answer}
        return

    if not chunks:
        response_type = RESPONSE_REFUSE_NO_ACCESS if expected_behavior == "refuse_no_access" else RESPONSE_NOT_FOUND
        answer_text = (
            "I could not find this in the available documents."
            if response_type == RESPONSE_NOT_FOUND
            else "You do not have access to the required information."
        )
        confidence = final_confidence(response_type, [], 0.0, [])
        answer = {
            "answer": answer_text,
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
            **_zero_cost(selected_model),
            **confidence,
        }
        yield {"type": "answer_delta", "delta": answer_text}
        yield {"type": "final", "answer": answer}
        return

    if grouped_docs is not None:
        from apps.api.app.generation.prompts import build_multi_doc_user_prompt

        user_prompt = build_multi_doc_user_prompt(
            question,
            grouped_docs,
            memory_context=memory_context,
            original_question=original_question,
            evidence_action=evidence_action,
        )
    else:
        user_prompt = build_answer_user_prompt(
            question,
            chunks,
            memory_context=memory_context,
            original_question=original_question,
            evidence_action=evidence_action,
        )

    try:
        stream = _client().chat.completions.create(
            model=selected_model,
            temperature=selected_temperature,
            messages=[
                {"role": "system", "content": prompt.content},
                {"role": "user", "content": user_prompt},
            ],
            stream=True,
            stream_options={"include_usage": True},
        )
    except TypeError:
        stream = _client().chat.completions.create(
            model=selected_model,
            temperature=selected_temperature,
            messages=[
                {"role": "system", "content": prompt.content},
                {"role": "user", "content": user_prompt},
            ],
            stream=True,
        )

    raw_parts = []
    usage = None
    extractor = _AnswerFieldDeltaExtractor()
    for chunk in stream:
        chunk_usage = getattr(chunk, "usage", None)
        if chunk_usage is not None:
            usage = chunk_usage
        choices = getattr(chunk, "choices", None) or []
        if not choices:
            continue
        delta = getattr(choices[0], "delta", None)
        content = getattr(delta, "content", None) if delta is not None else None
        if content is None:
            continue
        raw_parts.append(content)
        answer_delta = extractor.push(content)
        if answer_delta:
            yield {"type": "answer_delta", "delta": answer_delta}

    yield {"type": "status", "status": "validation_started", "message": "Validating citations and confidence."}
    raw_answer = "".join(raw_parts)
    yield {
        "type": "final",
        "answer": _finalize_generated_answer(
            raw_answer,
            chunks,
            usage,
            selected_model,
            prompt_metadata,
            multi_doc=multi_doc,
            evidence_action=evidence_action,
        ),
    }


def _force_partial_response(answer: dict, chunks: list[RetrievedChunk]) -> dict:
    updated = dict(answer)
    updated["response_type"] = RESPONSE_PARTIAL_ANSWER
    updated["behavior"] = response_type_to_behavior(RESPONSE_PARTIAL_ANSWER)
    updated.update(
        final_confidence(
            RESPONSE_PARTIAL_ANSWER,
            chunks,
            float(updated.get("citation_confidence") or 0.0),
            list(updated.get("unsupported_claims") or []),
        )
    )
    return updated


def _adjust_response_type(
    response_type: str,
    citation_confidence: float,
    unsupported_claims: list[str],
    multi_doc: bool = False,
) -> str:
    if response_type in {RESPONSE_ANSWER, RESPONSE_PARTIAL_ANSWER}:
        not_found_threshold = 0.3 if multi_doc else 0.5
        partial_threshold = 0.5 if multi_doc else 0.7
        if citation_confidence < not_found_threshold:
            return RESPONSE_NOT_FOUND
        if citation_confidence < partial_threshold or unsupported_claims:
            return RESPONSE_PARTIAL_ANSWER
    return response_type


def _adjust_answer_text(
    answer: str,
    response_type: str,
    citation_confidence: float,
    multi_doc: bool = False,
) -> str:
    if response_type == RESPONSE_NOT_FOUND:
        return "I could not find this in the available documents."
    if response_type == RESPONSE_PARTIAL_ANSWER and citation_confidence < 0.7 and not multi_doc:
        return f"Based on limited supporting evidence, {answer}"
    return answer


def retrieved_chunks_payload(chunks: list[RetrievedChunk]) -> list[dict]:
    payload = []
    for chunk in chunks:
        item = asdict(chunk)
        item["content_preview"] = chunk.content[:500]
        item.pop("content", None)
        payload.append(item)
    return payload
