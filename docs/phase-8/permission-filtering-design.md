# Permission Filtering Design

## Role Model

Supported roles:

- Employee
- Sales Representative
- Manager
- HR Admin
- IT Admin

`IT Admin` and `IT/Admin` are treated as aliases because the synthetic corpus uses both spellings across phases.

## Document Permissions

Each document has:

- `external_document_id`
- `title`
- `department`
- `category`
- `access_roles`
- `restricted`
- `sensitivity`

Sensitivity is derived from the `restricted` flag:

- `restricted = true` -> `sensitivity = restricted`
- `restricted = false` -> `sensitivity = internal`

## Chunk Permission Inheritance

Chunks inherit permission metadata from their parent document at retrieval time:

- document ID
- document title
- section heading
- access roles
- restricted flag
- sensitivity

## Query-Time Filtering

Retrieval filters by role before returning chunks:

```sql
d.access_roles && role_variants(user_role)
```

The same rule applies to:

- vector retrieval
- keyword retrieval
- hybrid retrieval

Hybrid retrieval uses permission-filtered vector and keyword candidate sets before merging scores.

## Safety Rule

The answer generator validates the retrieved chunks again before making an LLM call.

If any chunk is not allowed for the provided role, generation returns `refuse_no_access`, logs the event, and does not call the model.

