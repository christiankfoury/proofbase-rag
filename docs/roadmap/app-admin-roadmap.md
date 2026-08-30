# App And Dev/Admin Roadmap

## Purpose

This roadmap turns Proofbase from an evaluation-heavy RAG dashboard into a presentable application with two clear surfaces:

- App side: the user-facing knowledge workspace where people create projects, organize departments, upload knowledge, and ask project-scoped questions.
- Dev/Admin side: the evaluation, ingestion, permissions, observability, audit, cost, and algorithm control center.

The goal is not to remove the existing engineering depth. The goal is to make that depth support a product experience that is immediately understandable.

## Current State

Implemented strengths:

- A synthetic enterprise corpus with role metadata.
- A 60-question benchmark.
- Vector, keyword, hybrid, and multi-document retrieval experiments.
- Permission filtering before generation.
- Cited answers, citation validation, confidence scoring, and response types.
- Session memory and query rewriting.
- Prompt experiments and regression analysis.
- Feedback, audit logs, observability, cost estimates, and Docker packaging.
- Interactive pages for chat, permission demo, retrieval comparison, failed questions, run comparison, and observability.

Current presentation issue:

- Most routes are Dev/Admin pages: metrics, runs, failures, observability, audit, prompt experiments, and retrieval experiments.
- `/chat` exists, but it behaves like a demo console rather than the center of an end-user application.
- There is no project workspace, department organization, document management flow, or App-side information architecture.

## Product Split

### App Side

The App side should answer: "What would an employee or knowledge manager actually use?"

Primary pages:

- Projects: left-panel list of projects with create, search, status, and recent activity.
- Project Home: overview of departments, document coverage, recent questions, and quality status.
- Department Workspace: department icon, description, documents, ingestion state, and department-scoped assistant.
- Assistant: project-scoped and optionally department-scoped chat with citations, source previews, confidence, and feedback.
- Documents: upload, ingestion status, extracted Markdown preview, versions, and access summary.
- Answer Review: saved answers, user feedback, and suggested benchmark candidates.

App-side tone:

- Productive, calm, and understandable to a non-engineering reviewer.
- Shows what the assistant does before exposing how the engine is tuned.
- Keeps citations and source traceability visible, but avoids making every screen feel like a benchmark table.

### Dev/Admin Side

The Dev/Admin side should answer: "How do we know the system is safe, accurate, and improving?"

Primary pages:

- Evaluation Overview and Runs.
- Failed Questions.
- Algorithm Comparison / Retrieval Playground.
- Prompt Experiments.
- Permission Safety.
- Memory Evaluation.
- Multi-Document Evaluation.
- Feedback.
- Observability.
- Audit Logs.
- Cost Tracking.
- Ingestion Jobs.
- Role and Permission Management.

Dev/Admin tone:

- Dense, auditable, metric-driven.
- Honest about failures and missing measurements.
- Optimized for debugging, regression review, and quality gates.

## Proposed Information Architecture

```text
App
  Projects
    Project Home
    Departments
      Department Detail
      Department Documents
      Department Assistant
    Assistant
    Documents
    Answer Review

Dev/Admin
  Evaluation
    Overview
    Runs
    Failed Questions
    Algorithm Comparison
    Prompt Experiments
  Safety
    Permissions
    Audit Logs
  Operations
    Ingestion Jobs
    Observability
    Feedback
    Cost
```

The navigation should make this split obvious. Existing pages can remain, but they should be grouped under Dev/Admin rather than competing with App pages.

## Domain Model Concepts

### Project

A project is a knowledge workspace. It may represent a company, department rollout, client demo, or corpus. The first implementation can treat it as a local demo workspace.

Suggested fields:

- `id`
- `name`
- `description`
- `status`
- `created_at`
- `updated_at`
- `default_retrieval_profile`
- `quality_summary`

### Department

A department is a project-local knowledge area.

Suggested fields:

- `id`
- `project_id`
- `name`
- `icon`
- `description`
- `default_access_roles`
- `document_count`
- `indexed_chunk_count`

### Document

Documents should belong to a project and optionally a department.

Suggested fields:

- existing document fields from the current schema
- `project_id`
- `department_id`
- `source_file_name`
- `source_file_type`
- `raw_file_uri`
- `extracted_markdown`
- `ingestion_status`
- `active_version`

### Ingestion Job

Tracks upload, extraction, Markdown normalization, chunking, embedding, and indexing.

Suggested states:

- `uploaded`
- `extracting`
- `normalizing`
- `chunking`
- `embedding`
- `indexed`
- `failed`

### Retrieval Profile

A named algorithm configuration that can be compared and assigned to projects.

Suggested fields:

