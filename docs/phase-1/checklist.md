# Phase 1 Completion Checklist

Complete these items before moving to Phase 2 implementation.

## Product Scope

- [x] Finalize the product overview.
- [x] Finalize recruiter-facing positioning.
- [x] Finalize MVP boundaries.
- [x] Finalize later-version scope.
- [x] Finalize intentionally excluded features.

## Use Cases and Roles

- [x] Finalize the four MVP use cases: HR, IT/security, sales, manager-only.
- [x] Finalize the five user roles: Employee, Sales Representative, Manager, HR Admin, IT/Admin.
- [x] Finalize document categories and default access rules.
- [x] Define what each role can and cannot access.
- [x] Define good and bad AI behavior for each persona.

## Evaluation

- [x] Finalize success metric categories.
- [x] Finalize benchmark question categories.
- [x] Set first benchmark target size to 60 questions.
- [x] Define benchmark item schema.
- [ ] Write the full 60-question benchmark.
- [ ] Create synthetic company documents that match the benchmark.
- [ ] Map benchmark questions to gold documents and chunks.

## Baseline Behavior

- [x] Define baseline system behavior: retrieve, answer with citations, refuse unsupported or unauthorized questions.
- [x] Decide PostgreSQL full-text search and/or pgvector comes before Azure AI Search.
- [x] Decide LangGraph/LangChain is deferred unless orchestration complexity requires it.
- [x] Define the recruiter demo narrative: baseline RAG to improved RAG to enterprise RAG with measurable gains.

## Ready for Phase 2 When

- [ ] Synthetic document inventory is drafted.
- [ ] The first benchmark dataset is drafted.
- [ ] The initial data model can be derived from roles, document categories, and benchmark schema.
- [ ] The first implementation milestone is scoped to Version 1 Baseline RAG only.
