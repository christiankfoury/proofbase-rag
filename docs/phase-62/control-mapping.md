# Phase 62 Security Control Mapping

This is a coverage map, not certification. It references [OWASP ASVS 5.0.0](https://owasp.org/www-project-application-security-verification-standard/), [OWASP API Security Top 10 2023](https://owasp.org/API-Security/editions/2023/en/0x03-introduction/), and the [OWASP Top 10 for LLM and GenAI 2025](https://genai.owasp.org/initiatives/top-10-for-llm-and-genai/). A qualified assessor must pin detailed requirement IDs and applicability in the authorized test plan.

| Proofbase area | ASVS 5 families | API Security 2023 | LLM/GenAI 2025 | Evidence / gap |
| --- | --- | --- | --- | --- |
| OIDC, sessions, offboarding | authentication, session management | API2 broken authentication | LLM02 sensitive disclosure | local signed fixture and revocation tests; hosted IdP unconnected |
| tenant/RLS/object access | authorization, data protection | API1 object authorization, API5 function authorization | LLM02 | forced-RLS direct-query tests; independent validation required |
| request/schema/rate controls | validation, API/web services | API4 unrestricted resource consumption, API8 misconfiguration | LLM10 unbounded consumption | local and Redis contract tests; hosted proxy/cache absent |
| upload/parse/review | file handling, validation, malicious input | API8 misconfiguration, API10 unsafe API consumption | LLM03 supply chain, LLM04 data/model poisoning | fixture scan and bounded parser; hosted isolation/scanner absent |
| prompt/source defenses | business logic, validation | API6 sensitive business flows | LLM01 prompt injection, LLM04 poisoning, LLM07 system prompt leakage | visible development suites only; sealed cases untouched |
| evidence/citations/output | output encoding, business logic | API3 property authorization, API10 unsafe consumption | LLM05 improper output handling, LLM09 misinformation | permission-aware evidence and post-generation validation |
| secrets/logging/monitoring | cryptography, configuration, logging | API7 SSRF where applicable, API8, API9 inventory | LLM02, LLM03 | mounted-secret and local content-free monitoring boundaries; managed services absent |
| dependency/container build | secure configuration, files/resources | API8, API9 | LLM03 supply chain | web lockfile, secret scans, non-root runtime; Python pins/CVE tooling backlog |
| agent/tool authority | authorization, business logic | API5, API6 | LLM06 excessive agency | no autonomous external tools; semantic assessment cannot grant authority |
| embeddings/vector retrieval | data protection, authorization | API1, API3 | LLM08 vector and embedding weaknesses | tenant/project/department/document filtering before generation |

No checklist result changes the system's `Independent validation required` status.
