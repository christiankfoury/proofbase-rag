# Fresh suite authorship provenance

Author: Codex agent `/root/fresh_holdout_author`, context-isolated subtask; not human authorship or human labeling.

Authored on 2026-09-14 after the supplied runtime freeze `5841c9ec222bd457be477b9eda43e09dabb68ee1` and supplied freeze custody commit `33496ee230c1b2d34e38c55c0225a2c87947453f`. These identifiers were supplied by the coordinator; the author did not inspect git history to verify them.

Materials read: `docs/phase-64/authoring-contract.md` and all 19 Markdown documents under `data/synthetic-documents/`. No runtime or evaluator code, prior suites, results, failure discussions, roadmap, repository history, or parent conversation were read. The isolated task supplied the neutral contract and freeze identifiers. No application or external API was executed. Only the assigned suite and this note were written.

Output: `data/evaluation/fresh-current/holdout.json`, version `fresh-current-1`, 60 cases. Categories: factual 8; multi_document 10; memory 8; permissions 10; ambiguity 6; missing_information 6; injection 6; conflicting_policies 4; uploaded_document_isolation 2. The permission category contains five allowed/denied pairs. Injection includes two benign source-discussion controls and four adversarial prompts. Every case targets Northstar with no department restriction. Upload fixtures are short ASCII text intended solely for a separate project.

Local author checks: exact gold-quote inclusion in source documents, unique IDs and question wording, category totals, UUID syntax, answer versus non-answer fact presence, required memory histories, multiple source paths for each multi-document case, and upload text length/ASCII constraints. Role labels follow the contract; IT Admin corresponds to corpus frontmatter IT/Admin. Gold facts were authored from document content rather than runtime behavior.

Limitations: this is agent-authored synthetic evaluation, not independent human validation or production assurance. The author did not inspect or compare historical questions and cannot establish historical non-overlap; the coordinator must perform that mechanical check. Source truth, permission labels, non-answer decisions and originality require the separately assigned validator. No execution results were observed and no case was tuned to observed outcomes. Upload isolation is specified, not yet executed or verified by the author.

## Mechanical overlap replacement

The coordinator reported that fresh-055 alone exceeded the historical token-overlap threshold (Jaccard 0.90625 versus 0.8). No historical question or runtime result was disclosed or inspected. The author replaced that case with a substantively different conflicting-policy topic combining Operations and device-security sources; this is not a paraphrase of the rejected topic. Category totals and 60-case size remain unchanged. Exact replacement quotes were checked against the allowed corpus. The separate validator was notified to review the replacement.

Validator feedback was applied before sealing: clarified duration and weekend-specific question scope, completed team-plan gold requirements, and separated independently checkable review intervals, equipment ownership, and meal-limit approval obligations. No runtime results informed these corrections.

The validator further removed a redundant inference that extended an approval-path clause to reporting. Replacement fresh-055 now relies directly on its two explicit reporting obligations. Final suite has 69 gold facts.
