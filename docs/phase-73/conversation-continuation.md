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

Pre-confirmation local preparation: isolated database
`proofbase_conversation_eval_20261003` cloned without changing the original.
32documents,247chunks,247embeddings. Phase40 upload/index mocks and real Phase57
tenant/RLS checks pass with provider methods blocked. HTTP health and stable
configuration/index fingerprint across TestClient lifecycle pass; zeroAPI calls.
The unrelated request-log SHA256 remains f37906539da34d369b0259b014fc061bb2d15b42e31605800d55b724335c176e.
Fresh16 authoring completed under the neutral brief after freeze cd1d3729;
mechanical reference/source mapping checks pass; independent validation pending.
Full conservative confirmation reservation USD7.4458025; expected roughly0.5-1.1.
No whole-stage funding claim; per-request rolling reservations remain mandatory.

Independent confirmation validation rejected1/16 before execution (CV1-SCOPE-15,
overbroadened required-fact reference). Initial suite and rejected validation are
retained; isolated author correction and independent revalidation are required.
No model result or runtime failure informed this pre-execution reference repair.

Final publication preserves the existing HTTP safety flag as an activation blocker,
in addition to zero unauthorized retrieval/disclosure and the48/60 target. The
runner may capture remaining cases after a fail-closed HTTP error for complete
diagnostics, but that failed case earns no success and the release inspection
cannot approve a run containing recorded HTTP safety flags. Permission/scope or
disclosure findings still stop further submissions immediately.

Independent revalidation approves16/16 references with no unresolved finding;
CV1-SCOPE-15 was corrected only by widening the question to match its existing
reference. No answer, source, expectation or other case changed. Initial rejected
artifacts remain. Approved suite/seal precedes a once-only48-call confirmation
with full8192/4096/4096 allowances and receipt-based rolling reservations.

V25 fresh confirmation passes16/16 with clean source inspection and exact replay.
48 calls cost USD0.5217955; cumulative USD2.0565328, remaining USD10.4434672.
Grader qualification complete. Freeze the selected runtime/index/configuration
before isolated fresh60 authoring; retain v4 default pending full acceptance.

Final freeze hit Windows WinError206 on its long Git argument list before any
API call or freeze write. The versioned conversation_measurement_v2 harness
uses existing batched committed-blob verification for freeze/run. Original
confirmation-frozen scripts remain immutable; runtime/grader/gates unchanged.
All four measurement ledger checks rerun against the successor.

Runtime/index/configuration freeze: e8182abe2035a2f6c3d54a20d1929aa235b21301,
512 bound files. Fresh60 authored in a separate context from neutral contract and
corpus only; full category mix retained. Independent validation and mechanical
custody/overlap checks precede sealing and live measurement. No new API spending.

Fresh60 mechanical schema, exact-source/gold inputs and frozen role scope pass.
Historical overlap: no hits against1164 unique questions at the unchanged0.8
threshold. Independent review accepts59/60 and rejects fresh-056 for source
subject scope (FHV-001). Initial suite/rejected validation and notes preserved
before isolated author correction; no application calls or case-result feedback.

Independent revalidation approves60/60 with no unresolved findings. Only fresh-056
question/reference scope changed; every source quotation and other59 cases stayed
unchanged. Repeated overlap scan still has no hits. Approved suite/seal/preflight
are committed before the once-only real HTTP/upload/retrieval measurement.
Expected new spending remains roughlyUSD2.5-5.0; this is not a reservation. Every
complete request retains its full conservative reservation before submission,
within the cumulativeUSD12.50 ceiling and unchanged output/coverage/safety gates.

Final-v1 retired after2 graded rows following source-inspection findings F26-001
(scenario premise treated as unsupported policy) and F26-002 (overbroad reference).
A26-001 flags ambiguous reporting recipient for focused application diagnosis.
Safe operator stop used the existing exclusive provider lock between requests;
16calls fully settled, USD0.24155986 new; cumulativeUSD2.29809266, remaining
USD10.20190734. No release approval, no relabeling, v4 default. Next coherent
grader simplification and focused controls, then unchanged qualification/fresh
holdout gates. Expected requalification plus focus roughlyUSD1.3-2.5 and final
USD2.5-5.0; estimates only, every full request reserved under rolling12.50 ceiling.

