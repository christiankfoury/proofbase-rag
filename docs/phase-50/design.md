# Phase 50 Manual-Test Findings Remediation

## Goal

Close the seven findings from the complete user-facing manual test campaign without weakening project scope, document-role filtering, citation requirements, or the sealed-holdout policy.

## Findings And Changes

| Finding | Observed behavior | Remediation |
| --- | --- | --- |
| `DEPT-001` | A newly created empty department crashed after refresh because cleanup metadata was null. | The separately committed `0c3c934` hotfix treats missing cleanup metadata as an empty state. Manual retest passed. |
| `CHAT-AMB-001` | `What approval do I need?` selected procurement guidance without enough context. | A pre-retrieval ambiguity guard now asks which activity and decision variables apply. |
| `MEM-AMB-001` | A fresh chat answered `How far ahead do I need to book it?` as travel without an antecedent. | Fresh unresolved booking/deadline pronouns now clarify; the same wording may proceed when memory supplies the referent. |
| `CHAT-INJ-001` | A direct user instruction could request an invented value while bypassing documents and citations. | Direct evidence/access/citation override requests are blocked before retrieval, return no citations or chunks, and create an audit event. Questions *about* hostile instructions inside retrieved sources remain evidence-answerable. |
| `REV-UI-001` | A saved evaluation review existed in Postgres and the audit log but could not be reopened in the UI. | Review reads can filter by source ID. The review panel loads the ten most recent decisions, restores the latest fields, and displays saved history. |
| `CHAT-UI-001` | Every scoped chat was titled `Northstar assistant`, including Atlas Forge. | The title now derives from the selected project and falls back to `Proofbase assistant` while scope loads. |
| `MEM-GAP-001` | New projects had no App-side way to assign demo-user memberships. | Project owners and Kai Admin can assign or remove viewer, contributor, and owner memberships in Project Settings. API checks authorization server-side and audits mutations. |

## Permission And Data Boundaries

- Membership is a project-entry gate; document `access_roles` still filter chunks before generation.
- Membership-directory reads and mutations require an existing owner membership for non-admin users.
- Kai Admin remains an explicit local-demo override and is not stored as a project membership.
- Only active, non-admin demo users can be assigned.
- Archived projects cannot receive new assignments.
- Switching demo identity clears project detail state and reloads the accessible project list, avoiding stale project content from the previous identity.
- Review history remains Dev/Admin-only through the existing admin dependency.
- Prompt-override audit metadata records scope and actor identifiers, never the prompt or source text.

## Evaluation Policy

Benchmark `1.1` expectations and sources were not edited. Phase 47-49 sealed holdouts were not opened, changed, or rerun. Verification uses targeted local controls, the existing 130-question non-sealed benchmark, the 20-probe generalization suite, and the 20-question permission suite.

The first full Phase 50 run exposed an over-broad safety guard on `ADV-001` and `ADV-005`: it safely clarified, but those questions ask how to handle hostile *source content* and must be answered from `LEGAL-001`. The guard was narrowed, all five prompt-injection benchmark cases then passed, and the complete benchmark was rerun against the reviewed code.
