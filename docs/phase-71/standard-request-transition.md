# Standard-request transition

The user rejected the waiting time of Batch execution on 2026-09-30. The active
roadmap now defaults to standard synchronous requests. The pinned model, evaluator,
all scoring/custody gates and USD 10 additional ceiling remain unchanged. Cost
savings continue through cached-input settlement and reuse of unchanged passing
development evidence, not queued execution or a weaker evaluator.

The existing Batch was still in_progress when checked. One cancellation request
was accepted, returning cancelling with 23 completed, zero failed and 32 total
requests. The request and raw provider response are preserved beside the original
submission. Do not cancel twice or resubmit the Batch. Do not claim cancelled or
zero charges from a cancellation request. Wait for the terminal provider state,
collect all partial results and audit costs before replacement execution.

The official [Batch guide](https://developers.openai.com/api/docs/guides/batch)
states that cancellation can take up to 10 minutes while in-flight requests finish.
The observed job has remained cancelling beyond that documented window. No
terminal output files have been exposed at the latest check; no completion-time
promise is justified. Provider status is read by the existing Batch ID only.
This is cancellation of work already submitted, not another queued evaluator
stage. No new Batch stage or reviewer wave will be submitted.

Goal: resume the strict evaluator gate through standard requests after safe outcome
resolution. Acceptance: all partial evidence preserved; no unknown spending,
duplicated completed request or cap increase; unchanged frozen semantic behavior;
reviewed/tested synchronous successor before fresh isolated confirmation when
needed; exactly 16/16 judgments and zero semantic findings before Phase 73. Preserve
the cancelled suite as historical if its one-shot execution is incomplete. No
selective reruns, reference edits or readiness inferred from partial outputs.

This work unit changes execution policy and cancels queued work. It does not
change application behavior or declare evaluator readiness. The existing standard
v18 transport already defines synchronous request bodies and parsing; the new
shared additional-budget wrapper must retain these exact bodies and usage/cost
receipts. Live successor execution remains blocked until cancellation is terminal.


## Prepared synchronous implementation

`quality_standard_grading.py` reserves each direct request against the shared
additional envelope, preserves the raw response before parsing, prices cached
input correctly, and verifies exact requests/settlements offline. It refuses
pending predecessors, existing attempts, SDK retries, excess calls, unsafe paths,
unknown outcomes and budget overruns before further provider calls.
`quality_confirmation_standard_v18.py` reuses the unchanged v18 request builders,
parser and reducer, with the same independent 16-case custody and 16/16 source
inspection gate. Its maximum is 48 standard requests, each output-capped at 4096,
with conservative whole-confirmation headroom checked before execution.

The future standard policy/journal preserves both prior reservations and requires
terminal cancellation plus complete partial-output accounting. No policy is
activated while the provider still reports cancelling. The cancelled suite will
remain historical; a fresh post-freeze suite is required for replacement, with
no paid repetition of unchanged development calibration.

Verification: nine no-network tests pass. They replay all 72 saved calibration
request bodies/parsed outputs and a full 16-case, 48-request confirmation, preserve
failed development gating, reject duplicate attempts, enforce no-provider-call
budget/retry stops, and preserve unknown-call reservations. Compilation passes.
These are transport tests on existing development evidence, not new model results
or evaluator readiness. No application behavior or scoring standard changed.

Commands: `python -m unittest scripts.test_quality_cost_standard
scripts.test_quality_standard_grading scripts.test_quality_confirmation_standard_v18`
(9 passed), plus scoped Python compilation and `git diff --check`.
The cancellation tests independently replay raw token usage, reject missing or
altered outputs and nonterminal state, retain both full historical reservations,
and block spending beyond the unchanged shared ceiling. No frontend or application
build is required for this transport-only change. Existing v18 development
calibration and Phase 72 tests are reused; no paid recalibration was performed.

Pre-commit review covers the full intended implementation, neutral briefs,
workflow amendment and cancellation evidence. Remaining limitation: standard
policy activation, freeze, isolated authorship/validation and paid confirmation
cannot occur until the provider exposes the terminal cancellation receipts.
Next read-only action: `python scripts/quality_confirmation_batch2_v18.py collect
--wave initial --allow-external-ai`. No new approval or billing change is needed.


## Terminal reconciliation and activation

The provider is now terminal cancelled. Its output and error files contain all
32 request identities: 23 successful responses and nine HTTP 500 server_error
responses with no usage. The successful-response cache-aware estimate is USD
0.11908150. Cancellation took 25 minutes 8 seconds according to provider timestamps,
longer than the documented window. No reviewer wave was sent.

The successor policy binds the original plan, cancellation, terminal state, both
raw files, extracted successful responses and predecessor journal. The accounting
validator independently recomputes successful usage and recognizes only the
observed server-error receipt shape, retaining the full reservation rather than
inferring unreported usage is zero. Both historical reservations remain accounted
at USD 2.80849875 total. The old attempt is incomplete and permanently historical.
No model outputs were used to change evaluator semantics or new reference labels.

Verification: four cancellation-accounting tests pass, including a new terminal
server-error receipt and rejection of ambiguous usage. The other six transport
checks remain applicable from e11dfe1; total ten tests. Live policy/raw accounting
validation passes against actual terminal receipts. Complete intended diff review
found no remaining blocker to freezing the unchanged standard evaluator. No paid
confirmation, new quality score or Phase 73 readiness is claimed yet.

Standard evaluator freeze binds 60 code/test files at preparation commit e335105,
the unchanged passing v18 development gate, standard policy and both neutral
briefs. It precedes all v10 authorship. No paid request was issued to freeze.
