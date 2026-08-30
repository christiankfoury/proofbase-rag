# Phase 1 Product Scope

## Product Overview

Proofbase is a secure internal knowledge assistant for company employees. It helps users ask questions across internal documents and receive answers that are grounded in accessible source material, cited, and evaluated for quality.

The product simulates how a real company would deploy an internal AI assistant. Employees can ask about HR policies, IT/security rules, sales enablement content, and manager-only operating documents. The assistant retrieves relevant knowledge, filters results by role permissions, answers only when evidence is available, cites the source material, and refuses unsupported or unauthorized requests.

The business problem is internal knowledge fragmentation. Employees waste time searching across handbooks, onboarding docs, policies, sales playbooks, and process documents. A normal chatbot is risky because it can hallucinate, cite weak evidence, or expose restricted information. This project demonstrates a production-minded alternative: an evaluated enterprise RAG system with access control, citations, measurable retrieval quality, and continuous improvement.

## Product Positioning

Proofbase is an enterprise RAG platform that simulates a secure internal company assistant. It combines document ingestion, hybrid retrieval, role-based permissions, cited answers, citation confidence, and an evaluation dashboard to show measurable improvements across retrieval and answer quality experiments. Unlike a simple PDF chatbot, it is built around evaluation-driven development: benchmark questions are defined upfront, retrieval and answer quality are measured, permission leaks are tested, and latency/cost are tracked as part of production readiness.

## MVP Scope

The MVP should prove enterprise RAG quality, not breadth.

Included:

- Synthetic but realistic company document set across HR, IT/security, sales, and manager-only categories.
- Role-based access model with five roles: Employee, Sales Representative, Manager, HR Admin, IT/Admin.
- Document metadata: category, role visibility, source title, version, effective date.
- Baseline RAG using PostgreSQL full-text search and/or pgvector.
- Answers with citations and refusal behavior.
- Benchmark question set created before chatbot implementation.
- Evaluation runner measuring retrieval quality, answer quality, citations, permissions, latency, and cost.
- Simple dashboard or report showing baseline versus improved versions.
- Guided demo flow with four scripted enterprise scenarios.

## Later Version Scope

- Hybrid retrieval with weighted full-text plus vector search.
- Query rewriting and multi-step retrieval.
- Citation confidence score.
- Conversation memory constrained by user role and cited evidence.
- Prompt versioning and experiment comparison.
- LangGraph or LangChain only if orchestration complexity justifies it.
- Azure Blob Storage ingestion.
- Azure deployment with Docker.
- Optional Azure AI Search comparison.
- OpenTelemetry or LangSmith tracing.
- Admin interface for document upload and benchmark management.

## Intentionally Excluded Features

- Slack, Teams, Google Drive, or SharePoint integrations in MVP.
- Fine-tuning.
- Autonomous agents that take business actions.
- Real employee data.
- Complex multi-tenant enterprise SSO.
- Full legal or compliance certification.
- Complex workflow automation.
- Azure AI Search before PostgreSQL search baseline is measured.
- Broad document ingestion formats beyond what supports the demo.

## Baseline System Behavior

The baseline assistant must:

- Identify the current user role.
- Retrieve only documents visible to that role.
- Return cited answers when relevant evidence is found.
- Refuse when the answer is unsupported by retrieved evidence.
- Refuse when the user asks for content outside their permissions.
- Log retrieval results, selected citations, latency, token usage, and estimated cost.
- Preserve enough evaluation data to compare Version 1, Version 2, and Version 3.
