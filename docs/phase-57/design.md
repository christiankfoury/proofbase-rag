# Phase 57: Database-Enforced Authorization And Tenant Isolation

## Outcome

Proofbase now carries the authenticated tenant and actor into every normal PostgreSQL transaction and relies on forced row-level security for tenant-owned data. Missing an application `tenant_id` predicate is no longer sufficient to read or mutate another tenant's rows through the runtime role.

## Runtime database boundary

`get_connection()` starts a transaction-scoped security context before application SQL runs:

- `SET LOCAL ROLE proofbase_runtime` selects a non-login, non-superuser, non-`BYPASSRLS` role.
- `app.current_tenant_id`, `app.current_user_id`, and `app.platform_admin` are set with `set_config(..., true)` so they cannot leak beyond the transaction.
- production rejects the PostgreSQL superuser connection name and rejects disabled RLS enforcement.
- schema migration uses a separate owner connection path and never borrows the runtime role helper.

Local migration and evaluation scripts may use the explicit system/platform context for synthetic platform-owned artifacts. Production requests fail closed when no tenant context was resolved.

## Policy and invariant coverage

Forced RLS applies to tenant-owned application, ingestion, chat, feedback, audit, identity/session, and tenant-scoped evaluation tables. Platform benchmark/evaluation rows with a null tenant remain readable as global evidence, while only the explicit platform system context may create or change them.

Composite tenant keys and foreign keys prevent relationships such as a document version, chunk, ingestion job, or message being attached to an object owned by another tenant. The embedding cache key also includes tenant identity. Observability summaries discard tenantless legacy records and filter current records to the active tenant.

Denied direct project access records a generic hashed audit event. The response and event do not reveal whether the requested project exists in another tenant.

## Honest security boundary

- The local PostgreSQL container uses the schema-owner login and immediately assumes `proofbase_runtime` for normal transactions. The runtime role itself cannot bypass RLS, and production configuration rejects the `postgres` login, but a separately provisioned hosted application login has not been connected or tested.
- PostgreSQL session settings are trusted application inputs. These controls defend against missing application filters and cross-tenant relationships; they are not a claim that arbitrary SQL injection into the trusted database session is safe.
- Storage quarantine, queues, distributed rate-limit state, hosted identity, and hosted observability remain later phases or external integrations.
- No cloud resource, paid service, premium licence, or Marketplace product was created.
