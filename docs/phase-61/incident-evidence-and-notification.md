# Incident Evidence Retention And Notification Responsibilities

## Evidence

- Preserve content-free security events, configuration/version provenance, relevant audit fingerprints, deployment identifiers, and integrity-chain status.
- Do not copy prompts, source documents, secrets, access tokens, raw personal data, or another tenant's identifiers into incident tickets or chat channels.
- Local incident evidence follows the Phase 60 application-log 30-day policy by default. An authorized incident hold may suspend deletion; it must record an owner, reason, start, review date, and release decision.
- A production policy must separately define external security-log retention, backup expiry, legal preservation, regional storage, access review, and tenant deletion/export behavior.

## Responsibility matrix

| Activity | Portfolio/local owner | Production requirement |
| --- | --- | --- |
| Detection review | unassigned | named primary and backup on-call |
| Technical containment | service/security owner unassigned | authorized incident commander and service owners |
| Tenant/customer notice | prohibited from local automation | privacy/legal-approved decision maker and channel |
| Regulator/law-enforcement notice | not applicable to synthetic local data | legal determination against applicable deadlines |
| Evidence access | local admin only | least-privilege incident role with access audit |
| Closure/retest | local tabletop reviewer | independent or separate reviewer for material incidents |

No local alert sends email, SMS, chat, or customer notification.
