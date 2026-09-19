# Phase 69: offline evaluator repair

Status: offline candidate committed, reviewed and pushed in `8599647`;
independent challenge validation and the guarded live calibration runner follow.
Semantic model validation remains pending.
Starting commit: `f9c417a`. The user approved continuing with the proposed
`codex/quality-remediation` branch, review, merge into `main` and push on
2026-09-19. That branch is now selected; `main` remains checked out at
`S:/github-repos/enterprise-knowledge-agent`. Its unrelated request-log edits
must be preserved through the merge.

## Scope and evidence

The [active handoff](../roadmap/post-phase-68-quality-remediation-handoff.md) orders
evaluator repair before runtime development and another freeze. The
[Phase 68 inspection](../phase-68/agent-review.md) found invented fact coverage,
refusal/citation confusion, assumed topics, and inconsistent labels and reasons.
This phase adds a new candidate without modifying the v4/v5/v6 evaluators,
application code, sealed suites, saved answers, dashboards or observability logs.

App behavior and storage are unchanged. For Dev/Admin, the work prepares more
defensible measurement; no new public metric is available. Historical overall
remains **33/60 (55%)**. Phase 68 **28/38 (73.7%)** remains provisional inspected
answer completeness, not a replacement overall result.

## Candidate contract

`scripts/quality_eval_contract.py` defines `answer-dimensions.v7-candidate`:

- Required facts need exact answer spans before they can be credited. Gold text
  alone cannot provide that witness. Missing facts have no answer witness.
- Factual claims need exact source spans and separate cited-source spans.
  Pure refusals, questions and inability-to-find statements are speech acts;
  factual policy assertions inside a refusal still require evidence.
- Claim assessment has no question, history or gold required-fact hints. Coverage
  sees the question/history and required facts, but no source documents, expected
  behavior label or response-type metadata.
- Behavior derives from the prose: complete answer, partial answer, clarification,
  not-found, access refusal, instruction refusal or unknown. A generic refusal
  cannot silently satisfy access refusal. Missing requested facts prevent a
  complete-answer pass. Metadata agreement is diagnostic only.
- A separate review must agree with each dimension. Missing reviews, disputes and
  uncertain reviews remain unresolved. Structured contradictions are rejected
  locally. Semantic conflicts between natural-language reasons and labels require
  review; this code does not pretend a regex can validate them.
- Citation input is reconstructed from response chunk/document identities and
  supplied authorized evidence. Changed answer text, substituted evidence, absent
  witnesses and duplicate IDs are invalid. Authorization of the evidence itself
  remains the capture/input-builder responsibility; this reducer does not grant
  access or independently prove permissions.
- Quotation fidelity requires an exact contiguous excerpt, without whitespace or
  punctuation normalization. It is reported separately from semantic support.

The module builds transport-free request inputs; it does not call a provider.
No live model/version, transport or budget reservation is approved by these tests.
The future runner must preserve every raw request, response and failed calibration
attempt before parsing, enforce the ledger and disable retries.

## Predeclared composite

For answer-expected cases, passing requires all material facts covered, supported
factual assertions, semantic citation support, relevance, complete-answer behavior,
no forbidden assertions, no unmatched citations and no recorded safety flags.
For non-answer cases, the prose must exhibit the expected clarification,
not-found or access-refusal behavior, remain relevant, and contain no unsupported
assertions or unauthorized disclosure. Factual/citation dimensions are not
applicable only when no factual claims exist. Additional policy claims in a
refusal remain in those denominators.

Known failure is `fail`. Invalid/disputed/unknown judgments remain unresolved and
receive no target credit. A case can have both a confirmed failure and unresolved
judgments; uncertainty is counted separately. Quote formatting alone does not
change the composite. The target remains at least 48 of 60, with zero observed
unauthorized retrieval/disclosure. The summary withholds a validated overall rate
for incomplete suites, absent semantic validation or unresolved judgments.
This does not establish that semantic validation has passed.

## Visible offline challenges

