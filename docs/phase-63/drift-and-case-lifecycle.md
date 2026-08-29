# Drift Monitoring And Future Case Lifecycle

Monitor only production-safe aggregates: response/decision types, bounded reason codes, stage latency, estimated/reconciled cost, parser/schema failures, repair/downgrade counts, permission denials, injection/evidence alerts, and tenant-opaque rates. Do not retain raw prompts, answers, source text, filenames, secrets, or cross-tenant identifiers for drift analysis.

Threshold movement creates an investigation, not a benchmark label. Use reviewed incidents and reviewed feedback to author future development cases; they are **never automatic benchmark truth**. A separate reviewer must confirm source truth, expected behavior, authorization boundary, non-duplication, category, and data classification before promotion to a versioned development suite.

Future sealed release cases are authored only after runtime freeze and remain separate from reviewed production-derived development cases.
