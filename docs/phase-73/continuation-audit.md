# Phase 73 continuation audit

Work unit started 2026-09-30 after interruption publication `f3faad60`.

Goal: reconcile the interrupted call and shared budget, distinguish evaluator
findings from reference defects, and establish whether a successor can execute
under the existing gates. Acceptance requires immutable original evidence,
offline-reproducible accounting, source-supported dispositions and an explicit
continuation decision. This affects evaluation tooling/documentation only; no
App/API behavior, database, sealed labels or scoring standard may change.

Required checks: original interruption replay, shared-journal comparison,
negative accounting controls, source-quote verification, compilation, local
links and full intended-diff review. Reuse unchanged application/UI checks.
Stop paid execution while the provider outcome remains unknown. No new API
call, retry, resumed case, fresh suite or budget increase is authorized by this
audit. Existing standing authorization applies once the actual gates permit it.

## Accounting and recovery

The complete original report replays without alteration. The current shared
journal exactly matches the interrupted snapshot: 414 entries, including the
same final unknown entry. The cumulative call ledger still has 3,039 attempts.

| Item | USD |
| --- | ---: |
| Settled usage estimate for the interrupted attempt | 0.61799184 |
| Final unknown call, reservation retained in full | 0.14677500 |
| All additional accounted spending | 6.69192009 |
| Existing additional ceiling | 10.00000000 |
| Remaining headroom | 3.30807991 |

No release, duplicate charge, omitted receipt or newly incurred cost was found.
The earlier Batch reservations remain included. Accounting is reconciled;
**the provider outcome is still unknown**. A reservation is neither a provider
receipt nor evidence that server execution ended. Elapsed time does not settle it.

