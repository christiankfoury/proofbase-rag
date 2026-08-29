# Finding Triage, Remediation, And Retest Workflow

Status: process definition; **Independent validation required**.

## Record

Each finding receives a stable ID, reporter, discovered time, affected tenant/data/control, reproducible evidence location, CWE/OWASP mapping when applicable, exploit preconditions, impact, likelihood, severity, owner, target date, containment, fix commit, verification, residual risk, and disclosure decision. Store no exploit secret, token, prompt/source content, or cross-tenant data in the ticket.

## Severity and target service levels

| Severity | Triage | Containment/decision | Fix target | Retest |
| --- | --- | --- | --- | --- |
| Critical | 4 hours | 24 hours | 72 hours or service remains disabled | independent before restoration/promotion |
| High | 1 business day | 3 business days | 14 calendar days | separate reviewer; independent when externally found/material |
| Medium | 5 business days | 10 business days | 30 calendar days | separate internal reviewer |
| Low | 10 business days | as planned | 90 calendar days | regression evidence |

Targets are proposed portfolio policy, not an operational SLA until owners and coverage are assigned.

## Decision states

`new` -> `triaged` -> `contained` -> `fix_in_progress` -> `ready_for_retest` -> `verified_closed`.

`accepted_risk` requires named business/security authority, rationale, expiration, compensating controls, and release-gate treatment. `false_positive` requires reproducible counter-evidence and reviewer approval. Critical/high findings cannot be silently accepted or bypassed.

## Retest

Retest the original reproduction plus adjacent tenant, role, route, streaming/non-streaming, and regression cases. Record runtime commit and environment. A developer self-test may prepare a fix but cannot replace independent retest where that claim is required.
