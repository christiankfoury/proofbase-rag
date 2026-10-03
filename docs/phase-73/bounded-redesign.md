# One bounded conversational reliability redesign

## CAD 20 continuation (2026-10-03)

**Outcome: application gate failed; this attempt is closed.** The comparison ran
once against frozen commit `2010ff0a`: all 36 task/profile pairs and 45 HTTP turns,
138 provider calls, no provider retry or uncertain charge. V4 remains default;
neither candidate is selected. No grader revision, qualification, holdout authoring
or final measurement followed. The remaining money does not authorize another cycle.

| Profile | Inspected complete tasks | Provider USD | Median turn latency |
| --- | ---: | ---: | ---: |
| V4 | 7/12 | 0.0373580 | 6.925 s |
| Candidate mini | 9/12 | 0.0154688 | 4.228 s |
| Candidate GPT-5.4 low | 9/12 | 0.1001548 | 6.098 s |

These are agent-inspected development outcomes, **not a qualified overall score**.
Every profile has one unresolved scope/source-expectation finding (`dev-09`), with
no success credit. No expectation was changed. The suite and exact per-task reasons
are preserved in the [inspection](../../data/evaluation/bounded-redesign/cad20-inspection.json).
Even granting every disputed item, both candidates still fail the mandatory
two-turn control `dev-03`; the stopping decision does not depend on those judgments.

The decisive failure occurs before the simplified pipeline: shared request
assessment asks the user for the office-supply threshold on the USD 290 turn,
although it is available in the authorized source. All profiles correctly handle
the corrected USD 330 turn, but both turns are required. This isolates an unchanged
upstream problem; changing the producer/checker model does not resolve it.

Additional source/draft/checker inspection:

- Mini produces a correct no-source abstention on `dev-10`. Its checker says
  `accept`, explains that no citations are required, but sets `citation_support`
  false. The all-true release contract correctly fails closed with HTTP 503.
  Challenger releases the correct abstention. No restricted amount is disclosed.
- Challenger describes both conflicting limits on `dev-07` but does not request
  the applicable policy/version. Its checker nevertheless marks response behavior
  and completeness true. Mini requests clarification; v4 asks generically but
  omits the expected conflicting amounts/evidence. These are completion findings,
  not fabricated-value claims.
- All profiles omit the frozen `dev-09` Ontario qualifier. The synthetic source's
  outside-Canada sentence does not explicitly repeat that qualifier, creating a
  source/expectation ambiguity. This remains unresolved, not silently rescored or
  asserted to prove hallucination. The factual HR+IT requirement is preserved.
- V4 needlessly labels the complete premise correction partial, and rejects a
  harmless lack-of-information caveat on the equality case before reconstructing
  an unnecessarily incomplete reply. Candidate corrections/equality replies avoid
  those failures. V4's confirmation omits the expected above-limit condition from
  both answer and quotation; mini preserves it in the returned quotation.

All **46 returned quotations** are exact contiguous text from authorized fixture
sources. No unauthorized citation, private fixture content in provider payloads or
final responses, or injected marker in final answers was found. These checks cover
controlled development retrieval, not real PostgreSQL retrieval or production
tenant assurance. Mini returns 14 HTTP 200 and one HTTP 503; the other profiles
return 15 HTTP 200 each. HTTP success alone is not task completion.

**Total receipt-derived spending: USD 0.1529816**, approximately CAD 0.21794 at the
reference rate (CAD 0.24477 using the buffer). Remaining new authorization is
**USD 12.3470184**, with **USD 0 unresolved reservations**. This is receipt arithmetic,
not an independently verified provider balance/invoice. The USD 1.7965755 preflight
was a maximum reservation; unused reservations were not charges. Historical
journals, original stopped artifacts and the unrelated request log are unchanged.

