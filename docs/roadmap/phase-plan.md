# Future Phase Plan

## Planning Rule

These phases are documentation targets until implementation begins. Each implementation phase should add or update its own `docs/phase-{index}` folder with a checklist, design notes, verification output, and limitations.

The numbering starts after the existing Phase 17 work.

Use `docs/roadmap/progress.md` as the durable phase tracker. Before starting work, confirm the current phase there. Before committing a phase, update the tracker with status, verification, commit references if already known, skipped checks, and the next expected phase.

Default assumptions for future phases:

- A project is a generic knowledge workspace.
- Durable product concepts should be persisted in Postgres when practical.
- The existing synthetic corpus should be seeded as `Northstar Analytics`.
- Prefer archive or soft-delete semantics before hard delete.
- Retrieval behavior should remain unchanged until the project-scoped RAG phase.
- Seeded/demo data must be honest and must not create fake metrics, fake activity, or fake quality claims.
- Each phase should update its docs and verification notes as part of the implementation.

## Phase 18: App And Dev/Admin Navigation Split

Goal: Reframe the product so the first visible surface is an App, while existing evaluation pages become Dev/Admin.

User-facing outcome:

- Clear top-level navigation between App and Dev/Admin.
- App landing page shows projects, assistant entry points, and document coverage.
- Existing routes remain available under a more coherent Dev/Admin grouping.

Scope:

- Information architecture.
- Navigation labels.
- App shell layout.
- Empty-state copy.
- No new RAG algorithm.
- No fake project data beyond clearly marked seeded demo state.

Verification:

- Frontend build passes.
- Existing routes still render.
- Recruiter demo flow starts on App side.

Questions before starting:

- Should the App landing page replace `/`, or should `/` remain the metric overview with a new `/app` route?
- Should existing dashboard pages be renamed or only regrouped in navigation?

## Phase 19: Project Workspace Model And UI

Goal: Add projects as first-class knowledge workspaces.

User-facing outcome:

- Users can create, edit, select, and delete projects.
- A left panel lists projects.
- Project Home shows departments, document count, recent activity, and quality status.

Scope:

- Project data model.
- Project CRUD API.
- Project list and detail pages.
- Seeded demo project for the existing Northstar corpus.
- Audit logging for create/update/delete.

Verification:

- CRUD flow works locally.
- Project filter does not change retrieval until Phase 22.
- Existing evaluation outputs remain unchanged.

Questions before starting:

- Override the default Postgres-backed project model only if the current repo state makes it impractical.
- Override the default seeded `Northstar Analytics` project only if a better corpus mapping already exists.

## Phase 20: Department Workspaces

Goal: Let each project organize knowledge by departments with icons.

User-facing outcome:

- Users can create departments inside a project.
- Departments have icons, descriptions, and access defaults.
- Existing HR, IT/Security, Sales, Management, HR Admin, and IT Admin corpus categories map into departments for the seeded project.

Scope:

- Department model and API.
- Department cards/list.
- Department detail page.
- Icon selection.
- Department access defaults.

Verification:

- Department CRUD works.
- Seeded departments match existing document inventory.
- Department navigation is usable on desktop and mobile widths.

Questions before starting:

- Should department icons be limited to a fixed set or allow free-form icon names?
- Should departments be archived or hard-deleted?

## Phase 21: Document Library And File Ingestion Planning

Goal: Create the App-side document management surface before adding new file parsing complexity.

User-facing outcome:

- Department document list.
- Upload entry point.
- Document status and version display.
- Extracted Markdown preview placeholder for indexed documents.

Scope:

- Document library UI.
- Ingestion job model.
- Status display.
- Version metadata.
- Link existing Markdown corpus documents into project/department views.

Verification:

- Existing synthetic documents are visible in the seeded project.
- Document metadata matches current source inventory.
- No document is searchable outside its intended role.

Questions before starting:

- Should document versions be exposed to App users or only Admin users?
- Should upload be disabled until Phase 22/23 extraction is ready?

## Phase 22: PDF And Document Extraction Pipeline

Goal: Support real file ingestion with reviewable Markdown output.

User-facing outcome:

- Users can upload supported files.
- System extracts text and produces Markdown.
- User can review extracted Markdown before indexing.

Scope:

- PDF extraction.
- Optional DOCX extraction if chosen.
- Markdown normalization.
- Extraction confidence or warnings for low-quality layout.
- Raw source file storage decision.
- Ingestion state machine.

Verification:

