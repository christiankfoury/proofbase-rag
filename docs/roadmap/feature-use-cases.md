# Feature Use Cases

## Overview

These use cases define the planned App-side features and the supporting Dev/Admin workflows. They are intentionally written before implementation so the next phases can be evaluated against product behavior instead of only technical completion.

## Roles

| Role | Purpose |
|---|---|
| Employee | Asks questions in project and department workspaces. |
| Knowledge Manager | Creates projects, departments, uploads documents, and reviews extracted Markdown. |
| Department Owner | Manages documents and source coverage for one department. |
| Admin | Manages roles, permissions, ingestion, audits, and system settings. |
| RAG Evaluator | Reviews algorithm comparison, benchmark failures, and quality regressions. |
| Recruiter/Reviewer | Views the polished demo flow and understands the system quickly. |

## UC-01: Create A Project

User: Knowledge Manager.

Goal: Create a new knowledge workspace.

Flow:

1. User opens Projects.
2. User clicks Create Project.
3. User enters name, description, and optional default retrieval profile.
4. System creates the project and opens the Project Home page.

Expected behavior:

- Project appears in the left panel.
- Project Home starts with empty departments, documents, and evaluation status.
- System does not claim the project is indexed until documents are added.

Validation:

- Project can be created, selected, edited, and deleted.
- Empty states are clear.
- No existing synthetic documents leak into the new project unless explicitly seeded.

## UC-02: Manage Project Details

User: Knowledge Manager.

Goal: Keep project metadata accurate.

Flow:

1. User opens Project Settings.
2. User edits name, description, status, or default retrieval profile.
3. User saves changes.

Expected behavior:

- Project metadata updates everywhere it is shown.
- Changing default retrieval profile affects new assistant queries unless the user overrides it.
- Deleting a project requires confirmation and does not silently delete unrelated global evaluation artifacts.

Validation:

- Project changes are persisted.
- Deletion behavior is explicit.
- Audit event is recorded for destructive changes.

## UC-03: Create Departments With Icons

User: Knowledge Manager or Department Owner.

Goal: Organize project knowledge into recognizable business areas.

Flow:

1. User opens a project.
2. User creates a department.
3. User selects an icon and optional color.
4. User adds description and default access roles.

Expected behavior:

- Department appears in project navigation.
- Department icon is shown in project overview and document views.
- Department can be edited or archived.

Validation:

- Department-scoped document counts update.
- Department-scoped assistant filters to that department when selected.
- Access roles inherit sensible defaults but can be overridden at document level.

## UC-04: Upload Files Into A Department

User: Knowledge Manager or Department Owner.

Goal: Add knowledge to a project department.

Flow:

1. User opens a department.
2. User drops a file into the upload area.
3. System creates an ingestion job.
4. User sees upload, extraction, chunking, embedding, and indexing status.

Expected behavior:

- Supported files are accepted.
- Unsupported files receive a clear error.
- Ingestion failures are visible and recoverable.
- Documents are not searchable until indexing succeeds.

Validation:

- Upload status moves through expected states.
- Failed ingestion produces a useful error.
- Indexed document appears in the department document list.

## UC-05: Convert PDF To Reviewable Markdown

User: Knowledge Manager.

Goal: Turn a PDF into clean text for chunking and citation.

Flow:

1. User uploads a PDF.
2. System extracts text.
3. System normalizes headings and sections into Markdown.
4. User previews extracted Markdown.
5. User approves indexing or sends it back for correction.

Expected behavior:

- Extraction is traceable to the original file.
- AI cleanup is optional and does not invent policy content.
- Markdown preview shows title, sections, and extracted text.
- Tables and complex layouts are flagged if extraction confidence is low.

Validation:

- Extracted Markdown preserves core facts from the PDF.
- Chunks cite the extracted document and original filename.
- Evaluation questions can target newly uploaded sources.

## UC-06: Ask The Project Assistant

User: Employee or authorized role.

Goal: Get a cited answer scoped to the selected project.

Flow:

1. User opens a project or department assistant.
2. User asks a question.
3. System retrieves only accessible project and department chunks.
4. System generates an answer, not-found response, clarification, partial answer, or refusal.
5. User reviews citations and source previews.

