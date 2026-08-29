# AI Cost Abuse Runbook

Local tabletop scenario: a tenant reaches its admission budget and external AI is not called.

## Trigger
Unusual-cost event, sustained rate-limit denials, accounting drift, or concurrency saturation.
## Immediate containment
Close tenant/provider admission, reduce concurrency, stop retries, and preserve authorization behavior.
## Evidence
Collect content-free tenant fingerprints, operation counts, leases, estimated/reconciled cost, model/version, and time window.
## Investigation
Check retry amplification, client identity, proxy attribution, duplicate jobs, pricing config, and provider billing separately.
## Notification
Service/finance/security owners and channel are unassigned; local alerts do not page or contact a provider.
## Recovery
Correct limits/accounting, require explicit budget approval, and reopen with bounded quotas.
## False positives
Approved evaluation bursts, stale leases, pricing changes, or estimate-versus-bill timing differences.
## Exit and retest
Admission blocks before external calls, counters reconcile, concurrency releases, and owner approves restoration.
