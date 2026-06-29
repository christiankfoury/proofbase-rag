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
- Phase 46 phrase starts such as `what containment`, `what approvals`, `which answer`, and `which one`
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
| Remote work, "security expectations" | "For remote work, what security expectations from the remote work and device security policies apply?" |
| Promotion calibration, "calibration" | "What does manager guidance say about promotion calibration?" |
| Privileged access incidents, "containment" | "What privileged access containment steps should I take?" |
| Acceptable use, "BYOD" | "What does the Device and BYOD Security Policy say about BYOD device security requirements?" |

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
| Answer accuracy | `0.850` | `0.925` |
| Citation accuracy | `0.850` | `0.925` |
| Response type accuracy | `1.000` | `1.000` |
| All required sources cited | `0.700` | `0.850` |
| Failed questions | 4 | 2 |
| Hallucination rate | `0.050` | `0.000` |

The later Phase 39 live `/query` answer-quality scorecard resolved the benchmark failed-question backlog and reports `0` failed questions over 130 benchmark v1.1 questions. Multi-document source planning is still heuristic, so future work should expand generalization beyond the current benchmark instead of treating this as a production guarantee.

## Ambiguity Behavior

Current ambiguity handling has three layers:

1. `apps/api/app/reasoning/clarification.py` applies pre-retrieval guards for underspecified project, department, role, topic, document-reference, and comparison targets. When it fires, `/query` returns `response_type="clarify"` and a safe `clarification_reason`.
2. Prompt `v8` instructs the model to ask a clarifying question when approval, location, data classification, role, amount, contract status, customer tier, vendor risk, deployment timing, or sales stage is unclear.
3. `_policy_response` has `AMBIGUOUS_PATTERNS` that return `clarify` before generation.

Phase 46 improved the non-benchmark generalization probe suite from `12` failed probes to `0`, with clarification behavior improving from `0.000` to `1.000`. The detector is still pattern-based, but the reason field makes non-answer behavior explainable without exposing restricted information.

## Main Limitations

| Area | Limitation |
| --- | --- |
| Memory detection | Heuristic and benchmark-tuned; new follow-up styles may need new rules. |
| Memory context | Previous source labels are included, but previous source text is not revalidated unless retrieved again. |
| Query decomposition | Uses OpenAI; if it fails, fallback is just the original question. |
| Multi-doc source coverage | Source planning covers known cross-domain pairs, but unseen domain combinations may still need new rules or decomposition help. |
| Ambiguity | Strict behavior relies on pattern lists, pre-retrieval guards, and prompt instructions rather than a full intent model. |

## Current Remediation State

Phase 46 added the first measured generalization remediation pass. The implementation kept the same boundaries:

- memory can rewrite the retrieval query, but retrieved documents remain the only source evidence
- clarification can happen before retrieval when the user intent is underspecified
- each retrieval path still applies project, department, and role filtering before generation
- direct answers are only used when the required retrieved chunks are present
