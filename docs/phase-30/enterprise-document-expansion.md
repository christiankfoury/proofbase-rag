# Enterprise Document Expansion

Phase 30 expands the synthetic Northstar corpus from 14 to 19 Markdown documents before the benchmark is expanded. The goal is product credibility: the App side should feel like a real enterprise knowledge workspace, while Dev/Admin metrics remain tied only to measured artifacts.

## Added Documents

| Document | Department | Category | Restricted | Key patterns |
| --- | --- | --- | --- | --- |
| `FIN-001` | Finance | Finance | No | Expense limits, procurement thresholds, reimbursement timing, old-vs-new policy language, tables, exceptions |
| `LEGAL-001` | Legal | Legal | Yes | NDA rules, contract approval matrix, retention, legal hold, do-not-reveal section, prompt-injection test text |
| `ENG-001` | Engineering | Engineering | Yes | Deployment windows, approval matrix, on-call severity table, change freeze, do-not-reveal section, prompt-injection test text |
| `SUPPORT-001` | Support | Support | Yes | SLA targets, escalation triggers, refund guardrails, obsolete threshold note, do-not-reveal section |
| `OPS-001` | Operations | Operations | No | Vendor onboarding, travel booking, equipment requests, cross-policy ownership, tables, exceptions |

## Seeded Department Mapping

The existing ingestion script maps Markdown documents into the seeded `Northstar Analytics` project by matching document metadata `category` to `project_departments.seeded_data_key`.

Phase 30 adds seeded department rows for:

- Finance
- Legal
- Engineering
- Support
- Operations

The department ordering in `project_store.py` was updated so these categories appear predictably after the existing HR, IT, Sales, and Management departments.

## Permission Scope

The new restricted documents have role metadata:

- `LEGAL-001`: Sales Representative, Manager, HR Admin, IT/Admin
- `ENG-001`: Manager, IT/Admin
- `SUPPORT-001`: Sales Representative, Manager

No new permission-safety metric is claimed in Phase 30. The current permission safety dashboard run still covers the existing 10 restricted-access benchmark questions. Phase 31 should add benchmark questions for the new restricted documents before any new safety claim is made.

## Metric Scope

The expanded corpus does not change the current evaluation results. Existing dashboard metrics remain tied to their recorded run IDs, sample sizes, benchmark version, and timestamps.

OpenAI-backed embedding regeneration and expanded evaluation were intentionally not run in Phase 30. The documents are ready for ingestion, and Phase 32 is expected to capture the expanded baseline after Phase 31 adds validated benchmark questions.
