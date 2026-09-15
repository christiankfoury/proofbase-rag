# Isolated holdout validation

Status: approved for sealing, after pre-seal label corrections. Validator: `/root/phase68_holdout_validator`; author: `/root/phase68_holdout_author`. These are separate agent contexts, not human annotators or independent external assessors.

The validator read only the neutral authoring contract, all 19 synthetic Markdown documents, the new suite and authorship note. No application/evaluator code, prior suites/results, roadmap, or parent conversation history was inspected. No application/API calls were made. The validator did not edit the suite or commit changes.

All 60 cases were semantically reviewed. All 83 gold facts have exact source-quote matches and explicit frontmatter role access (IT Admin maps to IT/Admin; no Employee or Manager inheritance). All cases use Northstar with null department scope. Each non-answer label was checked against source absence, unresolved intent, or explicit lack of role membership. Memory is context only. All ten multi-document cases require complementary facts. Four conflict cases use documented precedence or hold conditions; the old-email example is a hypothetical premise governed by an actual precedence rule, not a claim that the corpus contains that historical email. Injection coverage includes three adversarial requests and three benign discussion controls. The two short ASCII fixture facts are absent from the corpus and belong to a different project by contract.

Before approval the author corrected five findings: attestation rationale field count, explicit Canadian-payroll eligibility, Wednesday out-of-hours release scope, system-of-record-only gold text, and separate retaliation recipient/deadline facts. These revisions were requested before runtime execution and are not driven by runtime results.

The approval hash and all per-case findings are in `author-validation.json`. The raw suite SHA-256 is `272de84a314895f9a1510231be8e81c3615cb256286a5ad4dd58d79c1f9d0b93`.

Diversity covers business functions, explicit role pairs, temporal conditions, comparisons, exceptions and memory falsehoods. Several policy facts deliberately recur across controls and adversarial cases, and ambiguity questions are short. This is a bounded synthetic suite, not broad enterprise coverage. Department isolation is not covered because every department scope is null.

The supplied freeze was not independently inspected. Root owns historical overlap checking; no historical questions were shown here, and lexical originality would not establish semantic independence. No claims are made about runtime pass rates, scorer quality, actual upload isolation, costs or production safety. Context separation cannot establish absence of latent model knowledge.
