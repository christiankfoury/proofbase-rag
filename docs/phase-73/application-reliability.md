# Offline application reliability

Started 2026-10-01 on main at `c1d842ee`; implements R1–R4 of the
[active plan](../roadmap/application-reliability-plan.md). External API budget:
USD 0. Preserve historical evidence and the USD 3.79479490 remainder.

Goal: correct source-confirmed application defects in App chat without a new
overall score. No UI/schema/database change, evaluator candidate, paid call,
benchmark edit, security-policy change or new holdout. Stop after R4 publication.

Acceptance: reproduce each code defect before editing; retain the same new
positive/negative/interaction fixtures after editing; verify actual validator and
caller behavior, one repair, source-only grounding and authorization boundaries.
Run affected shared offline regressions, review complete diffs and push main.
Mocked semantic decisions establish plumbing only, never live entailment quality.

## Predeclared coverage and attribution

| Cause / owning layer | Valid / negative / interaction coverage | Evidence and disposition |
| --- | --- | --- |
| Overlapping numeric spans, dropped sign/currency and 20-literal truncation / post-generation validator | Grouped money, codes, decimals, dates, durations, repetitions and sentence boundaries; changed amount/unit/currency/sign; false approver/negation plus semantic handoff, timeout, missing/unauthorized citations and one-repair caller | V6 source review 056 locates fragments after retrieval; new fixtures use unrelated values. Baseline/after recorded under `data/evaluation/application-reliability-v1`. Fixed in `afd9fcd7`. |
| Scenario quantity treated as a policy literal / post-generation validator | Question-only value versus changed policy threshold and hostile override | V6 002/012/016/055 are diagnostic pointers, not acceptance fixtures. No numeric whitelist planned; interpretation remains semantic and requires live validation if not safely reproducible offline. |
| Late ambiguity keyword overrides sufficient evidence / generation routing | Answer and partial-answer in both generation paths; no-evidence, unauthorized chunks, unresolved intent and conflict controls | Newly composed software-policy fixture fails in four route combinations before the fix. Application defect; not attributed to a specific v6 row. |
| Repeated interrogative mistaken for a named subject / request normalization | New schedule/version choices versus historical named incident lookup; hostile role instruction remains blocked | V6 041 raw call `03945` requests clarification for `which calendar`; runtime normalization erases it before retrieval. New independent choice fixtures reproduce the general cause. |
| Unverified display excerpt / citation formatting | Exact span unchanged; stitched, strengthened-modality and hostile fabricated excerpts replaced; semantic rejection still required for unsupported answer | V6 014/023/054 show noncontiguous quotations. New blue-form source independently reproduces the missing substring check. Application quotation defect; separate from grader disagreement over support. |
| Partial downgrade loses claim-to-citation linkage / final response | Two independent supported parts; only one cited; no authorized citation; unsupported deadline; actual one-repair caller | New fixture reproduces uncited retained claims and a partial answer with no citations. Application safety defect found during source review; no claim this caused a particular v6 failure. |
| Focused queries replace full request / multi-document retrieval handoff | Planned and decomposed searches; conditional approval and second question; role/project/department/exclusions; original-query fallback | Final review reproduced the loss of conditions in a new archive-request fixture before changing the shared search caller. Fixed without extra retrieval calls; live ranking impact remains unverified. |

Historical model failures are not an oracle. Attribution compares the question,
authorized source, saved candidate if present, validation and final response;
grader errors are tracked separately. Missing saved stages remain unknown.

## Compact handoff

R1 tests authored before runtime editing. Required artifacts: baseline and after
test results with source hashes, final regression record, cost/time assessment and
evaluator decision record. Unrelated request-log hash at start:
`f37906539da34d369b0259b014fc061bb2d15b42e31605800d55b724335c176e`.

## R1 result

Baseline: 10 test methods, 4 passed, 6 failed (7 failed assertions including
subtests). After: 10/10 numeric methods and 2 shared wrappers pass. `r1-before.json` and `r1-after.json` retain
the same numeric fixtures, failures, source hashes and elapsed test time. The
shared wrapper was added afterward; numeric assertions were unchanged.

