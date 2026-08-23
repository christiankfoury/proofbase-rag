# Phase 48: Generalization Failure Remediation And Fresh Holdout

## Purpose

Phase 48 remediates the general mechanisms exposed by the Phase 47 independent holdout without changing, rerunning, or republishing that holdout. Improvement claims must come from the inspectable 70-case development suite and one newly authored, independently reviewed, frozen 30-case holdout.

## Historical Evidence Lock

- The Phase 47 holdout remains frozen at `14/30` and is historical evidence only.
- `data/evaluation/independent-generalization/holdout-v1.json`, its hash, raw result, failure matrix, adjudication, and published report must not change.
- Phase 48 must not execute any Phase 47 holdout case.
- Runtime and evaluator remediation must be committed and pushed before the new holdout is authored.
- The new holdout must use new wording and scenarios derived from the synthetic corpus and this contract, not variants of known Phase 47 failures.

## Root-Cause Workstreams

1. **Evaluator semantics**: distinguish semantic denial from affirmation, require exact numeric agreement for numeric forbidden facts, keep behavior mismatches separate from factual hallucination, and distinguish citation grounding from requested-source completeness.
2. **Clarification boundaries**: recognize missing decision variables by intent and slots rather than exact question strings.
3. **Memory corrections and references**: resolve topics by recency, honor explicit corrections and returns to earlier topics, and keep memory as query context only.
4. **Multi-source coverage**: plan one permission-filtered retrieval query per required policy domain and preserve coverage during merge and citation selection.
5. **Restricted-response taxonomy**: classify restricted intents before generation with generic, non-disclosing refusals while preserving pre-generation permission filtering.

## Evaluation Contract

### Development gate

- Suite: unchanged `development-v1.json`, 70 inspectable cases.
- Aim: `70/70` through general mechanisms and evaluator corrections only.
- Partial development runs are diagnostics; the published result is one full run.

### Regression gates

- Benchmark 1.1 live `/query`: `130/130` pass.
- Permission leakage, restricted citation leakage, and unauthorized chunks reaching generation: exactly `0`.
- Memory as evidence: exactly `0`.
- Existing local Phase 39, 46, and 47 controls must pass.

### Fresh holdout gate

- Suite: 30 cases, authored only after the runtime/evaluator freeze.
- Target: at least `27/30`; `24/30` is reported as meaningful improvement but does not meet the portfolio target.
- Required-source recall: `>=0.90`.
- Behavior accuracy: `>=0.90`.
- Required-fact completeness: `>=0.85`.
- Citation document accuracy: `>=0.90`.
- Factual hallucination rate: `<=0.05`, no more than one flagged case.
- Permission hard gates and memory-as-evidence gate: exactly zero.
- Execute exactly once as a complete suite. Human-adjudicate every failed case and a fixed sample of passes.

## Metric Definitions

- **Required-fact completeness** uses deterministic canonical token coverage plus explicit yes/no polarity handling. It is a diagnostic, not semantic proof.
- **Forbidden-fact violation** requires the answer to assert the forbidden proposition. A quoted, negated, superseded, or numerically different proposition is not an assertion.
- **Factual hallucination** means an asserted forbidden fact or a substantive factual claim returned by the generator as unsupported. A response-type mismatch or a validator's weak-support diagnostic is reported separately.
- **Citation document accuracy** remains strict requested-source completeness for answer cases. Emitted-citation grounding is reported separately and cannot substitute for missing required sources.

## Cost And Execution Budgets

- Each development or benchmark answer run: maximum `$2.00`.
- Each embeddings-only permission run: existing guarded runner budget and configuration.
- One-time fresh holdout: maximum `$2.00`.
- Prefer local tests, dry runs, and targeted development diagnostics before full live runs.
- Disable optional telemetry for evaluation commands so only required OpenAI calls occur.

## Freeze And Isolation Procedure

1. Implement and locally verify general remediation.
2. Run the complete development and regression suites.
3. Commit, review, and push the runtime/evaluator freeze to `main`.
4. Record hashes for protected runtime paths, corpus, development suite, and original Phase 47 holdout.
5. Give an isolated author only the corpus, schema, category distribution, and this contract.
6. Give a separate reviewer the candidate suite, corpus, schema, and contract; the reviewer must not alter runtime code.
7. Hash and commit the approved holdout without executing it.
8. From a clean tree, verify no protected runtime/corpus changes since the freeze and execute all 30 cases once.
9. Adjudicate, publish honest results, commit, review, and push.

## Stop Conditions

- Do not claim improvement from rescoring the original holdout.
- Do not weaken a permission, citation, completeness, or hallucination threshold to reach a target.
- Do not add question IDs, expected answers, exact holdout wording, or case-specific rules to runtime code.
- If the fresh holdout misses a target, publish the miss and queue another phase with another future holdout; do not rerun this holdout.
