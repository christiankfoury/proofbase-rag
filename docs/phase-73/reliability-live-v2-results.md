# Six-question reliability diagnostic

Frozen runtime: `d4c50ebef687d96b00b474227b03e44f81175764`, committed and pushed
after offline review. Executed 2026-10-02. Six questions completed once, with
**20 chat calls and 7 query embeddings**, no provider retries, no evaluator,
no repair generation and no full evaluation. Usage-based cost is
**USD 0.02128484**, leaving **USD 3.74777920** in the existing authorized ledger.
The USD 0.50 ceiling was not enlarged. All outcomes and receipts are retained.
This is an exposed development diagnostic, not an overall success-rate estimate.

## Confirmed implementation improvements and limits

- The same captured equipment answer, bad model quote and source were replayed
  through the previous and current formatter. The old 240-character prefix omits
  payroll text; the new contiguous excerpt includes payroll review and the
  policy-alone-does-not-authorize-deductions caveat. See the saved
  [counterfactual](../../data/evaluation/application-reliability-live-v2/excerpt-counterfactual.json).
- Complete payload estimation admitted all six cases without truncation or a
  local bound interruption, including multi-source and permission routes that
  were blocked in the prior diagnostic. Every actual provider token count stayed
  below its reservation. This confirms execution coverage, not answer quality.
- The new laptop question planned HR-003/IT-002 searches without a PTO source
  request. Three query embeddings retained the complete original question.
  The exact-candidate contract was honored for the completed synthesis and
  equipment answers; it refused to accept rewritten/omitted units in case 05.
- The employee permission contrast returned `refuse_no_access`, with no
  restricted source chunks or restricted facts. The authorized counterpart still
  failed for another reason. This is one observed role pair, not a safety gate.

Offline contract fixes are verified, but the model still fails to use parts of
those contracts reliably. No live improvement is claimed for scenario answering,
false-premise answering, or overall geographic fidelity.

## Every-case source inspection

Judgments below are coding-agent inspection of the saved authorized source text,
not independent human adjudication or evaluator scores. Original case definitions
remain immutable under [the evidence folder](../../data/evaluation/application-reliability-live-v2).

| Case | Source inspection and remaining defect | Cost USD |
| --- | --- | ---: |
| 01, USD 217 supplies scenario | FIN-001 says USD 300 per purchase, manager approval above limit. Generation applies that rule correctly. The validator returns an empty numeric_context list despite repeating USD 217; the provenance guard fails closed to not_found. Evidence assessment also incorrectly describes the user's amount as supported by the policy chunk. The original blanket deterministic rejection is removed, but live scenario answering remains unresolved. | 0.00397286 |
| 02, two false thresholds | The retrieved FIN-001 table directly supplies USD 300 and USD 1,500 with the appropriate approval rules. Assessment explicitly mentions the correct values in its missing-information explanation, yet labels both facts unsupported instead of contradicted. Final not_found remains unnecessary. The safer normalizer correctly refuses to promote unsupported facts merely because they have chunk IDs. | 0.00163292 |
| 03, domestic/outside-region contrast plus laptops | Authorized HR-003 and IT-002 support the short domestic rule and listed personal-device safeguards. The final answer includes both requested areas and retains the named Canada/US boundary. However, its combined sentence says longer temporary changes OR outside-region work need review and that “such requests” are ambiguous, extending ambiguity to longer domestic changes. HR-003 attaches ambiguity only to outside-Canada/US requests. Validator copies this actual sentence exactly but still labels it supported. Claim-rewriting is prevented; semantic scope checking remains defective. | 0.00644966 |
| 04, payroll and shipping | OPS-001 says HR Admin and IT Admin review damage before payroll/final-pay action; policy alone does not authorize deductions; Operations MAY provide a label. The answer includes that caveat and a relevant contiguous excerpt. It still returns partial_answer and treats automatic deduction/mandatory shipping as missing rather than giving a direct bounded denial. Saying the automatic deduction requirement is not specified is cautious, but routing and completeness remain weak. | 0.00374254 |
| 05, authorized privileged access | IT-ADMIN-001 supports monthly production reviews, quarterly business-application reviews and owner/expiry/business-justification exception fields. The generator emits malformed JSON with overescaped citation quote delimiters. The existing parser falls back to treating raw JSON as answer text, producing 23 candidate units. The validator summarizes three selected fragments; v3 rejects the omitted/rewritten units. Final not_found is safe but unusable. Generation serialization/fallback is the earliest confirmed defect, not missing source access. | 0.00375806 |
| 06, employee contrast | Same question, Employee identity. Retrieved chunks are role-authorized public policies; no IT-ADMIN-001 source or restricted facts appear. Final refuse_no_access is appropriate. Query-vector reuse explains why this case needed no additional embedding; permissions were checked separately. | 0.00172880 |

