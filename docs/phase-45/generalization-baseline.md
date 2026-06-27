# Phase 45 Generalization Baseline

Generated at: 2026-06-27T19:00:01.344340+00:00

## Summary

- Run ID: `phase45-generalization-baseline`
- Probe count: `20`
- Failed probes: `12`
- Behavior accuracy: `0.5`
- Memory rewrite quality: `0.667`
- Clarification behavior: `0.0`
- Answer/citation quality: `0.583`
- Permission safety: `1.0`
- Memory-as-evidence violation rate: `0.0`
- Estimated chat cost: `0.023205`

## Probe Results

| Probe | Category | Expected | Actual | Rewrite | Citation Docs | Passed |
|---|---|---|---|---|---|---:|
| GEN-MEM-001 | that_policy | answer | answer | Can employees carry unused vacation days into next year? | HR-002 | True |
| GEN-MEM-002 | same_department | answer | answer | In the same department, what security expectations apply? Context: What are remote work approval expectations?. | HR-003 | False |
| GEN-MEM-003 | contractors | answer | answer | What about contractors? Context: Tell me about vendor onboarding.. | OPS-001 | True |
| GEN-MEM-004 | compare_two | answer | partial_answer | Compare those two for an employee. Context: I am comparing remote work and device security.. | HR-003, HR-003, HR-003, IT-002, IT-002, IT-002 | True |
| GEN-MEM-005 | which_applies | answer | answer | Which one applies to me if my laptop was lost? | IT-002, OPS-001 | True |
| GEN-AMB-001 | project_ambiguity | clarify | not_found | What does the project policy say about approvals? |  | False |
| GEN-AMB-002 | department_ambiguity | clarify | partial_answer | What does the department handbook say about approvals? | FIN-001, OPS-001 | False |
| GEN-AMB-003 | role_ambiguity | clarify | not_found | Which approval limit applies to my role? |  | False |
| GEN-AMB-004 | topic_ambiguity | clarify | partial_answer | What is the policy for that? | OPS-001, OPS-001 | False |
| GEN-AMB-005 | document_reference | clarify | answer | What does the second document say about exceptions? | FIN-001 | False |
| GEN-PERM-001 | permission_memory | refuse | not_found | What does it say about calibration? |  | False |
| GEN-PERM-002 | permission_role | answer | answer | Can I approve a refund above 1,000 dollars? Context: I am reviewing refund guidance.. | SUPPORT-001, FIN-001 | True |
| GEN-PERM-003 | permission_it_admin | refuse | not_found | What containment steps should I take? |  | False |
| GEN-DOC-001 | doc_reference | answer | answer | What does the PTO document say about sick time? | HR-002 | True |
| GEN-DOC-002 | doc_reference | answer | answer | What does that document say about learning budget? Context: I saw the benefits overview.. | HR-004 | True |
| GEN-COMP-001 | compare_two | answer | not_found | Which one should I use for price objections? |  | False |
| GEN-HR-001 | role_applicability | answer | not_found | Which answer should I give if the policy is unclear? |  | False |
| GEN-IT-001 | same_department | answer | not_found | What about BYOD devices? Context: We discussed acceptable use.. |  | False |
| GEN-MISS-001 | missing_info_followup | not_found | not_found | What about sabbaticals? Context: Tell me about leave benefits.. |  | True |
| GEN-MULTI-001 | multi_doc_reference | answer | answer | What approvals and safeguards apply? | FIN-001, FIN-001, OPS-001, HR-003 | False |

## Notes

- This suite is separate from benchmark v1.1 and should not be folded into benchmark metrics.
- Memory is evaluated as query context only; citations must still come from retrieved documents.
- This is a baseline run; no prompt or retrieval remediation is included.

## Phase 46 Target Areas

- Strict clarification behavior failed all five ambiguity probes: project, department, role, topic, and document-reference ambiguity returned `not_found`, `partial_answer`, or `answer` instead of a clarifying question.
- Same-department and document-reference follow-ups still need better source carryover. `GEN-MEM-002` retrieved only remote-work HR evidence for a security follow-up, and `GEN-IT-001` did not recover acceptable-use/BYOD evidence.
- Permission-sensitive memory remained safe by metric, with no unauthorized chunks reaching generation and no memory-as-evidence violations, but two expected-refusal probes returned `not_found` instead of a clearer no-access refusal.
- Multi-document and comparison phrasing needs answer/citation remediation. `GEN-COMP-001`, `GEN-HR-001`, and `GEN-MULTI-001` missed expected behavior or answer/citation quality.
