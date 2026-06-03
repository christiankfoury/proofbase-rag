# Phase 2 Access Control Matrix

Access control is document-level in Phase 2. Retrieval must filter inaccessible documents before any content is sent to the model.

## Role Matrix

| Document ID | Employee | Sales Representative | Manager | HR Admin | IT/Admin |
|---|---:|---:|---:|---:|---:|
| HR-001 | Yes | Yes | Yes | Yes | Yes |
| HR-002 | Yes | Yes | Yes | Yes | Yes |
| HR-003 | Yes | Yes | Yes | Yes | Yes |
| HR-004 | Yes | Yes | Yes | Yes | Yes |
| HR-ADMIN-001 | No | No | No | Yes | No |
| IT-001 | Yes | Yes | Yes | Yes | Yes |
| IT-002 | Yes | Yes | Yes | Yes | Yes |
| IT-003 | Yes | Yes | Yes | Yes | Yes |
| IT-ADMIN-001 | No | No | No | No | Yes |
| SALES-001 | No | Yes | Yes | No | No |
| SALES-002 | No | Yes | Yes | No | No |
| SALES-003 | No | Yes | Yes | No | No |
| MGR-001 | No | No | Yes | No | No |
| MGR-002 | No | No | Yes | No | No |

## Restricted Documents

| Document ID | Restricted Reason | Refusal Behavior |
|---|---|---|
| HR-ADMIN-001 | Contains HR operations workflow and sensitive case handling guidance | Non-HR Admin users should be told the information is restricted or unavailable to their role |
| IT-ADMIN-001 | Contains admin-only security operations and privileged access guidance | Non-IT/Admin users should receive a restricted access refusal without operational details |
| SALES-001 | Contains internal sales process and approved messaging | Employees without sales access should not receive sales strategy details |
| SALES-002 | Contains sales-facing product positioning and implementation messaging | Employees without sales access should not receive sales enablement details |
| SALES-003 | Contains competitor positioning and objection handling | Employees without sales access should not receive competitive strategy |
| MGR-001 | Contains manager-only escalation and team management guidance | Non-managers should receive a restricted access refusal |
| MGR-002 | Contains promotion calibration and performance process details | Non-managers should receive a restricted access refusal |

## Enforcement Rules

- Filter by `access_roles` before retrieval context is built.
- Do not pass inaccessible content to the LLM as hidden context.
- Do not mention restricted document titles unless the product decision is to reveal document existence. MVP default: avoid naming restricted documents to unauthorized users.
- Refusals must not summarize restricted content.
- Permission leakage rate should trend toward 0%.
