# Fresh current suite agent validation

Status: **approved** for sealing, bound to the exact suite bytes below. This is context-isolated separate-agent validation, not human labeling or external independent review.

- Validator: `fresh_validator_v3`.
- Suite: `fresh-current-2`; supplied frozen commit: `875700732e79016596aa26fc962d631976ddb990`.
- Raw-byte SHA-256: `2df8e5b58ce4bef0d550d4810f560d4fbd6c1c0071df3f2ffebbc23c36153a02`.
- Reviewed all 60 cases, all 89 required facts, all 19 corpus documents, and the authorship note. Exact quotes and explicit role membership were mechanically checked for every gold fact after manual semantic review. The 89 facts cite 17 documents.
- Reviewed all 23 non-answer rationales, all question/fact coverage, source conditions and modality, atomicity, forbidden assertions, memory boundaries, qualitative difficulty, and within-suite diversity.
- The 10 multi-document cases require complementary authorized sources. Five permission pairs use explicit ACL membership without Employee inheritance; IT Admin and IT/Admin are aliases. Two injection cases are benign source-discussion controls. Four conflict cases use actual documented precedence or conditions. Both separate-project upload fixtures are ASCII, below 600 characters, and introduce corpus-absent facts.
- Verified author corrections in `fresh-026`, `fresh-027`, `fresh-028`, `fresh-036`, `fresh-045`, `fresh-051`. These address atomic forbidden disclosures, source modality, a missing material condition, and topic diversity. No unresolved content defects remain.

The JSON validation artifact contains one review record for every case and aggregate counts. Approval does not report runtime performance, successful indexing, or a generalization win. Any suite-byte change invalidates this hash-bound approval and requires review.

## Limitations

- Agent validation only: not human labeling or external independent review.
- No runtime, evaluator, historical case/results, repository history or application/API inspection; actual runtime enforcement and upload/indexing outcomes were not tested.
- The supplied frozen commit identity was checked against authored metadata; actual freeze ordering was not independently established.
- Historical lexical overlap result was reported by parent; historical semantic originality was not independently verified. Within-suite wording and topic diversity were reviewed.
- Difficulty labels are qualitative estimates, not empirical success or failure measurements.
- Forbidden assertions are specific probes and are not an exhaustive catalogue of all possible falsehoods or leaks.
- All cases use project-wide Northstar scope; department-scoped isolation is not independently covered by this suite.
