# Phase 55 Design: Defense Evaluation, Observability, And Page Evidence

## User-facing goal

Make the Phase 52-54 defense stack inspectable as one product control: a reviewer should be able to see what each stage decided, which measured artifact supports the claim, what the privacy boundary is, and which production controls are still absent.

## Scope

- Consolidate the three fixed development suites under `defense-evaluation-manifest.v1` and reject drift, duplicate case IDs, unknown schemas, missing result evidence, or any Phase 47-49 sealed-holdout reference.
- Add a bounded `defense_trace.v1` response object covering request guards, semantic request assessment, permission filtering, evidence sufficiency, generation, post-generation validation, and final response selection.
- Exclude user text, prompt text, source text, memory text, raw model output, and inaccessible identifiers from the trace.
- Export one generated readiness artifact that drives the Dev/Admin defense page and the measured portions of `/trust`.
- Freeze the Phase 52-54 runtime before a separately model-authored holdout is sealed. The new holdout will not be executed, opened, scored, or used for a claim in this phase.

## Predeclared evidence gates

These targets are frozen before the Phase 55 exporter or any new external-AI stability/authoring command is run.

| Gate | Target | Sample / evidence |
| --- | ---: | --- |
| Consolidated fixed-suite sample | `>= 100` | Phase 52-54 development manifests |
| Request assessment action accuracy | `>= 0.95` | 48 fixed cases |
| Evidence assessment action accuracy | `>= 0.95` | 30 fixed cases |
| Post-generation validator action accuracy | `>= 0.95` | 24 fixed cases |
| Legitimate-request intervention rate | `<= 0.05` | Phase 52 legitimate/source-discussion cases |
| Unsafe attack compliance / acceptance | `0` | All labeled attack/unsafe cases |
| Semantic-stage p95 latency | `<= 5,000 ms` per stage | Fixed-suite recorded calls |
| Full 130-case control cost | `<= $0.35` | Request + evidence + post-generation controls |
| Full 130-case generation-plus-control cost | `<= $0.65` | Definitive Phase 54 run |
| Runtime benchmark accuracy | `>= 0.95` | Benchmark 1.1, 130 questions |
| Stability | `3/3` identical bounded summaries | Repeated manifest validation/export with timestamps excluded |

Stability here proves deterministic evidence assembly and schema validation, not model-output determinism. Semantic stability remains a limitation until the new sealed holdout is opened under a later predeclared release protocol.

## Hard safety gates

- permission leakage: `0`
- unauthorized chunks reaching generation: `0`
- restricted citations: `0`
- assessment-caused tenant or scope expansion: `0`
- memory used as source evidence: `0`
- unsafe compliance with tested injection attacks: `0`
- invalid request/evidence schemas silently continuing: `0`

Any miss remains visible in the evidence artifact and Trust page. It does not authorize benchmark edits, holdout inspection, or relaxed wording.

## App and Dev/Admin surfaces

- App: `/trust` reads measured values and provenance from the generated Phase 55 readiness artifact while its claims and limitations remain code-reviewed prose.
- Dev/Admin: `/dev-admin/defense-readiness` presents stage routing, intervention and unsafe outcomes, insufficiency, failures, latency, cost, repair outcomes, hard gates, and evidence provenance.
- API: query and streaming final payloads expose the bounded defense trace. Existing detailed assessment objects remain for local debugging; the new trace is the default safe cross-stage view.

## Verification

- focused trace, manifest, exporter, privacy, schema-failure, stream/non-stream parity, and page-evidence tests
- three consecutive manifest/export summary checks
- existing Phase 52-54 focused tests and benchmark validator
- Python compile, dashboard export, Docker Compose config, secret/content scan, and production web build
- commit review focused on permission ordering, trace disclosure, metric provenance, and misleading claims

## Explicit limitations

This phase does not add production identity, tenant isolation, database row-level authorization, hosted monitoring, or independent security testing. Development suites are not unseen evidence. The new sealed holdout is future evaluation material and cannot support a Phase 55 generalization claim.
