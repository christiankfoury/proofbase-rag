# Lower-cost continuation of Phases 71-73

User authorized the recommendations and selected **USD 10 additional** on
2026-09-30 UTC. This single envelope covers remaining evaluator and application
requests, including embeddings, auxiliary checks, failed/uncertain attempts and
Batch jobs. Continue autonomously inside it; do not increase it automatically.
The account's independent enforced limit remains unresolved and unchanged.

## Scope and acceptance

Keep the validated v18 model, prompts, schemas, reducers, fact references and
24/24 + 3/3 development, 16/16 confirmation and 60-case runtime gates unchanged.
Prepare discounted Batch execution where scheduling is compatible with the
protocol; enforce one shared ceiling before every new request; report cache-aware
estimates without rewriting historical evidence. Test all paths without a network.
No account setting, credential, application algorithm or historical suite changes.
Completion here means reviewed/pushed local cost-control tooling and reporting,
not a passed confirmation or measured application score. Stop live work for the
known provider limit, missing custody, unknown outcomes or insufficient headroom.

## Accounting and implementation

`quality_cost_control.py` validates model/usage/context size and distinguishes
standard and Batch pricing, cached input and output. `report_quality_costs.py`
reconstructs 887 completed queue requests from hash-bound raw responses. The
unchanged conservative historical floor is USD 2.14328077. Current-queue estimates
are USD 8.61915250 at full input price and USD 7.64686450 with recorded cache hits
(432,128 tokens). The resulting derived cumulative estimate is USD 9.79014527;
USD 0.09326750 remains a separate prior reservation. These are token-price
estimates, not invoice reconciliation or a claim of new savings already realized.
All frozen ledgers and their original USD 10.76243327 estimate remain untouched.

`policy.json` records the user's additional USD 10 ceiling and binds the original
ledger. `prior-outcome-resolution.json` separately classifies the observed HTTP
429 `project_spend_limit_exceeded` as an explicit rejected request with no returned
generation. It preserves the original unknown marker and conservative reservation;
it neither reruns that attempt nor asserts a verified zero charge.

`SpendJournal` serializes new reservations across Batch and synchronous calls.
Before any request, settled estimates plus pending reservations plus the next
worst-case reservation must fit the additional ceiling. Pending/unknown operations
block further spending; duplicate identities and changed policies are refused.
The approved ceiling is not a promise that every required gate fits in USD 10.
No automatic retry or fallback to standard-price requests is permitted.

Phase 73's intercepted application, embedding and grader calls now use this
shared envelope. GPT-4.1 mini cache discounts and GPT-5.4 cache discounts are
included in settlement and independently reconstructed by the offline reporter.
Freeze inventory includes the new implementation and policy. Application queries
and their safety grading remain sequential: do not delay a disclosure stop by
queuing all runtime cases into a batch. Its conservative USD 240.413952 theoretical
all-maxima bound is not authorized spending; the tighter USD 10 shared envelope
stops requests earlier when necessary.

## Batch preparation and execution

`quality_batch_grading.py` prepares the unchanged v18 claims and coverage requests
as the first wave. Only valid, complete collected outputs permit constructing the
second wave's unchanged reviewer requests. Reference labels are excluded from
both waves. Grading input key order is preserved because it affects the exact
JSON string sent by the frozen transport. The reducer is unchanged. The Batch
transport binds request bytes, model, full evaluator code closure and supplied
protocol artifacts; it saves upload/submission metadata, provider status, raw
output/error files, IDs, usage, cache-aware cost and extracted responses.

The public CLI separates local preparation, submission and collection:

```powershell
python scripts/quality_batch_transport.py prepare <new-job-directory> --requests <reviewed-request-spec.json>
python scripts/quality_batch_transport.py submit <new-job-directory> --allow-external-ai
python scripts/quality_batch_transport.py collect <new-job-directory> --allow-external-ai
python scripts/report_quality_costs.py --check
```

