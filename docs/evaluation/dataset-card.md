# Dataset card

## Ownership and purpose

- Dataset: [benchmark-questions.json](../../data/evaluation/benchmark-questions.json), version `1.1`, 130 cases.
- Corpus: [synthetic Northstar Analytics documents](../../data/synthetic-documents), with expected document IDs and supporting sections/quotes.
- Author and label review: project author, with AI assistance (author disclosure, 2026-09-14). No independently collected labels or measured inter-rater agreement.
- Intended use: development and regression checks for retrieval, answers, citations, permissions, memory, and safe non-answer behavior.
- Excluded interpretation: representative enterprise traffic, an unseen test set, expert semantic correctness, production security certification.
- Dataset and system share the same project ownership. The benchmark influenced iterative fixes. There is no random train/test split of these 130 cases.

## Composition

| Category | Cases | Example challenge |
| --- | ---: | --- |
| Simple factual | 30 | Locate a policy fact in a named company corpus |
| Multi-document | 20 | Retrieve and combine more than one policy |
| Permission-restricted | 20 | Refuse access to an expected restricted source |
| Missing information | 20 | Say the accessible corpus does not contain an answer |
| Conversation memory | 20 | Resolve a follow-up from previous turns |
| Ambiguous | 10 | Ask for clarification |
| Prompt injection | 5 | Resist user/source instruction attacks |
| Conflicting source | 5 | Apply current versus obsolete policy |

Author-assigned difficulty is 32 easy, 70 medium, and 28 hard. These labels are not independently calibrated. There are 60 `answer` and 20 `answer_with_memory` expectations; the remaining 50 expect refusal, not-found, or clarification. This is why answer/citation scores cover **80**, not 130, cases.

Each row supplies a stable question ID, category, difficulty, role, question, previous turns, expected behavior/answer, expected documents, source sections/quotes, allowed documents, and evaluation notes. [Validation](../../scripts/validate_benchmark.py) checks schema and source references; passing validation does not prove the question is difficult or the label is semantically correct.

## Difficulty and coverage limits

Questions and source documents use the same synthetic company terminology. Many are direct policy lookups. The corpus is small and curated, with explicit role metadata; it does not capture the distribution of messy, contradictory, multilingual, OCR-derived, or changing production knowledge. Prompt injection and conflicting-source coverage are only five cases each. Several questions share sources, so their outcomes are correlated.

The focused 20-case permission suite is drawn from this benchmark, not 20 additional independent questions. Its authorized retrieval controls reuse those cases with authorized roles. Historical static-corpus regressions exclude uploaded documents with `UPLOAD-` IDs. A single upload/project-isolation fixture in the separate holdout does not establish broad document-conversion quality.

## Separate sealed evaluation

The [Phase 49 v3 suite](../../data/evaluation/independent-generalization/holdout-v3.json) has 30 separately authored cases across nine categories. Distribution and pass counts are in [public-evidence.json](../../data/evaluation/public-evidence.json). It includes multi-document, longer memory, permission/scope pairs, missing information, ambiguity, adversarial, versioned-policy, and upload-isolation cases.

Its source-only authoring constraints and validator role record improve separation from tuning. They do not establish organizational or human independence. It was sealed and executed once against a historical frozen runtime. Phase 47, 48, and 49 use different questions; comparing their scores as a numerical improvement trend is invalid. Phase 48 was interrupted and has no complete exact aggregate.

## Dataset changes and contamination policy

Preserve benchmark expectations during runtime remediation. A proven label defect must have a separate record: case ID, original expectation, source evidence, reviewer, rationale, date, new dataset version, and effect on comparability. Do not silently replace a failing question or adjust expected facts to match the model.

All published holdouts are now visible to developers and reviewers. Future unseen-performance claims require a fresh suite authored after a new runtime freeze under separate custody. Do not alter or execute the existing sealed suites for development. Any future independent human label review should record reviewer role/identity, source evidence, disagreements, and adjudication while keeping original automated results intact.
