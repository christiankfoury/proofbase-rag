# Read-only runtime triage while evaluator validation runs

No runtime changes or API calls were made for this inspection. These are exposed
Phase 68 diagnostic cases, not new evaluation evidence. New development variants
and before/after traces are required before implementing or claiming remediation.

| Phase 68 case | Trace evidence | Follow-up hypothesis |
| --- | --- | --- |
| 003 | 10 chunks; evidence recommends answer; output guard downgrades after one repair; unsupported literal `16` | Inspect candidate text and whether the literal is a claim, citation metadata or context before changing validation. |
| 011 | Five chunks; evidence recommends answer; generator emits partial answer; output accepted | Inspect missing retrieval coverage and generation requirements, not only the final validator. |
| 013, 014 | Evidence recommends answer; generation takes 15/16 ms with zero tokens; fixed not-found response | `answer_generator.py` checks broad missing-topic strings before generation, including customer-specific commitments. They can override sufficient evidence. |
| 022 | Request assessment clarifies before retrieval | Verify intent ambiguity using a new named-policy development question. |
| 050, 051 | Request assessment blocks before retrieval | Active request prompt explicitly mandates blocking mixed legitimate/hostile requests. A safe separable question needs a scoped design change, preserving authorization and rejecting the override. |
| 054 | Evidence recommends answer; output guard downgrades for literal `001` | Check whether a document identifier was mistaken for an asserted policy number. |
| 055 | Evidence recommends answer; output guard downgrades for literal `100` | Inspect statement polarity and support before judging this a false positive. |
| 057 | Evidence recommends answer; output guard downgrades for literal `20 months` | Inspect whether answer endorses or rejects the quantity; never accept user premises as evidence. |

Relevant paths: `apps/api/app/generation/answer_generator.py` (`MISSING_PATTERNS`
and `_policy_response`), `apps/api/app/reasoning/post_generation_validation.py`
(`extract_exact_literals`, `exact_literal_supported`),
`apps/api/app/prompts/versions/request_assessment_v2.md`, and the generation/evidence
handoff in `apps/api/app/main.py`. Each saved case is under
`data/evaluation/current-runtime-v3/run/fresh-<id>.json`.

This is a failure-path inventory, not proof that every downgrade is wrong. Current
records establish the route and unsupported literal but do not by themselves
justify disabling guards. Preserve permission filtering, numeric correctness,
source-only evidence and memory-as-context in all proposed variants.