Expected behavior:

- The assistant does not answer from other projects.
- Department-scoped questions prioritize department documents.
- Unauthorized chunks never reach generation.
- User can submit feedback.

Validation:

- Project filter is enforced before generation.
- Department filter changes retrieved sources.
- Citations point to accessible project documents.
- Permission leakage remains zero in restricted cases.

## UC-07: Compare Algorithms On One Question

User: RAG Evaluator or Admin.

Goal: See how retrieval profiles behave on the same question.

Flow:

1. User opens Algorithm Comparison.
2. User selects project, optional department, question, and profiles.
3. System runs each profile.
4. UI displays answer, citations, retrieved sources, confidence, latency, and cost side by side.

Expected behavior:

- Comparison uses the same input question and role.
- Differences in source coverage and citations are visible.
- The UI does not mark a winner unless a scoring rule exists.

Validation:

- Vector, keyword, hybrid, and multi-doc runs are comparable.
- Costs and latencies are shown when available.
- Missing values are shown honestly.

## UC-08: Verify Algorithm Quality With Evaluation Sets

User: RAG Evaluator.

Goal: Prove whether a retrieval or prompt change improved results.

Flow:

1. User creates or selects an evaluation set.
2. User runs selected retrieval profiles and prompt versions.
3. System calculates metrics and failure buckets.
4. User reviews regressions before promotion.

Expected behavior:

- Evaluation questions include expected behavior and expected sources.
- Metrics include source coverage, answer accuracy, citation accuracy, response type, leakage, hallucination, latency, and cost.
- Regressions are shown alongside improvements.

Validation:

- New profile is not promoted unless gates pass.
- Permission leakage remains zero.
- Failed-question list updates from real output.

## UC-09: Promote A Retrieval Profile

User: RAG Evaluator or Admin.

Goal: Make a verified algorithm configuration the default for a project.

Flow:

1. User compares current default and candidate profile.
2. User reviews metrics and regressions.
3. User promotes candidate profile with notes.
4. System records an audit event.

Expected behavior:

- Promotion requires real evaluation output.
- Notes explain tradeoffs.
- Project assistant uses the promoted profile by default.

Validation:

- Promotion is blocked or warned if evaluation is missing.
- Audit log records profile change.
- App-side queries use the new default.

## UC-10: Convert Negative Feedback Into Evaluation Candidates

User: RAG Evaluator.

Goal: Turn real user feedback into future benchmark coverage.

Flow:

1. User reviews thumbs-down feedback.
2. System proposes benchmark candidates.
3. User verifies expected answer, expected behavior, and expected sources.
4. User manually adds validated cases to an evaluation set.

Expected behavior:

- Feedback candidates are never auto-promoted into benchmark questions.
- Human review is required.
- The original bad answer and user comment stay linked for context.

Validation:

- Candidate export preserves source feedback.
- Reviewed questions can be evaluated.
- Benchmark growth is intentional and auditable.

## UC-11: Manage Permissions

User: Admin.

Goal: Ensure project and document access is safe.

Flow:

1. Admin opens permission management.
2. Admin reviews role access by project, department, and document.
3. Admin changes access rules.
4. System applies filters to future retrieval.

Expected behavior:

- Permission changes are audited.
- Users cannot retrieve restricted chunks.
- Refusals do not reveal restricted facts.

Validation:

- Restricted benchmark cases still pass.
- Unauthorized chunk exposure remains zero.
- Permission matrix matches expected access.

## UC-12: Recruiter Demo Flow

User: Recruiter/Reviewer.

Goal: Understand the project quickly.

Flow:

1. Reviewer lands on App side, not an admin metrics table.
2. Reviewer sees projects and departments.
3. Reviewer opens a project assistant and asks a normal question.
4. Reviewer sees citations and source preview.
5. Reviewer opens Dev/Admin to see evaluation proof.
6. Reviewer sees known failures and algorithm comparison.

Expected behavior:

- The first impression is a usable product.
- The second impression is engineering rigor.
- Metrics are real and limitations are visible.

Validation:

- Demo can be completed in five minutes.
- Screenshots show both App and Dev/Admin surfaces.
- No page requires reading README to understand the core value.

