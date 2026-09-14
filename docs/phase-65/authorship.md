# Fresh current suite authorship

- Version: `fresh-current-2`.
- Author: `fresh_author_v3`, agent authorship, not human labeling.
- Authored after supplied frozen commit `875700732e79016596aa26fc962d631976ddb990`.
- Exactly 60 cases: factual 8, multi_document 10, memory 8, permissions 10, ambiguity 6, missing_information 6, injection 6, conflicting_policies 4, uploaded_document_isolation 2.
- Source reads were limited to `docs/phase-64/authoring-contract.md` and all 19 Markdown files under `data/synthetic-documents`. No runtime, evaluator, historical tests/results, roadmap or history was read. No application/API execution or commit was performed.
- The authoring helper verified exact source-quote inclusion, explicit role membership for every gold fact (normalizing only IT Admin to IT/Admin), category counts and unique wording. Every answer rationale names source access; non-answer rationales explain source absence, ambiguity, scope or denied membership.
- Gold facts are separated into independently checkable claims. Ten multi-document cases require complementary sources. Five varied permission pairs include a Sales role non-inheritance control. Memory is context only, with false memory claims forbidden. Injection cases include two benign source-discussion controls.
- Both upload fixtures are ASCII, under 600 characters and contain novel facts absent from the corpus, intended only for a separate project.
- Historical originality, freeze ordering, runtime enforcement and actual indexing outcomes cannot be independently verified within this isolation boundary. Root must perform historical overlap checks without exposing older material.
- Ready for separate context-isolated validation. Not yet sealed or evaluated; no performance claim.

Separate-agent validator revision pass: split forbidden HR disclosure fields and recipient/deadline claims, preserved source should modality, included the executed-agreement repository non-deletion rule, and replaced one overlapping absent-formula question with a distinct missing-address question. Revised suite has 89 required facts. Revisions accepted by the separate context-isolated agent validator. This is agent validation, not external independent or human validation.
