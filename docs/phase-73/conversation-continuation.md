# Conversational completion under the shared CAD-authorized ceiling

The 2026-10-03 user explicitly supersedes the single-attempt and candidate-failure
stopping rules. Continue focused diagnosis/corrections, then qualification and
measurement, until accepted activation or a concrete budget/external blocker.
The total remains **USD 12.50 including USD 0.1529816 spent**, leaving
USD 12.3470184 at this authorization. No historical allowance is added. Stage
allocations may move; whole-stage reservations and per-request receipt settlement
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
