# Account Compromise Runbook

Local tabletop scenario: repeated invalid tokens followed by unexpected admin changes.

## Trigger
Authentication alert plus suspicious authorization or admin activity.
## Immediate containment
Revoke affected sessions/tokens, block the identity, preserve tenant isolation, and pause high-risk admin actions.
## Evidence
Preserve content-free event fingerprints, token IDs where policy permits, audit records, timestamps, and integrity status. Never collect token plaintext.
## Investigation
Validate issuer/audience, membership/offboarding state, admin changes, and affected tenant scope.
## Notification
Security on-call and tenant-notification owner are unassigned; local automation sends nothing externally.
## Recovery
Restore identity through the approved provider, rotate credentials if implicated, and revalidate memberships.
## False positives
Expired sessions, clock skew, fixture-token rotation, or a legitimate admin bulk operation.
## Exit and retest
Confirm revocation, no cross-tenant access, expected audit events, and separate reviewer approval.
