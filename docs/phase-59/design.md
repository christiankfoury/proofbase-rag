# Phase 59: Secure File Processing And Storage

## Outcome

The upload workflow now admits only a tightly validated PDF envelope, writes the original under a randomized tenant key in local quarantine, creates a tenant-owned lifecycle record protected by forced PostgreSQL row-level security, performs a fixture-only signature check, and parses through a bounded subprocess before creating a pending-review document. Rejected or failed content cannot create chunks, embeddings, or retrievable evidence.

## Control flow

1. Project editor authorization and the Phase 58 upload quota run first.
2. The API requires a `.pdf` extension, exact `application/pdf` declaration, `%PDF-` signature, a final `%%EOF`, no archive/polyglot or active-content markers, no non-whitespace trailing payload, the 10 MB bound, and the explicit `non_sensitive` classification.
3. `LocalQuarantineStorage` writes with an opaque UUID key below the active tenant directory and rejects cross-tenant or traversal paths.
4. `file_objects` records a filename hash, content hash, MIME facts, size, state, scanner result, page count, retention expiry, document binding, and legal-hold flag. Tenant-aware foreign keys and forced RLS protect the row.
5. The accurately named `FixtureSignatureScanner` rejects the approved local marker. It is not represented as general malware detection.
6. The local parser subprocess receives a minimal environment and enforces timeout, page, and extracted-character bounds. API errors expose only bounded reason codes.
7. Only a successful scan and parse can create a pending-review version. The original remains subject to seven-day expiry until successful human approval/indexing extends it to 30 days.

The schema also prevents concurrent active duplicates by tenant, project, department, and SHA-256 digest. A signed, short-lived tenant/file grant contract is tested, but no public download endpoint is exposed.

## Hardened worker contract

The optional `security-contract` Compose profile documents a no-network, read-only, capability-dropped worker with `no-new-privileges`, PID, memory, CPU, and temporary-disk limits. The local API is not connected to that container: it uses a subprocess for deterministic portfolio verification. Selecting the future hosted scanner or isolated-worker modes fails closed because those adapters are not connected.

## Honest limitations

- The fixture scanner detects only the approved test marker; it is not malware protection.
- The local subprocess has a sanitized environment and timeout but no OS-enforced network, memory, CPU, or filesystem sandbox.
- The hardened container is a deployment contract, not an end-to-end connected parser service.
- Local quarantine is not encrypted by the application. Hosted encrypted object storage, TLS access, key management, secure deletion guarantees, and scanner/worker delivery remain external work.
- PDF parser/container vulnerability scans were not available in this environment; dependency and image scanning remains required before deployment.
- Archive nesting is eliminated by the PDF-only policy. Page and extracted-size bounds reduce decompression risk, but a production worker still needs enforced resource limits and patched dependency operations.
- Retention expiry is represented and indexed; Phase 60/61 operational scheduling and monitoring must execute and evidence cleanup.
