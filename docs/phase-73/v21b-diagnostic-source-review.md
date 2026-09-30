# V21 replacement diagnostic source inspection

All five new cases and all three reviewer probes match exactly. The 18 settled
standard requests cost an estimated USD 0.23565000. The original failed diagnostic
and its ambiguous reference remain unchanged; its first four clean results are
reused under identical evaluator semantics. This establishes nine inspected
development cases and three reviewer controls, not an application accuracy score.

| New control | Source inspection |
| --- | --- |
| explicit-examples | The conditional tool recommendation and two explicitly labeled examples are supported. Missing the customer-requirement exception and its full condition correctly fails coverage. Prose answers both requested parts; derived behavior still fails incomplete coverage. |
| explicit-exclusion | The whole answer expressly denies a sourced exception. That context makes its exception list exclusive. Both extracted claims are incompatible with the source, citations cannot support them, and the required fact is contradicted rather than merely missing. |
| explicit-optional | Mandatory directly contradicts the explicit optional/not-mandatory source. Factual, citation, completeness and derived-behavior failures are correct; the prose remains an on-topic answer. |
| closing-task-framing | Destination, parcel weight and contact name are fully sourced. The closing documentation phrase refers to the task expressly requested in the question; it adds no institutional reason or guaranteed result. Complete claim/citation support and coverage are correct. |
| guaranteed-approval | All fields are covered, but the guarantee is separately extracted and unsupported. Unknown factual support and missing citation support correctly prevent target credit. |

Reviewer controls also pass source inspection: false-purpose disputes only factual
and citation support; missed-purpose detects the unsupported legal rationale while
preserving complete fields; overbroad-coverage disputes completeness and derived
behavior because the sealed fact itself only asks about hotels. It does not
authorize ignoring genuinely broader sealed facts.

All new grade contracts, exact claim/source spans, fact statuses, reducers and
reviewer decisions were inspected. Four reused controls and their reasons are in
[the original inspection](v21-diagnostic-source-review.md). No unresolved semantic
finding remains among these accepted controls. The original ambiguous case is
uncredited and its failed stage stays failed. This is agent/model development
validation, not human adjudication or a fresh confirmation.

Permit the unchanged full 24/24 calibration and 3/3 reviewer-probe gate next,
within the already declared USD 1.30 stage cap and USD 2.90482141 shared headroom.
Fresh isolated 16/16 confirmation remains required afterward. No selective retry,
sealed-reference edit, application measurement or quality claim is authorized by
this development result.