- At least one sample PDF extracts correctly.
- Extracted Markdown is reviewable.
- Chunking and embeddings run only after approval or explicit indexing.
- OpenAI use is documented if AI cleanup is used.

Questions before starting:

- First version: PDF only, or PDF plus DOCX?
- Should AI cleanup rewrite headings only, or summarize/restructure content?
- Where should raw uploaded files be stored locally before Azure Blob Storage exists?

## Phase 23: Project-Scoped RAG

Goal: Make retrieval and generation respect project and department scope.

User-facing outcome:

- Assistant answers only from the selected project.
- Department assistant can narrow answers to department knowledge.
- Citations show project and department context.

Scope:

- Add project and optional department filters to retrieval.
- Extend query request/response shape.
- Update App-side assistant UI.
- Preserve role-based permission filtering before generation.
- Add project-scoped audit and observability fields.

Verification:

- Same question across two projects cannot retrieve the wrong project's chunks.
- Department filter changes source set as expected.
- Permission evaluation still reports zero leakage.
- Existing global benchmark still runs or is clearly separated from project benchmarks.

Questions before starting:

- Should department scope be strict or a ranking boost?
- Should users be able to ask across all departments in a project by default?

## Phase 24: Algorithm Quality Lab

Goal: Turn retrieval playground into a serious algorithm comparison workflow.

User-facing outcome:

- Admins can compare retrieval profiles on one question or an evaluation set.
- Results show source coverage, citations, answer quality, latency, and cost.
- Candidate profiles can be promoted only after review.

Scope:

- Named retrieval profiles.
- Side-by-side question comparison.
- Evaluation set runner by project.
- Promotion notes and audit event.
- Failure bucket summary.

Verification:

- Existing vector, keyword, hybrid, and multi-doc configurations can be compared.
- A known failure such as `MULTI-005` remains visible until actually fixed.
- Metrics are generated from real outputs.

Questions before starting:

- Which metric is the primary promotion gate: source recall, answer accuracy, citation accuracy, hallucination, cost, or latency?
- Should reranking be added in this phase or saved for a focused algorithm phase?

## Phase 25: Result Verification And Human Review

Goal: Make it practical to verify whether answers make sense.

User-facing outcome:

- Evaluators can review answer, expected answer, citations, retrieved chunks, and failure reason in one workflow.
- Negative feedback can become evaluation candidates after human review.
- Evaluation sets can grow without corrupting benchmark quality.

Scope:

- Human review queue.
- Answer correctness labels.
- Citation correctness labels.
- Feedback-to-evaluation workflow in the UI.
- Project-level benchmark authoring.

Verification:

- Review decisions are saved.
- Candidates are not auto-promoted.
- Evaluation re-run reflects approved questions.

Questions before starting:

- Should review labels follow the existing 1.0/0.5/0.0 rubric?
- Should users write expected answers manually, or can AI draft them for review?

## Phase 26: Recruiter Presentation Polish

Goal: Make the project demo feel finished without hiding engineering depth.

User-facing outcome:

- App-side first impression is polished.
- Dev/Admin proof is easy to reach.
- Demo script, screenshots, README, and case study all tell the same story.

Scope:

- Visual pass across App and Dev/Admin.
- Demo data reset path.
- Screenshot checklist update.
- README update.
- Portfolio case study update.
- Known limitations update.

Verification:

- Frontend build passes.
- Demo script can be completed in five minutes.
- Screenshots show project workspace, department documents, assistant answer, citations, algorithm comparison, and failed-question inspection.
- No claims exceed implemented behavior.

Questions before starting:

- Should the final presentation optimize for recruiters, engineering managers, or AI platform teams?
- Should the README lead with product screenshots or metrics?

## Phase 27: Auth And Deployment Readiness

Goal: Move from demo controls toward production-shaped access and deployment.

User-facing outcome:

- Users sign in through a real auth layer or documented local equivalent.
- Role selection is no longer just a demo dropdown.
- Project membership and permissions can be assigned.

Scope:

- Auth provider selection.
- User/project membership.
- Role management.
- Azure storage and database decisions.
- Deployment docs update.

Verification:

- Unauthorized users cannot access project data.
- Existing permission benchmark still passes.
- Deployment docs do not claim work that has not been run.

Questions before starting:

- Should auth use Clerk, Auth.js, or a simpler local demo auth first?
- Should Azure deployment be implemented before or after real uploaded files?

## Phases 28-37: Evaluation And Credibility Improvement Roadmap