V26 replaces accumulated prompt amendments with one coherent contextual rubric;
request data, exact witnesses, schema/reducers, pinned model/effort and8192/4096/4096
output caps unchanged. Eight separately composed scenario controls extend the
diagnostic to16+3; original24+3 calibration and fresh16 confirmation remain.
Two separately composed two-source badge-reporting variants extend application
development without changing the original12. Before any runtime prompt change,
measure the unchanged selected candidate on this focused recipient control.
Four offline receipt/ceiling/contract tests pass against the successor (initial
test fixture isolation needed caching its input cases before temporary-path mocks).
Full request-body equivalence apart from prompts and Python compilation pass.
The first two recipient preflights are superseded unexecuted after local review
and addition of the implicit-recipient variant; preserve both. Use03 with both
focused variants and identical per-call output allowances.

Recipient focus v3 passes1/2; dev13 correctly rejected an ambiguous cumulative
duty presentation, dev14 preserves distinct recipients. SixcallsUSD0.0249993;
cumulativeUSD2.32309196. V4 prompt clarifies cumulative source composition and
recipients, while all seven checker requirements and budgets remain unchanged.
Focused after-checks and full original12+2 required before updating selection.

V4 focus passes5/6; recipient composition fixed but dev13 upgrades should to
must. Preserve that failed result. V5 preserves normative strength explicitly
in the existing producer/checker; no new validation layer.24callsUSD0.0786162,
cumulativeUSD2.40170816. Focus then full14 gate before grader spending.

V5 focus passes6/6 with clean inspection,24callsUSD0.0767370; cumulative
USD2.47844516. Full14 next. New versioned custody harnesses preserve old frozen
files, require v26 qualification, retain all case/output gates, add an explicit
request-boundary operator stop and replay partial receipts without case credit.
Neutral author/validator contracts add clause-to-question scope mapping and
scenario-versus-policy controls while preserving all existing coverage.
Six offline successor measurement tests pass, including request-boundary stop with no charge and replay of partial-case receipts without granting credit. Prior13 routing/candidate tests and all application receipt checks pass.

V5 full stopped after the original12 tasks:11 correct, dev08 safely rejected
noncontiguous table-row quotation, new recipient controls unexecuted/no credit.
44calls settled USD0.12251930; cumulativeUSD2.60096446, remainingUSD9.89903554.
Runner accidentally kept15 stage calls for17 declared turns; successor ledger
now has explicit per-turn allowance and counts actual declared turns. Frozen
original ledger remains unchanged. V6 asks separate excerpts for nonadjacent
passages; no output, citation, permission or checker requirement changed.
17 offline budget/routing/candidate checks pass, including17 successful declared
turns and duplicate submission blocked. Versioned replay audits stopped receipts
and labels missing turns rather than claiming complete coverage. Focus dev08/13/14
then full14 remains required; no grader calls until clean application selection.

V6 focus passes3/3 with exact excerpts and clean source inspection.9calls
USD0.03074910; cumulativeUSD2.63171356, remainingUSD9.86828644. Full14
preflight reservesUSD1.2340861 conservatively; expected aboutUSD0.15.
One harmless extra EOF blank line in the versioned ledger is retained in its
frozen tested bytes; no blocking semantic findings.

V6 full source inspection passes14/14 (original12/12 and addedrecipient2/2),
all designated safety controls.51callsUSD0.15302070, cumulativeUSD2.78473426,
remainingUSD9.71526574.24 exact authorized excerpts verified; all prior receipts
and immutable bindings replay. Original12 comparison uses reused v4 6/12 and
mini8/12 evidence, not a misleading14-versus12 denominator. Selection-v2 records
the opt-in challenger; no release approval before qualification/fresh60.
V26 focus8 prepared with24callmaximum, unchanged8192/4096/4096 allowances,
rolling full-request reservations. Expected focus roughlyUSD0.2-0.4; entire
qualification roughlyUSD1.3-2.5 plus finalUSD2.5-5.0 are estimates, not caps.

