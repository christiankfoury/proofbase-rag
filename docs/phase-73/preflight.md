# Phase 73 preparation and declared measurement protocol

Status: qualified v20 and runtime freeze prepared. Development and fresh
confirmation passed with full replay and zero source-inspection findings. The
runtime source is frozen at 8bd72ba1 with 244 files and the local environment;
isolated holdout authoring follows the separate freeze commit. No fresh application
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
row hashes, roles, projects, departments, memberships and prompts. It also binds
the installed Python/package versions and PostgreSQL server/extensions, so a
dependency-file hash alone cannot conceal an environment change. Tenant records
and memberships are included. RLS policies/table flags, runtime-role attributes,
table grants and public function definitions are hashed to detect authorization
metadata drift without publishing credentials or identities.

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
The removed cumulative USD 5 cap is not reintroduced. The newer user-selected
**USD 10 additional** shared envelope overrides this theoretical bound and
reserves each call before issuance; it includes all remaining Phase 71/73 calls.
Account budget remains user-reported and unmodified. All historical calls and their conservative cost
floor are retained; application, embedding and grader charges remain distinguishable.

Pricing checked in official documentation on 2026-09-29: [GPT-4.1 mini](https://developers.openai.com/api/docs/models/gpt-4.1-mini)
USD 0.40 input / 1.60 output per million; [text-embedding-3-small](https://developers.openai.com/api/docs/models/text-embedding-3-small)
USD 0.02 input per million. The validated evaluator uses [GPT-5.4](https://developers.openai.com/api/docs/models/gpt-5.4)
USD 2.50 input / 15.00 output per million at the bounded context size. Reasoning
output is included; reservations assume uncached input. New settlement and replay
use returned cached-token counts (GPT-4.1 mini USD 0.10 and GPT-5.4 USD 0.25 per
million). Estimates are token-cost accounting, not an invoice reconciliation.
[Cost reduction](../phase-71/spending-reduction.md) preserves sequential runtime
safety stops; the user-selected standard-request path avoids Batch waiting.

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
scripts.test_quality_confirmation_v18 scripts.test_phase73_eval` passed all 12
focused tests; scoped Python compilation passed. Confirmation tooling preserves
16/16, all intermediate fact statuses, separate validation and one-shot custody.
No freeze, authoring, confirmation or runtime measurement is implied by this
preparation commit. Application checks are reused from unchanged Phase 72 code.

Additional pre-freeze review closed the tenant/authorization-metadata gap in the
older fingerprint. Read-only local verification found one tenant, seven tenant
memberships, 22 RLS policies, 26 table flags, one runtime role, 286 table grants
and 126 public functions. Two reads and a post-health read produced identical
fingerprints. `/health` returned 200; all five declared business roles have the
expected Northstar membership. No query, external API call or database write was
used by this verification. Scoped compilation passed; the SQL uses fixed catalog
queries and binds the configured runtime role as a parameter.


## Local accounting handoff preparation (2026-09-30)

The Phase 73 gate now points at the sealed Batch confirmation's complete replay
and source-review readiness. That confirmation was rejected by provider billing,
so no ledger initialization, runtime freeze or fresh runtime authorship occurred.
No readiness or measurement result is inferred from local tests.

The new historical-prefix reader preserves every original row and its conservative
floor, including the separately audited original quota rejection and its retained
reservation. Only that exact rejected row can be recognized as resolved by the
existing immutable audit; any other unknown remains blocked. A qualifying future
Batch confirmation must contribute all 48 requests, raw hashes and cache-aware
charges, with unchanged historical bytes. Initialization requires readiness first.
This code does not clear the latest Batch reservation or permit its reuse.

Each runtime run saves the shared additional-spend journal. Offline publication
must reproduce its prior Batch entries and every new request reservation and
settlement, reject missing/extra/duplicate entries, and enforce the unchanged
USD 10 additional ceiling. Gold-input construction validates every sealed case's
role access and source quotes before the first application call. Frozen source
inventory includes the accounting helper and tests.

Verification: `python -m unittest scripts.test_phase73_eval_history
scripts.test_phase73_eval` passed 15 tests, including four new interrupted-prefix
checks and shared-journal replay/tamper checks. Scoped `py_compile` passed for all
seven affected scripts. Existing application checks are reused because runtime
behavior, dependencies and corpus are unchanged. No DB or paid call was needed
for these local changes. Full intended diff review found no remaining blocking
implementation issue; live acceptance remains pending external billing and
qualifying evaluator confirmation. The provider rejection and preparation are
committed separately to preserve evidence custody. Unrelated logs stay excluded.


### Successor accounting wiring

Phase 73 now binds the billing-resolved Batch successor and its new policy/journal.
Its cumulative conservative prefix includes the retained USD 1.40344250 rejected
Batch reservation without inventing model calls or modifying either old ledger.
A successful fresh confirmation still must contribute exactly 48 recorded model
requests; its report independently binds both actual estimate and retained amount.
The same USD 10 additional ceiling includes both amounts and all runtime calls.

Review also closed a stop-propagation gap: if shared headroom refuses a request,
the runtime ledger durably marks budget exhaustion before the provider is called.
Application error handling cannot turn this accounting stop into an ordinary
measured abstention. The affected provider-not-called regression passes.

Verification: 15 focused accounting/custody tests passed for the successor wiring;
the cap-stop regression was rerun after the small propagation fix and passed.
Compilation and intended-diff review passed. No runtime freeze or measurement yet.


### Pre-freeze gold-source scope check

Code review found that the shared gold-input builder checks corpus quotes and
frontmatter roles, but not the case's project/department against the indexed
source. The Phase 73 fingerprint now binds active Markdown source paths and their
actual tenant/project/department/roles. Custody validates every required fact
against exactly one authorized frozen source before any application call.
A corpus-correct fact outside the case's scope cannot become evaluation evidence.

The focused custody tests pass, including wrong tenant/project/department/role
and duplicate-source negative controls. Compilation passed. A read-only local
check found exactly 19 Markdown sources, all with complete scope metadata.
This is evaluation preparation; it changes no application answer behavior and
makes no quality claim. The fingerprint will be freshly captured for the later
runtime freeze after evaluator readiness. Full diff review found no open issue.


### Standard-request continuation

The Phase 73 readiness, budget and publication paths now bind the standard v18
confirmation and its successor cost policy. The cumulative prefix preserves all
2,595 original rows, 32 cancelled-Batch receipts, and exactly 48 future qualifying
standard calls. The nine HTTP 500 receipts remain failed with unknown usage price;
their costs are covered by the full retained Batch reservation. Successful partial
usage is shown separately and is not added twice to that reservation. Neither
old journal is rewritten or given readiness credit.

Sixteen focused accounting, custody and gold-scope tests pass with no external
calls. Scoped compilation and full intended-diff review pass. Actual Phase 73
ledger initialization remains gated on complete standard confirmation, raw replay
and clean source inspection; no runtime freeze or 60-case measurement exists yet.
This is preparation with synthetic accounting fixtures, not new quality evidence.


### Contingent v19 accounting chain

Phase 73 now requires the v19 confirmation adapter. Its conservative history will
include all original rows, all 32 cancelled receipts, the failed v18 standard
confirmation and both v19 development stages before the qualifying v19 confirmation.
Exactly 210 standard calls (48 + 39 + 75 + 48) are expected only after all gates
pass. Existing failed/partial evidence remains visible. Actual standard usage is
summed once; successful cancelled usage remains included within its retained
reservation, and failed cancelled receipts have no invented usage price.

Sixteen focused local tests pass, including complete-history preservation and
changed-row rejection. Scoped compilation and full intended-diff review pass.
This is contingent preparation: no evaluator readiness, Phase 73 initialization,
runtime freeze or runtime holdout follows from fixture tests. Current live v19
diagnostic evidence is separate and is not modified by this accounting change.


### Live-grader binding review fix

Review found that the newer readiness adapter had been selected while the runtime
run/report modules still imported v18 grading. Before any runtime freeze or paid
application measurement, the protocol now exports the selected evaluator contract
and transport, and both execution and replay use those exports. The budget uses
the same version's re-exported unchanged reservation primitives. A regression
asserts the runtime version and function binding match the qualification adapter
and that replay uses the identical transport. All three focused custody tests and
scoped compilation pass. This fixes prospective evaluator wiring, not a measured
application defect or published result. No frozen runtime evidence exists yet.


### Contingent v20 qualification and complete history

V19 full calibration failed, so v19 cannot qualify the runtime measurement.
The unfrozen Phase 73 path now uses the v20 readiness adapter, contract and transport
consistently. The future prefix includes all original rows, 32 cancelled receipts,
48 failed v18 standard calls, 39 v19 diagnostic calls, 75 v19 calibration calls,
33 v20 diagnostic calls, 75 v20 calibration calls and 48 qualifying v20 confirmation
calls: 318 standard calls only if every remaining stage completes and qualifies.
A partial or failed stage cannot initialize measurement. Historical actual costs
and retained reservations remain separate and are summed without duplication.

Nineteen offline tests pass across the contingent confirmation runner, history,
budget, custody and report paths. This includes full saved-response replay, stop
before loading fresh content when development is unready, shared-budget prevention
before provider invocation, evaluator binding and changed-prefix rejection.
Compilation and complete intended-diff review pass. No runtime freeze, holdout
authoring, application measurement or evaluator readiness is claimed by these tests.
The active diagnostic is separate; this preparation does not modify its code or
inputs. No new paid call was needed for this work unit.


### Qualified evaluator and runtime freeze

V20 qualification is pushed as 8bd72ba1: 24/24 + 3/3 full calibration and fresh
16/16 confirmation, all raw/cost replay and source inspection clean. The final
confirmation cost USD 0.5213645; full shared additional accounting USD 5.92715325,
leaving USD 4.07284675 under the unchanged USD 10 ceiling. No new cost authority
is inferred. Per-call reservations may stop the one runtime run if it exhausts
that headroom; a partial run cannot be reported as a complete score.

The complete immutable accounting prefix contains 2,945 historical rows: all
2,595 original attempts, 32 cancelled Batch receipts and 318 standard evaluator
calls. Prior conservative cumulative accounting is USD 16.78285402, with held
reservations retained and cancelled successful usage not double-counted. The
successor ledger is initialized and unused; no Phase 73 paid request exists.

The runtime freeze binds 244 committed files at 8bd72ba1, exact installed package
and PostgreSQL metadata, corpus/index, roles/scopes, qualified evaluator evidence,
Phase 72 development evidence and full prefix provenance. Current and committed
file inventories agree. The existing proofbase_eval_phase73 database has 32
documents and 247 chunks/embeddings. Read-only /health and /ready are both 200.
Reuse the 19 unchanged focused tool checks and Phase 72 application regressions;
no dependencies, corpus or application behavior changed since that evidence.
No frontend build is needed before publication changes. Next: isolated fresh
60-case authorship, independent source/role validation, overlap checks and seal.

### Fresh suite and pre-execution seal

The separate author and validator completed 60 cases across the nine predeclared
categories. All 136 required facts have exact corpus quotations and authorized
frozen source scope. Independent validation accepted every case with no unresolved
finding; root inspected the complete case references, source corpus and validation
reasons. Mechanical overlap against 877 historical unique questions found no hit
at token Jaccard 0.8. This checks lexical reuse, not statistical independence.

The suite has 38 expected answers and 22 expected non-answers. All five business
roles and 19 corpus documents are represented, including five allowed/denied role
pairs and two novel foreign-project upload fixtures. All cases use Northstar scope
with no department restriction; no department-only coverage is claimed. Isolation
is procedural between agents, not expert human review or technical sandboxing.
The author and validator disclose supplied standing instructions and freeze metadata.
No application output informed authorship or pre-execution validation.

The separate seal binds raw suite, validation, overlap and freeze hashes before
any application call. Author and validator notes are also bound. Unchanged focused
tests are reused. Fresh `python scripts/phase73_eval_run.py --preflight` passed:
custody, evaluator readiness, exact runtime/index, reservations and unused run
verified without API calls. Complete intended-diff review found no open issue.
Next is the one-shot standard run, then complete source inspection and offline
replay, honest publication, frontend build/smoke and reviewed commit/push. No
selective retry, exposed-case tuning, altered expectations or raised cost cap.
