# Bounded application reliability diagnostic

## Scope declared before execution

On 2026-10-02 the user authorized the proposed 12-question live diagnostic,
allocating at most USD 1 from the existing USD 3.79479490 remainder. This is a
development diagnostic of the R1–R4 runtime (`8e9fcb97`), not evaluator
qualification, a full evaluation, or an overall before/after success-rate claim.
No application behavior or scoring standard is changed during this run.

Acceptance: predeclare six source-backed contrasts; enforce synchronous calls,
zero automatic retries, seven chat and three query-embedding calls per question,
84 chat / 40 embedding / 124 total calls; save raw requests, responses, usage,
authorized database sources and source inspection for all executed questions.
Stop on uncertain provider outcomes, safety failures or any exceeded bound.
Never resubmit an attempted case. Preserve historical evidence and local edits.

Current official model pages checked before execution:
[GPT-4.1 mini](https://developers.openai.com/api/docs/models/gpt-4.1-mini)
lists USD 0.40 input, 0.10 cached input and 1.60 output per million tokens;
[text-embedding-3-small](https://developers.openai.com/api/docs/models/text-embedding-3-small)
lists USD 0.02 input per million. Each chat request is bounded by 16,384 input
and 2,048 output tokens; each embedding request by 8,192 input tokens. The
uncached maximum is USD 0.8323072. The four optional fixture embeddings are
reserved in that estimate but existing synthetic documents are sufficient.

The existing configured key is reused under the user's live-run authorization;
only its presence was inspected. Credentials are never captured. Local database
startup and preparation do not authorize new cloud resources. An isolated local
database copy preserves the historical evaluation database and demo data.

Required checks: offline transport failure/boundary tests, case/source preflight,
raw-evidence/accounting replay, historical v6 report/capture replay, semantic
diff review, verified commit and push to main. Reuse the unchanged runtime's
30-method offline gate; no frontend change, build, paid evaluator or full suite.

## Result and accounting

**Twelve questions were attempted once: nine application outcomes and three
input-guard interruptions. This is not twelve completed quality measurements.**
There were **53 settled calls: 35 chat and 18 query embeddings**, costing
**USD 0.02573086**. There were no fixture embeddings, evaluator calls, provider
retries or unknown outcomes. The USD 1 allocation was a subset of the existing
allowance: **USD 3.76906404 remains**, including the unused allocation. The old
USD 0.146775 unknown reservation is still retained unchanged.

| Paid operation | Calls | Receipt-derived USD |
| --- | ---: | ---: |
| Request assessment | 12 | 0.00451920 |
| Query decomposition | 3 | 0.00025560 |
| Query embeddings | 18 | 0.00001086 |
| Evidence assessment | 8 | 0.00917600 |
| Initial generation | 6 | 0.00530280 |
| Application repair | 1 | 0.00086760 |
| Post-generation validation | 5 | 0.00559880 |
| **Total** | **53** | **0.02573086** |

The single application repair is the predeclared distinct repair stage, not an
SDK retry; its request body differs from initial generation. Charges use reported
cached input tokens where present. No cache savings were assumed in launch bounds.
Application HTTP time summed to **152.301 seconds**, with **96.521 seconds** inside
provider calls. These are small-diagnostic timings, not a latency improvement over
the historical full evaluation. Service recovery, preparation and inspection are
outside HTTP timing; total preparation time was not instrumented.

All original evidence, the unchanged runtime and corpus, and the unrelated
request log are preserved. Only the mutable shared spending journal received
53 new entries; all its prior entries are byte-for-byte equal as JSON values.
The historical v6 ledger, report and capture remain unchanged.

## Bounds, interruptions and limited continuations

Preflight verified prices, existing credentials, the remaining journal, source
quotes in the actual index, roles, models and planned query counts. Before any
paid call, it rejected the initial wording of question 7: `laptop` contains `pto`,
so the substring source planner added an unrelated leave-policy search, producing
four searches. The retained [preflight rejection](../../data/evaluation/application-reliability-live-v1/preflight-rejection.json)
records the original question. Equivalent `personal device` wording was declared
before launch, without changing source expectations or runtime behavior.

The input estimate uses serialized UTF-8 bytes plus a 2,048-token framing reserve.
It is deliberately conservative, but the initial preflight did not construct
every dynamic evidence-assessment payload. Three 10-chunk payloads exceeded that
estimate despite being only slightly beyond its byte-based bound:

| Case | Reconstructed input bound | Limit | Stage never submitted |
| --- | ---: | ---: | --- |
| 07, conditional remote work / device rules | 16,578 | 16,384 | Evidence assessment |
| 11, permitted privileged-access question | 16,392 | 16,384 | Evidence assessment |
| 12, denied privileged-access question | 16,764 | 16,384 | Evidence assessment |

Actual provider token counts for those unsent requests are **unknown**; these
are harness-bound failures, not proof that actual tokens exceeded 16,384, a
provider outage, or application quality failures. The application represented
the local guard as temporary evidence-assessment unavailability. No inputs were
trimmed and no cap was increased. Original stopped manifests remain interrupted.

After inspecting each settled stop, two separately preflighted segments attempted
only untouched questions: 08–12, then 12 alone. No previously attempted question
or paid request was repeated. Their aggregate reservations remained within the
same USD 1 / 124-call envelope. This explicitly narrows the initial no-resume
rule: interrupted cases were never resumed; new segments contain untouched cases
only. Segment journal identities have `remaining-` and `final-` prefixes over
their local ledger identifiers. The initial continuation runner is preserved with
its preflight hash; the final version adds only the last untouched segment.

This exposed a preflight weakness to fix **offline before another live stage**:
use a verified model tokenizer with conservative message/schema overhead and
exercise maximal assembled assessment payloads. Preserve the 16,384/2,048 caps;
do not solve it by silently shrinking source evidence or increasing limits.

## Source inspection of every question

Expectations were authored before execution in [cases.json](../../data/evaluation/application-reliability-live-v1/cases.json).
The following judgments are coding-agent source inspection, not independent human
adjudication or an external evaluator. They do not produce a score.

| Case | Actual result and source inspection | Attribution / disposition |
| --- | --- | --- |
| [01](../../data/evaluation/application-reliability-live-v1/run/diag-01.json), grouped amount | Correctly returns USD 1,500 per event and manager approval before purchase, matching FIN-001 Expense Categories. Whole literal survives validation without repair. | Positive live numeric control; no causal before/after rate claim. |
| [02](../../data/evaluation/application-reliability-live-v1/run/diag-02.json), nearby mismatch | `not_found`, although the retrieved FIN-001 table explicitly contradicts USD 500 and the no-approval premise. | Confirmed unnecessary abstention. Earliest wrong stage is evidence assessment: it treats the false premise as a required supported fact and says the amount/approval rule is missing. |
| [03](../../data/evaluation/application-reliability-live-v1/run/diag-03.json), scenario amount | Evidence assessment supports answering; initial and repair candidates correctly compare the user's USD 143 purchase against the USD 300 category limit. Final response is `not_found`. | Confirmed known numeric-validation defect: the deterministic guard requires scenario USD 143 to appear in the policy, then exhausts one repair. Do not broadly whitelist user numbers as policy evidence. |
| [04](../../data/evaluation/application-reliability-live-v1/run/diag-04.json), false threshold | `not_found` despite the retrieved USD 300 office-supplies row. | Same evidence-assessment defect as 02. Retrieval has the answer; no benchmark/reference change is warranted. |
| [05](../../data/evaluation/application-reliability-live-v1/run/diag-05.json), resolved context | Answers the short same-country change with manager approval and distinguishes longer changes needing People Operations review, supported by HR-003. | Positive routing control. This wording does not hit the changed late keyword guard; that particular fix remains supported by offline tests, not this live case. |
| [06](../../data/evaluation/application-reliability-live-v1/run/diag-06.json), unresolved choice | Asks domestic versus cross-border before choosing a route; no retrieval or generation. | Positive ambiguity control. No unsupported route is selected. This is not a live causal test of every normalization change. |
| [07](../../data/evaluation/application-reliability-live-v1/run/diag-07.json), conditional multi-source | Correct approval and personal-device sections are retrieved; all three embedding requests retain the full original condition. The first ranked chunk is nevertheless Cross-Border Work for a domestic scenario. Final answer is blocked by the local bound. | Retrieval input preservation observed; ranking usefulness and final synthesis remain unvalidated. No answer-quality verdict. |
| [08](../../data/evaluation/application-reliability-live-v1/remaining/diag-08.json), missing part | Gives a cited `partial_answer` with supported approval rules and explicitly says the visa form is not specified. However, it describes cross-border/international requests generally as ambiguous, while HR-003 attaches that qualification specifically to work outside Canada or the US. | Partial-answer handling works in this example; geographic qualifier is broadened. The validator silently describes a narrower, source-correct claim than the actual answer and accepts it. Remaining generation/validation defect. |
| [09](../../data/evaluation/application-reliability-live-v1/remaining/diag-09.json), modality | Correctly states 10 business days unless HR Admin extends, and that Operations may provide a label without guaranteeing one. | Positive modality control; source and displayed quote agree. |
| [10](../../data/evaluation/application-reliability-live-v1/remaining/diag-10.json), added obligations | Rejects automatic payroll deduction and mandatory prepaid shipping, but uses `partial_answer`, omits the explicit policy-alone-does-not-authorize-deductions caveat and displays a fallback excerpt ending before payroll text. | Confirmed quote-fidelity improvement: joined source passages are replaced with an actual contiguous excerpt. Evidence assessment still calls contradicted premises missing, and excerpt selection/completeness need work. Full chunk supports the core negations; displayed excerpt alone does not support the payroll claim. |
| [11](../../data/evaluation/application-reliability-live-v1/remaining/diag-11.json), permitted scope | IT/Admin receives authorized privileged-access chunks containing review frequency and exception fields. Evidence assessment is blocked locally. | Authorized retrieval observed; permitted final answer unvalidated. |
| [12](../../data/evaluation/application-reliability-live-v1/final/diag-12.json), denied scope | Employee receives only permitted public chunks; no IT-ADMIN-001 chunk or restricted fact is disclosed. Evidence assessment is blocked locally, returning temporary unavailability rather than the expected refusal. | Filtering observation only; final refusal behavior is unvalidated. This is not a completed permission-safety gate. |

Every displayed citation excerpt is a contiguous substring of its captured,
authorized source. The [offline source diagnostics](../../data/evaluation/application-reliability-live-v1/offline-source-diagnostics.json)
replay the same captured case-10 model excerpt through the pre-R3 formatter at
`d203b4c2` and the current formatter. Only the current formatter replaces the
noncontiguous join. That is a specific demonstrated implementation improvement,
not evidence of an improved overall success rate. No uncited partial-downgrade
path was exercised live; its offline regression evidence remains the relevant check.

All captured sources pass independent role/tenant/project checks. Every question
has null department scope, and the permission pair stops before final generation;
department isolation and complete permission response routing remain untested here.

## Evidence, verification and handoff

Evidence root: [application-reliability-live-v1](../../data/evaluation/application-reliability-live-v1).
[Receipt summary](../../data/evaluation/application-reliability-live-v1/receipt-summary.json)
contains deterministic counts and costs, not quality labels. Raw request/response
pairs include token usage and hashes; per-question captures retain database source
text. Frozen historical evidence was not regenerated or relabeled.

- `python -m unittest scripts.test_application_reliability_live -v`: ten offline
  transport tests passed before launch. Final review passed twelve tests in
  2.870 seconds, adding no-network evidence replay and altered-receipt rejection;
  transport coverage includes caps, cache accounting, unknown outcomes,
  rejected models, duplicate prevention and SDK retries disabled.
- Python compilation of the diagnostic scripts passed. The unchanged runtime's
  30-method offline R1–R4 evidence is reused, not claimed as a new run.
- `python scripts/report_application_reliability_live.py --check`: receipt,
  source/hash, prior-journal preservation, all-case custody and local counterfactual
  replay; no provider calls.
- `python scripts/report_phase73_v6.py --check` and
  `python scripts/report_phase73_v6_capture.py --check`: preserved historical gates.
- No benchmark edits, evaluator qualification, full evaluation, frontend build,
  cloud provisioning or application runtime change.

Local startup recovery preserved Docker's inaccessible zero-byte telemetry socket
by renaming its otherwise-empty `run` directory to `run.stale-20261002`. Existing
PostgreSQL/Redis containers were started, and `proofbase_reliability_diag_v1` was
copied from the prior local evaluation database. Neither original database nor
volumes were replaced. Initial failures involved Docker startup and conservative
preflight bounds; none triggered a provider retry.

Next work is offline: reproduce contradiction-as-missing routing, scenario-number
provenance, lost geographic qualifiers, irrelevant substring planning and source
excerpt selection; repair diagnostic payload estimation. Then propose **up to six
new live contrasts**, expected USD 0.02–0.06 with a **USD 0.50 hard ceiling** from
the remaining allowance, subject to fresh pricing/payload verification and user
authorization. At current caps, 42 chat plus 18 embedding calls reserve at most
USD 0.41582592 without caching. Do not spend the unused current allocation
automatically. Qualification and full evaluation remain deferred; the unchanged
USD 4.50 full-measurement launch floor exceeds the remainder by USD 0.73093596.
The historical comparable qualification plus measurement cost of USD 5.20520510
is context, not a new sufficient funding authorization.

Semantic review covered the complete intended scope, every answer/source pair,
continuation subsets, receipt integrity, historical accounting and limitations.
Review added raw-byte Git preservation and a receipt-tampering test. All reviewed
changes are evidence, diagnostic tooling, accounting or documentation; application
code remains at `8e9fcb97`. This work unit is committed to main with commit-content
verification and the requested push; no further runtime phase starts in this turn.
