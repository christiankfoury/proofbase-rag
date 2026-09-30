# Phase 73 v5 isolated holdout validation

Status: **approved**. All 60 final cases accepted; no unresolved findings. This approval applies only to the exact suite hash below.

- Validator: `/root/holdout_v5_validator`.
- Final revalidation time: 2026-09-30T22:25:08.187024+00:00.
- Frozen commit: `1cb44e30478919be93a59281907e006fa665acf2`.
- Final suite SHA-256: `20365d175afe198e226e80bb1e096eb2685e8ea91e4dd7f9f1a8497a750416ad`.
- Freeze SHA-256: `53e1b65252352c87f91d02e5debb38b745d91c8b15778dc04f540003e9526765`.
- Detailed reviews: `data/evaluation/current-runtime-v5/author-validation.json`.

## Isolation and review

Read the two neutral v5 contracts, supplied freeze record, all 19 frozen corpus Markdown files and the supplied holdout. Reused the validator's own current validation and note during pre-execution revisions. The validation artifact lists exact files read. No runtime/evaluator source, author note, prior application questions/results, Git operations, API calls, external services or application execution were used. Freeze metadata mentions implementation and evidence artifacts; their contents were not opened.

Independently inspected every final case against the source quotations, complete source context, explicit role membership, requested subjects and scope, conditions, modality, history boundaries and behavior rubric. Rechecked all 60 final cases after revision. Mechanical whole-artifact checks passed for version/freeze identity, category totals, sequential IDs, unique questions, role/user UUIDs, Northstar scope, exact source quotations, fact IDs, answer/non-answer structure, history placement, complementary multi-document source counts, fixture presence/ASCII/length/novelty, and every corpus hash against the freeze. Frozen source-scope metadata agrees with the required-fact role and project access.

## Pre-execution findings resolved

The first suite was rejected for `V5-VAL-001` (`fresh-026`, ambiguous reference construction). Root later raised two independent reference-scope concerns without runtime or evaluator behavior. The validator sustained them as `V5-VAL-002` (`fresh-055`) and `V5-VAL-003` (`fresh-058`), both reference scope overreach. These two additional checks were prompted by root; the original full-case review was independent. Root reported preserving both rejected validation versions, original suite and notes before author revision.

The final `fresh-026` now contains an unresolved singular reference after a direct selection question; the two possible source rules have distinct units and reference dates. Clarification is supported. The final `fresh-055` and `fresh-058` explicitly request the effective dates previously required without being asked. Their complete facts now align with the questions. All three findings are resolved before execution; no cases were edited by the validator.

## Coverage and limitations

Category totals: factual 8, multi-document 10, memory 8, permissions 10, ambiguity 6, missing-information 6, injection 6, conflicting-policies 4, uploaded-document isolation 2. Difficulty totals: easy 5, medium 49, hard 6. Domains, role pairs, conditional questions, benign source-discussion controls and adversarial attempts are varied. Policy precedence is explicitly documented. All department IDs are null; department-filter coverage is not claimed.

This is agent validation, not expert human labeling. Root performs historical overlap separately; the validator has not checked historical suites or execution. No actual application or live upload-isolation behavior is established by this review. Approval does not prove runtime quality. Do not alter any case after the first application call.
