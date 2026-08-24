# Phase 49 Blind Holdout Authoring Record

## Status

This record accompanies `data/evaluation/independent-generalization/holdout-v3.draft.json`. The suite is a draft for independent review. Every case has `review_status: "draft"`, an empty `reviewed_by`, and an empty `reviewed_at`.

No evaluation was run and no runtime behavior was changed during authoring.

## Allowed Sources Consulted

The blind author consulted only:

- `data/synthetic-documents/**/*.md` (the 19 synthetic source documents)
- `data/evaluation/independent-generalization/schema-v3.json`
- Neutral constants and the locked category distribution in `scripts/independent_generalization_common.py`. The initial read command returned the whole module rather than a sliced constants-only view; only the neutral constants and distribution were used, and no referenced artifact was followed or opened.

The suite was authored from source truth. Every corpus-backed expected quote was copied exactly from the named synthetic document. The upload-isolation case uses only fixture content declared inside that case.

## Locked Distribution

| Category | Cases |
| --- | ---: |
| factual_robustness | 4 |
| multi_document_claim_coverage | 5 |
| multi_turn_memory | 5 |
| ambiguity_boundaries | 3 |
| permission_scope_pairs | 5 |
| missing_information_abstention | 3 |
| prompt_injection_adversarial | 3 |
| conflicting_versioned_sources | 1 |
| uploaded_document_project_isolation | 1 |
| **Total** | **30** |

## Coverage

- Roles: Employee, Sales Representative, Manager, HR Admin, and IT Admin.
- Difficulties: easy, medium, and hard.
- Behaviors: answer, clarify, refuse_no_access, and not_found.
- Scopes: global, project, and department.
- Conversation depth: single-turn cases plus multi-turn cases containing two or three prior turns.
- Permission design: two same-intent answer/refusal pairs plus one standalone department-and-role boundary case.
- Source coverage: HR-001, HR-002, HR-003, HR-004, HR-ADMIN-001, IT-001, IT-002, IT-003, IT-ADMIN-001, SALES-001, SALES-002, SALES-003, OPS-001, FIN-001, LEGAL-001, MGR-002, ENG-001, and SUPPORT-001 are represented through expected sources, allowed-document boundaries, or both. The declared upload fixture adds one in-scope and one out-of-scope project document.
- Multi-document coverage includes remote work and device controls, vendor onboarding and procurement, sales discovery and positioning, onboarding and vacation timing, and engineering change plus privileged-account safeguards.

## Blind-Isolation Attestation

During this authoring task, I did not read, search, list, open, or infer from prior holdout suites, their hashes or results, Phase 47 or Phase 48 documentation or roadmap plans, git history or diffs for those artifacts, request logs, failure or adjudication artifacts, runtime prompt code, scoring code, remediation tests, or remediation context. I did not tune any case to a known failure.

The only files written were:

- `data/evaluation/independent-generalization/holdout-v3.draft.json`
- `docs/phase-49/blind-authoring-record.md`

No commit was created.
