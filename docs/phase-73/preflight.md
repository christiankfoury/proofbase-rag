# Phase 73 preparation and declared measurement protocol

Status: contingent preparation. Tooling currently binds v17, which failed full
calibration and cannot be used. Advance bindings to a qualified successor and
reverify before runtime freeze or isolated holdout authorship. No fresh application
score exists yet.
Phase 72's reviewed runtime fixes and relevant passing regression evidence remain
unchanged; this work versions the measurement tooling and local environment.

Goal: one complete, auditable current-runtime measurement on 60 newly authored
synthetic cases, then consistent README, methodology and Dev/Admin publication.
The case distribution and complete-response standard remain unchanged. Target:
at least 48/60; unresolved judgments receive no credit. Zero observed unauthorized
retrieval/disclosure is mandatory. Quotation fidelity is reported separately.
Publish a valid miss honestly. No post-exposure expectation edits, selective
retries or runtime tuning on this suite.

The existing local PostgreSQL database was cloned into `proofbase_eval_phase73`
with CREATE DATABASE TEMPLATE, refusing an existing target. The source is retained.
The clone has 32 documents, 247 chunks and 247 embeddings; local API health is 200.
Runtime logs, uploads and quarantine use the ignored `local-runs/current-phase73`
directory. Telemetry is off. Test-process tenant admission is USD 10; application
defaults are unchanged. SDK retries are explicitly zero in settings and intercepted
clients. The pre-run fingerprint binds configuration, model settings, corpus/index
row hashes, roles, projects, departments, memberships and prompts.

Freeze all runtime/evaluator source and dependencies, prompts, corpus, configuration,
index, passing evaluator evidence, authorization and complete ledger prefix before
fresh authoring. Separate author and validator receive only neutral contracts,
freeze and corpus. The validator independently checks all 60 cases and quotes,
roles, scope and expected behavior. Root checks historical lexical overlap without
showing old questions to either agent. Seal hashes before the one live attempt.
These are procedural context boundaries in a shared workspace, not technical
isolation or human labeling.

## Calls, token bounds and cost accounting

Each case permits at most 32 application calls including embeddings, assessment,
decomposition, generation, validation and upload fixture indexing, plus three
grader calls. This is a conservative allowance, not a planned retry count. The
current request path normally needs substantially fewer calls; deterministic paths
can make none. Whole-run maximum: 2,100 calls. Every provider request has its raw
body, raw response, usage, model identity and charge saved durably. Unknown outcomes
retain the reservation and stop work. Existing requests cannot be overwritten.

Application requests are text only, limited to 131,072 conservative input tokens
(serialized UTF-8 bytes plus framing) and 2,048 output tokens. Grader uses the
unchanged GPT-5.4 snapshot, medium reasoning, 4,096 output tokens and at most
272,000 conservative input tokens, below its higher-rate context tier. Calls are
checked before issuance. The deliberately conservative whole-run reservation is
**USD 240.4139520**, assuming every permitted request uses its maximum at the most
expensive applicable rate. This is neither expected spend nor a purchased budget.
The removed local USD 5 cap is not reintroduced. Account budget remains
user-reported and unmodified. All historical calls and their conservative cost
floor are retained; application, embedding and grader charges remain distinguishable.

Pricing checked in official documentation on 2026-09-29: [GPT-4.1 mini](https://developers.openai.com/api/docs/models/gpt-4.1-mini)
USD 0.40 input / 1.60 output per million; [text-embedding-3-small](https://developers.openai.com/api/docs/models/text-embedding-3-small)
USD 0.02 input per million. The validated evaluator uses [GPT-5.4](https://developers.openai.com/api/docs/models/gpt-5.4)
USD 2.50 input / 15.00 output per million at the bounded context size. Reasoning
output is included; no cached-input discount is assumed. Estimates are token-cost
accounting, not an invoice reconciliation.

## Verification and publication gates

Eight focused no-network tests verify mixed chat/embedding settlement, immutable
historical floor, unknown-outcome reservation and stop, pre-call token bounds,
duplicate-path refusal, per-case auxiliary-call bounds, SDK retry disabling and
output caps, raw-evidence tamper detection and pre-execution custody failure. Scoped compilation and isolated local health/role/model checks pass.
An initial tuple/list serialization mismatch in declared pricing was found and
fixed by these tests before execution. No application behavior changed.

The offline reporter must reconstruct all grade requests, responses, intermediate
claims/facts, reducers, call costs and case intervals. Source inspection of all
fresh outputs remains mandatory before a validated score is published; schema
validity alone is insufficient. Keep invalid/disputed dimensions unresolved and
include latency and full auxiliary cost. A mismatch, permission/scope violation,
unknown call, quota error or compromised custody stops dependent execution.
Report remaining limitations and any incomplete denominator explicitly.

Preparation review: the full new runner, ledger, custody/replay code and neutral
contracts were inspected before commit. `python -m unittest
scripts.test_quality_confirmation_v17 scripts.test_phase73_eval` passed all 12
focused tests; scoped Python compilation passed. Confirmation tooling preserves
16/16, all intermediate fact statuses, separate validation and one-shot custody.
No freeze, authoring, confirmation or runtime measurement is implied by this
preparation commit. Application checks are reused from unchanged Phase 72 code.
