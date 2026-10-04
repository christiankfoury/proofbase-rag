# Ordering contract v2: implemented remedy and completion boundary

The latest user request authorizes a separately versioned reference remedy and
offline implementation, with paid execution conditional on funding the entire
remaining path. This work implements that remedy. Acceptance is **blocked by
budget**; V4 remains active and candidate v6 remains unaccepted. No API calls were
made. This is a development contract, not a qualified grader or a new quality score.

## Decision and implemented behavior

Adopt explicit interpretation uncertainty prospectively. When the complete
question/history/answer leaves materially different presentation-order and
action-order readings, retain the entire claim and grade factual support and
citation support as unknown. Do not select a convenient interpretation. A clearly
asserted unsupported sequence instead remains factual unknown / citation missing;
a contradicted sequence remains contradicted / missing. Supported explicit order
and explicit explanation order retain their positive controls.

This resolves the reference *specification* defect: the former contract forced a
single interpretation without a rule deciding between plausible readings. It does
not prove a definitive historical reading. The policy source still establishes
only reporting and payment, not their order. Neither repetition nor agreement
between correlated model calls can supply that missing interpretation rule.

- [V35 contract](../../scripts/quality_eval_contract_v35.py) replaces the ordering
  interpretation in both claims and semantic-review prompts. Evidence boundaries,
  enums, reducers, exact witnesses and independent coverage assessment stay intact.
- [V35 transport](../../scripts/quality_eval_transport_v35.py) builds the three
  requests and processes their responses without changing model, reasoning effort,
  output allowances (8192/4096/4096), or introducing retries. Claims/coverage use
  high effort; review uses medium. This retains the existing reviewer architecture;
  the four-request blind-review prototype and its paid pilot remain deferred.
- [Versioned references](../../data/evaluation/conversation-continuation/ordering-contract-v2/references.json)
  retain all 24 original cases, exact inputs, source/citation evidence, ordering,
  and all three reviewer probes. Only the disputed case's two support expectations
  change to unresolved in this successor. Its old rationale is explicitly marked
  historical; this document and the amendment field provide the new rationale.
  All original files, labels, results and ledgers remain unchanged.
- Eight supplemental controls cover explanation order, explicit either-order
  permission, supported/invented/reversed prerequisites, omitted prerequisites,
  incomplete ambiguous order and complete ambiguous order. Seven reuse the
  completed v1 examples; the eighth adds complete-answer uncertainty. The successor
  calibration therefore requires **32/32 reference matches plus 3/3 probes**.
- [Reference loader/comparator](../../scripts/conversation_ordering_v2.py) rejects
  undeclared changes to the original cases or probes, verifies historical source
  hashes, and checks the disputed intermediate claim and fact labels explicitly.
  A superficially matching overall failure cannot hide a wrongly graded claim,
  an invented uncertainty witness, or a fee falsely labeled covered.

For `answer-injection-award-pass`, reporting stays covered; the nine-credit fee
stays missing. Factual/citation dimensions become unresolved under the new
convention, while completeness and response behavior **fail**, so overall **fails**.
The injected evaluator instruction still has no authority. For the new complete
ambiguous answer, completeness passes but overall is **unresolved**, never success.

A correct grader identifying uncertainty may match its calibration reference;
that is not credit for the supplied answer and not a resolved interpretation.
The final 48/60 target still counts only successful answers. No unknown outcome,
unsupported citation, permission disclosure or mandatory safety failure is waived.

## Whole-path budget decision

[Reproducible reconciliation](../../scripts/conversation_completion_budget_v2.py)
replays the complete cache-aware ledger prefix and produces the
[saved assessment](../../data/evaluation/conversation-continuation/ordering-contract-v2/completion-budget.json).
No credential access, services or network are required.

| Item | USD |
| --- | ---: |
| Cumulative ceiling | 14.88536776 |
| Accounted, including retained unknown-request hold | 9.31867776 |
| Retained hold (not released) | 0.14820250 |
| Remaining authorized headroom | 5.56669000 |
| Mandatory final-measurement launch floor | 4.50000000 |
| Available above that floor | 1.06669000 |
| Diagnostic 16 cases + 3 probes, empirical estimate | 0.75984250 |
| Calibration 32 cases + 3 probes, empirical estimate | 1.19941125 |
| Fresh 16-case confirmation, historical proxy | 0.52179550 |
| Qualification estimate | 2.48104925 |
| Qualification plus final launch floor | 6.98104925 |
| Estimated gap against remaining headroom | 1.41435925 |

