# Phase 60 Secrets And Log Operations Policy

## Access

- Application users cannot call observability or audit endpoints; only Dev/Admin identities can.
- The application runtime can append its local observability file and tenant-scoped audit rows. A hosted deployment must separate runtime, operator, backup, and incident-responder permissions.
- Logs and exports must never be used as RAG evidence or a cross-tenant search surface.

## Retention, deletion, export, and backup

- Observability JSONL: 30 days by default.
- Audit/security records: 365 days by default.
- Incident evidence hold overrides routine deletion until the incident owner releases it.
- Malformed local lines are retained for review rather than silently discarded.
- Tenant content export/deletion and backup expiry must include chats, feedback, documents, file objects, audit rows, external telemetry, and backups. The local helper proves JSONL deletion semantics only; an end-to-end tenant workflow is not claimed.
- Production logs, exports, and backups require encryption in transit and at rest, restore testing, access review, and documented cryptographic-key ownership.

## Rotation and revocation rehearsal

1. Create a replacement provider credential without disabling the active credential.
2. Atomically replace the mounted file and apply owner-only permissions.
3. Restart the application because settings are process-cached; verify readiness and one bounded synthetic operation.
4. Revoke the previous provider credential and confirm it fails from a controlled test client.
5. Search privacy-safe security events for unexpected failures, then record credential ID/fingerprint, owner, time, and result—never the value.
6. For suspected exposure, revoke first, preserve incident evidence, rotate dependent credentials, assess Git/build/log history, and follow the Phase 61 incident process.

The local test rewrites and deletes a temporary mounted file to demonstrate rotation/revocation behavior. It does not rotate a live external credential.

## External and deployment requirements

- Managed secret store and workload identity: not connected.
- Central log/SIEM destination, on-call owner, and notification channel: Phase 61 external-integration gate.
- Independent validation: required; no internal test or checklist substitutes for it.
