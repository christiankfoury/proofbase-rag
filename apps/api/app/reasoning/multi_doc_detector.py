from __future__ import annotations

import re


# Cross-domain keyword pairs. Each tuple is (domain_a_terms, domain_b_terms).
# A question fires if it contains at least one term from each set.
_DOMAIN_PAIRS: list[tuple[frozenset[str], frozenset[str]]] = [
    # HR-003 (remote work) + IT-002 (device security)
    (
        frozenset({"remote", "hybrid", "abroad", "cross-border", "work location", "working remotely"}),
        frozenset({"device", "byod", "security", "mdm", "personal laptop", "personal device", "laptop"}),
    ),
    # IT-001 (acceptable use / AI tools) + IT-003 (data classification)
    (
        frozenset({"ai tool", "ai assistant", "llm", "copilot", "ai to summarize", "artificial intelligence"}),
        frozenset({"data classification", "confidential", "restricted data", "internal data", "summarize internal"}),
    ),
    # HR-001 (employee support / contacts) + HR-002 (leave / vacation)
    (
        frozenset({"contact", "people operations", "hr question", "support queue"}),
        frozenset({"vacation", "pto", "paid time off", "leave", "time off", "entitlement"}),
    ),
    # HR-001 (contacts) + HR-004 (benefits / learning)
    (
        frozenset({"benefits", "benefit", "enrollment", "coverage"}),
        frozenset({"learning", "development", "tuition", "l&d", "learning budget", "course"}),
    ),
    # MGR-001/MGR-002 (manager) + HR (people ops)
    (
        frozenset({"performance", "pip", "performance improvement", "performance concern"}),
        frozenset({"hr", "people operations", "consult", "employee relations", "formal process"}),
    ),
    # SALES-001 (sales stages) + SALES-002 (implementation)
    (
        frozenset({"proposal", "deal stage", "opportunity", "pipeline", "sales stage", "move to proposal"}),
        frozenset({"implementation", "deployment", "go-live", "timeline", "weeks"}),
    ),
    # SALES-002 (northstar positioning) + SALES-003 (prohibited claims)
    (
        frozenset({"northstar", "position northstar", "positioning", "competitor", "bi tool"}),
        frozenset({"prohibited", "banned claim", "restricted claim", "avoid claiming", "not claim"}),
    ),
    # IT-ADMIN-001 (privileged access) + IT-001 (account sharing)
    (
        frozenset({"privileged access", "admin account", "elevated access", "production access"}),
        frozenset({"account sharing", "shared credentials", "mfa", "password sharing", "sharing"}),
    ),
    # HR-003 (cross-border remote) + HR-ADMIN-001 (exceptions)
    (
        frozenset({"cross-border", "international", "another country", "outside canada", "outside the us"}),
        frozenset({"exception", "waiver", "hr admin", "people operations review", "legal"}),
    ),
    # SUPPORT-001 (customer escalation) + ENG-001 (engineering incident severity)
    (
        frozenset({"enterprise customer", "customer reports", "suspected data exposure", "support escalation"}),
        frozenset({"engineering response", "response target", "sev-1", "severity", "incident"}),
    ),
    # ENG-001 (API authorization) + IT-003 (data storage/classification)
    (
        frozenset({"api", "authorization", "database fetch", "customer data", "employee data"}),
        frozenset({"storage", "approved company systems", "restricted data", "data classification", "review principles"}),
    ),
    # FIN-001 (software purchase approval) + OPS-001 (vendor/overlap policy)
    (
        frozenset({"software purchase", "software or vendor", "software subscription", "procurement"}),
        frozenset({"vendor", "approval path", "policies overlap", "overlap", "stricter approval"}),
    ),
]

_CONJUNCTION_RE = re.compile(
    r"\bboth\b.{0,80}\band\b|\bas well as\b|\bwhile also\b|\bin addition to\b|\band also\b",
    re.IGNORECASE,
)


def is_multi_document_question(question: str) -> bool:
    normalized = question.lower()
    words = normalized.split()

    for domain_a, domain_b in _DOMAIN_PAIRS:
        hit_a = any(term in normalized for term in domain_a)
        hit_b = any(term in normalized for term in domain_b)
        if hit_a and hit_b:
            return True

    if len(words) >= 8 and _CONJUNCTION_RE.search(question):
        return True

    return False
