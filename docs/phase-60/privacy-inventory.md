# Phase 60 Sensitive-Data Inventory

The approved portfolio data stance is synthetic or non-sensitive business data only. This inventory describes where content exists; it does not authorize regulated or personal data.

| Surface | Necessary content | Operational-log rule | Access and lifecycle |
| --- | --- | --- | --- |
| Browser/API requests | Question, reviewed Markdown, feedback, upload bytes | Never copy full content, auth headers, or cookies to logs | Authorized user request lifetime; HTTPS is deployment-required |
| Chat sessions/messages | User questions and assistant answers | IDs, hashes, counts, timings, response type only | Tenant RLS and project membership; tenant deletion/export workflow remains operational work |
| Retrieved chunks/prompts/model payloads | Authorized source text and minimum query/memory context | Never log prompt, source text, model payload, citation text, or memory text | Exists only for the request/provider call; external-provider handling must be configured and reviewed |
| Uploaded originals | Approved non-sensitive PDF bytes | Opaque file ID/hash/state only | Tenant quarantine; 7-day rejected/unapproved and 30-day approved-original policy; legal hold overrides |
| Extracted/approved documents | Reviewable Markdown and indexed chunks | Content hash/count only | Tenant RLS; retained until tenant archive/delete under the Phase 59 decision |
| Feedback | Question, answer, citations, comment needed for review | Feedback ID/category/rating and hashes only | Tenant RLS; Dev/Admin review; deletion/export workflow remains operational work |
| Audit records | Actor/resource/action/outcome/reason and bounded metadata | IDs, codes, counts, hashes; content fields recursively fingerprinted | Tenant RLS, Dev/Admin API, 365-day policy; incident hold overrides |
| Observability JSONL | Latency, tokens, cost, confidence, route, IDs | Question/rewrite fingerprints; no prompt/source/answer text | Dev/Admin API, owner-only local file where supported, 30-day policy |
| Defense traces | Stage, route, reason, latency, cost, invariants | Existing seven-stage bounded schema; no user/source/memory text or identity authority | Development evidence and Dev/Admin view |
| External platform telemetry | Allowlisted operation/model/token/cost metadata | Recursive redaction after allowlisting; question hash only | Disabled by default; destination/credential and retention are external decisions |
| Evaluation artifacts | Synthetic questions, expected answers, model outputs, citations | Detailed artifacts stay in declared evaluation locations, not runtime logs | Repository/local-run retention policy; sealed holdouts remain immutable |
| Secrets/configuration | API, signing, DB, Redis, telemetry credentials | Never log values or place them in client bundles/artifacts | Environment local-only; mounted files production-shaped; managed provider unconnected |

## External AI provider boundary

Questions, authorized retrieved evidence, system prompts, and limited memory context are sent to the configured OpenAI API when an approved workflow invokes it. Before deployment, the operator must review the organization/project data controls, retention terms, regional requirements, DPA, abuse-monitoring settings, access logs, and deletion obligations applicable to its account. Proofbase does not claim zero-data-retention eligibility or a particular provider-retention configuration.
