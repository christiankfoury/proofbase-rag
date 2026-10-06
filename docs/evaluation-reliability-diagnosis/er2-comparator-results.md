# ER2: offline comparator v1

Plan: freeze ER1 inputs and implement only comparison.v1 in separately versioned
offline code. Baseline: the frozen comparator requires exact interpretation kind
labels and ignores meaning text in its comparison key. New comparison must retain
meaning and every plausible/excluded reading, coverage and safety dimension.
Acceptance: all 32 predeclared controls, symmetry, ordering, malformed input and
immutable-evidence checks pass; replay all 44 saved packets or explain incompatibility.
No release credit, model calls, provider client or runtime changes. Stop for any
unjustified equivalence or unresolved mandatory equivalence control.

## Result

`comparison.v1` is accepted for this declared offline diagnostic scope. It is not
a qualified evaluator or a solution for arbitrary semantic equivalence. All 32
controls pass at the contract's three-outcome level: 10 equivalent, 6 substantive
differences, 16 unresolved/invalid. False matches 0/22 non-equivalence controls;
missed matches 0/10 mandatory equivalence controls. The missing-claim control's
original expected subtype was unresolved; inherited validation produces invalid.
Its frozen annotation is retained, and the report records this sole subtype
difference. Both are the same no-credit contract outcome; no scoring change.

[Machine report](../../data/evaluation/evaluation-reliability-diagnosis/er2/v1/report.json)
replays all 44 saved pairs: 13 equivalent, 31 unresolved, 0 invalid, 0 substantive
differences. All 29 absent slots remain absent. These saved pairs do not have
independently certified equivalence labels, so false/missed-match rates on them
are unavailable. Counts are not model accuracy. All 519 historical bindings match.

The frozen baseline disagrees on the synthetic same-meaning/category control;
the new comparator establishes its equivalence. Conversely the baseline agrees
on six changed-meaning controls and a disjoint-witness control that the new
comparator correctly leaves unresolved. Coverage/status/forbidden differences
remain substantive. Split/combined and additional claims never disappear.
The latest `permission-modality-upgraded` pair remains unresolved: its free-form
meanings differ. No historical 22/23 qualification failure is repaired or relabeled.

## Verification, review and handoff

Commands on the ER2 working diff based on pushed ER1 `5e4f5c6d`:

- `python -B -m unittest scripts.test_offline_judgment_comparator_v1 scripts.test_structured_blind_evaluator_v2`: 12 methods pass, including all matrix rows, symmetry, input preservation, renamed controls and safety.
- `python -B -m scripts.offline_judgment_comparator_v1 --write`, then the same command without `--write`: full deterministic replay and hash verification.
- In-memory compilation of the two new modules passes; whitespace and complete intended diff review pass.

Socket connections are blocked in tests/replay. No provider client is created.
Frozen validators/references are reused unchanged. Review found that probe rows
store judge B in `second`, while `review` is a verdict about the candidate; the
adapter now selects the actual packet and regression tests cover all three probes.
This fixed an adapter error before publication, not historical evidence.

No unresolved blocking finding. The conservative unresolved rate is a limitation,
not a claim of semantic reliability on unseen outputs. All originals and detailed
normalization traces are retained via hash-bound paths. Context eligibility here
is inherited from the controlled source inputs, not fresh production permission
testing. App/benchmark/UI checks are skipped because no such code changed.
New calls/spend: 0/USD0; elapsed work time not instrumented. V4 remains active,
V6 disabled/unaccepted, remainder USD8.10754050 untouched. Next: AD1 after this
phase's verified commit/push; no paid requalification is proposed by this result.