Request specifications contain `requests` (`custom_id`, `body`) and `bindings`
(repository-relative artifact paths to SHA-256). The grading module's
`prepare_initial`, `prepare_review` and `replay` functions construct/reconstruct
both waves from supplied case records. Each submission also requires an agent
review record `authorization.json` with `status: approved`, `plan_sha256`, the
identical `protocol_bindings`, and `human_adjudication: false`. This records a
completed protocol gate under standing authorization; it is not another routine
permission question for the user. The transport is not a replacement for the
phase's authoring, seal, expectation validation and source-inspection workflow.

Collect retrieves one status snapshot per invocation, not a busy polling loop.
Incomplete batches can be checked later by their same provider ID without
resubmission. Missing/duplicate/unknown IDs, provider errors, expired/cancelled
batches, invalid models or usage retain reservations and block promotion. Raw
malformed data is preserved. A timeout after submission is never retried because
acceptance may have occurred. Completed local replay does not issue API calls.
A Batch job may take up to 24 hours; dependent waves can therefore take longer.

No job was submitted or authorized for live execution in this work unit. The
provider gate is false. Before continuation: resolve the account limit, review
and freeze the successor execution protocol, then author/validate/seal fresh
confirmation under the standing isolation rules. Retire the interrupted suite;
do not relabel or resume it. Reuse unchanged v18 development evidence rather than
paying to repeat it solely for a transport change. Qualifying confirmation results
must be bound into Phase 73 readiness before its runtime freeze. These custody
and publication steps remain pending; the new transport alone grants no readiness.

## Earlier defect detection

For any future semantic correction, inspect the complete source-based hypothesis
and reference expectations locally first; run the smallest new positive/negative
controls before broader diagnostics and stop at the first disagreement. Current
v18 already orders new context controls first and stops a failed diagnostic.
Preserve that behavior rather than batching an entire diagnostic before knowing
whether its first case fails. Batch is intended for accepted fixed suites after
these prerequisites, not blind speculative cycles. No reduced sample size or
weaker acceptance standard is authorized. Unchanged evidence is reused.

## Verification and review

`python -m unittest scripts.test_quality_cost_control scripts.test_phase73_eval
scripts.test_quality_confirmation_v18` passed 24 no-network tests. They cover
cache arithmetic, shared cumulative headroom, pending reservations, unknown
submission, SDK retry refusal, absent authorization, malformed/missing/duplicate
outputs, changed inputs, idempotent collection, cache-aware runtime replay and
cap refusal before any provider request. The two-wave integration test replays
all 24 saved calibration cases with shuffled results: exact initial/reviewer
requests, intermediate grades and dimension reductions match the frozen records.
It proves local orchestration equivalence, not new live model accuracy.

Scoped Python compilation and the derived cost report replay pass. No app/runtime
algorithm changed, so prior Phase 72 behavior evidence is reused; web build and
live checks are not required for this tooling change. Complete intended diff and
new files reviewed before commit. Frozen hash verification covers v18 code, suite,
validation and seal. Unrelated request-log edits remain excluded. New paid calls:
zero; additional envelope spent: zero. No infrastructure or account-limit changes.

## Pricing sources

Checked 2026-09-30 in official OpenAI documentation:
[Batch API](https://developers.openai.com/api/docs/guides/batch) gives 50% lower
input/output token pricing and a 24-hour completion window. The implementation
applies that factor to the [GPT-5.4](https://developers.openai.com/api/docs/models/gpt-5.4)
standard USD 2.50 input / 0.25 cached input / 15 output per million tokens.
[GPT-4.1 mini](https://developers.openai.com/api/docs/models/gpt-4.1-mini) is USD
0.40 input / 0.10 cached input / 1.60 output per million. Reservations assume
uncached input; only returned cached-token counts reduce settlement estimates.

Handoff: main after `090e566`; provider limit still blocks live work. Commit this
reviewed unit, preserve the failed attempts, and resume the protocol only once
the provider limit is resolved. No additional phase approval is needed.
