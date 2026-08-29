# Phase 60: Secrets, Privacy, And Log Controls

## Outcome

Proofbase now has one recursive privacy boundary for audit records, request JSONL, telemetry, and observability reads. Request logs retain a question fingerprint instead of prompt or rewritten-prompt text. Audit metadata hashes content-bearing fields and reduces free-form reasons to bounded codes or fingerprints. FastAPI validation responses retain field location/type without echoing submitted input, and external generation/cleanup failures use generic client messages.

## Secret boundary

`SecretProvider` separates deployment-mounted files from a deliberately unconnected managed-provider adapter. Local development can still use environment values, explicit files, or a process-ephemeral file-access signing key. Production rejects environment-only secret delivery, placeholder credentials, a superuser database URL, non-TLS/unauthenticated Redis, short file-access signing keys, and enabled telemetry without a credential.

Selecting `managed` fails closed because no managed secret-store adapter is connected. This is a provider boundary, not a Key Vault, workload-identity, or managed-secret claim. Mounted files are a production-shaped option and require deployment-owned permissions, rotation, and restart/reload operations.

## Privacy and retention boundary

- Request/audit logs default to IDs, counts, timings, costs, bounded codes, and SHA-256 fingerprints.
- Recursive value-pattern redaction covers bearer tokens, API keys, GitHub/AWS-style credentials, credential-bearing database/cache URLs, common secret assignments, and email addresses.
- JSONL files are created with owner-only mode where the OS supports it.
- Docker build context excludes environment files, runtime logs, uploads, quarantine, local evaluation rows, and local build caches; the image scan also fails if runtime log/upload paths are present.
- Observability defaults to 30 days; audit policy defaults to 365 days. The local JSONL purge helper preserves malformed lines as potential evidence and honors an incident hold.
- Observability and audit endpoints remain Dev/Admin-only. Tenant RLS still scopes database audit records.
- Existing historical local files are sanitized on API read; the unrelated working-tree request-log file was not rewritten or staged.

## Honest limitations

- No managed secret store, workload identity, automatic provider rotation, centralized log platform, immutable/WORM storage, tenant export service, backup workflow, or cryptographic deletion is connected.
- Settings cache secrets for the process lifetime; mounted-file rotation requires a controlled application restart until reload support is added.
- Local application files are not encrypted by Proofbase. Production disk/object/backup encryption and TLS termination require deployment evidence.
- Core product records such as chats, feedback, approved source text, and evaluation cases intentionally retain content under their authorization boundary; they are inventoried separately and are not copied into operational logs.
- Historical database audit metadata is redacted when read but is not destructively rewritten in this phase.
