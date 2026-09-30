# Phase 73 primary-agent source inspection

Status: inspection completed for all 11 captured responses; full-suite publication
approval denied. Ten cases have complete grading and one stopped during reviewer
execution. Forty-nine cases were not executed. No validated score exists.

The primary agent inspects every completed answer, authorized source/citation
mapping, required-fact coverage, behavior, forbidden assertions, model judgments
and reviewer agreement. This is source inspection by an agent, not human
adjudication or an independent security assessment. Sealed expectations and raw
outputs remain unchanged. Disputed or invalid judgments earn no target credit.

## Case decisions

| Case | Source inspection | Disposition |
| --- | --- | --- |
| fresh-001 | Pure not-found response omits both HR-004 facts: September 1 for the supplied August start and location-dependent plans. No factual claims or citations; completeness and behavior fail correctly. Trace records exact-literal rejection of the user-supplied 18 despite sufficient evidence. | Application miss; no grader finding. |
| fresh-002 | The complete six-day vacation answer preserves the HR-002 longer-than-five-days rule and 20-business-day notice. C1 quotes that exact authorized rule. The limited-evidence prefix is metacommentary; partial_answer metadata does not override complete answer prose under the frozen reducer. | Pass; no grader finding. |
| fresh-003 | Pure not-found response supplies none of the six FIN-001 receipt/attestation facts. No policy claims or citations; missing coverage and wrong behavior are correctly recorded. | Application miss; no grader finding. |
| fresh-004 | Sales-to-Solutions-Engineering handoff precedes technical validation; discovery and stakeholder mapping precede proposal. All three required facts and both authorized SALES-001 citations support the full answer. | Pass; no grader finding. |
| fresh-005 | All three stable API error fields and the versioned-endpoint OR at-least-90-day compatibility alternative are covered. Authorized ENG-001 C1 supports both claims and preserves the alternative. | Pass; no grader finding. |
| fresh-006 | All three IT-ADMIN-001 fields and the exact authorized citation are correct. Both grader passes isolate “to ensure proper documentation” as an unsupported policy-purpose claim. In this question context it can also be ordinary framing of the requested documentation task, rather than an additional organizational purpose. This entailment/claim-boundary judgment remains semantically uncertain; no adjusted credit is assigned. | Unresolved inspection finding SR-006; recorded failure retained. |
| fresh-007 | Deadline, HR extension, joint review and no automatic missing-laptop deduction are all supported by OPS-001. Grader requires the broader general no-deduction-authority statement even though the question asks specifically about a missing laptop. Question-specific completeness versus broader sealed fact is a reference/coverage concern; original fail remains. C1 concatenates noncontiguous source sentences, so separate quotation-fidelity failure is correct. | Unresolved inspection finding SR-007; recorded failure retained. |
| fresh-008 | IT-003 supports the confidential classification and public-channel prohibition; full cited chunk also supports restriction on unapproved recipients. However, the answer never communicates both business need and appropriate access in required fact 3. Exact C1/C2 quotes and factual support pass; completeness fails without implying false policy. | Application coverage miss under sealed facts; no grader finding. |
| fresh-009 | Pure not-found response omits all eight HR-003 and IT-002 location/device conditions. Factual/citation N/A and coverage/behavior failure correctly describe this abstention. | Application miss; no grader finding. |
| fresh-010 | Pure not-found response omits the distinct HR-004 annual learning budget, FIN-001 per-event limit and both advance approval requirements. Empty claim assessment is correct; completeness and behavior fail. | Application miss; no grader finding. |
| fresh-011 | OPS-001 supports HR initiation and IT fulfillment; HR-001 supplies mandatory onboarding training with a should-before-access formulation. The claims grader flags stronger must timing. The coverage grader also demands production-system scope even though the question asks only about customer data, raising the same question/gold breadth concern as case 7. The review request timed out; no final grade or reducer result is manufactured. | Ungraded; preliminary coverage concern SR-011, not a completed model decision. |

## Findings and limits

SR-006 concerns whether a documentation-purpose phrase is factual policy content
or ordinary contextual framing. SR-007 concerns a broader sealed fact versus the
specific missing-laptop question; SR-011 shows a related issue in unfinished
coverage grading. These concerns remain unresolved; the inspection does not
assign substitute labels, adjust scores or alter references after execution.
The model reviewer agreed with all ten completed grades, which did not eliminate
these source-inspection concerns. Passing calibration and fresh confirmation
therefore does not establish grader infallibility on application responses.

The three recorded model passes are fresh-002, fresh-004 and fresh-005. Seven
completed model failures remain unchanged. Cases 001, 003, 009 and 010 are pure
abstentions on answerable questions. Case 001's validation trace rejects the
user-supplied date number 18; case 003 rejects amount 68 and identifier 001.
Those traces support a future source-confirmed investigation of literal checking;
no frozen runtime fix or rerun was made. Case 008 omits a required recipient
condition. Case 007 also has a separately valid quotation-fidelity failure because
its quoted excerpt concatenates noncontiguous source sentences.

All 11 captured HTTP responses are 200 and their saved evidence has no recorded
role/project safety flags. The dedicated permission, memory, ambiguity, missing-
information, injection, conflicting-policy and uploaded-isolation groups were not
reached. Neither zero flags nor the 3/10 selected-prefix model result establishes
full-suite quality or safety. No population percentage or adjusted score is claimed.

The final review timeout is an APITimeoutError after a transport read timeout,
with no response/usage receipt. It is not evidence of exhausted billing or an
authentication error. The 60-second request timeout and zero retry policy were
frozen. The full USD 0.146775 reservation remains accounted; no provider charge
or successful completion is inferred. This inspection uses no new paid calls.
