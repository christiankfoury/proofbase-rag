# Secret Exposure Runbook

Local tabletop scenario: startup rejects a placeholder or unreadable mounted secret.

## Trigger
Secret/config alert, credential found in logs/build/image, or suspected credential disclosure.
## Immediate containment
Disable affected integration, revoke/rotate the credential through its owner, stop vulnerable deployments, and preserve content-free evidence.
## Evidence
Record secret name/category, version fingerprint, detection location, runtime commit, and timestamps; never copy the secret value.
## Investigation
Inspect provider access, build context, logs, history, downstream use, and rotation/revocation status.
## Notification
Security and credential owners are unassigned; external notification follows provider/privacy policy only.
## Recovery
Issue least-privilege replacement, deploy through the approved provider, verify revocation, and rerun scans.
## False positives
Documented fake tokens, hashes, redaction markers, or synthetic scan fixtures.
## Exit and retest
No live value in repository/log/image, old credential rejected, new credential loaded, and access reviewed.
