# Phase 27 Local Demo Auth Design

## Purpose

Phase 27 adds a production-shaped local identity and membership layer for the portfolio demo. It is not production SSO and does not add passwords, OAuth, sessions, MFA, Clerk, Auth.js, or hosted identity claims.

The goal is to stop App-side flows from trusting arbitrary client-sent roles. The API now resolves a seeded demo user, derives the effective business role server-side, and checks project membership before returning project-scoped data.

## Seeded Demo Users

The schema seeds `demo_users` and `project_memberships`.

| Demo user | Business role | Admin | Northstar membership |
| --- | --- | --- | --- |
| Emma Employee | Employee | No | Viewer |
| Sam Sales | Sales Representative | No | Viewer |
| Mina Manager | Manager | No | Viewer |
| Harper HR Admin | HR Admin | No | Viewer |
| Ira IT Admin | IT Admin | No | Viewer |
| Kai Knowledge Manager | Knowledge Manager | Yes | Owner |
| Gus Guest | Employee | No | None |

`DEFAULT_DEMO_USER_ID` controls the fallback user when no `X-Demo-User-Id` header is supplied. The default is Emma Employee.

## API Behavior

New endpoints:

- `GET /auth/demo-users`
- `GET /auth/me`

New request header:

- `X-Demo-User-Id: <demo_user_id>`

Project and query behavior:

- `/projects`, project detail, department detail, and document-library reads require project membership unless the resolved user is admin.
- Project, department, and upload mutations require admin or project `contributor`/`owner` membership.
- Project-scoped `/query` ignores client-provided `user_role` and uses the resolved demo user's `business_role`.
- Unscoped Dev/Admin simulation queries still allow the admin user to pass a simulated role for evidence tools.
- Retrieval permission filtering remains unchanged: document and chunk `access_roles` still gate context before generation.

Dev/Admin behavior:

- Evaluation, audit, observability, feedback review, and algorithm review endpoints require the admin demo user.
- Non-admin users receive `403`.

## Frontend Behavior

The header strip includes a compact signed-in-as selector. The selected ID is stored in localStorage for client requests and mirrored into a same-site cookie so server-rendered Dev/Admin pages fetch with the selected local demo identity.

The Chat Demo shows the current signed-in role as read-only context. Presets can switch the demo user, but App queries no longer use a free-form role selector as the authority.

Dev/Admin pages show an access-denied state for non-admin demo users. Admin-only comparison tools are labeled as simulations/evidence tools.

## Limitations

- This is local demo auth only.
- The `X-Demo-User-Id` header is not a secure production credential.
- There is no hosted identity provider, session hardening, tenant isolation, password flow, SSO, MFA, or SCIM.
- Authorization is suitable for local portfolio demonstration and architecture review, not real enterprise deployment.

## Production Handoff

A production phase should replace the demo header with a real identity provider, map provider claims to users and memberships, add migration scripts, add admin permission management, secure cookies or bearer tokens, and define operational ownership for user lifecycle events.
