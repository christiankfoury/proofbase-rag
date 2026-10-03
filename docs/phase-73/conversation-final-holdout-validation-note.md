# Independent final holdout validation

Status: approved before execution. All 60 cases accepted; no unresolved findings. FHV-001 (fresh-056; source_subject_scope) was resolved by an isolated pre-execution revision and independent revalidation. The original suite and rejected validation remain preserved as initial-rejected artifacts.

- Validator: isolated-agent-/root/final_validator
- Validation time: 2026-10-03T19:15:42.918124+00:00
- Frozen commit: e8182abe2035a2f6c3d54a20d1929aa235b21301
- Approved suite SHA-256: 46b45321788f8b8963e017986e730cfe8308037a58c2e734ac2605d34e302c93
- Freeze SHA-256: 4ff842060a40e25a4516bd6ddeb937e4693d069d88523e1d1161fc3d85d5d2c8
- Initial rejected suite SHA-256: a8232cad0d47e727b999b9d8482e1c6d753dcd230e7ab328c8678047b0bb5fd6
- Initial rejected validation SHA-256: ccd1ddbe9b5de792dba81f6881051bd20b132cba25fb3c35eaa432570673efaf
- Validation artifact: `data/evaluation/conversation-continuation/final-v1/author-validation.json`

The validator read only the two neutral contracts, supplied freeze record, all nineteen Markdown corpus documents, and the completed new holdout. The validator then reread all sixty revised-suite questions and reference expectations, reused the already read source context, and reran all exact-quotation and role checks. Its own prior validation artifact was read to preserve the individually reviewed records; preserved original artifact hashes were verified. No author note, runtime/evaluator code, historical evaluation questions or results, parent conversation, model outputs or application state was inspected. No API calls, Git operations, application executions or additional agents were used. The freeze includes configuration and file-binding metadata; those are not source evidence for questions.

All 61 reference quotations occur exactly in their named sources. Identity/role membership, project and declared department scope, category counts, history structure and ASCII upload fixture structure pass. All ten multi-document questions require complementary documents. Five allowed/denied pairs use explicit memberships, without inherited HR or IT permission. Memory falsehoods are excluded as authority. Injection cases include benign source discussion and adversarial requests. Both novel fixture facts are absent from the corpus and assigned to separate projects by the neutral contract. Four conflict cases rely on documented precedence or conditions.

Every case has an independently reviewed expected behavior, source-based reason, and explicit reference-scope review. Review considered requested subjects and outputs, source modality and material conditions, and excluded unasked adjacent facts. FHV-001 initially identified an unsupported source-subject mapping. The revised question and gold fact now ask about the source's explicit subject; the separate old-document precedence question also directly matches the source. No scoring relaxation or implementation-specific reasoning was used. Difficulty distribution is 7 easy, 50 medium and 3 hard; these labels are not empirically calibrated.

This is agent validation, not expert human labeling. Historical overlap remains root's separate mechanical check. Actual upload/project isolation and model behavior were not executed or observed. Approval establishes source-grounded reference validity under the neutral contract, not an application quality or generalization result.
