# Conversational completion under the shared CAD-authorized ceiling

The 2026-10-03 user explicitly supersedes the single-attempt and candidate-failure
stopping rules. Continue focused diagnosis/corrections, then qualification and
measurement, until accepted activation or a concrete budget/external blocker.
The total remains **USD 12.50 including USD 0.1529816 spent**, leaving
USD 12.3470184 at this authorization. No historical allowance is added. Stage
allocations may move. The subsequent explicit rolling-reservation approval
supersedes whole-stage funding; per-request reservation and receipt settlement
remain mandatory. Original stopped artifacts are immutable historical evidence.

## Current work

Goal: ordinary questions should reach authorized evidence before deciding whether
the user needs to clarify. App HTTP and SSE share the fix; no UI/data model,
retrieval permission, tenant, upload/index lifecycle or calculator changes.

Recorded `dev-03` diagnosis: the pre-retrieval semantic assessor incorrectly treats
a requested policy threshold as missing user context. Its prompt already forbids
that error. Adding another keyword or amount-specific exception would leave the
same circular dependency. Candidate routing now defers successful, non-injection
clarification to the producer/checker after authorized retrieval. Deterministic
security blocks stay before retrieval. Deterministic ambiguity must still receive
semantic security review; uncertainty, block and unavailable assessment are never
deferred. Legacy v4 routing remains unchanged. The actual normalization is visible
in request-assessment diagnostics; uncertainty fields are preserved.

All checker criteria and individual pass flags remain mandatory. Clarify their
meaning for no-source abstention (no assertion to cite is not citation failure),
require an actionable clarification question, and preserve source applicability.
The automatic approval review rejected removal of individual checker flags as a
potential weakening. That proposed edit was not applied; the safer prompt/routing
fix retains the all-true gate and fail-closed behavior.

Acceptance is unchanged: at least 10/12 fixed application tasks, no worse than v4,
all safety controls; 24/24 grader calibration plus 3/3 probes; newly sealed 16/16
confirmation; no unresolved source findings; fresh 60-case real-retrieval run with
at least 48/60 and zero unauthorized retrieval/disclosure. No unresolved credit,
exclusions, fixture edits or lower output allowances. V4 stays default until all
gates pass. Prior development source/expectation ambiguity remains a finding.

Verification: replay the exact failed paid request-assessment response through
both HTTP and SSE with offline producer/checker fixtures; require authorized
retrieval and correct final delivery. Test legacy behavior, semantic safety after
deterministic ambiguity, direct/obfuscated attacks and failed/uncertain assessment.
Reuse original candidate tests for strict schema, every checker flag, citations,
scope, timeout and buffering. Run affected shared request/API regressions. Test
new cumulative accounting separately, including prefix spending and focused-turn
scope. Live focused tasks 03, 07, 09, 10, 12 precede any full comparison. Existing
12-task content/expectations and prior v4 results remain intact.

Paid stages use [authorization](../../data/evaluation/conversation-continuation/authorization.json)
and a separate preflight/frozen run directory for each correction. Every settled
receipt from the original comparison and all continuation runs counts against the
same ceiling. Unknown receipts stop further submissions and keep full reservation.
No provider retries. An unsuccessful semantic result drives a diagnosed correction,
not a silent replay of the same candidate. Tests do not establish model accuracy.

### Routing v2 freeze verification

Fresh passing checks: `test_conversation_routing.py` (5),
`test_conversational_candidate.py` (8), `test_conversation_budget.py` (3),
`test_bounded_redesign_run.py` (7), `test_phase52_request_assessment.py`, and
`test_application_reliability.py` (30 plus shared suites, with its v2 evidence and
validation test-fixture configuration). The initial new routing test correctly
blocked two telemetry network attempts; the test harness now mocks the candidate's
telemetry sink, and the entire test rerun passes with zero network attempts. No
provider request was made by tests. Frozen Python sources compile in memory;
diff/semantic review checks pass. The unrelated log hash remains unchanged.

The prepared mini focus reserves USD 0.0844464 for all six turns across five tasks,
including full output allowances and dynamic input headroom. Existing preparation
is reused with only revised prompts/schema refreshed. The receipt-derived prefix
remains USD 0.1529816. Broader paid comparison follows only after focused inspection.

### Routing v2 focused result and v3 correction

The six-turn mini focus completed at `84db2f68`, 18 settled calls costing
USD 0.0075640; cumulative USD 0.1605456. Both correction turns now pass; correct
no-source abstention and equality handling pass. The conflict task fails: producer
uses partial_answer for incompatible limits and checker wrongly accepts it. Scope
remains unresolved against the original ambiguous fixture. Result: 3/5 focused
tasks, no full comparison or acceptance claim. Raw pairs and inspection are retained
under `routing-v2-focus`; no safety disclosure or quotation defect was observed.

V3 makes the existing response-behavior distinction explicit: unresolved conflict
about the same fact requires an actionable clarification, whereas partial coverage
is for separable requested parts. It adds no policy-specific pattern or extra layer.
All checker flags, output caps and citation checks remain. Expanded rejection tests
now exercise each individual false checker flag, not just the numerical flag.

Fixture defect correction is separate from runtime behavior. Original `dev-09`
expects Ontario applicability but its second source sentence does not state that
restriction explicitly. `development-v2.json` adds only: "This temporary-work policy
applies only to employees based in Ontario." Original source text follows verbatim.
All 12 questions, expectations, safety flags and remaining sources are unchanged.
The new explicit restriction strengthens the check against scope broadening; all
previous unqualified `dev-09` answers still fail it. No historical score is changed.
Because source evidence changes for 05/09, a new full comparison uses the versioned
suite consistently; the original v4 score is not a matched-source comparison.

