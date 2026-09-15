# Phase 66: evaluator correction and saved-response reanalysis

The user accepted the agent's observations and authorized evaluator correction. This is not evidence that a person adjudicated every case. Human review fields remain unchanged.

## Declared before reanalysis

Keep Phase 65's runtime, sealed cases, raw responses, grades, 33/60 protocol result and API ledger immutable. A new ledger starts with the exact previous ledger entries, retaining the same cumulative USD 0.75 ceiling. The approved existing API credential is reused. No application queries or embeddings are permitted in this phase.

Use a separately versioned model grader, answer-dimensions.v5, with six dimensions and no combined headline score:

- Factual support: supported by available authorized sources, contradicted by those sources, or unresolved. Missing evidence is not proof of falsity. Pure non-answers have no factual claims and are not applicable.
- Completeness: semantic coverage of required facts. Missing information does not make other true statements false. Faithful paraphrases count; redundant repetition of an inapplicable normal threshold is not required when the relevant exception is explained.
- Relevance: addresses the user's question in conversation context. A true answer on the wrong topic fails here.
- Citation support: actual cited chunk content entails each factual assertion. Gold reference quotes and other uncited sources cannot satisfy this dimension. This deliberately changes the unit from the original exact excerpt to the cited chunk; it is a new rubric, not a correction of historical totals.
- Quotation fidelity: deterministic contiguous normalized substring check. Stitched sentences can fail this while being factually supported.
- Response behavior: the prose provides an appropriate answer, refusal or clarification. Metadata type matching remains a separate diagnostic.

Malformed grading produces unresolved semantic dimensions, never an inferred product error or pass. A source reference must exist and a claimed text span must appear in the answer; only sentence-initial capitalization differences are tolerated. The model's claim coverage and semantic entailment judgments remain fallible. No factual-accuracy percentage or human-validation claim will be inferred.

## Inputs and custody

Only saved response text, the original question/history, required facts, forbidden assertions, authorized retrieved chunks and role-authorized original gold quotes enter the grader. Full cited chunks are independently matched to saved authorized evidence; source and citation references use separate namespaces. History and source instructions remain untrusted data. Runtime diagnostics, original verdicts and original grader reasons are excluded from the model input. The original corpus/runtime freeze is verified before preparing inputs.

Save model inputs, output judgments, deterministic dimension results and hashes for each response. A new run refuses an existing output folder; no selective retries. A frozen evaluator-code inventory and passing calibration must precede the reanalysis. Preserve interrupted rows if calls fail. Offline replay verifies source hashes, inputs, grading contracts and aggregates; it does not rerun semantic judgments.

## Calibration and verification

Twelve visible agent-authored fixtures cover correct/wrong numbers, negation, omissions, wrong-topic truth, stitched quotes, uncited true facts, unknown additions, safe/nonresponsive refusals, response-type disagreement and grader-directed injection. Require all fixtures to meet their predeclared dimension outcomes with valid contracts before freezing. These are development checks, not human-labeled or independent grader accuracy.

Local tests cover dimension separation and malformed/reference/span validation. Check old/current Phase 65 reports unchanged, scan artifacts for credentials, build the web page, review the commit, push main, and publish an easy-to-read per-case comparison. Runtime remediation is a later phase; do not tune against this exposed suite or present rescoring as application improvement.

Reference: [OpenAI evaluation best practices](https://developers.openai.com/api/docs/guides/evaluation-best-practices) and [pinned grader model](https://developers.openai.com/api/docs/models/gpt-4.1-mini), checked 2026-09-14. Model judgments require scrutiny even when structured outputs are valid.

First calibration attempt: 8/12 passed. Preserved with the exact grader source in calibration-attempt1.json. Corrected speech-act handling, conjunction support and verbatim-span instructions before the second calibration; expected fixture outcomes remain unchanged. No saved-response reanalysis occurred before this correction.

Second calibration: 11/12 passed, still accepting an unsupported addition despite stronger instructions. Preserved in calibration-attempt2.json. Version 3 separates claim verification (no question or gold facts) from relevance/completeness/behavior assessment. Each response uses two bounded grader calls. Expected outcomes remain unchanged.

Third calibration: 11/12 passed. The unsupported addition now fails citation support and remains factually unresolved, but a conflicting numeric amount was labeled unknown rather than contradicted. Preserved in calibration-attempt3.json. Version 4 clarifies incompatible values for the same rule; expected outcomes remain unchanged.

Fourth calibration: 11/12 passed. A shared source-checking instruction caused the coverage-only call to demand source evidence for an exactly correct answer. Preserved in calibration-attempt4.json. Version 5 uses a distinct coverage prompt so coverage does not attempt to rejudge truth or citations. Expected fixtures remain unchanged.

Fifth calibration passed 12/12 with valid grading contracts. Calibration hashes bind the grader, fixtures and budget wrapper. The runner additionally verifies the continued ledger preserves the entire original prefix; its final code is frozen separately after local testing. Passing these visible examples is not independent validation or a guarantee on the saved-response reanalysis.
