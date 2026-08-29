# Tenant Isolation Concern Runbook

Local tabletop scenario: one cross-tenant claim mismatch event.

## Trigger
Any cross-tenant attempt, unauthorized generation, restricted citation, or tenant-filter integrity failure.
## Immediate containment
Stop affected query/admin paths, revoke implicated sessions, preserve evidence, and do not widen database access for diagnosis.
## Evidence
Collect opaque tenant/user fingerprints, route/action, runtime commit, RLS state, and security-chain head; never copy another tenant's content.
## Investigation
Trace identity selection, tenant context, forced RLS, relationship constraints, permission filtering, and citation authorization.
## Notification
Incident commander and tenant/privacy notification authorities are unassigned; no local external notification occurs.
## Recovery
Patch the boundary, rerun tenant-isolation and permission suites, rotate implicated credentials, and restore gradually.
## False positives
Deliberate local fixture negative tests or stale browser tenant selection.
## Exit and retest
Require zero leakage across deterministic suites, documented scope, and independent retest for a material production finding.