Focused verification: eight candidate methods (now every false checker flag), five
routing methods and three cumulative-budget methods pass. Prior shared tests remain
valid for unchanged routing/runtime logic. Receipt/source replay checks exact raw
hashes, normalized committed freeze content (including historical mixed line
endings), turn coverage, quotations, private-data absence and cumulative charges.
The initial v3 preparation is retained but superseded before execution because the
offline replay helper was corrected for a pre-existing mixed-line-ending file.
Its successor `routing-v3-focus-02` has the same USD 0.4327248 reservation, challenger
profile and six turns; no paid submission used the superseded preparation.

V3 challenger focus at `7c43a94c` passes all five tasks/six turns by agent source
inspection: both correction turns, actionable conflict question, explicit Ontario
scope, no-source abstention and equality boundary. Eighteen calls cost USD 0.0503048;
cumulative USD 0.2108504. All checker flags remain required. No open finding in
this focused run; no full application or grader acceptance yet. Proceed to the
fixed 12-task comparisons on the versioned suite, retaining every result.

The full v3 challenger run at `b738bdc3` completes **12/12 tasks**, all designated
controls, by agent inspection of all 15 turns and source/draft/checker pairs. No
open inspection finding. Cost USD 0.1253276, cumulative USD 0.3361780. This is a
development result, not final accuracy or activation authority. Mini and v4 still
need the matched-source comparison; qualification and release remain pending.

Mini completes 8/12: two noncontiguous table quotations fail the exact-quote gate,
one conflict draft is blocked by the checker, and one delivered answer omits
Ontario applicability. All failures remain failures. Its 43 settled calls cost
USD 0.0167168, cumulative USD 0.3528948. Challenger remains the only eligible
candidate. Complete v4 on the same versioned suite before profile selection.

The user explicitly approved rolling reservations within the unchanged USD 12.50
total. See `rolling-authorization.json`: complete input and unchanged output caps
are reserved before each submission, unknown receipts retain reservation and stop.
Stage estimates are planning figures, not extra funding; incomplete stages earn
no acceptance. The final launch floor remains USD 4.50. No retries or coverage
reductions. The prior whole-stage final output reservation alone was USD 14.7456;
rolling funding uses settled actual spending instead of reserving all 60 at once.

Matched v4 completes 6/12 under the unchanged expected details: first correction
turn diverted, scope omitted, conflict values omitted, confirmation approval detail
omitted, conference condition/unit incomplete, equality validation unavailable.
Its 50 calls cost USD 0.0346460, cumulative USD 0.3875408.
No observed disclosure. Candidate selection: challenger 12/12 >=10 and >=v4 6/12,
all designated controls; mini8/12 fails. These are development inspection results.

Grader v24 preserves v23 schema, reducers, exact witnesses and metadata limits.
It clarifies contextual coverage witnesses, evidence-caveat speech acts, mixed
partial answers and scenario references, based on the preserved v6 source review.
Pinned GPT-5.4 medium: claims8192, coverage4096, review4096. Qualification keeps
eight diagnostic controls plus three probes, 24 calibration cases plus three
probes, then newly sealed16 confirmation. No fresh60 launch without qualification.
Estimated remaining costs are approximately USD 0.3-0.7 diagnostic, 0.8-1.6
calibration, 0.5-1.1 confirmation, and 2.5-5.0 final application/grading. These are
planning estimates, not reservations or promises. Full conservative request bounds
are saved separately; rolling calls must fit the actual remaining ceiling.
Offline tests replay all24 calibration and3 probe semantics unchanged and prove
pre-submission reservation, cached receipt settlement, unknown-outcome stop,
no repeats, exact cap/model enforcement and ceiling rejection. All four pass.

V24 diagnostic stops after3/4 matches (12calls, USD0.1837735; cumulative
USD0.5713143). Wrong document attribution is correctly unknown/missing in the
whole sentence, but the extractor duplicates its subjectless predicate and marks
that fragment supported. The reviewer correctly disputes the inconsistent claim;
the case is unresolved, not accepted. Other three source-inspected cases agree.
V25 keeps attributed predicates with their subject and avoids duplicate overlapping
extractions; schema/reducers/reviewer independence unchanged. A focused rerun of
the failed case precedes the complete8+3 diagnostic. Historical v24 remains failed.

V25 focus passes1/1 with three settled calls, USD0.0545040; cumulative
USD0.6258183. Source inspection confirms a single whole-sentence claim, correct
unknown/missing attribution, covered underlying rule and independent reviewer
agreement. Full8+3 diagnostic follows; focus alone grants no qualification.

V25 full diagnostic passes8/8 and3/3 probes, no source-inspection findings.
27calls cost USD0.2796570; cumulative USD0.9054753. Full24+3 calibration next.

V25 calibration passes24/24 and3/3 probes with no source-inspection finding.
75calls cost USD0.6292620; cumulative USD1.5347373, remaining USD10.9652627.
Fresh16 confirmation is next, with separate context-isolated author/validator
authorized by the existing quality-completion plan. Neutral briefs and all grader
code freeze before authorship. Final harness preparation reuses real HTTP,
authoritative evidence capture and upload/index fixtures in a separate local DB.
Nine offline grader/measurement checks pass, including embedding receipt settlement
and per-case/model/output/ceiling bounds. No final suite or paid measurement yet.