After Phase 27, `docs/roadmap/phases-improvement.md` was the executable source of truth for the evaluation and credibility improvement sequence.

Phase mapping:

- Phase 28: Dashboard Transparency.
- Phase 29: Benchmark Schema Cleanup And Validation.
- Phase 30: Enterprise Document Expansion.
- Phase 31: Benchmark Expansion.
- Phase 32: Expanded Baseline Run.
- Phase 33: Precision@k Improvement.
- Phase 34: Hallucination And Abstention Reduction.
- Phase 35: Citation Accuracy Improvement.
- Phase 36: Permission And Memory Evaluation Expansion.
- Phase 37: Regression Scorecard.

Implementation rule:

- Make current metrics defensible before improving them.
- Expand enterprise documents before expanding the benchmark heavily.
- Capture an expanded baseline before retrieval or prompt tuning.
- Do not publish target-metric claims until phase notes and dashboard run IDs prove them.
- Preserve zero permission leakage as a hard gate for every quality phase.

## Phases 38-40: Post-Phase 37 Remediation Roadmap

After Phase 37, continue from `docs/roadmap/post-phase-37-remediation-plan.md`. That document is the executable source of truth for the next remediation sequence.

Phase mapping:

- Phase 38: Answer-Quality Failure Remediation.
- Phase 39: Multi-Document And Ambiguity Orchestration.
- Phase 40: Uploaded-Document Local E2E Workflow.

Implementation rule:

- Start from the measured `phase35-citation-alignment-v7` answer-quality backlog: benchmark `1.1`, sample size `130`, and `16` failed questions.
- Use a code-first benchmark policy; change benchmark expectations only for documented defects.
- Target `<=8` answer-quality failures before claiming Phase 38 success.
- Use strict ambiguity behavior for underspecified questions that should ask for clarification.
- Finish upload -> review -> approve/index -> ask locally before adding Azure Blob Storage or AI Markdown cleanup.
- Preserve zero permission leakage as a hard gate for every remediation phase.

## Phases 41-46: Post-Phase 40 Product Polish Roadmap

After Phase 40 and the Phase 39/40 polish/audit-backlog work, continue from `docs/roadmap/post-phase-40-product-polish-plan.md`. That document is the executable source of truth for the next product-polish sequence.

Phase mapping:

- Phase 41: Recruiter Demo Project Home.
- Phase 42: Guided Demo Flow And Answer Proof.
- Phase 43: Guarded AI Markdown Cleanup Draft.
- Phase 44: AI Cleanup Metadata, Cost, And Review Diff.
- Phase 45: Generalization Probe Suite Baseline.
- Phase 46: Memory And Ambiguity Generalization Remediation.

Implementation rule:

- Improve demo/product clarity before adding deeper algorithm work.
- Keep optional AI Markdown cleanup editor-triggered, reviewable, reversible, and separate from indexing until approve/index.
- Start memory and ambiguity generalization with a measured non-benchmark baseline before fixing failures.
- Preserve zero permission leakage and keep memory as query context only, never source evidence.
- Keep benchmark expectations, prompts, retrieval ranking, and metrics unchanged unless a defect is proven and documented.
- Each phase must use the full loop: plan, implement, verify, commit, review commit, perform code review, push `main`, then continue.

## Cross-Cutting Algorithm Explanation Audit

Before or between implementation phases, the user may request a documentation-first review of the current algorithm. Use `docs/roadmap/algorithm-explanation-audit-plan.md` for that work.

Purpose:

- Explain the implemented RAG algorithm in Markdown documents that a portfolio reviewer or developer can understand.
- Review the actual code paths before writing explanations.
- Identify design risks, confusing areas, and improvement opportunities.
- Preserve a clear boundary between documentation findings and runtime behavior changes.

Rules:

- Do not change retrieval, prompts, permissions, benchmark expectations, or metrics during the explanation pass unless the user explicitly asks for implementation.
- Keep explanations grounded in code references and measured artifacts.
- Put output documents under `docs/algorithm/`.
- Phase 39 remains the next remediation implementation phase unless the audit finds a more urgent correctness or permission issue.

## Promotion Gates For Every Future Phase

Each phase must answer:

- What changed for the App side?
- What changed for Dev/Admin?
- What did we verify?
- What remains incomplete?
- Did any metric or permission guarantee regress?
- Are new screenshots or README updates needed?

Algorithm phases additionally require:

- before/after metrics
- failure bucket changes
- cost and latency notes
- permission leakage check
- explanation of tradeoffs
