# Prompt Injection Campaign Runbook

Local tabletop scenario: three bounded injection detections trigger one local alert.

## Trigger
Injection threshold, source-instruction validator failures, unsafe compliance, or correlated obfuscated attempts.
## Immediate containment
Keep authorization unchanged, disable affected model/prompt path if unsafe output is plausible, and preserve content-free traces.
## Evidence
Retain reason codes, route, model/prompt versions, suite/runtime hashes, counts, and citation/evidence decisions. Do not copy tenant prompts or sources into alerts.
## Investigation
Separate direct requests, hostile source content, legitimate security-policy discussion, memory poisoning, and validator drift.
## Notification
AI security/service owners are unassigned; live paging and tenant notification await external decisions.
## Recovery
Patch deterministic/semantic/validator layers, use development cases only, then execute the approved release protocol.
## False positives
Legitimate questions describing injection defenses or approved adversarial evaluation traffic.
## Exit and retest
Zero unsafe compliance and hard safety violations, false-positive review complete, rollback ready, and human approval recorded.
