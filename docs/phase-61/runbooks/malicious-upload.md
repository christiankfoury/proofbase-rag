# Malicious Upload Runbook

Local tabletop scenario: the known harmless scanner signature is rejected in quarantine.

## Trigger
Malware detection, scanner anomaly, archive/polyglot suspicion, or repeated parser failure.
## Immediate containment
Keep the original quarantined, prevent review/index/download grants, stop the worker if compromise is suspected, and preserve metadata.
## Evidence
Retain opaque storage key, content hash, scanner/parser versions, bounded reason, lifecycle state, and event fingerprints; do not open on an analyst workstation.
## Investigation
Confirm envelope, signature, scanner status, parser sandbox boundary, duplicates, and other objects processed by the worker.
## Notification
Security/service owners are unassigned; tenant notification requires privacy/legal authorization and a connected channel.
## Recovery
Rebuild the worker if needed, update detections, rescan safe retained objects, and never auto-index a rejected file.
## False positives
The explicit local fixture signature or malformed benign PDF.
## Exit and retest
Prove rejection, no indexing, storage isolation, worker health, and regression coverage before reopening uploads.
