# Decision: separate scenario inputs from policy evidence

2026-10-02; reviewed code: `572966bf`. **Design only.** Implementation, paid
diagnostics and prompt changes are paused; no API calls or evaluator changes.

**Recommendation:** if separately authorized, implement a narrow source-backed
scenario calculation first. Carry input/rule provenance into deterministic
rendering; a number appearing in the question never makes it policy evidence.

## Earliest errors and why previous changes were insufficient

In the preserved [live-v2 traces](../../data/evaluation/application-reliability-live-v2/run),
request routing and retrieval supplied the needed evidence. These are application failures.

| Failure | Earliest demonstrated error → final consequence | Why earlier fixes did not settle it |
| --- | --- | --- |
| Scenario number, case 01 | [Call 002](../../data/evaluation/application-reliability-live-v2/run/raw/call-002.json) labels “purchase amount … USD 217” as supported by FIN-001, although it comes from the user. This is an attribution error, not the cause of abstention. Call 003 correctly applies the category's USD 300 limit; [call 004](../../data/evaluation/application-reliability-live-v2/run/raw/call-004.json) omits `numeric_context`, causing the provenance contract to downgrade the answer. | Numeric extraction fixes addressed token boundaries. v3 deferred request numbers to model-authored provenance; v4 enumerates obligations but still makes the model reconstruct their role and quote. Neither establishes a separate scenario-input object before assessment. Missing provenance still fails closed, correctly. |
| False premise, case 02 | [Call 007](../../data/evaluation/application-reliability-live-v2/run/raw/call-007.json) recognizes the actual USD 300/1,500 rules in its explanation but marks required facts unsupported. Normalization derives insufficient; generation receives no chunks and returns not_found. | `contradicted` helps only if the model selects it. Prompts still ask the same model to decide whether evidence answers the question. Promoting unsupported-with-ID would revive an unsafe shortcut: a topical reference is not proof. Reading corrections out of free-text `missing_information` is also not a grounding contract. |
| Geographic scope, case 03 | Evidence assessment in call 012 correctly finds the comparison answerable. [Generation call 013](../../data/evaluation/application-reliability-live-v2/run/raw/call-013.json) joins longer changes and outside-Canada/US work, then applies “such requests are … ambiguous” to both. HR-003 attaches ambiguity only to outside-region requests. Call 014 wrongly accepts that sentence. | v3 prevents omitted/rewritten sentences, but a sentence can contain several differently conditioned predicates. v4 adds another model judgment, `preserves_scope`; checking that the field exists cannot prove that judgment. |

**Evidence limit:** v4 has not been tried live. The
[offline replay](../../data/evaluation/reliability-remediation-v3/after.json)
rejects missing fields, not proven meaning errors. The
[legacy-contract control](../../data/evaluation/reliability-remediation-v3/after-legacy-contract.json)
still accepts the geographic error. Mocked judgments prove routing, not model accuracy.

## Smallest structural changes, in order

**1. Scenario amounts: bounded calculation, explicit provenance.** Add an internal
decision record: current-request span/value/currency, uniquely matched category,
authorized source row/span, limit/operator/approval rule, comparison result.
Never cite a document for the scenario span. Initially support only explicit
single-purchase, single-currency threshold questions and unambiguous “approval
above limit” table rows. Parse row values, not hard-coded amounts/documents/cases;
use decimal arithmetic, preserving sign, currency and units.

A declared grammar must cover the complete request and distinguish “my purchase
costs X” from “the policy limit is X.” Multiple amounts, quoted policy claims,
unclear categories, conversion, exceptions or unmatched clauses decline this path.
Do not expand a keyword blacklist to force coverage. Verified bindings permit:
“For the amount you supplied, this category's above-limit condition is/is not
triggered.” This does not grant purchase approval or waive other requirements.
Ambiguous applicability still needs model reasoning or clarification.

