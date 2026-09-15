# Phase 68 development and measurement gates

Phase 67 is committed and pushed as `a7aa503`. The runtime fixes pass 46 local
tests, historical evidence checks, benchmark validation, compilation and the
source secret scan. Phase 39/46 regressions also pass with external calls blocked.

The user approved a USD 2.00 cumulative token-cost ceiling on 2026-09-14. The new
ledger preserves every previous call, records the earlier USD 0.75 limit and the
explicit increase, and rejects changed historical prefixes. Old ledgers and
budget code remain unchanged. New work uses an isolated local database,
`proofbase_eval_phase68`, and separate logs/uploads. No cloud resources are used.

## Grader development

`answer-dimensions.v6` uses the same two-call dimension rubric with pinned
`gpt-4.1-2025-04-14`, replacing the mini grader for this new experiment only.
Its 18 visible fixtures pass on the first attempt, costing USD 0.07466. The
fixtures cover the previous 12 challenges plus access refusal without citations,
appropriate not-found language, retrieval gaps versus factual contradiction,
an omitted purpose requirement, UTF-8 apostrophes, and true uncited answers.
These are author-designed calibration examples, not independent grader accuracy.

Pricing was checked against the official
[GPT-4.1 model documentation](https://developers.openai.com/api/docs/models/gpt-4.1):
USD 2 input and USD 8 output per million tokens. Cached discounts are ignored in
the estimate. The application still uses its existing mini configuration.

All text input and artifacts are explicitly UTF-8. Invalid grades remain
unresolved. The one-shot runner records the actual grader requests and raw
provider responses before parsing, so truncation and validation failures remain
inspectable. A grade failure is never grounds to retry an application case.

## Live development findings

Four new development probes returned HTTP 200 with no recorded unauthorized
evidence flags. Cumulative estimated cost after calibration and probes is
USD 0.65385488, leaving USD 1.34614512.

- Memory correction: the rewritten question preserves wellness funding and its
  contrast with parental leave; retrieval includes the wellness policy; evidence
  assessment marks the expiry fact supported. Generation nevertheless returns
  not-found. This is a remaining over-abstention failure, not a successful answer.
- Combined retirement-matching and collaboration-hours request: answers both
  facts with the required sources (3 months; Monday-Thursday 10 a.m.-3 p.m.).
- Employee request for the privileged-access runbook: refuses access.
- Unpublished company bicycle-shop discount: returns not-found.

The first result is retained openly. No new special-case answer was added to
force this development probe to pass. The runtime is ready to measure with this
known limitation, not certified free of incomplete answers.

## Fresh holdout protocol

Freeze the runtime, evaluator, corpus, indexed data and configuration before
authoring. Use 60 new cases with the previous category mix, separate isolated
author/validator passes and a lexical-overlap check over all historical artifacts
and new development questions. Record authorship as agent-assisted, not human.

Measure each case once. Keep six dimensions separate, with unresolved and
not-applicable counts. Report permission/scope flags separately. Do not collapse
the new result into the historical 55% protocol or claim a controlled before/after
gain across different question sets. Provider output is not deterministic;
replay means verification of saved evidence, not identical fresh generation.

The budget guard reserves a conservative bound before each call and retains
unknown-outcome reservations. Observed calibration cost plus prior application
costs indicate approximately USD 0.50-1.10 for the holdout; this is an estimate,
not a guarantee. Any stop leaves an incomplete experiment rather than hidden
retries or a new budget. No user review will be fabricated.
