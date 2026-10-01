# V22 diagnostic: failed output contract retained

All three completed cases were inspected against the separately composed source,
question, expected fact, exact answer spans, citations and reviewer decision.
The run stopped on its first mismatch after nine settled calls at USD 0.109716.
No probes ran. This is primary-agent inspection, not human adjudication.

| Case | Inspection |
| --- | --- |
| task-participant | One claim preserves the sourced recommendation and its two fields. The question supplies the task role; no verified identity or extra duty is asserted. Coverage, text witnesses and reviewer agreement are correct. |
| verified-identity | The explicit identity-verification claim is unsupported; the separate field-list recommendation is supported. Factual unresolved, citation fail, complete coverage and composite fail match the reference. No role-context exemption was improperly applied. |
| document-attribution | The policy and attribution are true from the source text and authoritative title. The model nevertheless emitted the document ID and title as extra source/citation witnesses; those fields only permit source/citation IDs and substrings of their text. The deterministic validator correctly rejects both spans. The model reviewer agrees with semantic support but does not repair the invalid contract. No credit or readiness is granted. |

The confirmed cause is an insufficiently explicit distinction between attribution
metadata and exact text-witness output fields. A successor can clarify where to
explain metadata while retaining the same strict validator and all original
references. No observed answer is relabeled, no invalid witness is accepted and
the failed v22 attempt is never resumed. Five development cases and three probes
were not executed. All v4/v5 evidence remains unchanged.
