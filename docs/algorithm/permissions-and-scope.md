# Permissions And Scope

> Phase 57 update: every App request resolves an explicit tenant alongside the internal user. The default UI still uses the isolated Northstar demo tenant. Optional local OIDC fixtures validate signed claims and then require an active internal membership; token claims cannot create membership. Normal database transactions assume a non-bypass runtime role with forced PostgreSQL row-level security, so a missing application tenant predicate does not expose another tenant.

Permission filtering is a hard design requirement in this project. Restricted chunks should not reach the model, citations, memory evidence, or user-visible retrieved context for roles that cannot access them.

## Scope Layers

The system applies three different boundaries:

| Boundary | Where it is applied | Purpose |
| --- | --- | --- |
| Tenant RLS | PostgreSQL policy on every tenant-owned table | Prevents runtime transactions from reading or mutating another tenant even if an application predicate is missing. |
| Project membership | API route before retrieval | The active user must belong to the selected project inside the active tenant. |
| Department scope | SQL retrieval filter when supplied | Restricts retrieval to one department inside a project. |
| Role access | SQL retrieval filter and generation recheck | Prevents documents outside the user's role from becoming evidence. |

## Project Scope

For App-side queries with `project_id`, `apps/api/app/main.py` calls `require_project_member`. If the user is not a project member, retrieval does not run.

The effective role is also derived differently:

- With project scope: use the signed-in demo user's `business_role`.
- Without project scope: admins can request a role for Dev/Admin testing; non-admins use their own business role.

This keeps `/chat` closer to an end-user assistant while preserving Dev/Admin evaluation workflows.

## Department Scope

If `department_id` is supplied, `project_id` is required. Both vector and keyword retrieval add:

```sql
and d.project_id = %s::uuid
and d.department_id = %s::uuid
```

Department scope is strict. It is not a ranking boost.

## Database Enforcement

Each normal database transaction sets a local runtime role plus tenant, user, and platform-admin settings. The runtime role is non-login, non-superuser, and cannot bypass RLS. Forced policies cover application data, ingestion data, identity/session records, audit records, and tenant-owned evaluations. Composite tenant foreign keys prevent children from being attached to parents in a different tenant.

Global benchmark evidence remains platform-owned with a null tenant and is writable only from the explicit platform system context. Local setup and evaluation scripts use that context outside production. A hosted database with separately provisioned owner/runtime logins has not been connected, so this is local policy evidence rather than a hosted deployment claim.

## Role Filtering Before Generation

The Phase 52 request assessor runs before retrieval, but it is not part of authorization. It receives no effective role, project or department authorization, document metadata, or retrieved content. A `continue` action means only “the request may proceed to the normal authorization and retrieval path”; it never means “the user may access the requested subject.”

Vector and keyword retrieval both use:

```sql
where d.access_roles && %s
```

The `%s` value is the list from `role_variants(user_role)`. This allows role aliases such as `IT Admin` and `IT/Admin`, and gives `Admin` broad access in the local demo.

Only rows from this allowed query are converted into `RetrievedChunk` objects.

## Permission Audit Trace

The retrievers also run a candidate query before role filtering. That query collects metadata only:

- chunk ID
- document ID
- project ID
- department ID
- access roles
- restricted flag
- sensitivity

`build_permission_trace` compares candidate rows with the current role, counts blocked chunks, and logs audit events such as `permission_filtered_retrieval` and `unauthorized_candidate_blocked`.

This trace helps prove that restricted candidates were blocked without giving those chunks to generation.

## Generation Recheck

`generate_answer` performs a second defensive check:

1. It receives the retrieved chunks and user role.
2. It calls `unauthorized_chunks`.
3. If any chunk is not allowed, it logs `unauthorized_chunks_reached_generation`.
4. It returns `refuse_no_access` without calling OpenAI.

This does not replace SQL filtering. It is a fail-closed backup.

## Citations And Permission

Citations are built only from the retrieved chunks passed into generation:

- Model-provided citations are matched back to retrieved chunks.
- Citation backfill chooses from retrieved chunks only.
- Validation rejects citations whose chunk IDs are not in the retrieved chunk list.

So citations cannot point to a restricted document unless that document already passed retrieval. Permission evaluation checks for restricted citation leakage separately.

## Memory And Permission

Memory does not bypass permissions:

- Previous turns can rewrite the question.
- Previous citations can be listed as memory context by document ID and section heading.
- The current request still retrieves chunks using the current role.
- The answer prompt is told not to use memory as source evidence.

The Phase 36 memory run measured memory permission leakage as `0.000` over 20 follow-up questions, plus focused boundary probes.

## Current Permission Evidence

The latest permission run is `phase46-permission-evaluation`:

| Metric | Value | Sample |
| --- | ---: | ---: |
| Permission leakage rate | `0.000` | 20 |
| Blocked-answer accuracy | `1.000` | 20 |
| Unauthorized chunk exposure rate | `0.000` | 20 |
| Restricted citation leakage rate | `0.000` | 20 |
| Unauthorized chunks reached generation rate | `0.000` | 20 |
| Authorized retrieval accuracy | `1.000` | 20 |

The run also checks that an authorized role can retrieve each restricted source.

## Could Unauthorized Chunks Appear Elsewhere?

| Surface | Current behavior |
| --- | --- |
| Prompt context | Should not, because retrieval filters before generation and generation rechecks. |
| Citations | Should not, because citations are matched to retrieved chunks. |
| API `retrieved_chunks` payload | Should not, because it is built from retrieved chunks. |
| Memory | Prior citations can be summarized by document ID and section heading, but current retrieval still filters. |
| Audit logs | Candidate-blocked logs include blocked document IDs, not source text. |
| Feedback/review | User-submitted feedback can include answer and citations from a prior response; it should still be reviewed before benchmark promotion. |

## Product Readiness Boundary

The permission model is strong for the synthetic demo and benchmark:

- document-level role metadata
- project membership
- SQL role filtering
- generation recheck
- permission evaluation artifacts

It is not production identity yet. Local demo auth is not SSO, and real enterprise connector permissions are planned, not implemented.