The application validator generated `730.50` inside `$2,730.50`, treated positive
`34`/`$34` as present in negative evidence, split dates and ignored numbers beyond
20 distinct literals. One ordered scan now preserves whole tokens, signs,
currency codes, durations and percentages. Normalized whole tokens must agree;
USD and CAD and their symbols are deliberately not inferred equivalent. It also
checks single-digit claims. Only line-leading numeric list labels are structural.
All extracted values are checked; the silent 20-item slice is removed. A 26-value
test rejects an unsupported trailing claim. Evidence is tokenized once per
validation, so removing the cap does not multiply evidence scans per claim.

False approvers/negation still reach semantic validation and are rejected by the
controlled semantic response. Missing/unauthorized citations, timeouts, source
instruction checks and the one-repair limit remain active. The caller test now
passes the unchanged grouped amount to semantic validation without a repair.
No extra default model call is added. Numeric words, conversion, locale-specific
formats and scenario interpretation remain semantic/unverified limitations.
Question numbers are never added to policy evidence or whitelisted.

Verification: `python -B scripts/test_application_reliability.py NumericTests
--record data/evaluation/application-reliability-v1/r1-after.json`; shared wrapper
`SharedTests --record .../r1-shared.json` passes Phase 54 and all 7 quality-runtime
methods (including Phase 35/39/46/48 controls). HTTP/socket blockers record no
attempted external access. Compilation uses Python's in-memory `compile`.
No schema/benchmark/UI changes: benchmark validation, web build and live checks
are skipped by scope and the USD 0 instruction. Semantic diff review found no
remaining blocking issue. R1 implementation is complete; R2 follows the push.

## R2 result

R1 commit `afd9fcd7` was verified and pushed before R2. R2 baseline has five
methods: three pass, two fail (five failed assertions including route variants).
All five pass afterward; `r2-before.json` / `r2-after.json` preserve evidence.
Both changes are application routing corrections. Request normalization now keeps
an unresolved choice or missing decision variables instead of calling the echoed
question a named subject. Existing specific information-search normalizations
still pass. Generation's late ambiguity keyword fallback now respects the earlier
authorized-evidence answer/partial decision, like its existing missing-topic gate.
This can enable the normal generation and validation calls for requests previously
stopped incorrectly; it adds no retry or new processing stage.

New controls exercise both generation paths with sufficient evidence, absent
evidence and role-disallowed chunks; conflicts produce clarification, and mixed
hostile requests remain blocked before retrieval. The historical Phase 52 ASGI
tests also exercise `/query` and `/query/stream`. Retrieval, tenant, project and
department filtering code is unchanged. Unknown empty retrieval is still not
treated as access denial. Paraphrased restricted intents not recognized by trusted
role rules remain a refusal-wording limitation; no forbidden-document lookup was
added. This does not establish production or department-only security coverage.

Verification: `python -B scripts/test_application_reliability.py SharedTests
RoutingTests --record data/evaluation/application-reliability-v1/r2-shared-final.json`
passes all nine methods, including Phase 52/53/54 and quality-runtime suites.
The initial `r2-shared.json` failure was the harness blocking Windows asyncio's
local self-pipe, not a provider call or product failure. The final harness blocks
real HTTP transports and outbound `create_connection` while permitting the ASGI
transport and local self-pipe. Failed harness evidence is retained. Compilation,
complete intended diff review and whitespace checks pass. R2 is complete pending
its commit/push; R3 follows immediately. No API usage or historical rerun.

## R3 result

R2 commit `d203b4c2` was verified and pushed before R3. The corrected R3 baseline
has seven methods: one passes and six fail (eight assertions with variants).
All seven pass after the fix. `r3-baseline.json` / `r3-after.json` retain the same
fixtures; `r3-before.json` preserves an earlier wrong test import, corrected before
runtime changes. `r3-shared.json` passes all eleven selected methods/wrappers.

