# Core Use Cases

## 1. HR Policy Assistant

| Field | Decision |
|---|---|
| User role | Employee, HR Admin |
| Document types | Employee handbook, PTO policy, benefits guide, remote work policy |
| Example questions | "Can I work remotely from another province?" "How much parental leave is available?" |
| Expected behavior | Retrieve HR docs, answer with citations, refuse if policy is not found, distinguish general policy guidance from legal advice |
| Failure cases | Hallucinated policy, outdated citation, unauthorized manager policy shown |
| Enterprise value | Reduces HR ticket volume and improves policy consistency |
| Recruiter value | Shows grounded answers, citations, and refusal behavior |

## 2. IT/Security Policy Assistant

| Field | Decision |
|---|---|
| User role | Employee, IT/Admin |
| Document types | Acceptable use, MFA policy, device security, data classification |
| Example questions | "Can I use personal devices?" "What data can I store in shared drives?" |
| Expected behavior | Provide concise policy answer with security citations and allowed scope |
| Failure cases | Gives operational security details, misses restricted policy boundaries |
| Enterprise value | Improves compliance and reduces repetitive IT questions |
| Recruiter value | Shows permission-aware security RAG |

## 3. Sales Knowledge Assistant

| Field | Decision |
|---|---|
| User role | Sales Representative |
| Document types | Sales playbooks, product FAQs, objection handling, approved battlecards |
| Example questions | "How do I respond to price objections?" "What industries are best-fit?" |
| Expected behavior | Retrieve sales-approved content, cite playbooks, flag unsupported competitive claims |
| Failure cases | Uses stale claims, invents customer proof, exposes restricted strategy |
| Enterprise value | Helps reps find approved answers quickly |
| Recruiter value | Demonstrates domain-specific retrieval and hybrid search value |

## 4. Manager-Only Knowledge Assistant

| Field | Decision |
|---|---|
| User role | Manager |
| Document types | Manager handbook, performance review guide, escalation process, team planning docs |
| Example questions | "How should I document performance issues?" "What is the promotion calibration process?" |
| Expected behavior | Answer only for manager role, cite manager docs, refuse for employee role |
| Failure cases | Permission leak, missing refusal, vague citation |
| Enterprise value | Protects sensitive internal processes while improving manager productivity |
| Recruiter value | Strongly demonstrates RBAC and enterprise trust controls |
