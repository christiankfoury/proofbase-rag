# Fresh holdout agent validation

Status: **approved**. Reviewed 2026-09-14T21:19:59.025834Z by `context-isolated-agent-fresh_validator_v2`. This is agent validation, not human review.

Raw-byte suite SHA-256: `66337ea75f109463dae29a05339b7d348cbcd7e36d0a9a18dabe4b73049e964c`. Approval applies only to those exact bytes of `data/evaluation/fresh-current/holdout.json`.

Reviewed all 60 cases and 103 required facts against the 19 corpus documents. Exact quote containment, explicit role ACLs (including the IT Admin alias), role/project IDs, category counts, distinct multi-document sources and fixture constraints passed. Every case has an individual decision and reason in `data/evaluation/fresh-current/author-validation.json`.

Semantic review covered fact atomicity and material completeness, non-answer justifications, complementary document necessity, documented conflict precedence, history-as-context boundaries and varied realistic scenarios. Five allowed/denied permission pairs are present. Seven cases were corrected through the author before approval: `fresh-005`, `fresh-010`, `fresh-022`, `fresh-028`, `fresh-030`, `fresh-052`, `fresh-055`. Changes split independently checkable facts, prohibited partial restricted-field disclosure, and restored a material approval exception. No runtime output or evaluation feedback was used.

Supplied freeze: `5db5a0e19b8097b4f592a0c26ee59e2f11d0975a`. Supplied custody commit: `a022a2107e8c6b6ebed46e042676da8aae978e81`.

Limitations:

- This is separate AI-agent validation, not human labeling, external assessment or runtime validation.
- The orchestration environment supplied repository operating instructions. Through tools the validator read only the neutral authoring contract, synthetic corpus, final holdout and authorship note; no runtime, evaluator, historical suite, results, roadmap or git history was inspected.
- Historical semantic originality cannot be attested without prohibited previous suites. Root separately performs mechanical historical overlap checks; this report does not independently certify those checks.
- Runtime/evaluator freeze and custody identifiers were supplied metadata, not independently verified through git history.
- No application, API, upload, retrieval, generation or evaluator execution was performed. Correct labels do not prove runtime success or evaluator sensitivity.
- The 60 synthetic cases are a bounded sample: memory coverage emphasizes correction of false prior assertions, and injection coverage includes user-supplied adversarial instructions plus benign source-discussion controls. This does not prove coverage of arbitrary attacks, histories or enterprises.