Place it **after request security and permission filtering, before semantic
evidence assessment**. Preserve source-instruction and citation controls; duplicate
rules, unresolved precedence or unparsed conditions decline the calculation path.
At finalization, recheck spans, authorized citation,
operator and arithmetic. Only the verified template may use source-absent scenario
numbers without model-authored `numeric_context`; generated prose retains semantic
validation. Zero token usage must never establish this exemption.

In the [main callers](../../apps/api/app/main.py),
`_evidence_generation_chunks` empties evidence for not_found, and
`_validate_generated_answer` currently infers code-authored status from token
counts. The [numeric guard](../../apps/api/app/reasoning/post_generation_validation.py)
rejects source-absent numbers in code-authored answers. Bind spans to
`original_question`, not the rewritten question currently passed to validation;
memory cannot supply operands. This additional risk did not cause these memory-free failures.

**2. False premises: reuse supported rule facts, separate truth from answerability.**
For the same bounded table questions, resolve the requested field first and
compare the proposed value/approval rule to that source fact. A mismatch yields
a cited correction. Unknown fields stay unknown; conflicting applicable rows
remain unresolved. Outside that slice, model reasoning must identify the relevant
fact and whether it entails or contradicts the premise. Retain that relation and
its source span separately from answerability; do not collapse contradiction into
an apparently supported premise as `_complete_semantic_decision` currently does
in [evidence assessment](../../apps/api/app/reasoning/evidence_assessment.py).
No blanket override of an insufficient assessment is proposed.

**3. Geographic scope: bind each predicate to its own source condition.** For
cross-policy synthesis, use a small intermediate list of source-backed
condition → consequence items, not one supported label for a compound sentence.
Render distinct items without merging antecedents through “such requests.” Exact
source-span membership, item coverage and rendering can be deterministic;
selecting relevant clauses and interpreting geography, exceptions and entailment
still require reasoning. Do not claim a general natural-language scope checker
or infer that every cross-border case shares the outside-Canada/US ambiguity rule.
Keep this separate from the first scenario implementation.

## Acceptance cases and stopping rule

Use newly authored fixtures and the real assessment → answer → validation callers,
including sync/stream parity. These are future acceptance cases, not test results.

| Area | Positive cases | Negative cases / required boundary |
| --- | --- | --- |
| Scenario, first priority | Synthetic source: stationery approval above EUR 480. Independently worded explicit purchases of EUR 125 and EUR 620 yield below/above comparisons with separate input and policy provenance. EUR 480 does not trigger a strictly-above condition; EUR 1,250 grouping remains exact. | A proposed policy cap of EUR 125 is never a purchase operand. CAD 125, negative/refund amounts, two amounts, a missing category, unsupported units/operators, stale-memory amounts, injected overrides and unauthorized rows never enter the calculation path. Equality never means blanket permission. |
| Correction | A proposed EUR 125 stationery limit is corrected to the authorized EUR 480; a before-purchase approval rule disproves a claimed exemption. | A topical source lacking the field cannot prove a denial. Conflicting rows require resolution; an inaccessible source cannot supply the correction. |
| Scope | Synthetic rule: extended domestic work needs review; outside-region work needs review and remains pending. Render the two conditions separately, preserving personal-device conditions in an interaction case. | Reject “both … remain pending,” omitted qualifiers, fabricated geography, changed may/must, and a true `preserves_scope` label unsupported by the condition binding. Quoting a matching span alone does not prove semantic applicability. |

If later authorized, stop when the captured scenario and new positives require
no model-generated provenance, negatives retain their boundaries, and sync/stream
callers verify the same record. Stop earlier if this needs broad interpretation,
policy hard-coding, extra model calls or weaker guards; report unsupported inputs.
Do not automatically start correction/scope work or paid validation. General
semantic quality remains unmeasured.

Reviewed against traces, sources and callers; links and whitespace checked.
Only this document and tracker pointer change; no tests/builds needed. Historical
evidence and unrelated edits preserved. Calls/cost: **0 / USD 0**; remaining
ledger **USD 3.74777920**, paid work paused.
