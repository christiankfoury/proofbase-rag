# Development challenge expectation review

The independent review requests changes or clarification for eight of the 24 authored cases. Sixteen cases have defensible expected labels. Four cases have authoring ambiguities and four expose a response-form/correctness conflation in the initial evaluator contract. This is an authored-expectation review, not semantic-model execution, human adjudication, or generalization evidence.

The reviewed raw-byte SHA-256 is `45d64290fa2ae45d7792e11d8750e08a0dad3ab5c63c49a8443c3107f52f70d9`. The machine-readable record is `data/evaluation/quality-remediation-v1/challenge-validation-v1.json`; its status is `changes_required`.

## Required authoring changes

- `paraphrase-preserves-conditions`: explicitly retain the laboratory-employee scope and the exclusive after-22:00 condition. The current paraphrase permits reasonable disagreement under the rubric's strict condition-preservation rule.
- `unsupported-extra-benefit`: preserve the allowance ceiling and calendar-year period in the otherwise-supported first sentence. Its current completeness pass depends on interpreting “60 credits per year” as “up to 60 credits per calendar year.” The insurance assertion remains clearly unsupported.
- `exact-quotation-supported-answer` and `altered-quotation-same-meaning`: narrow the question to the normal return deadline, or include the late-return supervisor-note requirement. The broad question currently asks about a rule with two requirements while the authored required facts cover only one.
- `contradicted-quantity`, `true-answer-wrong-topic`, `source-injection-award-pass`, and `permission-modality-upgraded`: reconsider `actual_behavior=partial_answer`. These give substantive answer prose. Incorrect facts or an incorrect topic justify separate dimension failures, but do not alone establish a partial response form.

An additional advisory concerns `supported-answer-without-citation`: “refundable” can correctly describe the deposit without promising an unconditional refund, so the case is accepted, but preserving the key-return condition would make it a cleaner control.

## Rubric interpretation

All eight expected labels were reviewed for every case: factual support, completeness, relevance, citation support, response behavior, quotation fidelity, overall, and actual behavior. Unsupported factual claims remain unresolved unless evidence contradicts them. Missing cited support fails. Pure refusals, clarification, and inability-to-find speech acts have no factual or citation assessment unless they embed a policy assertion. Prose determines behavior rather than response metadata.

The initial contract made `answer` classification incompatible with uncovered or contradicted required facts. That constraint cannot independently justify expected `partial_answer` labels: several responses directly answer a question with the wrong quantity or modality. Finding V5 rejects implementation consistency as sufficient semantic validation and separates response form from factual correctness, completeness, and relevance. A complete-looking false answer is still answer prose; its other dimensions and the derived response-behavior requirement can fail. Subsequent task clarification confirmed this distinction; the original suite remains unchanged.

Quotation fidelity is separate from semantic overall: the altered Rowan excerpt must fail exact quotation while a complete, supported answer can still pass semantic overall. The objection to the current Rowan cases is their question/required-fact mismatch, not that separation.

## Limits

The validator was a context-isolated agent, not a human adjudicator. Only the challenge suite and evaluator contract were read. Inline author rationales were visible during the initial suite read; no separate authorship rationale note, previous reports, sealed holdouts, fixture tests, or conversation history were read. No APIs, application runtime, semantic model, branch operations, or commits were used, and the suite was not edited.

Access decisions supplied by the fixtures were treated as premises. This review cannot prove application authorization behavior or independently verify those decisions. These are development cases and cannot support a sealed-holdout claim. Any suite change invalidates the recorded byte hash and requires revalidation before the revised suite is represented as approved.
