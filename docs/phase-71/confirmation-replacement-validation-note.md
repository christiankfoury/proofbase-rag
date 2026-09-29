# Replacement confirmation validation

Status: **approved**. All 16 cases were independently reviewed and accepted before evaluator execution. No structural, coverage, or semantic-label findings remain. This is agent review, not human adjudication.

- Validated at: `2026-09-29T21:41:34.361077+00:00`.
- Frozen commit recorded by the allowed freeze artifact: `83c81d92ecd74c9dcd938a9f0dbf8db15b5d89cb`.
- Suite SHA-256: `61bca60cc7b0f63521d49cc0a166d02b21fee8a7b177ec6c1a3d1c266768ca31`.
- Freeze SHA-256: `17f33eaa405683c4c6b994bac6256fd611069331356db89d58f7476c99be10c4`.
- Validation artifact: `data/evaluation/quality-completion-v1/confirmation-validation-v3.json`.

Only the following inputs were read:

- `docs/phase-71/confirmation-replacement-validation-brief.md`.
- `docs/phase-71/confirmation-replacement-authoring-brief.md`.
- `data/evaluation/quality-completion-v1/replacement-freeze.json`.
- `data/evaluation/quality-completion-v1/confirmation-challenges-v3.json`.

Each review independently derives prose behavior, required-fact completeness, the ordered completeness override, and the composite, alongside factual support, relevance, citation support and quotation fidelity. A semantic failure dominates unresolved; a literal quotation defect is excluded from the composite as the rubric requires. N/A applicability was checked independently.

Structural checks verified 16 unique cases, answer/payload identity, exact label keys, nonempty required facts for expected answers, distinct numeric evidence identifiers, factual-source row mapping, citation identity and full cited-source text, and nonempty literal excerpt matching. The sole altered excerpt is the intentional quotation-fidelity negative control, whose expected failure is correct. All required facts follow from the synthetic policy sources.

Coverage includes all requested control categories, two conversational cases using history only for reference resolution, three cases with multiple evidence sources, and two complete answers requiring facts from two sources. Opposing controls cover mixed hostile/legitimate requests, source-embedded instructions, quotation fidelity and modality; distinct generic-refusal cases exercise the ordered override and unresolved behavior without an answer-only override. The expected unresolved composite in the latter is a correct control, not an unresolved validation finding.

The validator made no external/API calls, Git operations, evaluator executions or repository-module imports; it did not read evaluator source, prompts, earlier suites, reports, runtime failures or other repository files. The suite was not edited. Local standard-library checks accompanied the semantic review.

Isolation is procedural separate-agent isolation, not a technical access-control guarantee. Freeze source hashes and commit identity were accepted from the allowed freeze record, without source or Git verification. This validation is neither expert human adjudication nor a runtime holdout and makes no claim about evaluator performance.
