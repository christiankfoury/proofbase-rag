# Offline empty-reference correction

The structured-blind v1 diagnostic failed on `verified-identity`: one coverage
judgment asserted a forbidden proposition was present despite the input containing
no forbidden propositions. Its unsupported identity claim was already correctly
rejected by factual and citation checks. Historical v1 remains failed at 1/2;
all subsequent stages remain unexecuted.

Decision: derive absence from an explicitly empty `forbidden_assertions` array in
code. This field asks whether any listed proposition was asserted, so an empty
set has a deterministic result. It does not mean the answer is safe or supported.
Unsupported assertions, permission/scope failures, citations, omissions and all
other semantic judgments remain governed by their existing checks.

`scripts/structured_blind_evaluator_v2.py` is a separate offline version. It first
validates the complete original packet; malformed packets are never repaired.
For valid packets only, an explicit empty array projects the forbidden status to
absent before blind comparison. Original model labels are returned as provenance;
input packets and receipts are unchanged. Nonempty lists retain the original
model judgment and disagreement handling. No answer string or case ID controls
the projection. Requests, prompts, caps, sources and references are unchanged.

The recorded failed case remains overall fail, factual unresolved and citation
fail under the prospective projection. Its empty-set disagreement disappears;
this regression replay is not fresh qualification or a relabeled historic pass.
Six regression tests cover the actual failure, nonempty forbidden assertions,
remaining disagreements/ordering uncertainty, invalid witnesses, permission
flags, unchanged requests and unchanged other labels. The combined 42-check run passes 41 semantic/design checks and fails one historical
budget-snapshot assertion: it expects accounted USD10.90614776, which the six
legitimate new receipts increased to USD10.99323876. That old snapshot test is
preserved, not relabeled as passing. Receipt reconciliation independently verifies
the new total. No new provider call occurred during correction or testing.

This correction is not wired into the paid v1 runners. It needs a separately
frozen execution adapter and the full existing controls, fresh16 confirmation,
fresh60 measurement and 48/60 plus all safety/citation/source-review gates before
activation. Existing funding headroom is USD9.76470650 after the retained hold.
Reconcile the complete remaining path again before any future paid launch.
The user's no-retry limit prevents automatically starting another qualification.
