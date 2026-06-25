# Phase 27 Checklist

## Implemented

- Added seeded `demo_users` and `project_memberships`.
- Added local demo auth resolution from `X-Demo-User-Id`.
- Added `GET /auth/demo-users` and `GET /auth/me`.
- Added server-side membership checks for project, department, document-library, upload, and mutation routes.
- Changed project-scoped `/query` to derive `user_role` from the resolved demo user.
- Gated Dev/Admin API surfaces to the Admin persona.
- Added a header signed-in-as selector.
- Mirrored selected demo identity to a cookie for server-rendered Dev/Admin fetches.
- Replaced Chat Demo role selection with read-only signed-in role context.
- Labeled Dev/Admin role comparison tools as admin-only simulations.
- Updated README, deployment environment docs, demo notes, and roadmap progress.

## Not Implemented

- Production auth provider integration.
- Passwords, OAuth, SSO, MFA, SCIM, or hosted session management.
- Admin UI for editing users or memberships.
- Tenant-level isolation beyond seeded local demo project membership.
- Azure deployment.

## Recruiter Demo Note

Use the header selector to switch between demo users. Emma Employee can use the App workspace and scoped chat. Gus Guest demonstrates project denial. Kai Admin can access Dev/Admin evidence tools.
