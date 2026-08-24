# Phase 49 Independent Blind Validation

## Validation identity

- Validator: `phase49-independent-blind-validator`
- Review timestamp: `2026-08-24T00:32:06Z`
- Reviewed artifact: `data/evaluation/independent-generalization/holdout-v3.draft.json`
- Approved artifact: `data/evaluation/independent-generalization/holdout-v3.json`
- Schema: `data/evaluation/independent-generalization/schema-v3.json`

## Isolation and allowed sources

This validation used only the following inputs:

- `data/evaluation/independent-generalization/holdout-v3.draft.json`
- `data/evaluation/independent-generalization/schema-v3.json`
- `data/synthetic-documents/**/*.md`

No prior holdout, holdout hash, evaluation result, Phase 47 or Phase 48 document, Phase 47 or Phase 48 roadmap plan, Git history or diff, request log, failure or adjudication artifact, runtime prompt/retrieval/generation code, scoring code, remediation test, or failure-specific context was accessed. The validation was performed from the v3 draft, v3 schema, the supplied neutral IDs and distribution constraints, and corpus truth only.

## Checks completed

- Confirmed 30 cases with unique `P49-H3-*` case IDs and suite-level count consistency.
- Confirmed exact category distribution: 4 factual robustness, 5 multi-document claim coverage, 5 multi-turn memory, 3 ambiguity boundaries, 5 permission/scope cases, 3 missing-information abstentions, 3 prompt-injection adversarial cases, 1 conflicting-version case, and 1 uploaded-document isolation case.
- Confirmed every case uses the supplied role/user-ID mapping and every suite case uses either the supplied Northstar project ID or an intentional null global scope.
- Confirmed project, department, and global scopes are represented and department IDs use the supplied mapping.
- Checked every question against its expected behavior, required facts, forbidden facts, expected documents, and authoring intent.
- Confirmed every corpus-backed expected quote is verbatim and appears under the named section in the named document.
- Confirmed answerable cases use documents accessible to their role and that refusal cases do not allow the restricted target document.
- Confirmed each same-intent permission pair now has identical question, project scope, and department scope; the role/user and expected access outcome are the meaningful differences.
- Confirmed all five multi-turn cases have resolvable referents and that conversation context identifies the query while corpus documents remain the evidence.
- Confirmed all three ambiguity cases omit details that materially change the applicable policy path.
- Confirmed all three missing-information requests are not supplied elsewhere in the permitted corpus; each cited source explicitly states that the requested detail is absent or unavailable.
- Confirmed prompt-injection cases preserve permissions, source attribution, and document-as-data boundaries.
- Confirmed the version-conflict case uses the current source's explicit supersession note and does not rely on the obsolete amount.
- Confirmed the uploaded-document fixture is self-contained: the in-scope approved/indexed Aurora document matches the requested Northstar project and Sales department, while the conflicting document belongs to a different project and is excluded from allowed evidence.
- Confirmed all roles, difficulties, expected behaviors, and global/project/department scope forms are represented.
- Confirmed 16 distinct synthetic-corpus documents are expected sources, exceeding the minimum of 12; the declared upload fixture adds one in-scope expected document.
- Confirmed the approved JSON validates against `schema-v3.json` after corrections.

## Neutral corrections made

1. `P49-H3-008`: added the exact onboarding-timing sentence from `HR-001` so the first-10-business-days condition is directly evidenced, rather than only implied by the adjacent checklist quote.
2. `P49-H3-009`: changed `department_id` to null, making the case project-scoped. Its two required sources belong to Engineering and IT Admin departments, so a single Engineering department scope could not truthfully allow both.
3. `P49-H3-013`: changed the second required fact's subject from the generic “review” to “Managers,” matching the corpus attribution exactly.
4. `P49-H3-016`: added the standard under-USD-25,000 order-form row alongside the security-addendum row, making the agreement-type ambiguity directly evidenced.
5. `P49-H3-017`: added the USD 2,500–10,000 and above-USD-10,000 procurement quotes so the amount-dependent approval ambiguity is directly evidenced.
6. `P49-H3-018` and `P49-H3-020`: aligned each unauthorized permission case to the same department scope as its authorized pair and cleared unrelated allowed documents. Each pair now isolates role-based access while preserving exact intent parity.
7. `P49-H3-028`: cleared out-of-department allowed documents under the IT Admin department scope and added the exact incident-triage record-fields quote so both restricted targets in the question are represented.
8. All cases were set to `review_status: approved`, `reviewed_by: phase49-independent-blind-validator`, and the common UTC timestamp `2026-08-24T00:32:06Z`.

No expected answer, access entitlement, source truth, category assignment, difficulty, or behavioral outcome was changed to match known product behavior. No hash was created.

## Final coverage

| Dimension | Coverage |
| --- | --- |
| Categories | 9 of 9; exact required counts |
| Roles | Employee 8; Sales Representative 7; Manager 5; HR Admin 5; IT Admin 5 |
| Difficulties | Easy 5; Medium 11; Hard 14 |
| Expected behaviors | Answer 19; Clarify 3; Refuse no access 5; Not found 3 |
| Scopes | Global 4; Project 4; Department 22 |
| Distinct corpus source documents | 16 |
| Declared in-scope uploaded fixture documents | 1 |
| Permission pairs | 2 exact-intent, exact-scope pairs plus 1 standalone department boundary case |

## Post-validation fixture-completeness correction

Execution preflight identified that both declared uploaded documents in `P49-H3-030` lacked the explicit boolean `restricted` field required for reliable fixture declaration. `restricted: false` was added to `UPLOAD-P49-AURORA-001` and `UPLOAD-P49-OTHER-001`. No question, expectation, source, scope, role, or other field was changed.

Reliable execution preflight must be rerun after this fixture-completeness correction.

## Approval

The corrected `holdout-v3.json` is independently approved as a corpus-grounded blind holdout. Its facts, permission expectations, scope boundaries, memory referents, abstention conditions, adversarial expectations, version handling, and upload isolation fixture are internally consistent with the permitted source material.