Citation formatting now keeps an exact contiguous excerpt or substitutes the
existing bounded source-prefix fallback. It does not rewrite the source or call
a model. Confidence calculation uses that source excerpt, so a fabricated quote
cannot inflate lexical overlap. The semantic claim validator still checks the
answer: changing a quote never turns an unsupported must/may claim into support.
A prefix may not contain the most useful supporting sentence; excerpt selection
quality remains a limitation, while the full authorized chunk remains available.

The final partial downgrade now requires each retained claim to have a retained,
authorized candidate citation whose validation explicitly links that claim and
whose chunk is in the claim's evidence list. With no such claim it abstains.
Supported parts preserve their wording and cite independent sources; unsupported
parts are removed and a clear remaining-parts limitation is appended. The real
validator/caller test still performs at most one repair. No extra model calls.

Inspection of generation variants, prompt builders, evidence assessment, source
planning and decomposition found that generation already receives the entire
question and labels memory as context. New multipart/condition/memory controls
verify this boundary and the partial-response instruction. The planner remains
a bounded domain heuristic, and decomposer completeness cannot be established by
those checks. Final review found a separate retrieval-input omission, addressed
below; no prompt rewrite was made. Existing
semantic validation tests reject changed approvers, negation, modality and added
unsupported deadlines when the controlled judge identifies them; they cannot
prove the live judge reliably notices those defects.

Mixed override/legitimate requests are explicitly blocked by the current request
assessment contract. Answering their safe portion needs a securely defined
segmentation policy and live evidence; this offline change does not strip attacks
or grant claimed roles. General answer omissions, unsupported rationale/scope,
safe-part coverage and scenario interpretation remain open. Source-review v6
findings are preserved, never converted into new passes.

Verification includes in-memory compilation of changed modules, shared citation,
memory, request/evidence assessment and validation tests, complete intended diff
review and whitespace checks. No UI/schema change, live benchmark, evaluator
qualification or service startup. R3 is complete pending commit/push; R4 will
consolidate development evidence and the saved-receipt cost/evaluator assessments.

R3 was committed/pushed as `9bfa2d70`. During R4 review, the full question was
found to be replaced by focused search text before retrieval. The new fixture
reproduced loss of its urgent-request condition and absent-supervisor subquestion.
`r3-query-before.json` records failure; `r3-query-after.json` passes both planned
and model-decomposed paths plus shared regressions. Each focused search now
includes the complete original request with unchanged role, project, department
and document-exclusion configuration. The original-question fallback is not
duplicated. Retrieval call count is unchanged; embedding input grows by the
question length per focused query. Actual recall/ranking impact requires live
validation. No claim that this resolves v6 010's missing retrieval is made.

## R4 consolidated evidence

The offline milestone is complete. New development fixtures establish the
specific code behaviors above, not application accuracy or generalization:

| Fixture group | Before | After |
| --- | --- | --- |
| Numeric methods | 4/10 pass | 10/10 pass |
| Routing methods | 3/5 pass | 5/5 pass |
| Coverage/citation methods | 1/7 pass | 7/7 pass |
| Complete request in focused searches | Fails | Passes planned and decomposed paths |
| Whitespace-separated numeric signs | Fails | Preserved and distinct from positive values |

`r4-consolidated-final.json` records the final 30-method run: 24 new development methods,
four shared-suite wrappers and two history/known-limit controls. The shared
wrappers run Phase 52/53/54 and all quality-runtime checks, including Phase
35/39/46/48, under provider transport blockers. A separate scenario diagnostic
still rejects a legitimate USD 143 scenario absent from the USD 820 policy source;
this is explicitly an unresolved limitation, not an improvement. A question-value
whitelist would also admit hostile threshold changes and is not implemented.

Final sign review reproduced a whitespace-separated minus being dropped.
The initial `r1-sign-*` diagnostic did not distinguish a line-leading Markdown
bullet from an inline negative. Review corrected that fixture distinction, with
the initial records preserved. `r1-markdown-before.json` then reproduced a new
false rejection of a numeric Markdown bullet; `r1-markdown-after.json` passes
inline `Adjustment: - $34`, ordinary `- $34 per request` list items, and negative
`- -$34 adjustment` list items. Extraction treats line-leading Markdown list
markers as structure while preserving inline/inside-item signs. Semantic validation
still governs meaning; no claim that every numeric notation is normalized is made.