The final raw artifact contains `APITimeoutError`, `response: null`, and no
completion ID. Its request has no `store` option. The frozen runner uses Chat
Completions with a 60-second timeout and zero retries. Official
[retrieval documentation](https://developers.openai.com/api/reference/python/resources/chat/subresources/completions/methods/retrieve)
requires a completion ID and says only completions created with `store=true`
are returned. Therefore the saved request does not provide a supported API
recovery route. No replacement request or speculative retrieval was sent.
This is not a provider billing-limit rejection; no account setting was changed.

The [machine audit](../../data/evaluation/phase73-continuation-v1/audit.json)
records the exact request digest, shared-spend identity and ledger index 3038.
The request belongs to `fresh-011`'s final review in the run ending
2026-09-30 20:17:12.737033 UTC. Those identifiers support any external accounting
investigation without exposing the credential or changing the evidence.

The prior cancelled Batch transition is not precedent for clearing this flag:
that transition had terminal provider status and all 32 receipts. This request
has neither a terminal provider receipt nor usage. Both the frozen measurement
ledger and shared-spend journal deliberately reject further calls.

Remaining funds alone cannot lift the stop. A provider outcome/usage record is
needed, or an explicit change to the current unknown-outcome policy allowing
successor work with this uncertainty and full reservation retained. The latter
is a real gate decision, outside routine approval to continue. No such change
is inferred from this request. Even after resolution, this exposed suite remains
retired and cannot be resumed or selectively regraded.

## Source findings and development controls

These dispositions supplement the immutable [original inspection](source-review.md).
They do not change any original label, reference, answer or publication result.

**SR-007: reference construction, not permission to relax coverage.** The question
asks whether a missing laptop automatically authorizes a deduction. OPS-001's
general no-deduction-authority statement supports the answer's scoped denial.
However, sealed fact 03 requires the general statement. The v20 rubric explicitly
requires the entire reference meaning, so marking that broader fact missing
is consistent with its contract. The reference asks for more scope than this
question requires. Fix future reference construction before execution; do not
teach the grader to ignore sealed facts. The separate quotation-fidelity failure
remains valid, and the original failed result remains unchanged.

**SR-011: reference scope plus modality.** The question names customer-data access;
sealed fact 03 adds production systems. This repeats the scope-construction issue.
Separately, HR-001 says employees *should* complete the mandatory training before
access. Mandatory training does not by itself establish a mandatory timing rule.
The question's *must* premise and the answer's stronger timing assertion need
separate scrutiny; question wording cannot become policy evidence. Future authors
and validators must reject that premise or formulate the question with the source's
modality. The preliminary concern does not turn this unfinished case into a pass
or a completed grade.

**SR-006: claim-boundary uncertainty remains a development concern.** The answer
repeats the question's documentation task in “to ensure proper documentation.”
Reading this as task framing is plausible; reading it as a claim about the
organization's purpose is also possible. The source establishes the required
fields, not an independent purpose. Neither schema-valid grades nor reviewer
agreement resolve that distinction. No original credit is awarded. A versioned
candidate, if needed, must distinguish contextual framing from explicit additional
purpose or outcome assertions without exempting unsupported policy claims.

Six [new development controls](../../data/evaluation/phase73-continuation-v1/development-controls.json)
use vendor intake and travel-booking source passages rather than replaying the
exposed answers: task framing versus invented insurance-law purpose; narrow versus
broad questions with matching references; an omitted material exception; and
strengthened modality. Exact quotes were checked against OPS-001. The expectations
are primary-agent source-inspection proposals, **not executed model results or
fresh holdout evidence**. The audit validates quotes and structure only, not the
semantic correctness of those proposed labels. No evaluator prompt was changed.

Successor authoring and independent validation must explicitly compare every
required fact's subject/scope/modality with the question as well as its source.
All material in-scope conditions remain mandatory. Keep these development cases
and findings out of isolated fresh author/validator contexts; supply only the
neutral rule. Existing frozen authoring contracts remain untouched.

## Continuation decision

Phase 73 is still blocked on the unknown provider outcome, with evaluator
development/qualification pending if its semantics change. Phase 71's historical
qualification and Phase 72's completed application changes remain valid historical
evidence; they do not resolve the new finding automatically.

After the outcome gate is resolved: diagnose on the separate controls, preserve
any failed attempt, and require the unchanged 24/24 development + 3/3 reviewer
and fresh 16/16 confirmation gates for changed evaluator semantics. Then freeze
the entire runtime/evaluator/corpus/configuration/index, separately author and
validate 60 new cases, seal, and execute once with standard synchronous requests.
Keep per-call reservation, cache-aware costs and zero retries. Publish a valid
miss as well as a pass; the target stays 48/60 and observed leakage must be zero.

No assurance is made that USD 3.30807991 can fund all remaining gates. Recompute
stage bounds and the shared balance before any call. Do not reduce the sample,
skip confirmation, substitute a cheaper evaluator or increase the ceiling.

## Verification and handoff

- `python -m unittest scripts.test_phase73_continuation`: 4/4 passed. Repeated
  once after review added a raw-replay versus original-publication equality guard.
- `python -m unittest scripts.test_phase73_interruption`: 5/5 passed, including
  full raw request/response, reducer and historical cost replay.
- `python scripts/audit_phase73_continuation.py --check`: passed; saved audit
  agrees with original evidence and the current shared journal.
- `python -m py_compile scripts/audit_phase73_continuation.py
  scripts/test_phase73_continuation.py`: passed for final source.
- Local Markdown links in all four touched Markdown files and Git whitespace
  checks passed. Original results/source-review/run artifacts, frozen evaluator
  and cost policies/journals have no changes.

Semantic review covered the complete intended diff and all new files. It added
the original-publication equality check and byte-preserving Git attributes for
the new hashed JSON evidence (checked against staged bytes), confirmed no API client is instantiated,
and checked that prepared controls are never presented as passing model evidence.
No blocking finding remains in this audit/publication change. The provider and
claim-boundary blockers for the unfinished measurement remain explicit.

Application, permissions and web checks are reused from the unchanged Phase 72
and interruption publication evidence documented in [preflight](preflight.md) and
[results](results.md). No benchmark schema, runtime, dependency, Docker or UI code
changed, so no benchmark run, web rebuild or browser rerun was needed. Live
OpenAI checks were skipped because the unknown-outcome stop remains active.

Handoff: branch `main`, based on `f3faad60`; intended commit contains this audit,
its report/controls/test, evidence attributes and README/status/tracker corrections only. Preserve
the unrelated `data/observability/request-logs.jsonl` modification. Next action:
obtain provider outcome evidence or an explicit policy decision about retaining
an unknown outcome; do not invoke the frozen runner. Approximate active work:
20 minutes (agent estimate); two runs of four new tests, one run of five existing
tests, no builds, zero new evaluation API calls and USD 0 new API cost. Official
documentation was read without issuing model requests.
