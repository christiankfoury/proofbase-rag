# Phase 73 v5 isolated holdout validation

Status: **rejected**. Independently reviewed all 60 cases; 59 accepted and one rejected before any application execution.

- Validator: `/root/holdout_v5_validator`.
- Validation time: 2026-09-30T22:20:17.905230+00:00.
- Frozen commit: `1cb44e30478919be93a59281907e006fa665acf2`.
- Suite SHA-256: `225edd90af27b7676c8aedb325b9d914f3dea53a485eb9e79697caee5e308159`.
- Freeze SHA-256: `53e1b65252352c87f91d02e5debb38b745d91c8b15778dc04f540003e9526765`.
- Finding: `V5-VAL-001`, `fresh-026`, `ambiguous_reference_construction`.
- Detailed case reviews: `data/evaluation/current-runtime-v5/author-validation.json`.

## Isolation and method

Read only the two v5 neutral contracts, supplied freeze record, all 19 frozen corpus Markdown documents, and the final supplied holdout. The exact files read are listed in the validation artifact. Did not read the author note, runtime/evaluator code, prior questions/results, or parent conversation. No Git operations, application execution, API calls or external services were used. Freeze metadata mentions other artifacts; none of those referenced files were opened.

Independently inspected each question, required fact, forbidden assertion, rationale, difficulty and requested behavior against full source passages, explicit role membership, project scope, conditions and modality. Checked all exact quotations, role/user mapping, sequential IDs, unique questions, category totals, complementary multi-document sources, history placement, short ASCII fixtures and all 19 corpus hashes against the freeze. All mechanical checks passed. The rejected case has an answerable comparison whose authored clarification expectation is not unambiguous; the complete source-based reason is in its case review. Do not seal or execute this suite as approved.

## Coverage and limitations

Category totals match the contract: factual 8, multi-document 10, memory 8, permissions 10, ambiguity 6, missing-information 6, injection 6, conflicting-policies 4, uploaded-document isolation 2. Difficulty: easy 5, medium 49, hard 6. Domains and role pairs are varied. Both authorized discussion controls and adversarial prompts are present. Policy precedence is explicitly documented. All department IDs are null, so this suite does not establish department-filter coverage.

This is agent validation, not expert human labeling. Historical overlap is separately performed by root and was not verified here. No runtime behavior or live upload isolation has been observed. Preserve the original suite and this rejected validation before author revision, then independently revalidate the final artifact before execution. No case may change after the first application call.
