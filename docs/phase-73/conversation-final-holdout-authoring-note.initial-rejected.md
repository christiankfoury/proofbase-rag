# Fresh final holdout authorship

- Author: isolated-agent-/root/final_author; agent-authored synthetic cases, not human labeling.
- Frozen commit: `e8182abe2035a2f6c3d54a20d1929aa235b21301`.
- Completion time (UTC): 2026-10-03T19:06:45.098503+00:00.
- Output: `data/evaluation/conversation-continuation/final-v1/holdout.json`.
- Holdout SHA-256: `a8232cad0d47e727b999b9d8482e1c6d753dcd230e7ab328c8678047b0bb5fd6`.
- Total: 60 cases.

## Category counts

- factual: 8
- multi_document: 10
- memory: 8
- permissions: 10
- ambiguity: 6
- missing_information: 6
- injection: 6
- conflicting_policies: 4
- uploaded_document_isolation: 2

## Procedure and checks

Input file reads were limited to the neutral contract, supplied freeze record and all nineteen synthetic corpus documents listed below. The author also reread its own in-progress output for construction and self-checks. No runtime/evaluator source, prior questions/results, roadmap files, application execution, external API calls, Git operations or other agents were used. Ordinary Python constructed the JSON and checked category counts, unique wording, sequential IDs, role/user IDs, exact source-quote inclusion, explicit document role membership (including IT Admin alias), distinct documents for every multi-document case, memory-only history placement, and ASCII fixture size and novel facts. All structural checks passed.

Each required fact was reviewed against the question's subject, scope, modality and material conditions. Facts omit unrequested adjacent source guidance. Non-answer rationales distinguish underspecified intent, absent facts, unauthorized documents and foreign-project uploads. Five allowed/denied document pairs vary wording, and injection cases include two benign source-discussion controls. All source documents contribute either required evidence or specific absence/access rationale across the suite.

## Procedural isolation limitations

This is agent authorship in a separately assigned context, not human labeling. The environment injects repository operating instructions into the agent context; those ambient instructions could not be removed by the author. The author did not open AGENTS.md or use its historical discussion to select cases. The assigned task and neutral contract controlled authoring. The supplied freeze record contains runtime metadata and hashes; its full tool output was exposed as custody data, but none of its referenced runtime files were opened and no implementation behavior was used to design expectations. No parent conversation, historical questions, results or failure analysis was requested or retrieved.

Historical novelty cannot be independently proved by an author forbidden from seeing earlier suites. Root must perform mechanical overlap checks without revealing older questions. A separate isolated validator must review all sixty cases and requested-scope alignment before sealing. These self-checks do not constitute application or model-execution evidence. No holdout execution occurred during authorship.

## Input files read

- `docs/phase-73/conversation-final-authoring-contract.md`
- `data/evaluation/conversation-continuation/final-v1/freeze.json`
- `data/synthetic-documents/engineering/ENG-001-deployment-on-call-and-api-standards.md`
- `data/synthetic-documents/finance/FIN-001-expense-procurement-and-reimbursement-policy.md`
- `data/synthetic-documents/hr/HR-001-employee-handbook.md`
- `data/synthetic-documents/hr/HR-002-pto-and-leave-policy.md`
- `data/synthetic-documents/hr/HR-003-remote-and-hybrid-work-policy.md`
- `data/synthetic-documents/hr/HR-004-benefits-overview.md`
- `data/synthetic-documents/hr-admin/HR-ADMIN-001-hr-policy-operations-guide.md`
- `data/synthetic-documents/it-admin/IT-ADMIN-001-privileged-access-and-incident-response-guide.md`
- `data/synthetic-documents/it-security/IT-001-acceptable-use-policy.md`
- `data/synthetic-documents/it-security/IT-002-device-and-byod-security-policy.md`
- `data/synthetic-documents/it-security/IT-003-data-classification-and-handling-policy.md`
- `data/synthetic-documents/legal/LEGAL-001-contract-nda-and-data-retention-policy.md`
- `data/synthetic-documents/manager/MGR-001-manager-handbook.md`
- `data/synthetic-documents/manager/MGR-002-performance-review-and-promotion-guide.md`
- `data/synthetic-documents/operations/OPS-001-vendor-travel-and-equipment-policy.md`
- `data/synthetic-documents/sales/SALES-001-sales-playbook.md`
- `data/synthetic-documents/sales/SALES-002-product-positioning-and-faq.md`
- `data/synthetic-documents/sales/SALES-003-competitive-battlecard.md`
- `data/synthetic-documents/support/SUPPORT-001-escalation-sla-and-refund-guide.md`