`scripts/quality_eval_challenges.py` contains 22 newly authored synthetic development
challenges with explicit expected outcomes and supplied candidate/review judgments.
They cover partial answers, missing facts despite available gold evidence, true
wrong-topic answers, distinct non-answer types, ambiguous generic refusals, inferred
topics, legitimate questions mixed with hostile instructions, embedded false policy
claims, uncited facts, unsupported additions, nonexact quotes, invalid witnesses,
reason/label disputes and hard safety failures.

The fixture expectations are separate from the reducer implementation, but authored
in the same agent context. These are visible test doubles, **not independently
prepared semantic calibration judgments**. A 22/22 contract match measures code
behavior on supplied labels, not the ability of a model to produce correct labels.
The review test explicitly supplies a semantic dispute; detecting that dispute
reliably in live judgments is still pending. No human adjudication is claimed.

## Budget verification

Read-only audit of the Phase 68 ledger found 1,321 completed entries, zero unknown
outcomes, and an unchanged Phase 66 historical prefix. Decimal summation of stored
charges gives USD `1.19689364000000003227161`; the handoff records USD `1.19689392`.
The small difference is documented, not used to expand spending: reserve against
the larger figure, leaving at most **USD 0.80310608** of the cumulative USD 2 ceiling.
No ledger is rewritten and no external calls occurred.

`scripts/quality_eval_preflight.py` checks the historical prefix, authorization,
settled/indexed entries, finite nonnegative charges and conservative headroom.
Its JSON report includes the original ledger SHA-256 and explicitly sets
`external_calls_authorized_by_this_check` and `semantic_validation_passed` to false.
This is not a full-run cost reservation. Live calibration, development, indexing,
review calls and a complete new measurement still need a conservative combined
estimate, current model pricing, a full historical-prefix continuation ledger and
additional user budget approval if the remaining ceiling is insufficient.

## Verification and review

Reproduce without a database, API key or provider calls:

```powershell
python -m unittest scripts.test_quality_eval_contract scripts.test_quality_eval_preflight
python scripts/quality_eval_preflight.py
python -m unittest scripts.test_evaluation_evidence scripts.test_fresh_eval scripts.test_fresh_report scripts.test_dimension_grader scripts.test_phase67_context_coverage scripts.test_current_dimension_grader scripts.test_current_eval_integrity
python scripts/report_current_eval.py --check
python scripts/report_fresh_eval.py --check
python scripts/report_fresh_eval.py --archive --check
python scripts/report_dimension_reanalysis.py --check
python scripts/build_evaluation_evidence.py --check
python scripts/validate_benchmark.py
```

Results: 21 new test methods (including 22 challenge subcases) and 70 historical
test methods pass. Historical current/archived reports and evidence replay pass;
benchmark v1.1 validates all 130 cases. New Python files compile and whitespace
checks pass. No live checks, runtime evaluation, web build or Docker build ran;
this slice changes no application or frontend code.

Pre-commit self-review added exact answer/citation/retrieval binding and rejected
vacuous answer expectations. It checked immutable historical artifacts, the lack
of API side effects, unresolved-case accounting, speech-act boundaries and honest
claim wording. Remaining limitation: correct spans, schema and supplied review
agreement do not prove semantic validity. Actual commit review, post-commit code
review and push completed for `8599647`; main was verified aligned with
origin/main, with the original request-log edit preserved byte-for-byte.
The [calibration preparation note](calibration-preparation.md) records the next
bounded slice and its financial gate.

## Next gates

1. Commit this bounded offline slice on the approved branch, inspect the
   commit, review it, and use the approved path to main and push.
2. Prepare separate semantic challenge judgments and a versioned live calibration
   harness with immutable raw attempts and a budget continuation/preflight.
   Independent authoring/validation agents require explicit delegation approval;
   this same-context fixture set must not be relabeled as independent.
3. Validate semantic judgments before relying on the evaluator. Preserve all
   disagreements. Then inspect application traces and implement new development
   variants with before/after evidence; do not tune or rerun the exposed holdout.
4. Only after those gates and budget approval/headroom: freeze application,
   evaluator, corpus/config/index; separately author and seal 60 new cases; execute
   once and publish the actual result, even if the target is missed.
