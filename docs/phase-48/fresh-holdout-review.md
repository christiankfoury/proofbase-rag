# Phase 48 Fresh Holdout Authoring And Review

## Isolation

- Runtime/evaluator freeze `7bbb8b4af9e5f43e069347f69f2599b652d1a2c8` was reviewed and pushed before authoring began.
- The isolated author received only the synthetic corpus, field structure, category contract, and shared identity/category constants.
- The author did not receive the Phase 47 holdout or results, development suite, benchmark questions, runtime code, or historical failure details.
- A separate isolated reviewer received the candidate, corpus, schema, and contract. Neither agent executed evaluation or called OpenAI.

## Authoring Inventory

- Suite: `holdout-v2.json`, version `2.0`, 30 cases.
- Distribution: 4 factual, 5 multi-document, 5 memory, 3 ambiguity, 5 permission, 3 missing-information, 3 adversarial, 1 conflicting-source, and 1 uploaded-isolation case.
- Coverage: all five roles, all four expected behaviors, 16 of 19 corpus documents, and one isolated uploaded fixture.
- Permission structure: two paired restricted/authorized scenarios plus one standalone restricted case.

## Independent Review

- Approved: `30/30`.
- The reviewer corrected two questions so every requested source was responsive and corrected one permission pair so its expected fact preserved the source's non-mandatory wording.
- Exact source quotes, required and forbidden propositions, role access, pair symmetry, memory context, ambiguity and missing-information labels, upload isolation, identifiers, schema fields, and distributions passed review.
- Phase 48 dry-run validation passed with the exact required category distribution and no external calls.
- Exact normalized question overlap against both prior suites: `0`.
- Protected runtime/corpus diff from freeze commit before sealing: empty.

## Seal

- SHA-256: `394cb6a2accd6c244c86925403ac3b9b320fc504f472254e8830bfc045e3f866`.
- Every case is marked `approved` by `phase48-independent-reviewer`.
- The sealed suite must be committed and pushed before the one-time complete execution.