The frozen v6 report and capture inventory replay exactly on main with their
unchanged supported dependencies. No historical script, benchmark, sealed suite,
raw response, grade, source-review judgment or ledger was edited. No managed
checkout or service startup was needed. The unrelated request-log hash remains
the starting hash. Compilation and semantic review cover the complete runtime
diff; all blocking findings were fixed before the outgoing commits. Web build and
benchmark validation are skipped because their contracts/schema did not change.
Live model tests, embedding refresh and evaluator qualification are explicitly
skipped under the user's no-API instruction.

### Saved cost and time assessment

Reproduce the read-only arithmetic with:

```powershell
python -B scripts/test_application_reliability.py --assess-history data/evaluation/application-reliability-v1/history-assessment.json
```

Every saved receipt's raw hash and cache-aware charge is checked. The 453 calls
settled at USD 3.50002860, including all application auxiliary calls:

| Saved stage | Calls | USD |
| --- | ---: | ---: |
| Request assessment | 60 | 0.0233984 |
| Query decomposition | 17 | 0.0014208 |
| Evidence assessment | 53 | 0.0646900 |
| Initial generation | 36 | 0.0367460 |
| Repair generation | 7 | 0.0074856 |
| Post-generation semantic validation | 31 | 0.0363780 |
| Embedding | 75 | 0.0000253 |
| Claims grader | 60 | 1.3422535 |
| Coverage grader | 57 | 0.5722250 |
| Grader reviewer | 57 | 1.4154060 |

Application chat totals 204 calls/USD 0.1701188; grading totals 174 calls/USD
3.3298845, about 95.1% of provider cost. Eight cases record one repair: seven
generation repairs and one local citation prune. There are no repeated identical
request hashes within a case. Different scoped requests are not interchangeable;
these counts are not evidence of duplicate work that can simply be deleted.

Elapsed run time is 5,743.766 seconds (95m 43.8s). Application HTTP latency sums
to 1,916.581 seconds (31m 56.6s); grading plus grade persistence to 3,541.898
seconds (59m 1.9s); the remaining 285.287 seconds includes setup/indexing,
capture, preflight and orchestration. Per-call grader/embedding durations are
unavailable. Application trace totals include 387.301s request assessment,
527.524s retrieval, 372.741s evidence assessment, 302.798s initial generation and
259.134s validation; traces do not fully account for repair and HTTP time.
Permission/final-response timing is null, not zero. The JSON retains these limits.

Receipt inspection also verifies actual default generation versions: v1 for 33
responses, v4 for 20, and no generator for seven. V8/v9 remain experimental; their
stronger prose cannot be credited to the active defaults. V4 says all shown
documents are relevant and describes partial answers in terms of missing
documents, which can conflict with missing facts in a present document. Active
prompt/routing interactions, unsupported rationale, strengthened modality and
missing exceptions need live development contrasts; no unmeasured prompt win is
claimed and no historical prompt is rewritten.

### Evaluator reassessment decision

Recommendation: **do not start another automatic grader-version loop**. The
24/24 development, 3/3 probes and 16/16 fresh confirmation established finite
qualification, not coverage of every contextual combination in the 60-case run.
Source metadata was already present. Agreement of claim and reviewer passes can
repeat the same mistake; the rejected publication gate remains necessary.

| Problem | Appropriate next treatment |
| --- | --- |
| Non-exact witnesses (004), invalid/empty length-limited outputs (009/011/018), IDs, custody, charge arithmetic | Deterministic integrity checks already detect these. Keep invalid/unresolved with no credit; do not fix by retries or blindly raising output caps. |
| False rejection of caveats, contextual approval paraphrase, scenario/actor attribution (004/013/014/015/035) | Clarify application of the existing rubric with new contrast pairs: evidence caveat versus policy claim, supplied scenario versus invented threshold, named policy attribution versus invented approver. No example-specific exceptions. |
| Missed or misclassified omission/behavior (010), inconsistent short witness scope (003/023) | Inspect full answer meaning independently of witness length; contrast omitted prohibition with asserted permission. These require semantic review, not document-ID/word-overlap scoring. |
| Candidate/reviewer disagreements such as 022/057 | Preserve unresolved state. Reviewer agreement or disagreement is diagnostic, not independent human adjudication. |
| Reference ambiguity about caveats and standalone witnesses | Record explicit interpretation before a new candidate. Any change to scoring meaning or adjudication process requires the user's decision; do not revise sealed references. |
| New overall quality or production-safety claim | Current automated evidence is unsuitable: source inspection rejected publication and department-only coverage is absent. Keep validated score null. |

