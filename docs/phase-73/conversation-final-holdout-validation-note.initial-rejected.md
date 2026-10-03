# Independent final holdout validation

Status: rejected before execution. Reviewed all 60 cases; 59 accepted and 1 rejected. Unresolved finding: FHV-001 (fresh-056; source_subject_scope). The complete finding is in the validation artifact. The suite requires a pre-execution source-grounded revision and independent revalidation before sealing. Preserve this suite and rejected validation before any revision.

- Validator: isolated-agent-/root/final_validator
- Validation time: 2026-10-03T19:11:53.036999+00:00
- Frozen commit: e8182abe2035a2f6c3d54a20d1929aa235b21301
- Suite SHA-256: a8232cad0d47e727b999b9d8482e1c6d753dcd230e7ab328c8678047b0bb5fd6
- Freeze SHA-256: 4ff842060a40e25a4516bd6ddeb937e4693d069d88523e1d1161fc3d85d5d2c8
- Validation artifact: `data/evaluation/conversation-continuation/final-v1/author-validation.json`

The validator read only the two neutral contracts, supplied freeze record, all nineteen Markdown corpus documents, and the complete new holdout after author completion. No author note, runtime/evaluator code, historical questions or results, parent conversation, model outputs or application state was inspected. No API calls, Git operations, application executions or additional agents were used. The freeze record itself includes configuration and file-binding metadata; those were not treated as source evidence for questions.

All 61 reference quotations exactly occur in their named corpus sources. Identity/role membership, project and declared department scope, category counts, history structure and ASCII upload fixture structure pass mechanical checks. All ten multi-document questions require complementary documents. Five allowed/denied pairs use explicit memberships, including no inherited HR or IT permission. Memory falsehoods are excluded as authority. Injection cases include benign source discussion and adversarial requests. Two novel fixture facts do not occur in the corpus and are assigned to separate projects by contract. The source-specific issue prevents full approval despite otherwise passing checks.

Every case has an independently reviewed behavior, source-based reason, and explicit reference-scope review. Review considered each requested subject and output, retained source modality and material conditions, and excluded unasked adjacent facts. Difficulty distribution is 7 easy, 50 medium and 3 hard; labels describe intended demands and are not empirically calibrated.

This is agent validation, not expert human labeling. Historical question overlap is deliberately left to root's separate mechanical check. Actual upload/project isolation and model behavior were not executed or observed. No generalization or application quality outcome is asserted.
