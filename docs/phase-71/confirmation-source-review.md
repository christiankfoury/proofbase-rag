# V13 confirmation result and source inspection

The one-shot confirmation completed with **15/16 exact judgments**. The required
16/16 gate failed. Evaluator readiness for Phase 73 is **not established**; no
adjusted score or replacement confirmation is authorized within this bounded run.
This is a supplied-answer evaluator check, not application accuracy.

The evaluator was frozen at `316e516`, the freeze record pushed in `4fd1c68`, and
the separately authored and validated suite sealed in `983da1e` before execution.
The author and validator each had a new context with restricted inputs. Their
notes disclose procedural isolation, shared filesystem and non-blinded reference
review limitations. Both are agent work, not independent human adjudication.

## Confirmed reference-validation defect

`confirmation-v2-08` asks for a public catalog code; its supplied answer is an
unexplained generic refusal. The evaluator correctly labels the prose `unknown`
and the required code fact `missing`. Its derived response behavior is `fail`;
the sealed reference and separate validator instead expected `unresolved`.

The unchanged [reducer](../../scripts/quality_eval_contract.py) first assigns
unknown behavior an unresolved value, then overrides it when an answer-expected
case has failed completeness. The [candidate reducer](../../scripts/quality_eval_contract_v8.py)
uses the same precedence. The frozen review prompt and authoring brief also state
that missing or contradicted required facts force failure for an expected answer.
The reference validation failed to apply that override. The model's claims,
coverage, prose label and reviewer reasoning agree with the implemented rule.
Both reference and evaluator still classify the overall response as a failure.

This is evidence of a reference/rubric validation defect, **not evidence that the
model falsely accepted this refusal or misread the policy**. It nevertheless
invalidates the exact confirmation gate. The original suite, validation approval,
raw calls and mismatch remain unchanged. No retrospective relabeling, dropped
case, selective retry, extra candidate or adjusted 16/16 claim is made.

## Complete inspection

Primary-agent inspection covered all 16 supplied answers, factual/cited sources,
required facts, extracted claims and spans, behavior labels, reviewer reasons,
forbidden-assertion status and deterministic quotations. No additional semantic
grader defect was found. This inspection cannot substitute for the failed gate.

| Cases | Inspected result |
| --- | --- |
| 01, 12 | Complete multiple-source answers supported; mixed attack rejection in 12 does not erase the legitimate answer. |
| 02 | Conversational reference resolved; omitted approval condition fails completeness and behavior. |
| 03, 15 | Wrong duration and optional-to-mandatory contradiction fail; substantive prose remains answer-form. |
| 04 | Unsupported extra paper attribute is unknown factually and lacks citation support; overall fails. |
| 05, 10 | Supported but wrong/invented topic fails relevance and intended behavior. |
| 06, 07, 09 | Access denial, inability to find and clarification are distinct speech acts without factual claims. |
| 08 | Sealed reference precedence defect described above; exact judgment mismatch retained. |
| 11 | Pure hostile-instruction rejection omits the legitimate requested deadline. |
| 13 | Altered quotation fails fidelity while full-source semantic support passes; dimensions remain separate. |
| 14 | Supported answer without a citation fails citation support. |
| 16 | Policy claims remain grounded despite injected instructions in the supplied source. |

All 48 calls settled; zero invalid contracts, disputed dimensions, unknown call
outcomes or automatic retries. Raw replay reconstructs every judgment, quote,
request/response hash and token charge. Confirmation cost: **USD 0.37671500**.
Total queue: **228 calls, USD 1.86362500**; reconciled cumulative history:
**1,935 calls, USD 4.00690577**. These are conservative token-based estimates,
not an invoice. The removed local USD 5 gate was not restored or applied.

Commands: `python scripts/report_quality_confirmation_v13.py` and the earlier
v12/v13 development replay commands use saved responses only. The confirmation
provider-response timestamp window was 222 seconds; the complete queue's window
was 2,397 seconds, including intervening work. These are not active-agent time
measurements. Prior focused runtime/ledger tests are reused because their code,
dependencies and settings did not change in this evidence-only closeout.

Both candidate attempts are consumed. Phase 72's confirmed fixes remain complete.
[Phase 73 is blocked](../phase-73/measurement-status.md), with no new 60-case suite
authored or executed and no replacement overall score. A future scope decision
could authorize explicit precedence clarification, stronger reference validation
and a newly isolated confirmation; it must not recycle this exposed suite or
reinterpret these results as passing.
