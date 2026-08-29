# Phase 61 Security Monitoring And Incident Response Design

## Goal

Provide production-shaped, locally verifiable security monitoring without claiming a connected SIEM, pager, immutable external archive, or staffed response function.

## Architecture

Runtime and audit paths map bounded actions into `security_event.v1`. Raw tenant, user, request, project, and document identifiers become one-way fingerprints. Arbitrary string metadata is dropped; only an allowlist of operational enums, hashes, counts, booleans, and durations survives. Prompts, answers, source text, filenames, tokens, and secrets are never accepted as security-event fields.

The provider-neutral sink contract currently has one implementation: an append-only local JSONL hash chain. Every record commits to the previous hash, sequence, and canonical event. Reads fail closed when verification fails. Tenant-scoped admin reads compare only opaque tenant fingerprints. A separate local JSONL notification sink proves threshold-to-delivery wiring.

This local chain is tamper-evident, not immutable: the application runtime can rewrite the file. Production must send events to storage outside the runtime's rewrite authority.

## Event sources

- OIDC fixture authentication failures and cross-tenant claim mismatches.
- admin-boundary authorization denials.
- existing permission, injection, assessment, validator, rate-limit, upload/parser, admin-change, and cost audit actions.
- secret/config startup failures are taxonomy-ready; startup can fail before a sink exists, so the deployment platform must capture and route them externally.

## Decisions and boundaries

- Event and notification paths are local, gitignored, and excluded from container build context.
- Alert owners remain explicitly `*_unassigned`.
- The API and page are admin-only and tenant-scoped.
- Live destination, named on-call owner, escalation target, and notification channel require the Phase 61 external-integration decision.
- No Azure resource, paid service, premium licence, Marketplace purchase, or external call is part of this phase.
