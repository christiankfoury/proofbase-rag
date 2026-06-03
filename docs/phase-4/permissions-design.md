# Permissions and Access Control Design

## Roles

Use these canonical roles:

- Employee
- Sales Representative
- Manager
- HR Admin
- IT Admin

Users may have multiple roles. Access is granted if any assigned role has read permission for a document.

## Document Permission Model

Documents grant read access by role through `document_permissions`.

Chunks inherit permissions from their parent document. Phase 5 should implement document-level permissions first. Chunk-level permissions can be added later only if evaluation shows a concrete need.

## Query-Time Filtering

Permission filtering must happen before retrieval context is built.

The retrieval query should:

1. Resolve user roles.
2. Find document IDs visible to those roles.
3. Restrict vector and keyword search to visible document IDs.
4. Return only authorized chunks.
5. Log the permission filter summary.

Unauthorized chunks must never be passed to the LLM.

## Restricted Access Attempts

When a user asks a question that appears to target restricted content, the backend should:

- Return `refuse_no_access`.
- Avoid revealing restricted details.
- Avoid summarizing restricted document contents.
- Write an `audit_logs` record with action such as `restricted_query_refused`.

## Examples

Employee asks:

> What is the promotion calibration process?

Expected:

- `refuse_no_access`
- Reason: `MGR-002` is Manager-only.

Manager asks:

> What is the promotion calibration process?

Expected:

- Answer with citation from `MGR-002`.

Employee asks:

> What are the manager compensation bands?

Expected:

- `say_not_found` or safe refusal.
- Reason: compensation bands and compensation formulas are intentionally absent from the corpus and should not be invented for any role.

## Permission Leakage Measurement

Permission leakage rate is:

```text
unauthorized benchmark answers containing restricted facts / total permission-restricted benchmark questions
```

The metric should trend from X% to Y% toward 0% across system iterations.

## MVP Defaults

- Do not expose restricted document titles to unauthorized users unless a later product decision changes this.
- Do not log restricted chunk text by default.
- Use document-level access control in Phase 5.
- Use benchmark permission tests from `data/evaluation/benchmark-questions.json`.