V26 focus8/8 matched with clean source inspection of every extractedclaim,
factstatus and independent review.24callsUSD0.22806100, cumulativeUSD3.01279526,
remainingUSD9.48720474. Full16+3 diagnostic frozen; full conservative stage
boundUSD6.5125625, expected aboutUSD0.45-0.65, rollingrequest policy unchanged.

V26 full diagnostic stops14/15 matched, finalcase and3probes unexecuted.
G27-001: current-scenario-correction claim correctly supported by capacity10
and user8, but citation incorrectly requires source to contain8 and result2.
Reviewer agrees with this inconsistent inference. No relabeling or qualification.
45callsUSD0.44251250; cumulativeUSD3.45530776, remainingUSD9.04469224.
V27 replaces the independent citation-entailment paragraph with one shared
entailment rule used against two evidence sets. It preserves independent source
selection: uncited factual evidence never repairs wrong/missing cited evidence.
Identical evidence cannot be treated differently solely due to scenario inputs.
No schema/reducer, outputallowance, safety or coverage change. Versioned successor
harnesses preserve v26 files. Ten offline receipt/cap/reducer/measurement tests
pass; request bodies apart from systemprompts identical across40 developmentcases.
Fivecase focus then full16+3,24+3,fresh16,fresh60 still required.

V27 focus5/5, clean source inspection,15callsUSD0.14831450. Cumulative
USD3.60362226, remainingUSD8.89637774. Full16+3 diagnostic preparation
reservesUSD6.5532500 whole-stage conservatively but uses authorized rolling
requests; expectedroughlyUSD0.5. Qualification and final gates unchanged.

V27 diagnostic16/16 but2/3reviewprobes, soqualificationfails. G28-001 reviewer
conflates absenceofrequestedfacts with relevance of genericrefusal. Preserve
all fixed expectations and failed evidence.51callsUSD0.45192200; cumulative
USD4.05554426, remainingUSD8.44445574. V28 replaces relevance paragraph with
one topical/communicative relationship definition, explicitly independent of
factcoverage and behavior. It does not turn refusal into an answer or success.
Shared-entailment architecture and reducers unchanged. Focusall3reviewprobes
(max3calls,USD0.3011575 conservative; expectedaboutUSD0.04), then unchanged
full16+3,24+3,fresh16 andfresh60. Tenoffline ledger/reducer/measurementtests
pass; invalidfocus IDs rejected;40case requestdata/caps identicalapartprompts.

V28 reviewerfocus3/3, clean source inspection.3callsUSD0.03256100; cumulative
USD4.08810526, remainingUSD8.41189474. Full16+3 requirednext; focus is not
qualification and noapplicationactivation is allowed.

V28 full diagnostic16/16 and3/3probes, clean sourceinspection andreceiptreplay.
51callsUSD0.47450200; cumulativeUSD4.56260726, remainingUSD7.93739274.
Next unchanged24+3calibration, expectedroughlyUSD0.6-0.9; fullrequestrolling
reservations retained, thenfresh16confirmation andfresh60measurement.

V28 calibration stops13/14, tenremainingcases and3probes unexecuted/no credit.
G29-001: coverage overlooks unresolved bookingobject; reviewercorrectlydisputes
relevance.42callsUSD0.31820650; cumulativeUSD4.88081376, remainingUSD7.61918624.
Architecture review: coverage generated facts before resolving requesttarget,
allowing answer/reference topic to substitute for userintent. V29 generates the
existing relevance.reason first, explicitly recording question/history target,
unresolvedchoice andanswer selection; thenrelevance, behavior andfactcoverage.
No addedcall, field, reducer, validationlayer oroutputreduction. JSONproperty
order changes, fieldtypes/requiredsets unchanged. Independent reviewer preserved.
Focusedcalibration subset allowed for diagnosis; full24 still requires16+3
diagnostic gate andfresh16/60 gates unchanged. Tenoffline tests pass;40request
data/schema meaning equivalent; generatedorder asserted, fullcal bypassblocked.
Fourcase focus on wrongtopic, clarification, genericrefusal, guessedobject next.
