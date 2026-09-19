# Five-minute Proofbase walkthrough

This is a local portfolio demo over synthetic Northstar Analytics documents. Start at `/demo`; leave the deeper evaluation and upload flows for questions afterwards.

## Before presenting

Follow the [README local setup](../../README.md#docker-quickstart). Start the API, web, Postgres and Redis; confirm `/health` and `/ready` on the API. A fresh database needs schema setup and one corpus ingestion. An existing indexed database does **not** need re-ingestion for each demo. Ingestion, live answers and optional AI cleanup can call OpenAI and incur cost.

Open the web app, select **Emma Employee** in the header, and wait for the identity and project to load. Confirm that Northstar Analytics and the Employee Handbook are indexed. The September 19 verification used web `http://127.0.0.1:3001` and API `http://127.0.0.1:8001` to avoid another app's ports; standard Compose defaults are 3000 and 8000.

## The walkthrough

| Time | Action | What to say / verify |
| --- | --- | --- |
| 0:00–0:45 | Open `/demo`, then **Start at Northstar**. | “This workspace organizes synthetic company knowledge into departments.” Show Northstar Analytics and document counts. |
| 0:45–1:30 | **Review documents** → People Operations → **Employee Handbook**. | Show the indexed Markdown preview. It names Toronto, Montreal and New York. Explain that PDF extraction and optional AI cleanup are review steps; approval is required to index. |
| 1:30–2:30 | **Ask in chat**. Confirm Northstar / People Operations. Ask **Where does Northstar Analytics have offices?** | Press Send once. Wait for the final answer and citations, not just the streaming draft. The answer should name Toronto, Montreal and New York and cite the handbook. |
| 2:30–3:30 | Stay in that chat; expand **Why this answer?**. | Compare the citation/source snippet with the answer. Show the Employee role and department scope. Confidence is a support signal, not a calibrated correctness probability. |
| 3:30–5:00 | Select **Kai Admin**, then open `/dev-admin/evaluation`. | Show saved evaluation evidence. Explain that development benchmark scores and unseen-suite results answer different questions. Finish with the limitations below. |

Do not navigate back to a new chat to inspect proof: the current answer's proof panel is already in the conversation. Switch roles only after showing the answer; start a fresh chat when demonstrating a different identity.

## Optional checks after the five minutes

As Emma Employee, in a fresh chat:

- Ask **What is the sabbatical policy?** The current corpus does not define it; the assistant should abstain.
- Ask **What are the promotion calibration rules?** The assistant should refuse access without revealing restricted policy details.
- Inspect `/algorithm` and `/trust` for the implementation and production boundary.

A live PDF upload, AI cleanup, approval and indexing is a separate, longer demo. Use synthetic/non-sensitive material only. A failed historical upload remains visible as a failure; it is not evidence that a new upload succeeded.

## If something fails

- **Identity or project never loads:** check the API and database first, and that the web API URL points to the same running API. Refresh after restarting the API.
- **Scope is wrong:** use the project/department selectors before sending. Do not broaden scope to make a failed answer look successful.
- **Request errors or AI budget is exhausted:** stop retrying blindly. Show the source preview and clearly labeled saved screenshots; say the live request did not complete.
- **Dev/Admin denied:** select Kai Admin in the local demo header. This is a development identity selector, not production SSO.

## Explain the limits plainly

The earlier Phase 65 frozen-runtime evaluation recorded **33/60 (55%) automated protocol passes**, below its 80% target, with eight invalid grader outputs and human review pending. Phase 68 used a different 60-case suite and reported dimensions separately; unresolved judgments mean there is no validated replacement overall accuracy score. The older tuned benchmark's `0/130` recorded failures are not unseen accuracy. [Evidence and reproduction](../../README.md#evidence-snapshot).

These portfolio fixes were checked with focused before/after regressions and a live walkthrough. No new holdout was run, and historical scores do not measure the final patched runtime. Answers can still miss facts, over-abstain, or receive incorrect automated judgments. Synthetic safety checks are finite evidence; production identity integration, enterprise security validation and operational readiness are separate work. The evaluator v12 calibration and new holdout are deferred, not passed.