- `name`
- `retrieval_mode`
- `chunking_strategy`
- `top_k`
- `prompt_version`
- `multi_doc_mode`
- `reranker`
- `notes`

### Evaluation Set

A project-scoped set of validation questions. This extends the existing benchmark idea from a global synthetic corpus to each project.

Suggested fields:

- `project_id`
- `name`
- `questions`
- `expected_sources`
- `expected_behavior`
- `review_status`

## Feature Concepts

### Project Workspace

Create, edit, delete, and switch between projects. A left panel should make the product feel like a real workspace rather than a collection of standalone demo pages.

Why it matters:

- Gives the app a recognizable product shape.
- Makes project-scoped RAG easier to explain.
- Creates a natural home for departments, documents, and evaluations.

### Department Knowledge Areas

Inside a project, users can create departments such as HR, IT/Security, Sales, Management, or custom teams. Each department can have an icon and document set.

Why it matters:

- Maps cleanly onto the existing synthetic corpus.
- Makes access, source coverage, and scoped answers visible.
- Gives the guided demo a simple mental model.

### File Upload And Conversion

Users can drop files into a department. The system extracts text, normalizes it to Markdown, chunks it, embeds it, and indexes it.

Important distinction:

- PDF to Markdown should not mean the AI invents a new document.
- The first safe version should extract text deterministically and optionally use AI only to clean headings, tables, and section structure.
- The extracted Markdown should be reviewable before indexing or before promotion to active.

### Project-Scoped Assistant

The assistant should answer within a selected project and optionally a selected department. It should show citations, source previews, confidence, response type, and feedback.

Why it matters:

- This becomes the actual App-side demo.
- It can reuse existing `/query` behavior while adding project and department filters.

### Algorithm Comparison

The Dev/Admin side should compare retrieval profiles on the same project and evaluation set.

Comparison should include:

- answer output
- citations
- retrieved source coverage
- source ranks
- latency
- token usage
- estimated cost
- response type
- failure category

### Result Verification

Every algorithm improvement should be verified with project-level evaluation questions.

Verification should answer:

- Did expected sources appear in top-k?
- Did all required documents appear for multi-document questions?
- Did the answer cite the right source?
- Did the response type match expected behavior?
- Did permission leakage remain zero?
- Did hallucination rate decrease or remain acceptable?
- Did latency or cost increase enough to matter?

## Algorithm Enhancement Direction

The current evidence says:

- Vector section-based retrieval is the strongest general baseline.
- Hybrid did not clearly outperform vector-only on the current corpus.
- Multi-document failures were often generation and citation issues, not pure retrieval misses.
- `MULTI-005` remains a known source coverage issue involving `SALES-002`.
- V5 prompt improved overall failed-question count and hallucination rate, but some citation and confidence issues remain.

Future algorithm work should focus on measured improvements:

- Reranking only if it improves source coverage or citation accuracy on failed cases.
- Query decomposition only where multi-source coverage needs it.
- Department/project filters as first-class retrieval constraints.
- Source coverage scoring for multi-document questions.
- Pairwise answer comparison between retrieval profiles.
- Failure buckets that point to retrieval, prompting, citation validation, or benchmark-label issues.

## Presentation Principles

The next UI pass should make these points obvious:

- This is a product, not just a lab.
- The assistant works inside projects and departments.
- Uploaded knowledge becomes indexed, cited evidence.
- Admins can prove whether the AI improved.
- Failures are visible and actionable.
- Safety controls are part of the product, not a footnote.

## Agent Decision Defaults

Future phases should be implemented through a product-demo and technical-review lens. The agent should make a plan internally, use the repo and roadmap to choose reasonable defaults, and proceed without asking for plan approval. Ask the user only for decisions that are genuinely blocking, risky, costly, irreversible, or outside the established product direction.

Default product choices:

1. A project represents a generic knowledge workspace.
2. The existing synthetic corpus maps to a seeded project named `Northstar Analytics`.
3. Departments are project-local knowledge areas unless a later phase introduces reusable templates.
4. Durable App concepts should use Postgres-backed models when practical.
5. Archive or soft-delete should be preferred before hard delete.
6. Retrieval behavior should remain unchanged until project-scoped RAG is implemented.
7. Seeded/demo data must be honest and should never imply fake usage, fake metrics, or unverified quality wins.

## Questions To Resolve Before Implementation

These are still worth revisiting only if the implementation reaches a point where the defaults above are no longer sufficient:

1. Should departments eventually become reusable templates copied into each project?
2. Should the first upload flow support only PDF, or PDF plus Markdown and DOCX?
3. Should extracted Markdown require human review before indexing?
4. Should App-side role selection stay as a demo control, or should production auth be introduced before project work?
5. Should algorithm comparison prioritize answer quality, source recall, citation accuracy, cost, or latency?
