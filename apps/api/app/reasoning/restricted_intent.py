from __future__ import annotations

from dataclasses import dataclass


@dataclass(frozen=True)
class RestrictedIntentRule:
    topic_terms: tuple[str, ...]
    detail_terms: tuple[str, ...]
    allowed_roles: frozenset[str]


RULES = (
    RestrictedIntentRule(
        ("promotion", "performance"),
        ("calibration", "improvement process", "formal improvement", "manager guidance"),
        frozenset({"Manager"}),
    ),
    RestrictedIntentRule(
        ("manager", "team"),
        ("conflict handling", "conflict playbook", "sensitive conflict"),
        frozenset({"Manager"}),
    ),
    RestrictedIntentRule(
        ("employee relations", "hr investigation", "workplace investigation"),
        ("sensitive", "internal", "case", "outcome", "escalation"),
        frozenset({"HR Admin"}),
    ),
    RestrictedIntentRule(
        ("privileged access", "admin account", "production access", "elevated access"),
        ("contain", "containment", "review", "incident", "triage", "internal steps"),
        frozenset({"IT Admin", "IT/Admin"}),
    ),
    RestrictedIntentRule(
        ("rollback", "production deployment"),
        ("private", "checklist", "internal window", "step-by-step", "exact steps"),
        frozenset({"Manager", "IT Admin", "IT/Admin"}),
    ),
    RestrictedIntentRule(
        ("northstar", "sales", "deal", "opportunity", "customer"),
        ("positioning", "sales stage", "internal refund", "service credit", "competitive", "deployment timeline"),
        frozenset({"Sales Representative", "Manager"}),
    ),
    RestrictedIntentRule(
        ("legal", "contract"),
        ("internal risk rating", "legal risk rating", "signature authority"),
        frozenset({"Manager"}),
    ),
)


def restricted_intent_allowed_roles(question: str) -> frozenset[str] | None:
    normalized = " ".join(question.lower().replace("-", " ").split())
    for rule in RULES:
        if any(term in normalized for term in rule.topic_terms) and any(term in normalized for term in rule.detail_terms):
            return rule.allowed_roles
    return None
