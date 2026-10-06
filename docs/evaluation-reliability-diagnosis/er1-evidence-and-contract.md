# ER1: evidence and comparison contract v1

Goal: establish a defensible offline comparison boundary before application diagnosis.
Scope: Dev/Admin diagnostic artifacts only; no API, UI, data model or scoring change.
Acceptance: account for every selected slot, bind originals by SHA256, declare
positive/negative controls and leave unsupported semantic correspondence unresolved.
Stop on a required scoring/reference decision; none is adopted here.

## Selection and custody

Selection was declared before labeling: all saved structured-blind v1 diagnostic
and v2 diagnostic/calibration cases and probes, plus all unexecuted slots. Full
v34/v35 calibration files preserve predecessor context; ordering controls and
loaded reference/validator dependencies are hash-bound. No sealed fresh suite is
opened. [Inventory](../../data/evaluation/evaluation-reliability-diagnosis/er1/v1/inventory.json)
binds 519 files and 73 slots: v1 diagnostic 2 saved/17 unexecuted; v2 diagnostic
19 saved/0 unexecuted; v2 calibration 23 saved/12 unexecuted. V1 calibration never
started. Probe rows are included in these denominators. Raw envelopes, preflights,
runtime commits, references, exact questions/history/answers/sources and receipts
remain accessible through the inventory, without rewriting historical artifacts.

## Prospective diagnostic contract: comparison.v1

Three outcomes: `equivalent`, `substantively_different`, `unresolved_invalid`.
The last outcome has separate `unresolved` and `invalid` reasons/subtypes. This
is comparison of recorded judgments, not a claim that either judgment is correct.
`release_eligible` and `target_credit` are always false.

Validate each original packet with the frozen structured validator first. Add
exact answer-span binding, unique fact/claim IDs and input-source ID validation.
Invalid schema, witnesses or unauthorized IDs cannot be normalized into validity.
Compare facts by ID and claims by complete exact answer span. Reordering has no
meaning; duplicate claims/facts are invalid. Missing/additional or split/combined
claims stay unresolved, even if both overall answers fail.

Within a claim, compare all plausible AND excluded interpreted meanings, collapsing
whitespace in meaning prose only. Match meaning, plausibility, factual status and
citation status separately. A different category can be ignored only when the
complete meanings and plausibility match. Changed meaning, actor, recipient,
condition, negation, modality or scenario value is unresolved rather than an
invented semantic equivalence. Changed verdicts on a matched meaning, fact coverage,
behavior, relevance, nonempty forbidden sets or plausibility are substantive.

Witness order and repetitions are immaterial after validation. Alternative source
witnesses are equivalent only with identical source IDs and pairwise containment
coverage in both directions (each span contains or is contained by a counterpart).
Disjoint witnesses remain unresolved. This is an evidential-binding rule, not an
entailment proof. Apply the same rule to fact answer witnesses and context witnesses.
Reason prose is retained but not used as a verdict. Empty forbidden sets use the
already-versioned v2 projection; raw labels remain visible. Uncertainty, safety,
quotation/citation checks and historical failed qualification receive no credit.

The latest literal/action-order disagreement is not declared a mandatory match:
different free-form meanings or unmatched excluded readings cannot be certified
by taxonomy alone. This general limitation applies across the entire inventory;
no case name, company, phrase or expected score controls comparison behavior.

## Controls and verification

[Frozen matrix](../../data/evaluation/evaluation-reliability-diagnosis/er1/v1/matrix.json)
contains 32 synthetic controls with exact input packets, source case, rationale,
and prospective diagnostic expectation. It covers identities, order, category and
witness changes, omissions, actor/recipient/condition/modality/negation/scenario
changes, uncertainty, forbidden sets, malformed outputs and unauthorized witnesses.
These are agent annotations grounded in inherited source cases, not human labels
or model observations. No inherited reference is changed.

Verified `python -B -m scripts.evaluation_reliability_inventory --build` and its
read-only default: 519 unchanged bindings, 73 accounted slots. Reviewed complete
intended script/artifact/document diff for exclusions and hidden reference changes.
ER2 must execute all controls; these expectations are frozen before implementation.
No application build, benchmark change or live check is applicable. New calls/cost:
0/USD0. Unrelated request-log SHA256 remains
`f37906539da34d369b0259b014fc061bb2d15b42e31605800d55b724335c176e`.

Compact handoff: branch main, starting revision 3ffed831; intentional ER1 diff only.
Elapsed work time not instrumented. No blocking review finding; source-binding
coverage and normalization negative controls were added during review. Next: ER2
after verified commit/push. V4 active, V6 disabled/unaccepted; USD8.10754050 untouched.
