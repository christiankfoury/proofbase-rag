# Memory Permissions Safety

## Critical Rule

Prior conversation context must never bypass retrieval-time permissions.

## Safety Controls

- The current `user_role` is always used for retrieval.
- Prior messages are used only to clarify or rewrite the query.
- Prior assistant answers are not source evidence.
- Citations must come from currently retrieved and currently allowed chunks.
- The answer generator still refuses if unauthorized chunks ever reach generation.
- Session memory is scoped by `session_id`.

## Role Changes

If a role changes between turns, the system uses the role supplied on the current request. Retrieval is rerun with that current role.

If the prior topic was restricted and the current role lacks access, the system should refuse or return not found based on the current accessible corpus.

## Deferred

Production user identity, cross-session memory, and long-term personalization are intentionally deferred.

