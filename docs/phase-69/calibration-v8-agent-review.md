# Independent agent inspection of calibration v8-01

**Readiness verdict: not ready to serve as a validated semantic evaluator.** V8 improves substantially on the preserved first attempt, but has one unsupported overall pass, seven primary cases with label disagreements, and three false audit disputes. The manifest correctly keeps `semantic_validation_passed=false`.

This is independent agent inspection, not human adjudication. No APIs, application runtime, git operations, or edits to expectations or frozen outputs were performed. The review inspected all 24 final candidate/reviewer records, all three audit-probe records, the unchanged challenge suites, the frozen v8 contract, and selected raw requests. Counts below were independently recomputed from expected labels and stored results rather than copied from the manifest's matched flags.

## Agreement and false decisions

| Measure | Result |
| --- | ---: |
| Exact primary case agreement across all eight labels | 17/24 (70.8%) |
| Individual expected-label agreement | 167/192 (87.0%) |
| Overall-label agreement | 19/24 (79.2%) |
| Factual support | 22/24 |
| Completeness | 20/24 |
| Relevance | 20/24 |
| Citation support | 21/24 |
| Response behavior | 18/24 |
| Quotation fidelity | 24/24 |
| Actual behavior | 23/24 |

The overall transition counts preserve unresolved outcomes rather than treating them as ordinary failures:

| Expected overall | Observed overall | Cases |
| --- | --- | ---: |
| pass | pass | 6 |
| pass | unresolved | 1 |
| fail | fail | 13 |
| fail | unresolved | 3 |
| unresolved | pass | 1 |

There is **one false pass** when pass means granting credit to a case that should not receive it: `generic-refusal-unknown-reason` is promoted from unresolved to pass. No expected-fail case receives pass. There are zero explicit false fails (expected pass to observed fail), but one valid pass is withheld as unresolved: `pure-not-found`. The three expected failures weakened to unresolved are `not-found-is-not-access-refusal`, `not-found-with-unsupported-policy-claim`, and `permission-modality-upgraded`.

These are label-agreement counts on authored development material, not answer-quality or population accuracy estimates.

## Seven remaining primary disagreements

| Case | Independent diagnosis |
| --- | --- |
| `contradicted-quantity` | Candidate correctly identifies the 12-versus-24-hour contradiction. Reviewer disputes the derived response-behavior failure because prose is an answer, ignoring the contract's separate completeness requirement for expected answers. Overall remains fail, but behavior becomes unresolved. |
| `pure-not-found` | Correctly recognizes the utterance as `speech_act` yet emits `citation_status=missing` instead of the required unknown placeholder. `speech_act_contract` invalidates the judgment and all semantic dimensions become unresolved. |
| `not-found-is-not-access-refusal` | Candidate correctly classifies inability to find as not_found. Reviewer reinterprets it as access refusal and disputes the correct behavior failure, producing overall unresolved. Nothing in the answer says the user lacks access. |
| `generic-refusal-unknown-reason` | Candidate and reviewer infer access denial from a generic refusal. The answer only says “I cannot help with that request.” Its reason remains unknown; neither the question's restricted-document wording nor expected behavior supplies an answer span explaining denial. This is the false pass. |
| `not-found-with-unsupported-policy-claim` | The policy claim is now correctly unknown rather than contradicted, but the not-found speech act again has citation status missing. The structural error turns the known missing citation for the separate destruction assertion into overall unresolved. |
| `ambiguous-question-assumed-context` | Both stages accept relevance after the answer invents equipment context for an unscoped booking question with empty history. Reviewer also disputes completeness=not_applicable because the response failed to clarify, conflating behavior with required-fact coverage. Overall stays fail due to behavior. |
| `permission-modality-upgraded` | Candidate calls the factual claim contradicted but its citation supported by the same contrary source. Reviewer explicitly agrees that contradiction by a properly referenced source makes citation support pass. Entailment is required; provenance of contradictory text is insufficient. `support_labels_conflict` correctly prevents credit but leaves a clear failure unresolved. |

The three structural errors are correctly visible and do not result in passes. They still matter: a valid semantic extraction and audit should not depend on an invalid combination of claim fields, and an all-agree review is not evidence that these combinations are sound.

## Audit-probe specificity

All three probes detect every required dispute. The manifest's `matched=true` therefore describes minimum detection, not exact expected-review agreement.

| Probe | Required disputes detected | False disputes | Exact match |
| --- | ---: | --- | --- |
| `covered-label-with-missing-reason` | 2/2 | factual_support, citation_support | No |
| `generic-refusal-falsely-covers-policy` | 4/4 | None | Yes |
| `extra-factual-assertion-omitted-from-claims` | 2/2 | completeness | No |

Across the six reviewed dimensions per probe, there are eight required-dispute positions and ten positions where no dispute is expected. V8 detects 8/8 required disputes, falsely disputes 3/10 other positions, and therefore has observed specificity 7/10 and dispute precision 8/11. Exact probe agreement is **1/3**, not 3/3. These tiny counts are descriptive checks, not stable rate estimates.

The first probe still confuses omission with falsity: the answer's cap is supported by its source and citation, even though the second requested fact is absent. The third correctly notices omitted insurance but wrongly calls the requested allowance incomplete because the answer adds unsupported content. Its explanation also says unsupported insurance makes factual support fail; absence of evidence warrants unresolved, not contradiction. The generic-refusal probe has the correct dispute set, although its explanation emphasizes omitted policy coverage rather than clearly articulating why the refusal has no factual policy claims.

## What improved, and what remains unproved

Explicit speech-act classification fixes most v7 refusal/citation contamination and prevents source-only booking deadlines from being treated as answer assertions in this run. Explicit candidate dimension labels largely fix the earlier pattern of disputing every correct negative grade. The ordinary and altered Rowan quotation cases still match their intended distinct quotation outcomes. Unsupported extra insurance, uncited-but-supported content, history-only evidence, wrong-topic facts, and the two injection examples now match the full expected label set.

Matching labels do not guarantee a flawless explanation. For example, the source-injection reviewer says the answer does not cite the source, although the payload contains a citation; the actual defect is that the cited content contradicts the claim. That imprecision does not change this case's expected labels, but citation presence and citation entailment should remain distinct.

No source-grounded expectation defect was established. The unchanged suite hashes match the recorded plan: primary `b7f3c47f6c2c021e5ab652c2790db8a409e0b409101e60aeb1ea5352902d29ea`; audit `e3ff3431d60b50b419746175fce3aa865466627297ed0cd36862f86575d4f1ed`. The unresolved/fail distinctions should not be relabeled to improve agreement.

Before any promotion, the remaining refusal-reason, speech-act schema, citation-entailment, ambiguity, and dimension-independence issues need a separately versioned repair and preserved validation. Audit acceptance must account for false disputes as well as detecting seeded errors. Repeating known development cases can demonstrate remediation on those cases; it cannot establish performance on a newly sealed holdout or validate the underlying RAG runtime.
