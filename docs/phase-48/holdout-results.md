# Phase 48 Fresh Holdout Results

## Outcome

The sealed holdout does **not** support an improvement claim.

- Machine-observed result: `19/30` (`63.3%`).
- Human adjudication found one clear evaluator-only machine failure in the separately recovered fixture. No formal human-adjusted aggregate is published because the first 29 detailed rows were not retained atomically.
- Target: at least `27/30`; meaningful-improvement marker: `24/30`.
- Answer-generation cost: `$0.023159`.
- Phase 47 historical holdout: unchanged at `14/30` and not rerun or rescored.

Cases 1-29 executed exactly once in the sealed complete-suite process. The process then stopped before case 30 because legacy fixture setup could not instantiate the suite's generic declared-document fixture. A committed evaluator-only adapter subsequently executed only the untouched fixture once. No case was rerun.

## Metric Limitation

The initial process stopped before its atomic result write. Terminal observations preserve each case's pass/fail status and cost, and request logs preserve response type, retrieved documents, citation count, latency, and cost. They do not preserve complete answer and citation payloads.

Therefore Phase 48 must report the following target metrics as unavailable rather than inventing or approximating them:

- Behavior accuracy: `unavailable`.
- Required-source recall: `unavailable`.
- Required-fact completeness: `unavailable`.
- Citation document accuracy: `unavailable`.
- Factual hallucination rate: `unavailable`.
- Permission and memory hard-gate aggregates for this holdout: `unavailable`.

The separately completed upload fixture answered “Wednesday,” retrieved and cited only the current-project upload, had no forbidden fact, hallucination, unauthorized document, restricted citation, unauthorized generation, or memory-as-evidence violation. Its machine failure was required-fact completeness `0.667`: the answer omitted the expected fact's redundant “for the current project” wording despite proving project isolation through retrieval and citation metadata.

## Interpretation

The fresh suite reveals that the general remediation overfit the inspectable development mechanisms more than intended. The dominant observed failure areas are multi-policy synthesis, longer memory references, adversarial-source handling, and one restricted-response boundary. Another remediation phase must use these results only as development evidence, improve mechanisms without case-specific rules, harden checkpoint/preflight behavior, and use a different newly authored holdout before making any new generalization claim.