Two predeclared expectation phrases were too strong and are explicitly excluded
from these judgments: case 03 demanded explicit location/role clarification,
whereas the source says outside-region requests remain ambiguous until People
Operations reviews implications; case 04's “must not independently promise or
threaten deductions” wording does not occur in OPS-001. These are diagnostic
expectation defects, not application failures. Original expectations are retained;
the table uses the actual source rules and no score is recalculated.

## Cost, time and custody

[Receipt replay](../../data/evaluation/application-reliability-live-v2/receipt-summary.json)
independently checks request/response hashes, usage-priced charges, reservations,
per-case and total limits, source roles/tenant/project, contiguous citations and
preservation of every older spending entry. All 27 calls settled, with no unknown
outcome. Elapsed run time was about 78.94 seconds, application HTTP time 75.86
seconds and provider-call time 51.96 seconds. These overlap and must not be summed.

Two paid validation failures expose an existing telemetry defect: the application
returns zero tokens/cost after a contract exception even though the provider
completed the request. The independent transport ledger includes both receipts
and charges correctly. Application dashboards must not be used as this run's bill.

The tokenizer estimate also has a reproducibility limitation: saved JSON sorts
keys, while the original request dictionaries had different ordering. Replay
estimates differ by 1 or 3 input tokens on 20 chat calls. The report retains those
differences, checks the recorded reservation formula and verifies actual usage
below both bounds. It does not claim exact reconstruction of original serialized
ordering. Canonical serialization or retaining original payload bytes is needed
before a future diagnostic. No existing receipt was rewritten to conceal this.

Initial automatic approval review blocked external disclosure before process
launch. A read-only provenance audit then matched all 201 eligible indexed chunks
to committed synthetic corpus text or the exact synthetic upload-test fixture;
the unchanged command was approved with that evidence and the enforced
https://api.openai.com/v1/ destination. No paid call preceded the successful launch.
No real employee/customer data, key or environment file is included in evidence.

Verification: 25 new offline regressions plus the 30-method shared compatibility
suite passed before freeze. Post-run receipt/source replay and three no-network
positive/tampering tests pass. The formatter counterfactual uses the old formatter
from `44c24fcb` without modifying historical evidence. Unrelated request logs retain
SHA-256 `f37906539da34d369b0259b014fc061bb2d15b42e31605800d55b724335c176e`.

## Next work and budget

Prioritize offline reproduction of omitted numeric provenance, false-premise
classification, compound-sentence scope, malformed generation JSON, failed-call
telemetry and payload-order custody. Then verify with newly composed contrasts.
Another six-question stage is estimated at USD 0.02–0.06; a proposed USD 0.50 cap
would still be taken from the existing USD 3.74777920 remainder and requires new
authorization and pricing/payload preflight. This allocation is finished.

Evaluator qualification and full evaluation remain deferred. The unchanged
USD 4.50 full-measurement launch floor exceeds the remainder by USD 0.75222080;
the historical comparable qualification-plus-measurement cost of USD 5.20520510
is context only, not a new authorization. Broader security, department isolation,
generalization and any overall success-rate improvement remain unmeasured.
