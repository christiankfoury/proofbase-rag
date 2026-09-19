# Revised development challenge expectation review

The revised 24-case suite and all three audit-only probes are approved as authored expectations. This approval does not report a semantic-model result: no model, application runtime, API, or authorization check ran during this review. The validator is a context-isolated agent, not a human adjudicator.

The machine-readable record is `data/evaluation/quality-remediation-v1/challenge-validation-v2.json`.

| Suite | Cases | Raw-byte SHA-256 |
| --- | ---: | --- |
| `challenges-v2.json` | 24 | `b7f3c47f6c2c021e5ab652c2790db8a409e0b409101e60aeb1ea5352902d29ea` |
| `review-challenges-v1.json` | 3 | `e3ff3431d60b50b419746175fce3aa865466627297ed0cd36862f86575d4f1ed` |

All eight labels were checked per primary case: factual support, completeness, relevance, citation support, response behavior, quotation fidelity, overall, and actual behavior. Revised wording preserves laboratory eligibility, the annual ceiling and calendar-year period, and the key-return refund condition. The Rowan questions now ask only for the normal return deadline, removing the omitted late-return-rule ambiguity.

The four wrong-value, wrong-modality, or wrong-topic substantive responses now use `actual_behavior=answer`. Incorrect content and incomplete coverage can fail separate dimensions and the derived response-behavior requirement without changing the prose's response form. Cases answering only one of two requested parts still appropriately use `partial_answer`.

The audit probes contain demonstrable errors, not merely intentionally different labels:

- A candidate calls the absent shift condition covered while its own reason says missing, and claims both requested parts are answered. Completeness and response behavior require dispute.
- A candidate treats a generic refusal as an answer expressing two policy facts and as a supported factual claim. Factual support, completeness, citation support, and response behavior require dispute.
- A candidate omits the raw answer's insurance assertion while claiming complete claim enumeration. Its aggregate factual and citation support judgments require dispute.

The expected dispute sets are supported directly by the raw answers and authorized evidence. They do not depend on whether the implementation accepts the candidate structure. The other supplied dimension judgments remain defensible in these probes.

The original v1 suite and review record remain unchanged; their rejected ambiguities are preserved as provenance. For this revision, only the two new suites and current evaluator contract were read. Prior review context remained in the same validator task. No separate authorship notes, past evaluation reports, holdouts, fixture tests, or git operations were used.

Access decisions were treated as fixture premises. These development cases provide no independent permission verification or sealed-holdout claim. Approval means the expected labels are defensible, not that an evaluator achieved them. Any suite edit invalidates its byte hash and requires another review.