The diagnostic estimate reuses the complete V34 diagnostic receipt total.
Calibration extrapolates V34's 66 requests / USD0.79960750 to 99 requests for
32 cases and three probes. Confirmation uses the prior 48-request V25 run as an
optimistic proxy, not reused qualification evidence. Different prompts, reasoning
and fresh inputs may cost more. These are receipt-derived estimates, not current
price quotes, guaranteed costs, mathematical minimums or new spending allowances.

The known diagnostic and calibration full-output conservative reservations are
USD7.0032525 and USD13.6527950 respectively. These are deliberately distinct from
expected settled costs; rolling reservations historically permitted lower actual
spend, but cannot make the new whole-path funding assessment pass. No allowance is
reduced to force a fit. No optimistic new cache discount is assumed.

The fresh 60-case final still requires application execution and 180 grading
requests, with the existing maximum of 32 application calls per case. Its exact
future inputs and cost cannot be computed before qualification, runtime freeze,
isolated authoring and validation. USD4.50 is a launch floor, **not** an upper bound
or guarantee of completion. Even using that floor rather than an added contingency
already exceeds the authorized budget. No focus, repair, pilot or retry is included.

**Decision: do not start paid execution.** Preserve all USD5.56669000 of headroom
and the held reservation. No top-up is requested or assumed. Under the user's fixed
budget, floor, allowances and quality gates, there is no credibly funded acceptance
path. The smallest actionable scope decision is to close this delivery as an
implemented but unaccepted candidate with V4 retained. That is the recommendation;
it is not Phase 73 completion or a replacement quality claim. Requiring accepted
activation would require revisiting a stated constraint; USD1.41435925 is only an
estimated gap, not an offer or assurance that additional money buys acceptance.

## Verification, custody and remaining gates

Acceptance for this offline work: usable versioned contract/transport/reference
comparison; original coverage and evidence preserved; negative controls for
uncertainty, omissions, citations, reviewer disputes and safety; entire-path budget
reconciled; reviewed changes committed and pushed. No App/API, schema, database,
frontend, default-model or provider configuration changes are part of this unit.

Verified on the intended working diff:

- `python -B -m unittest scripts.test_conversation_ordering_v2 scripts.test_procedural_ordering_review scripts.test_conversation_blind_review_design`:
  **25/25**, network blocked, including nine new checks. Synthetic reducer and
  transport responses demonstrate software behavior, not semantic model accuracy.
- `python -B -m scripts.conversation_completion_budget_v2 --check`: exact receipt
  reconciliation matches the saved blocked assessment.
- `python -B -m scripts.conversation_grader_v11 report grader-v34-calibration`:
  unchanged early stop, **21/22**, 66 calls, USD0.79960750; no new result or score.
- Historical hashes, the full retained ledger prefix and the unrelated request-log
  hash remain unchanged. The log remains unstaged; tests do not use it.
- All five added Python modules compile, 243 local documentation links resolve,
  and the complete intended diff passes `git diff --check`.

Reuse the prior 14/14 application development inspection; it is not a final score.
Application regression/build and service startup are skipped because application
files/configuration did not change. All paid verification is skipped at the
whole-path budget gate, before any request. No fresh holdout is authored prematurely.

Still required for acceptance: source-reviewed V35 diagnostic 16+3, calibration
32+3, then freshly isolated authored/validated 16-case confirmation after freeze;
a separate fresh frozen 60-case final reaching 48/60 with every safety/citation
gate; accepted activation, results and limitations. Old V34 results cannot satisfy
the new version. Successor live orchestration/freeze adapters are deliberately
not launched or presented as qualified; the frozen V34 confirmation/final tools
remain unchanged. No further automatic paid experiment follows this delivery.

Review disposition: the complete intended diff, added references and budget were
reviewed; exact original input/probe and receipt preservation are executable checks.
The remaining semantic limitation is unmeasured model compliance with the new
contract, which only full qualification can establish. No external/human reference
adjudication is claimed. External call count/cost for this work: **0 / USD0**.
