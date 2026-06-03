# Phase 3 Benchmark Design

## Purpose

The Phase 3 benchmark defines how the Enterprise Knowledge Agent will be evaluated against the synthetic Northstar Analytics knowledge base. It is designed to test whether the RAG system retrieves the right context, answers accurately, cites the right source sections, respects document permissions, refuses missing information, and handles follow-up questions.

The benchmark is intentionally created before backend implementation so quality can be measured from the first baseline RAG version.

## Source-of-Truth Rule

The only source of truth for answerable benchmark questions is `data/synthetic-documents/`.

Every answerable question must map to one or more specific document IDs and source sections or quotes. The benchmark must not introduce facts that are absent from the synthetic corpus.

Restricted and missing-information questions test refusal behavior. They should not require the model to reveal unauthorized details or invent unsupported answers.

## Distribution

| Question Type | Count | Expected Behavior |
|---|---:|---|
| Simple factual lookup | 20 | `answer` |
| Multi-document | 10 | `answer` |
| Permission-restricted | 10 | `refuse_no_access` |
| Missing-information | 10 | `say_not_found` |
| Ambiguous | 5 | `ask_clarifying_question` |
| Conversation memory | 5 | `answer_with_memory` |

Total: 60 questions.

## Evaluation Goals

The benchmark supports these metrics:

- Retrieval hit rate
- Answer accuracy
- Citation accuracy
- Faithfulness
- Refusal accuracy
- Hallucination rate
- Permission leakage rate
- Memory accuracy

## Benchmark Rules

- Answerable questions must include at least one expected source document.
- Multi-document questions must include at least two expected source documents.
- Missing-information questions must have no expected source document.
- Permission-restricted questions should identify the restricted source being tested, but the expected answer must be a refusal.
- Conversation-memory questions must include previous turns and must still respect permissions.
- Ambiguous questions should ask for clarification instead of inventing approval.

## Recruiter-Facing Value

This benchmark makes the project measurable. It allows the portfolio demo to show baseline RAG results, identify weak retrieval or citation behavior, improve the system, and show measurable gains across versions.
