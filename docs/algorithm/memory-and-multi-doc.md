# Memory And Multi-Document Behavior

Memory and multi-document handling are separate features. Memory helps interpret follow-up questions. Multi-document mode tries to retrieve evidence from more than one source.

## Conversation Memory

Memory lives in `apps/api/app/memory`.

The system stores chat sessions and messages in Postgres. On a new request with a session ID:

1. Load up to 8 recent messages.
2. Detect whether the new question looks like a follow-up.
3. Rewrite the follow-up into a standalone retrieval question.
4. Build a small memory context string.
5. Retrieve fresh chunks using the rewritten question and current role.
6. Generate the answer from fresh retrieved chunks only.

## Follow-Up Detection

`followup_detector.py` uses simple rules:

- phrase starts such as `what about`, `does that`, `how long`, `when does`
- pronouns and references such as `that`, `it`, `this`, `same`, `also`
- previous turns must exist

This is intentionally cheap and predictable.

## Query Rewriting

`query_rewriter.py` has targeted rewrite rules for known benchmark scenarios. Examples:

| Previous topic and follow-up | Rewritten retrieval question |
| --- | --- |
| Vacation, "carry" | "Can employees carry unused vacation days into next year?" |
| Remote work location, "fewer than 15" | "For a temporary remote work location change, what happens if it is fewer than 15 business days?" |
| Personal device, "restricted data" | "Can an employee download restricted data to a personal device?" |
| Implementation, "how long" | "What is the typical implementation range for standard deployments?" |

If no specific rule matches but a topic exists, the system appends topic context to the question.

## What Memory Can Influence

Memory can influence:

- the standalone retrieval question
- the prompt note that says what the previous topic was
- source IDs from previous assistant citations, as context labels

Memory cannot safely supply:

- new factual evidence
- restricted details
- citations for the current answer
- authorization

The prompt explicitly says memory is for query clarification only.

## Memory Evaluation

The Phase 36 memory evaluation measured:

| Metric | Value | Sample |
| --- | ---: | ---: |
| Follow-up detection accuracy | `1.000` | 20 |
| Query rewrite quality | `1.000` | 20 |
| Memory answer accuracy | `1.000` | 20 |
| Memory citation accuracy | `1.000` | 20 |
| Memory permission leakage | `0.000` | 20 |
| Hallucination rate on follow-ups | `0.000` | 20 |

The evaluator approximates rewrite quality by checking whether the rewritten query retrieves the expected source.

## Multi-Document Detection

Multi-document mode is controlled by `multi_doc_mode`:

| Mode | Behavior |
| --- | --- |
| `off` | Always use normal retrieval. |
| `force` | Always use multi-document retrieval. |
| `auto` | Use `is_multi_document_question`. |

`multi_doc_detector.py` looks for:

- pairs of domain terms, such as remote work plus device security
- conjunction patterns such as "both ... and", "as well as", or "in addition to"
- enough question length to avoid firing on very short phrases

## Multi-Document Retrieval

`query_decomposer.py` implements multi-document retrieval:

1. Ask OpenAI to decompose the user question into 2 to 3 search queries.
2. If decomposition fails, fall back to the original question.
3. Run normal retrieval for each subquery.
4. Deduplicate chunks by chunk ID.
5. Sort merged chunks by score.
6. Return up to 10 chunks.

Each subquery still uses normal role and scope filtering.

## Multi-Document Prompting

For multi-doc answers:

- chunks are grouped by document with `group_chunks_by_document`
- generation uses a multi-document prompt format
- the API defaults to prompt `v4` for multi-doc mode unless another prompt version is supplied
- answer finalization uses lower support thresholds than single-doc mode

The lower thresholds reduce over-aggressive `not_found` responses, but can also make weaker multi-source support harder to distinguish.

## Current Multi-Doc Evidence

The standalone multi-document eval artifact compares baseline retrieval/generation against multi-doc mode:

| Metric | Baseline | Multi-doc |
| --- | ---: | ---: |
| Answer accuracy | `0.700` | `0.850` |
| Citation accuracy | `0.750` | `0.900` |
| Response type accuracy | `0.900` | `1.000` |
| All required sources cited | `0.600` | `0.800` |
| Failed questions | 4 | 2 |
| Hallucination rate | `0.667` | `0.700` |

The later Phase 38 answer-quality run still has 6 failed questions, mostly multi-document:

- `MULTI-004`
- `MULTI-005`
- `MULTI-008`
- `MULTI-013`
- `MULTI-017`
- `MULTI-020`

## Ambiguity Behavior

Current ambiguity handling has two layers:

1. Prompt `v8` instructs the model to ask a clarifying question when approval, location, data classification, role, amount, contract status, customer tier, vendor risk, deployment timing, or sales stage is unclear.
2. `_policy_response` has `AMBIGUOUS_PATTERNS` that return `clarify` before generation.

Phase 38 improved clarification accuracy from `0.500` to `1.000` on the measured answer-quality run. However, the detector is still pattern-based, and Phase 39 is planned to make ambiguity orchestration more explicit and general.

## Main Limitations

| Area | Limitation |
| --- | --- |
| Memory detection | Heuristic and benchmark-tuned; new follow-up styles may need new rules. |
| Memory context | Previous source labels are included, but previous source text is not revalidated unless retrieved again. |
| Query decomposition | Uses OpenAI; if it fails, fallback is just the original question. |
| Multi-doc source coverage | Merging by top score does not guarantee each required source domain is represented. |
| Ambiguity | Current strict behavior relies on pattern lists and prompt instructions rather than a full intent model. |

## Why Phase 39 Still Matters

Phase 39 is the right next implementation phase because current failures are concentrated in multi-document source coverage and citation completeness. The likely improvement is not just better wording in the prompt; it is more explicit orchestration:

- identify required answer parts
- retrieve for each part
- verify each required source is represented
- clarify underspecified intent before generation
- keep permission filtering before every synthesis step
