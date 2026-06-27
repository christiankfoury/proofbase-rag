from __future__ import annotations

from dataclasses import dataclass


@dataclass(frozen=True)
class SourcePlanItem:
    label: str
    query: str
    target_document_ids: tuple[str, ...]


def plan_multi_document_sources(question: str) -> list[SourcePlanItem]:
    normalized = question.lower()
    plan: list[SourcePlanItem] = []

    def add(label: str, query: str, *document_ids: str) -> None:
        if any(existing.label == label for existing in plan):
            return
        plan.append(SourcePlanItem(label=label, query=query, target_document_ids=tuple(document_ids)))

    if any(term in normalized for term in ["proposal", "sales-stage", "sales stage", "deal moves"]):
        add("sales_stage", "sales stages proposal discovery notes stakeholder mapping", "SALES-001")
    if "implementation" in normalized and any(term in normalized for term in ["deal", "proposal", "customer", "timeline", "constraints"]):
        add("sales_implementation", "standard implementation timeline deployment constraints customer handoff", "SALES-002")
    if any(term in normalized for term in ["position northstar", "bi tool", "bi tools", "competitor"]):
        add("product_positioning", "Northstar product positioning against generic BI tools", "SALES-002")
    if any(term in normalized for term in ["prohibited claim", "prohibited claims", "avoid prohibited", "banned claim"]):
        add("prohibited_claims", "prohibited sales claims restricted competitive claims", "SALES-003")

    if "benefits" in normalized and any(term in normalized for term in ["help", "support", "contact"]):
        add("people_ops_support", "People Operations benefits support contact help", "HR-001")
    if any(term in normalized for term in ["learning budget", "tuition", "course", "learning and development"]):
        add("learning_budget", "learning budget tuition course reimbursement policy", "HR-004")
    if any(term in normalized for term in ["remote", "hybrid", "cross-border", "another country", "outside canada", "outside the us"]):
        add("remote_work", "remote hybrid cross-border work policy approval", "HR-003")
    if any(term in normalized for term in ["device", "byod", "personal laptop", "laptop", "mdm"]):
        add("device_security", "device BYOD security personal laptop MDM requirements", "IT-002")

    if any(term in normalized for term in ["ai tool", "ai assistant", "llm", "copilot", "ai to summarize"]):
        add("acceptable_ai_use", "acceptable use AI tools internal data customer data", "IT-001")
    if any(term in normalized for term in ["data classification", "customer data", "confidential", "restricted data", "data exposure"]):
        add("data_classification", "storage rules customer restricted data approved company systems", "IT-003")
    if any(term in normalized for term in ["privileged access", "admin account", "elevated access", "production access"]):
        add("privileged_access", "privileged access admin account production access review", "IT-ADMIN-001")
    if any(term in normalized for term in ["account sharing", "shared credentials", "password sharing", "mfa"]):
        add("credential_sharing", "account sharing shared credentials MFA password policy", "IT-001")

    if any(term in normalized for term in ["support escalation", "customer reports", "enterprise customer", "suspected data exposure"]):
        add("support_escalation", "support escalation enterprise customer suspected data exposure SLA", "SUPPORT-001")
    if any(term in normalized for term in ["engineering response", "incident response", "response target", "deploy", "deployment"]):
        add("engineering_response", "SEV-1 data exposure risk 15 minutes on-call severity levels engineering response target", "ENG-001")
    if any(term in normalized for term in ["api", "authorization", "customer data"]):
        add("api_standards", "API standards authorization customer data review principles", "ENG-001")

    if any(term in normalized for term in ["software purchase", "software or vendor", "approval path", "procurement"]):
        add("finance_procurement", "software subscription trial USD 500 annualized IT review manager approval expense categories", "FIN-001")
    if any(term in normalized for term in ["vendor", "vendor purchase", "vendor start", "onboarding"]):
        add("vendor_operations", "overlap with other policies stricter approval path vendor operations legal IT admin review", "OPS-001")

    if any(term in normalized for term in ["exception", "waiver"]) and any(term in normalized for term in ["cross-border", "remote", "international"]):
        add("hr_exception", "HR remote work exception escalation People Operations Legal", "HR-ADMIN-001")

    return plan if len(plan) >= 2 else []
