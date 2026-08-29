# Phase 61 Alert Catalog

| Category | Severity | Threshold/window | Provisional owner | Escalation and false-positive handling |
| --- | --- | --- | --- | --- |
| authentication failure | High | 5 / 5 min | security on-call unassigned | Check issuer/client clock and deployment health before account containment. |
| authorization denial | Medium | 10 / 5 min | security on-call unassigned | Check UI retries and role changes; escalate repeated identity/resource patterns. |
| cross-tenant attempt | Critical | 1 / 60 min | security on-call unassigned | Contain immediately and use the tenant-isolation runbook. |
| injection detection | High | 3 / 10 min | AI security owner unassigned | Sample privacy-safe traces; distinguish policy discussion from attacks. |
| evidence/validator failure | High | 3 / 10 min | AI security owner unassigned | Disable affected model/prompt path if unsafe output is plausible. |
| rate limit | Medium | 20 / 5 min | service owner unassigned | Check legitimate bursts, retry loops, and proxy identity attribution. |
| malicious upload | High | 1 / 60 min | security on-call unassigned | Keep object quarantined and run the malicious-upload playbook. |
| parser failure | Medium | 3 / 10 min | service owner unassigned | Check malformed-but-benign files before security escalation. |
| admin change | Info | 1 / 60 min | service owner unassigned | Review change provenance; notify only for unexpected or high-impact changes. |
| secret/config failure | Critical | 1 / 60 min | security on-call unassigned | Fail closed, contain exposure, rotate through the provider workflow. |
| unusual cost | High | 1 / 60 min | service owner unassigned | Close admission, inspect tenant/accounting drift, and preserve aggregates. |

All thresholds are local starting points, not production-tuned policy. A named owner, backup, acknowledgement SLA, escalation tree, paging channel, maintenance suppression, and tenant-notification authority remain external decisions.