[Receipt summary](../../data/evaluation/bounded-redesign/cad20-receipt-summary.json),
[run manifest](../../data/evaluation/bounded-redesign/cad20-comparison/manifest.json),
[ledger](../../data/evaluation/bounded-redesign/cad20-comparison/api-ledger.json), and
[draft/checker extract](../../data/evaluation/bounded-redesign/cad20-draft-checker-extract.json)
retain raw-path/hash links. `python -B scripts/report_bounded_redesign.py` replays all
receipts, request/raw hashes, saved turn equality, model/input/output/call bounds,
45-turn coverage, source filtering, quotation integrity, policy arithmetic and
unchanged historical/frozen-file hashes offline. The report does not grade semantics;
it derives counts from the separately documented agent inspection. Complete result
diff/source review and whitespace checks pass. No additional paid work or runtime
fix is part of publication.

### Authorization and pre-execution reconciliation

The latest user authorization replaces the old budget with **CAD 20 total remaining
balance**, not USD 70 and not CAD 20 plus historical headroom. Bank of Canada's last
business-day rate, October 2, is CAD 1.4246/USD. A conservative CAD 1.60/USD budgeting
rate gives **USD 12.50 maximum new spending**; at the reference rate that is
CAD 17.8075 with CAD 2.1925 buffer. Account balance is user-reported, not queried.
[Rate source](https://www.bankofcanada.ca/rates/exchange/daily-exchange-rates-lookup/?dF=2026-09-18&dT=2026-10-02&lP=lookup_daily_exchange_rates_2017.php&rangeType=dates&sR=2017-01-01&se=FXUSDCAD).

| Stage | New USD cap | Conservative reservation status |
| --- | ---: | --- |
| Application comparison | 2.00 | Existing complete 1.7965755 fits |
| Grader diagnostic | 1.00 | Exact successor preparation pending; historical proxy 4.2638925 |
| Calibration, 24 cases + 3 probes | 2.00 | Historical proxy 11.91232 |
| Fresh confirmation, 16 cases | 1.50 | Historical proxy 8.3236 |
| Final measurement, 60 cases | 6.00 | Historical proxy 38.3018628; launch floor 4.50 unchanged |
| Total | **12.50** | No promise that later stages fit |

Expected spending for a fully successful path is roughly USD 7-12, an uncertain
planning estimate from historical receipts (previous final run USD 3.5000286),
the new candidate and larger claims allowance. Expected usage is not authorization
to ignore reservations. Later-stage proxies include full outputs and dynamic
payload headroom; they are not forecasts of the bill. Exact whole-stage preflight
must fit before any stage runs. This budget funds the comparison now; later work
can stop for budget even if semantic gates pass. No coverage, output allowance,
safety rule, acceptance gate or default changes to fit the money.

Scope: reuse the frozen candidate, suite, complete preflight and regression evidence;
add a durable once-only comparison transport under the separate
[CAD policy](../../data/evaluation/bounded-redesign/cad20-policy.json).
No historical journal is rewritten or credited to the new allowance. Preserve
stopped evidence below as a historical record. Save requests, raw responses,
cache-aware charges and real HTTP outcomes. Unknown outcomes retain reservation
and stop; no provider retries. Both turns must pass for conversational task credit.
Inspect source/draft/checker/final pairs before selecting a profile. All original
application and grader gates below remain binding; v4 stays default.

Verification: seven offline runner tests (reservation-before-network, receipt/cache
settlement, duplicate-stage/turn stops, unknown outcomes, malformed receipt,
model/payload caps, dollar cap and HTTP turn callbacks) and the two preserved
preflight replay tests. Eight candidate integration methods rerun. Existing shared
regressions from `86d706f3` are reused because application code/config is unchanged.
This continuation changes execution/accounting only; no web build is relevant.

The historical sections below describe the earlier authorization and stop, not
the current available balance or permission to start another attempt.

## Original attempt and preserved stopped evidence

User authorization (2026-10-02): implement one candidate, compare two fixed model
profiles, revise the grader once, qualify and measure once if preceding gates pass.
This supersedes the planning-only handoff. V4 remains default until all gates pass.

App chat gains an opt-in shared producer/checker after unchanged authorized
retrieval. Identity, tenancy, request guards, indexing and calculator grammar stay
unchanged. Conversation is reference only. Deterministic shape/quotation checks
precede one contextual check; errors use HTTP/SSE, with no repair or partial-answer
reconstruction. Existing public response types, citations and persistence remain.

Acceptance: prepare 12 fixed development tasks (three two-turn conversations),
compare v4 and candidate mini/challenger profiles. Candidate needs >=10/12, no worse
than v4, and every safety control. Select success count, then cost, then latency.
Development inspection is not a validated overall score. Stop if neither qualifies.
Offline checks cover permission/scope, citation tampering, numeric boundaries,
corrections/context, malformed output/timeouts, accounting and sync/stream parity.

Only after application selection: one successor grader revision, unchanged rubric,
reducer and pinned model; claims allowance 8192, other stages unchanged. Require
24/24 development, 3/3 reviewer probes, freshly sealed 16/16 confirmation and no
open source-inspection findings. Failure ends this attempt. Freeze runtime,
evaluator, configuration, corpus/index before independent fresh 60-case authorship
and sealing. Execute once through real retrieval. Release requires >=48/60,
zero unauthorized retrieval/disclosure and publication gates. No selective retries,
expectation edits, denominator reductions or human-validation claims.

Spending ceiling is USD 10 TOTAL for this attempt: existing USD 3.73106560 plus
USD 6.26893440 additional, not USD 10 additional. Historical journals/reservations
remain immutable. Stage caps: application 1.30, grader diagnostic 1.00, calibration
1.50, confirmation 1.20, measurement 5.00. Their sum is also 10.00. Preserve 4.50
measurement launch floor. Whole-stage payload/call preflight must fit before any
paid call; synchronous transport, no retries, cache-aware receipts. Stop on budget
or declared failure boundary; no second cycle. Provider balance is unverified.

Fixed application models: gpt-4.1-mini-2025-04-14 and gpt-5.4-2026-03-05 (low
reasoning). Verified official pricing: mini input/cache/output USD .40/.10/1.60
per million; challenger 2.50/.25/15.00, below long-context threshold.
Sources: [mini](https://developers.openai.com/api/docs/models/gpt-4.1-mini),
[challenger](https://developers.openai.com/api/docs/models/gpt-5.4).

Non-goals: cloud provisioning, calculator expansion, model search, historical score
revision or further cycles. Prior 28/21/11 remains unvalidated.

## Execution record

Starting main: b752b3f9. The candidate is implemented behind
`CONVERSATIONAL_CANDIDATE_ENABLED=false`; the model selector accepts only the two
fixed snapshots. Both endpoints invoke the same implementation. Same-session
history is bounded to six messages/2000 characters each, receives no authority,
and never supplies source quotations. Request safety and retrieval stay unchanged.
The strict calculator retains its original grammar and independent finalization.
The checker runs on every ordinary candidate response type, including abstention.
No producer self-reported unsupported-claim/confidence field controls release.
Compatibility confidence values are diagnostic zeros, explicitly not probability.
Real producer/checker token/cost receipts remain separate; checker failure telemetry
retains received usage, and unavailable usage remains unknown. No fictitious
evidence-assessment receipt is emitted for the conversational path.

### Mandatory stop: complete comparison reservation exceeds allocation

[Complete offline preflight](../../data/evaluation/bounded-redesign/preflight-complete.json):

| Profile | Reserved USD |
| --- | ---: |
| Existing v4, pinned mini | 0.5148840 |
| Candidate, pinned mini | 0.2101740 |
| Candidate, pinned GPT-5.4 low | 1.0715175 |
| Total | **1.7965755** |
| Authorized application stage | **1.30** |

These are conservative full-stage reservations, **not observed costs or a claim
that typical usage would cost this much**. The method prices complete serialized
payloads with 2048 framing tokens and another 2048 for dynamic outputs/history,
all 15 turns per profile, full output allowances, and v4's possible single repair
plus revalidation. No speculative cache discount is used before a receipt exists.
The per-profile maximum payload is applied to every turn; this deliberately
conservative estimate exceeds the allocation by USD 0.4965755.

The user required stopping if the whole stage cannot fit. **The attempt ends at
this boundary: zero provider submissions, USD 0 spent.** No live runner was
activated. Application success/safety outcomes, correct drafts rejected and wrong
drafts accepted are unmeasured. The grader successor, 24/24 calibration, 3/3 probes,
fresh 16/16 confirmation and final 60-case measurement were not started. No holdout
was authored and no candidate can be promoted. The historical USD 3.73106560
remainder and all journals remain unchanged. The additional allowance was authorized
but unused; no provider-account balance is claimed.

An initial [incomplete preparation](../../data/evaluation/bounded-redesign/preflight.json)
incorrectly reported ready after application error handling swallowed unpriced
alias/tokenizer errors. It omitted v4 generation/validation and challenger stages.
It is invalid and retained only as failed preparation evidence. Review added
explicit complete-stage assertions, pinned the mini alias at the experiment
transport boundary, used the existing o200k tokenizer for both profiles, and
recomputed the full reservation before any paid execution. Only the complete
artifact is authoritative. A schema-name typo also failed locally before writing
the complete artifact. These were offline harness corrections, not paid retries
or a second candidate cycle.

### Verification and review

Fresh checks on the intended working diff:

- `python -B scripts/test_conversational_candidate.py`: eight methods pass; strict
  parsing, citations, role/project invariants, full context, malformed/timeout and
  checker rejection, no repair, cache costs/unknown usage, fixed models, bounded
  memory, HTTP/SSE parity and no draft text in rejected SSE responses.
- `python -B scripts/test_scenario_calculation.py`: 13 methods pass, retaining
  numeric equality/one-cent/currency boundaries, source injection, scope/role
  filtering and finalization in both endpoints.
- `python -B scripts/test_reliability_remediation_v3.py`: 17 methods pass, including
  source corrections, numeric/scope contracts, malformed generation and usage.
- `python -B scripts/test_reliability_v3_custody.py`: four historical custody,
  accounting, source-tampering and published-summary methods pass.
- `python -B scripts/test_application_reliability.py` with evidence/validation
  prompt versions `v2`: 30 methods pass plus its shared request/evidence/validation,
  memory and multi-document compatibility suites. Overrides are test fixtures.
- `python -B scripts/test_bounded_redesign_preflight.py`: two methods pass; replay
  complete stage arithmetic, required stage coverage, funding composition, saved
  payload reservations and rejection of unpriced/over-limit requests.
- In-memory Python compilation of all eight changed modules passes; AST comparison
  confirms both original legacy answer blocks are unchanged except indentation.
  `git diff --check` passes.

The focused candidate test was rerun after review added failed-checker telemetry
and direct rejected-SSE assertions. Prior shared evidence remains valid: the later
change only concerns disabled candidate telemetry/tests. Provider transports were
mocked/blocked in these tests; no local result proves model semantics or real
PostgreSQL/tenant integration. No frontend build was required for this opt-in API
change; no UI file or existing response type/citation shape changed.

Review inspected the complete intended diff and new artifacts. Findings corrected:
incomplete preflight, diagnostic trace labeling, checker cost loss on failure, and
missing direct SSE draft-leak assertion. The budget stop remains a release blocker,
not an implementation-success claim. Historical scores remain unchanged.

Payload replay exposed token-count sensitivity to JSON key order after persistence.
The preparer now canonicalizes before counting. Every saved payload's canonical
reservation fits the complete artifact's declared stage bound, and the declared
conservative totals still replay exactly. Original preparation artifacts are not
rewritten. This corrects local preparation only; there was no paid submission or
post-freeze runtime measurement to invalidate. The script refuses a second full
preflight when the complete stopped artifact exists.

Unrelated request-log SHA256 remains
`f37906539da34d369b0259b014fc061bb2d15b42e31605800d55b724335c176e`.
Commit/push reviewed preparation and this stopped-result record, then stop. No
automatic continuation, allocation transfer, cap reduction or second cycle.
