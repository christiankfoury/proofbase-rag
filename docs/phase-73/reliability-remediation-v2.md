# Reliability remediation after the small live diagnostic

Authorized 2026-10-02. Goal: correct source-confirmed false-premise routing,
scenario-number provenance, validator claim rewriting, citation excerpt selection,
substring source planning and conservative diagnostic payload estimation.
App chat/backend and diagnostic tooling are affected; no permission grants,
benchmark edits, evaluator qualification or full evaluation are authorized.

Acceptance: retain failing offline reproductions before fixes; add new positive,
negative and interaction controls; check shared request/evidence/validation and
permission paths; review, commit and push the offline change. Preserve old prompts,
raw evidence, ledgers and unrelated request logs. Semantic improvements still need
live evidence; no overall rate claim follows from mocked tests.

After the offline gate, the user explicitly authorizes six new live diagnostic
questions, at most USD 0.50 from the existing USD 3.76906404 remainder. Verify
current prices and assembled payloads before execution. Synchronous requests,
no provider retries, seven chat and three query embeddings per case, 42 chat /
18 embeddings / 60 total maximum. Input/output caps remain 16,384/2,048 for chat
and 8,192 for embeddings. Preserve any blocked or unknown outcome and stop paid
work; do not repeat exposed cases or spend unused allowance automatically.

## Reproduction and implementation

The preserved compatible baseline ran 15 new tests: seven failures, three errors,
five passes. The errors expose the missing proposed contradiction contract, not
three additional measured application failures. The earlier harness attempt is
also retained (it selected v3 before that prompt existed). All 25 final new tests
pass with network transports blocked, including v3 application caller tests,
one-repair exhaustion, unauthorized references and numeric provenance controls.

- Evidence assessment now recognizes a source-backed denial as answerable. Fact
  support determines the overall route; an unsupported fact is never promoted
  merely because the model attached a topical chunk ID. Unresolved source
  conflicts, genuinely missing facts and unauthorized references remain guarded.
- Validation v3 binds every claim to an exact complete candidate sentence/unit,
  requires a supporting authorized citation, and rejects omissions or narrowing.
  Request-only numbers require typed scenario provenance, an exact request quote,
  and supported rule application. Code-authored answers retain the stricter
  source-only numeric guard. This depends on semantic role classification; it
  is not a general guarantee that a model cannot misclassify a user number.
- Citation fallback ranks contiguous sentence/paragraph windows against answer
  text instead of showing an arbitrary prefix. Existing exact quotations remain
  unchanged; excerpt relevance alone never establishes entailment.
- Source planning and multi-document detection use complete terms, preserving
  ordinary plurals, phrase separators and the explicit remote/remotely variant.
  The shared tests caught and fixed the initial remotely regression.
- A pinned local tokenizer estimates complete JSON payloads including schemas,
  plus 2,048 tokens for framing. Fifty-six captured/reconstructed payloads pass;
  the three old blocked bodies reassemble at 5,570 / 5,353 / 5,433 reserved input
  tokens. Another 4,096-token dynamic allowance fits beneath the unchanged cap.
  Actual bodies are checked before every submission and receipt usage is checked
  afterward; unknown outcomes retain the full reservation and stop the run.

The 30-method shared R1–R4 suite passes (11.392 seconds), explicitly using legacy
v2 validation fixtures for compatibility, alongside the new default-v3 tests.
It includes request/evidence safety, one-repair behavior, scoped multi-source
retrieval, memory boundaries and frozen v6 history replay. The Phase 53 test that
formerly expected unsupported-with-ID promotion now correctly expects not_found;
no benchmark, historical receipt, evaluator judgment or quality gate was changed.
The prior live-v1 report is bound to its older runtime; its last verified evidence
is reused, not falsely reported as a current-runtime replay.

Review covered all runtime, prompts, tests, diagnostic transport, source cases,
accounting bounds and docs. Findings fixed before freeze include the remotely
variant, numeric Source-annotation handling, citation coverage per candidate unit
enforcing the standard service tier, and sharing the payload/ledger stop exception
so a rejected body blocks subsequent submissions. Python compilation and diff
whitespace checks pass. No provider calls occurred offline.

Remaining limitations before the live stage: semantic entailment and scenario-role
classification still need fresh observations; long answers above 16 units fail
closed; lexical planning is a heuristic; excerpt selection does not prove
completeness. Generation prompts and retrieval ranking are unchanged. Broader
permission, department, adversarial and generalization coverage is not measured
by this diagnostic. No evaluator qualification or full evaluation is started.

## Authorized six-question diagnostic

Newly worded source-backed cases and pricing are preserved under
[application-reliability-live-v2](../../data/evaluation/application-reliability-live-v2).
Current standard pricing was verified on 2026-10-02 against official OpenAI
[GPT-4.1 mini](https://developers.openai.com/api/docs/models/gpt-4.1-mini) and
[embedding](https://developers.openai.com/api/docs/models/text-embedding-3-small)
pages: USD 0.40 input / 0.10 cached input / 1.60 output per million chat tokens,
and USD 0.02 per million embedding tokens. At maximum calls and caps, uncached
exposure is USD 0.41582592. Expected consumption remains USD 0.02–0.06; unused
allocation does not authorize another run. Actual results/costs follow separately
after the reviewed offline commit and immutable runtime preflight.
