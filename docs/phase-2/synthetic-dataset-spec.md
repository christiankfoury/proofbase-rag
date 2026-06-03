# Phase 2 Synthetic Dataset Specification

## Summary

Phase 2 defines the synthetic enterprise knowledge base that will power retrieval, cited answers, role-based permissions, and evaluation. The dataset is intentionally realistic but small enough for a solo developer to build, inspect, ingest, and benchmark.

The dataset contains 14 markdown documents across HR, IT/security, sales, manager-only, HR admin, and IT admin knowledge. It supports factual questions, multi-document questions, permission-restricted questions, ambiguous policy questions, missing-information questions, and citation validation.

No real company confidential data is used.

## Synthetic Company Profile

| Field | Decision |
|---|---|
| Company | Northstar Analytics |
| Industry | B2B SaaS, analytics, workflow automation |
| Size | 450 employees |
| Locations | Toronto headquarters, Montreal office, New York sales hub, remote employees across Canada and the United States |
| Customers | Finance, healthcare operations, logistics, and professional services organizations |
| Product | Analytics and workflow automation platform for tracking operations, approvals, data quality, and business KPIs |
| Work model | Hybrid-first with approved remote work |
| Dataset purpose | Provide realistic internal documents for enterprise RAG, access control, and evaluation |

## Departments Included

- **People Operations / HR:** employee policies, PTO, benefits, remote work, onboarding.
- **IT and Security:** device use, MFA, data classification, access control, acceptable use.
- **Sales:** sales playbook, product positioning, objection handling, approved competitive battlecards.
- **Management:** performance reviews, promotion process, escalation handling, team planning.
- **HR Admin:** restricted HR operations and policy maintenance.
- **IT Admin:** restricted security administration and privileged access review.

## Dataset Principles

- Use synthetic but realistic policies with concrete facts, limits, roles, and exceptions.
- Keep the corpus small: 14 documents total.
- Use markdown for easy inspection, chunking, ingestion, and citation.
- Use consistent metadata headers in every document.
- Keep access control at document level for Phase 2.
- Include overlapping facts across documents to support multi-document retrieval.
- Include intentionally unresolved topics to support refusal and not-found evaluation.
- Avoid real confidential company data, real customer names, passwords, secrets, exploit details, and exact pricing tables.

## Required Metadata Header

Each synthetic document must start with:

```yaml
---
document_id:
title:
department:
category:
access_roles:
restricted:
version:
effective_date:
owner:
review_cycle:
summary:
---
```

## Intentionally Missing or Unresolved Information

The following topics should remain absent or deliberately unresolved across the corpus:

- Sabbatical policy.
- Exact salary bands or compensation formulas.
- Legal advice about employment law.
- Customer-specific contract commitments.
- Security incident exploit details.
- Passwords, tokens, secrets, or system credentials.
- Exact cyber incident severity scoring formula.
- Detailed HR investigation outcomes.
- Formal visa or immigration policy.
- Guaranteed remote work from any country.
- Unapproved competitor claims.
- Product roadmap commitments.
- Customer names tied to confidential deal details.
- Exact pricing tables.

If users ask about these topics, the agent should refuse, state that no policy was found, or direct the user to the correct internal team without inventing details.

## Evaluation Support

The document set must support:

- **Factual questions:** one answer appears clearly in one accessible document.
- **Multi-document questions:** the answer requires combining two accessible documents.
- **Permission-restricted questions:** the answer exists but the requesting role cannot access the document.
- **Ambiguous questions:** related policy exists but does not fully answer the question.
- **Missing-information questions:** no document contains the requested answer.
- **Citation validation questions:** answers must cite the exact supporting document section.
- **Role comparison questions:** the same question produces different results depending on role permissions.
