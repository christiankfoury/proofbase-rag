# Current-runtime-v3 holdout authorship

Author: `/root/phase68_holdout_author` (agent authorship, not human labeling).

Authored after supplied freeze `89b5a38550d1ccad479c944aac7d3d0d604a359c`.

## Source boundary

Read only `docs/phase-68/authoring-contract.md` and the 19 Markdown files in `data/synthetic-documents/` during this assignment. No runtime, evaluator, prior suites, results, failure analyses, roadmap files or parent conversation history were inspected. The assignment supplied the freeze identifier and output paths. No application execution, external API calls or commits were performed. Only the two authorized output paths were written. A temporary construction program used the authorship output path and replaced itself with this note after writing the suite.

## Suite and checks

Exactly 60 new questions: 8 factual, 10 multi-document, 8 memory, 10 permissions, 6 ambiguity, 6 missing-information, 6 injection, 4 conflicting-policy and 2 uploaded-document-isolation. Permission coverage has five allowed/denied pairs with explicit role membership, including Operations non-inheritance. Injection coverage has three adversarial attempts and three benign source/policy-discussion controls. Conflict cases use actual documented precedence or conditions. Memory includes false policy claims, a false role grant and an invented schedule. The upload fixtures contain novel facts in short ASCII text intended for a different project.

Construction checked exact source-quote substrings, explicit frontmatter role membership for every gold fact (IT Admin mapped to IT/Admin), category counts, sequential IDs, unique questions within this suite, complete UUID lengths, memory history, at least two source documents per multi-document answer, empty gold facts for non-answers, and fixture ASCII/length limits. Gold facts split separately checked table columns and material conditions.

## Limitations

The freeze commit was supplied and not independently inspected because repository history is outside the author boundary. Historical originality against earlier suites remains for root mechanical overlap checking without disclosing earlier cases. No application behavior, retrieval coverage, evaluation pass rate, upload execution or cost was measured. A separate isolated validator must check labels, material fact completeness, quotes, roles and non-answer reasoning before sealing. This is not human labeling or external independent assessment. No earlier questions or results were supplied to this author; assignment isolation cannot prove absence of latent model knowledge.

## Pre-seal validator corrections

Applied isolated validator findings before any runtime execution: made payroll eligibility explicit in fresh-002; narrowed fresh-003 to a Wednesday release outside normal hours; narrowed fresh-018 system-of-record gold text to the actual question; split fresh-029 retaliation escalation recipient and deadline into independent gold facts; and corrected fresh-001 rationale to four information fields plus signature. Exact source quotes, roles and category counts remain unchanged. The suite now has 83 gold facts. These changes reflect label and material-fact validation, not runtime feedback.
