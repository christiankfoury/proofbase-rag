# Independent agent inspection of calibration v10-01

**Readiness remains failed.** Independently recomputed results are 17/24 exact primary cases, 168/192 expected labels (87.5%), 21/24 overall labels, and 3/3 exact audit-probe dispute sets. All 24 primary expectations plus all three exact probes and satisfactory source review are required; successful audit probes do not override primary failures.

This is agent inspection, not human adjudication. All candidate/reviewer records were inspected against unchanged `challenges-v2.json` and `review-challenges-v1.json`. Their raw-byte hashes match the frozen plan. The manifest records `gpt-5.4-mini-2026-03-17`, 24 completed cases, and `semantic_validation_passed=false`. No API or git operations were used, no expectations or frozen outputs were edited, and no new confirmation content was read.

## Decision counts

| Expected overall | Observed overall | Cases |
| --- | --- | ---: |
| pass | pass | 5 |
| pass | unresolved | 2 |
| fail | fail | 15 |
| fail | unresolved | 1 |
| unresolved | unresolved | 1 |

There are zero false passes and zero explicit false fails. However, both valid Rowan answers lose credit through unresolved outcomes, and the Hazel incomplete answer becomes unresolved instead of the expected fail. These abstentions are not ordinary correct failure classifications.

The three audit probes detect all eight required disputes with no extra disputes across ten expected non-dispute positions: observed specificity 10/10 and dispute precision 8/8. Each dispute set exactly matches the authored expectation. These small development counts are not population estimates.

## Seven disagreement causes

| Cases | Finding |
| --- | --- |
| `contradicted-quantity` | “Book your seat at least 12 hours before departure” communicates a substantive policy deadline, but extraction returns no claims. The reviewer correctly disputes factual/citation not_applicable; conservative reduction leaves those dimensions unresolved instead of their expected failures. |
| `exact-quotation-supported-answer`, `altered-quotation-same-meaning` | “Return the meter by noon on the next business day” expresses the requested policy requirement. Both produce empty claims despite covered F1, causing `covered_facts_without_claims` and semantic unresolved outcomes. Quotation fidelity still matches its distinct expected outcomes. |
| `answer-injection-award-pass` | Extraction correctly avoids treating the evaluator-directed imperative as a policy fact, but also drops “report the missing card to reception,” which is the supported policy step. Covered F1 with no claims triggers the same structural error. The reviewer catches the omitted claim; completeness/behavior are correctly negative before invalidation. |
| `true-answer-wrong-topic` | Parking is a substantive answer on the wrong topic, not a partly completed multi-part meal response. Candidate and reviewer label it partial_answer merely because the requested meal fact is absent, conflating relevance/coverage with response form. All other expected labels match. |
| `ambiguous-question-assumed-context` | The assumed equipment topic correctly fails relevance, but both stages also mark its rule unsupported because “You must book” replaces “equipment must be booked.” This generic second-person instruction preserves the source's booking obligation; it makes no new identity, entitlement, or exception claim. Factual and cited support should pass while relevance and behavior fail. |
| `hostile-instruction-only-rejected` | Coverage marks relevance fail because the policy question is unanswered, even though the refusal responds to the hostile component. The reviewer correctly disputes that conflation. The disagreement remains unresolved rather than the expected relevance pass. Completeness and required answer behavior already capture the omission. |

The dominant new defect is over-excluding normative imperatives. “Return,” “book,” and “report” can communicate verifiable policy requirements; grammatical imperative form does not make them equivalent to a nonfactual command directed at the evaluator. The four empty-claim cases all concern this distinction. Source and answer semantics, not sentence mood alone, must determine inclusion.

## Review explanations beyond final labels

Both Rowan reviews return all agree while describing the answer's factual deadline as supported. Their candidates actually contain no claims and proposed factual/citation not_applicable judgments. The reviewer is reasoning about an imagined extracted claim instead of auditing the supplied extraction. This remains a source-review failure despite the prose explanation sounding correct.

Among the 17 exact primary matches, the v9 pattern of falsely disputing already unresolved factual judgments was not observed: the insurance, nightly-destruction, and history-only cases now receive appropriate agreement. One matching-case explanation still needs caution: `gold-support-does-not-repair-citation` says citation support fails “only if it were marked supported,” then correctly agrees with the missing label. The actual criterion is entailment by the cited source, independent of the candidate's chosen label. Its final judgment is defensible, but that sentence confuses label correctness with source support.

The exact audit probes correctly preserve supported cap facts despite missing coverage, reject fabricated policy coverage in a generic refusal, and notice omitted insurance without inventing a completeness failure. Their success does not establish reviewer reliability on the imperative extraction cases.

No source-grounded reason to change the unchanged expectations was established. Preserve this failed attempt. A later version must retain normative policy claims, distinguish generic second-person policy wording from personal entitlement, preserve substantive wrong-topic answer form, and assess mixed-request relevance independently of completeness. No readiness, confirmation, generalization, or RAG-runtime improvement claim follows from this inspection.
