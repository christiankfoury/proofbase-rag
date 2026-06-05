# Phase 9 Conversation Memory Design

## Goal

Phase 9 adds safe session-level conversation memory so the agent can answer follow-up questions without treating prior assistant messages as source evidence.

## Memory Scope

The system may use:

- previous user questions
- prior assistant answer summaries
- previous cited document IDs
- previous cited section headings
- previous response types

The system must not use:

- messages from other sessions
- messages from other users
- hidden chain-of-thought
- long-term preferences
- restricted prior context that the current role cannot access

## Runtime Flow

1. User creates or provides a chat session.
2. User asks a question.
3. The system loads recent messages for that session only.
4. A follow-up detector decides whether memory is needed.
5. If needed, the query rewriter creates a standalone retrieval question.
6. Retrieval runs against the rewritten question.
7. Permission filters still apply before generation.
8. The answer generator receives retrieved chunks plus a short memory summary.
9. The answer and metadata are stored as chat messages.

## Source-of-Truth Rule

Conversation memory is only used to clarify the question. Retrieved document chunks remain the only source of factual answers and citations.

