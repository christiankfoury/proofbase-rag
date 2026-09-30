# Phase 73 independent holdout validation

Status: approved. All 60 cases were independently accepted; no unresolved source, role, scope, behavior or coverage findings remain. This is agent validation, not expert human adjudication.

- Validator: `phase73_holdout_validator`
- Recorded at: `2026-09-30T19:59:27.546324+00:00`
- Frozen commit: `8bd72ba1a840307e69e63f80610dbeb67b401540`
- Suite SHA-256 (raw bytes): `231129164098d2582c08652b24e9cfae50eb9c3a3cd2c963bbcf0c65aedda841`
- Freeze SHA-256 (raw bytes): `27ebe1c314e027e43e0c3eb60725dc3d5dd79e702732dfed5df275e583525c7c`
- Validation artifact SHA-256 (raw bytes): `ac3770618a184510073f6b4fb3f1e85c80a40dd7598aa8eb6a2975b9c3178165`
- Decision artifact: `data/evaluation/current-runtime-v4/author-validation.json`

## Source review and checks

The validator read the two supplied Phase 73 contracts, supplied freeze record and all 19 corpus Markdown documents before opening the fresh suite. The suite was opened only after the explicit authorship-complete handoff. Each case's requested behavior, complete material answer facts, source quotations, active role, project and department scope, forbidden assertions, rationale and history was independently reviewed. The decision artifact includes a source-based reason and role/scope evidence for every case, and an individual verification entry for all 136 required facts.

Inline local data checks verified the 60 ordered unique case IDs, unique question wording, role-to-user UUID mapping, required fields, 136 exact quote matches, authorized answer-source membership, frozen source scope and all category counts. All 19 corpus raw-byte hashes match the freeze. Every one of the 10 multi-document cases requires complementary sources. The eight memory cases include history; the others have none. Five permission pairs check allowed and denied roles without Employee inheritance. The injection group contains two benign source-discussion controls and four adversarial cases. The four precedence cases rely on documented supersession or approval conditions rather than an invented policy ordering. The two fixture texts are ASCII, 195 and 202 characters, with novel identifiers/values absent from the full corpus; each expects not_found with empty required facts and forbidden isolated values.

| Category | Cases |
| --- | ---: |
| factual | 8 |
| multi_document | 10 |
| memory | 8 |
| permissions | 10 |
| ambiguity | 6 |
| missing_information | 6 |
| injection | 6 |
| conflicting_policies | 4 |
| uploaded_document_isolation | 2 |

Expected behavior counts are 38 answer, 7 clarify, 8 not_found and 7 refuse_no_access. Difficulty labels are 4 easy, 32 medium and 24 hard; they are qualitative source-review judgments, not measured application difficulty. All five roles and all 19 documents appear in the suite. Related topics recur intentionally across different skills; 60 different question wordings do not imply 60 statistically independent topics.

## Isolation and limitations

Only the 23 input files listed with raw-byte SHA-256 values in the decision artifact were opened as evidence. No repository runtime/evaluator code, earlier suite, result, model output, failure analysis, history or parent task transcript was opened. Standing system/developer and repository/environment instructions were supplied with the task; those are context, not prior evaluation evidence. The permitted freeze contains file names, hashes and measurement metadata; none of its non-permitted referenced files were opened. No external API, application or Git operation was performed. The suite was not edited. Only the decision artifact and this note were written.

The on-disk authoring contract has CRLF raw-byte SHA-256 `94ff4b577ca60a705f1dce15494c17379c239198ce9a3760869c5f0fc492cecc`; LF normalization yields the frozen `f48bcf59408eb343e00c92fe1d323c79cca7e7387012e0828909205c460372ff`. This is a verified line-ending difference, not a substantive contract change. The actual raw hash remains recorded in files_read.

Historical overlap is deliberately outside this isolated review and must be checked separately by root. The suite's authored_after_freeze field matches the supplied freeze commit; independent Git/time custody was not inspected. No claim is made about runtime success, actual ingestion, live permission enforcement or separate-project placement. All cases use null department_id, so the suite does not independently establish narrower department-isolation coverage. The review is source/contract validation by an agent, not human labeling or a production-safety certification.
