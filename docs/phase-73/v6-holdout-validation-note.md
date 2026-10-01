# Phase 73 v6 independent pre-execution validation

Status: **approved**. All 60 cases and all 102 required facts were reviewed; 60 cases accepted, zero rejected, zero unresolved findings. This is agent validation, not expert human labeling.

- Suite SHA-256: `3b17ecbfbfab9dbbd555640cd9b9977116e5fc1edb61572d378638f57d678e5f`
- Freeze SHA-256: `a0e1a2fced97a7763c11fb8d8b3e12341061e34476e99c890db3f72cfa7c2470`
- Frozen commit: `c44459b86f035006e5b7cf6bd671537ab3bb0dd6`
- Validation artifact: `data/evaluation/current-runtime-v6/author-validation.json`
- Validation artifact SHA-256: `ef4ffe9446125df110a5d598c49ef405312fd2cad26ae9f42b4eae20e25bda44`
- Validator: `/root/holdout_v6_validator`
- Recorded UTC: `2026-10-01T19:32:46.831029+00:00`

The validator read only the v6 authoring and validation contracts, the supplied freeze, the new holdout and all nineteen Markdown documents under `data/synthetic-documents`. The complete file list is in the JSON provenance. The separate validator context did not read prior questions or results, runtime or evaluator implementation, Git history, or the parent conversation. No API, application or Git operation occurred. The suite was not edited.

Each case has an independently derived expected behavior and a source-based access and scope reason. Each required fact has an individual clause-to-question mapping, exact quotation check, explicit role check and semantic support decision. Reviews covered conditions, subjects, negation, units and should/may/must distinctions. Non-answer cases were checked for genuine ambiguity, inaccessible source membership, corpus-wide missing information or separate-project evidence. The ten multi-document cases require complementary evidence; the four precedence cases rest on actual documented supersession or exceptions. The injection category includes two benign discussion controls and four adversarial prompts. Five permission pairs include an explicit no-inheritance test for the Operations document.

Category counts are factual 8, multi-document 10, memory 8, permissions 10, ambiguity 6, missing information 6, injection 6, conflicting policies 4 and uploaded-document isolation 2. Expected behaviors are answer 38, refusal for access 7, not found 9 and clarification 6. Difficulty labels are easy 2, medium 43 and hard 15. All 60 question strings are distinct. Intentional related policy material recurs across memory and permission controls; no historical novelty claim is made here.

The suite freeze binding matches the supplied commit, and all nineteen corpus hashes match the freeze. Independent authoring chronology and historical overlap cannot be established from this validator's permitted inputs; root performs the custody and overlap checks without exposing prior cases to the validator. The two fixtures are short ASCII text and contain facts absent from the Northstar corpus. Actual separate-project upload/index creation and prevention of cross-project retrieval remain runtime checks. No application performance, retrieved output, grader correctness or live enterprise state was assessed.
