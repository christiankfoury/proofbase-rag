# Phase 53 Permission-Aware Evidence Sufficiency Design

## Goal And Placement

Stop clear but unsupported, partially supported, or materially conflicting requests before ordinary answer generation. The gate runs only after identity, project membership, department scope, document-role, active-version, and chunk filtering. Its input is limited to the normalized request, bounded Phase 52 routing fields, and authorized retrieved chunks.

The gate receives no effective role, project or department identifier, access-role list, filtered candidate, hidden document identifier, audit trace, memory text, or prior answer. It cannot retrieve, grant access, widen scope, or introduce evidence. Every chunk ID in its returned result must be present in the authorized input list. Non-authorized model references are removed; answerability is deterministically downgraded when authorized support no longer remains. Invalid schema, provider failure, or an unresolvable contract returns fail-safe.

## Typed Contract

`EvidenceAssessment` schema `evidence_assessment.v1` records:

- answerability: sufficient, partial, insufficient, conflicting, or uncertain
- material required facts with supported, unsupported, or conflicting status
- required source-label coverage for decomposed multi-document requests
- authorized-evidence conflicts and whether precedence is resolved
- safely worded missing information
- answer, partial-answer, clarify, not-found, or temporary-unavailable action
- supporting authorized chunk IDs and bounded reason codes
- deterministic/semantic/fail-safe route, model, prompt, latency, tokens, and estimated cost

The application validates action/answerability consistency, derives duplicated summary fields from authorized fact references, and removes any chunk reference outside the authorized input set before the assessment can continue. Normalization is exposed in metadata and cannot add an ID, source, fact, permission, or answer action without authorized support. Similarity, rank, and retrieval score are not passed as proof of answerability.

## Deterministic And Semantic Modes

- `deterministic_only`: empty evidence and missing planned source coverage are handled explicitly; otherwise the existing optimistic generate path is retained as a measurable baseline.
- `hybrid`: deterministic empty-evidence and required-source-coverage checks run first; unresolved cases use strict-schema semantic assessment.
- `semantic_always`: invokes semantic assessment even for deterministic cases for comparison, while retaining application-side reference and source-coverage validation.

Candidate default: `hybrid`. No mode is promoted until the fixed suite and existing regression/permission gates pass.

## Partial And Conflict Policy

- No material support returns not found without sending chunks to answer generation.
- Partial support may reach generation with a bounded `partial_answer` instruction; the answer must identify the unsupported portion without inventing it.
- Unresolved accessible conflicts return clarification without generation.
- When accessible evidence explicitly establishes current applicability or precedence, the gate may allow an answer.
- Missing-information text may describe only the requested fact or source area. It must not name or imply an inaccessible source.

## Fixed Development Suite And Predeclared Gates

Suite: `evidence-assessment.v1`, fixed `n=30` before the first semantic run.

| Category | Cases | Purpose |
| --- | ---: | --- |
| No authorized evidence | 4 | Clear request returns not found |
| Related evidence missing exact fact | 6 | No false answer from topical similarity |
| Partial evidence | 5 | Supported subset is separated from missing facts |
| Complete multi-document evidence | 5 | Required source coverage can answer |
| Resolved/unresolved accessible conflict | 4 | Precedence vs clarification |
| Restricted/wrong-scope paired cases | 6 | Same question changes only with authorized input |

Promotion thresholds, declared before the first semantic run:

- overall action accuracy: `>=27/30` (`>=0.9000`)
- unsafe answer on no-evidence, missing-fact, or restricted/wrong-scope variants: `0/13`
- inaccessible-source disclosure and forbidden-term matches: `0`
- unauthorized or invented supporting chunk references: `0`
- partial-evidence action accuracy: `>=4/5`
- multi-document complete action accuracy: `>=4/5`
- conflict action accuracy: `>=3/4`
- parser/schema/contract failures: `0`
- p95 semantic latency: `<=5000 ms`
- mean estimated semantic cost: `<=$0.0015`; total suite cost: `<=$0.05`
- full benchmark `1.1`: `130/130`, hallucination `0.000`
- permission leakage, unauthorized exposure, restricted citations, unauthorized chunks reaching generation, inaccessible-source disclosure, and memory-as-evidence violations: `0`

## Verification

- Unit tests for schema, deterministic empty/coverage behavior, authorized-ID validation, semantic input minimization, action mapping, partial-generation instruction, failure paths, and stream/non-stream parity.
- Baseline and mode comparison through a guarded external-AI runner with explicit approval and cost cap.
- Full live `POST /query` regression plus focused permission evaluation after candidate promotion.
- Dashboard export, compile, benchmark validation, Docker Compose config, web build, diff, and secret checks.
- Phase 47-49 sealed holdouts remain immutable and are not rerun.
