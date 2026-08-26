# Phase 50 Generalization Regression

Generated at: 2026-08-26T01:23:37.322730+00:00

## Summary

- Run ID: `phase50-generalization-regression`
- Probe count: `20`
- Failed probes: `0`
- Behavior accuracy: `1.0`
- Memory rewrite quality: `0.8`
- Clarification behavior: `1.0`
- Answer/citation quality: `1.0`
- Permission safety: `1.0`
- Memory-as-evidence violation rate: `0.0`
- Estimated chat cost: `0.014537`

## Probe Results

| Probe | Category | Expected | Actual | Rewrite | Citation Docs | Passed |
|---|---|---|---|---|---|---:|
| GEN-MEM-001 | that_policy | answer | answer | Can employees carry unused vacation days into next year? | HR-002 | True |
| GEN-MEM-002 | same_department | answer | answer | For remote work, what security expectations from the remote work and device security policies apply? | HR-003, IT-002, IT-002, IT-002 | True |
| GEN-MEM-003 | contractors | answer | answer | What about contractors? Context: Tell me about vendor onboarding.. | OPS-001 | True |
| GEN-MEM-004 | compare_two | answer | answer | Compare those two for an employee. Context: I am comparing remote work and device security.. | HR-003, HR-003, HR-003, IT-002, IT-002, IT-002 | True |
| GEN-MEM-005 | which_applies | answer | answer | Which one applies to me if my laptop was lost? Context: I have a laptop replacement and a travel request.. | OPS-001, IT-002 | True |
| GEN-AMB-001 | project_ambiguity | clarify | clarify | What does the project policy say about approvals? |  | True |
| GEN-AMB-002 | department_ambiguity | clarify | clarify | What does the department handbook say about approvals? |  | True |
| GEN-AMB-003 | role_ambiguity | clarify | clarify | Which approval limit applies to my role? |  | True |
| GEN-AMB-004 | topic_ambiguity | clarify | clarify | What is the policy for that? |  | True |
| GEN-AMB-005 | document_reference | clarify | clarify | What does the second document say about exceptions? |  | True |
| GEN-PERM-001 | permission_memory | refuse | refuse_no_access | What does manager guidance say about promotion calibration? |  | True |
| GEN-PERM-002 | permission_role | answer | answer | Can I approve a refund above 1,000 dollars? Context: I am reviewing refund guidance.. | SUPPORT-001, FIN-001 | True |
| GEN-PERM-003 | permission_it_admin | refuse | refuse_no_access | What privileged access containment steps should I take? |  | True |
| GEN-DOC-001 | doc_reference | answer | answer | What does the PTO document say about sick time? | HR-002 | True |
| GEN-DOC-002 | doc_reference | answer | answer | What does that document say about learning budget? Context: I saw the benefits overview.. | HR-004, FIN-001 | True |
| GEN-COMP-001 | compare_two | answer | answer | For price objections, which objection-handling guidance should a Sales Representative use? | SALES-001, SALES-003 | True |
| GEN-HR-001 | role_applicability | answer | answer | What should HR Admins tell employees when an employee-facing HR policy is unclear? | HR-ADMIN-001 | True |
| GEN-IT-001 | same_department | answer | answer | What does the Device and BYOD Security Policy say about BYOD device security requirements? | IT-002 | True |
| GEN-MISS-001 | missing_info_followup | not_found | not_found | What about sabbaticals? Context: Tell me about leave benefits.. |  | True |
| GEN-MULTI-001 | multi_doc_reference | answer | answer | What approvals and safeguards apply? Context: personal device use. | IT-002, HR-003 | True |

## Notes

- This suite is separate from benchmark v1.1 and should not be folded into benchmark metrics.
- Memory is evaluated as query context only; citations must still come from retrieved documents.
- This is a remediation run against the same probe suite; compare with phase45-generalization-baseline.