Automated grading remains useful as a diagnostic checklist, with deterministic
contract enforcement and source inspection, but another costly candidate is not
justified until those general semantic boundaries have a defensible specification.
Independent human adjudication is an option to propose, not a process adopted by
this change. No alternative model, standard, evaluator version or label is added.

### Proposed next live stage — no execution authorized

Use 12 newly composed diagnostic questions (six contrasts) instead of repeating
the old 60-case/453-call measurement: grouped amounts versus nearby mismatches;
legitimate scenario application versus false thresholds; resolved context versus
unresolved choice; complete versus missing-part evidence; source modality versus
unsupported added obligations; and permitted versus denied scope. Include
conditional multi-source requests to assess the fuller retrieval inputs. Compare
responses with predeclared source expectations, not v6 labels; this is a live
development check, not a baseline/new-runtime success-rate comparison.

Proposed maximum per question: one request assessment, one decomposition, one
evidence assessment, one generation, two semantic validations and one repair
(seven chat calls), plus at most three query embeddings. Allow four additional
single-chunk synthetic fixture embeddings only if required. Total hard call cap:
84 chat + 40 embedding = **124 calls**. No external evaluator calls in this small
proposal; source inspection is diagnostic only and does not replace qualification.
Use synchronous requests, zero provider retries and unchanged guards. Preflight
must reject, not truncate, any case requiring more searches or tokens.

Reserve at most 16,384 input and 2,048 output tokens per chat call and 8,192 input
tokens per embedding. At the **saved ledger's prices**, without assuming cache
hits, total worst-case token reservation is USD **0.8323072**. Propose a **USD 1.00
hard allocation**, with expected actual spend roughly **USD 0.04–0.12**, based on
the saved application costs with extra room for answerable/repair-heavy cases.
Prices and exact payload reservations must be checked before execution. Expected
synchronous application time is roughly 8–20 minutes plus 15–30 minutes of source
inspection; timing is an estimate, not an SLA. Fuller search inputs add embedding
tokens; corrected R2 routes may now generate/validate instead of stopping, so no
fixed latency/cost reduction is promised.

The USD **3.79479490** remainder is preserved in full today; this proposal does
not allocate it. The USD 0.146775 old unknown reservation is unchanged. A later
overall claim still needs 24/24 development, 3/3 probes, fresh 16/16 confirmation,
full freeze, isolated authoring/validation and a new one-shot 60-case holdout with
48/60 target and zero unauthorized retrieval/disclosure. The USD 4.50 measurement
launch floor alone exceeds today's headroom by USD 0.70520510, before further
qualification. The most recent comparable qualification + measurement cost was
USD 5.20520510; that is historical context, not a sufficient future budget cap.

### Final handoff and efficiency

R1 `afd9fcd7`, R2 `d203b4c2` and R3 `9bfa2d70` are pushed. The final R4 commit
contains the retrieval-input correction, consolidated evidence and this handoff.
External API calls/spending for this implementation: **0 / USD 0**. Git pushes
are the requested repository publication, not model/API execution. Reproductions
and narrow reruns precede the integrated gate, repeated when review found new
changes. Earlier passing evidence is retained; no web build, live benchmark or
paid loop was run for routine changes. The first measured reproduction to the
final consolidated run spans 27.02 minutes; initial source-reading time is
unmeasured. There are 22 retained test-run records totaling 58.904 seconds inside
the runner, excluding process/import overhead. One harness self-pipe failure,
one import correction, one null-timing aggregation correction and the documented
query/sign/Markdown review findings justify the local repeats. No external calls
occurred. Stop at this offline milestone.
