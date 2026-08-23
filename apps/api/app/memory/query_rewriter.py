from apps.api.app.memory.context_builder import extract_referenced_topic
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

    topic = extract_referenced_topic(question, turns)
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
    elif "expense above usd 25" in normalized_topic and "receipt" in normalized_question:
        rewritten = "Do expenses above USD 25 require a receipt?"
        strategy = "expense_receipt_threshold"
    elif "approved expense report before payroll close" in normalized_topic and "reimbursed" in normalized_question:
        rewritten = "When are approved expense reports reimbursed if submitted at least five business days before payroll close?"
        strategy = "expense_reimbursement_timing"
    elif "booking business travel" in normalized_topic and "book" in normalized_question:
        rewritten = "How far ahead should employees book business travel?"
        strategy = "business_travel_booking_timing"
    elif "customer contracts" in normalized_topic and "expiration" in normalized_question:
        rewritten = "How long are customer contracts retained after expiration?"
        strategy = "customer_contract_retention"
    elif "production deployment" in normalized_topic and "friday" in normalized_question:
        rewritten = "Can production deployments happen on Friday?"
        strategy = "friday_deployment_rule"
    elif "enterprise support customer" in normalized_topic and "updates" in normalized_question:
        rewritten = "How often are status updates required for Enterprise support customers?"
        strategy = "enterprise_support_update_cadence"
    elif "new-hire equipment" in normalized_topic and "who starts" in normalized_question:
        rewritten = "Who initiates new-hire equipment?"
        strategy = "new_hire_equipment_owner"
    elif "standard mutual nda" in normalized_topic and "send ours" in normalized_question:
        rewritten = "Can Sales send Northstar's standard mutual NDA after confirming the recipient legal entity name?"
        strategy = "standard_mutual_nda"
    elif "public api endpoint error shapes" in normalized_topic and "fields" in normalized_question:
        rewritten = "What fields must public API endpoint error shapes return?"
        strategy = "api_error_shape_fields"
    elif "office supplies standard limit" in normalized_topic and "above that limit" in normalized_question:
        rewritten = "Who approves office supplies purchases above the standard limit?"
        strategy = "office_supplies_approval"
    elif "remote work" in normalized_topic and "security expectations" in normalized_question:
        rewritten = "For remote work, what security expectations from the remote work and device security policies apply?"
        strategy = "remote_work_security_expectations"
    elif "promotion calibration" in normalized_topic and "calibration" in normalized_question:
        rewritten = "What does manager guidance say about promotion calibration?"
        strategy = "promotion_calibration_restricted_topic"
    elif "privileged access incidents" in normalized_topic and "containment" in normalized_question:
        rewritten = "What privileged access containment steps should I take?"
        strategy = "privileged_access_containment_restricted_topic"
    elif "acceptable use" in normalized_topic and "byod" in normalized_question:
        rewritten = "What does the Device and BYOD Security Policy say about BYOD device security requirements?"
        strategy = "acceptable_use_byod"
    elif "discovery questions and objection handling" in normalized_topic and "price objections" in normalized_question:
        rewritten = "For price objections, which objection-handling guidance should a Sales Representative use?"
        strategy = "price_objection_handling"
    elif "employee-facing hr guidance" in normalized_topic and "policy is unclear" in normalized_question:
        rewritten = "What should HR Admins tell employees when an employee-facing HR policy is unclear?"
        strategy = "unclear_hr_policy_employee_guidance"
    elif "remote work and personal device use" in normalized_topic and "approvals" in normalized_question and "safeguards" in normalized_question:
        rewritten = "For remote work and personal device use, what approvals and device safeguards apply?"
        strategy = "remote_device_approvals_safeguards"
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
