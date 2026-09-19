# Portfolio finish — 2026-09-19

The user narrowed the remaining work to a finished portfolio version: run the app, fix a few demonstrated demo bugs, make a five-minute walkthrough reliable, preserve measured evidence, and polish README, screenshots and architecture. This completes that bounded scope. It does not complete the deferred evaluator or production-readiness roadmaps.

## Demonstrated fixes

| Problem | Before | After / focused verification |
| --- | --- | --- |
| Supported process questions matched a missing-information keyword | A development question about reviewing customer-specific requests returned `not_found` even with a matching source passage; the generator ignored the earlier positive evidence decision. | Both generation paths pass the evidence decision through. `answer` / `partial_answer` with authorized chunks can proceed to normal generation and validation. No-evidence and restricted-topic guards remain. Tests cover both blocked generation paths. |
| Citation ID treated as a policy number | `$500. Source: DOC-001` was sent for repair because `001` was absent from the policy text. | Only an exact authorized document ID following `Source:` is excluded from numeric claim scanning. Unknown IDs and unsupported amounts on the same line still fail. Semantic and citation checks continue. |
| Duplicate identity lookups disrupted navigation | Browser navigation/refresh reached HTTP 429 and displayed API offline even though project data had loaded. Shell and page components requested the same identity concurrently. | Concurrent requests share one promise per identity; different users remain isolated and completed/failed responses are not cached. Four simultaneous list lookups issue one fetch in the focused test. Server authentication limits remain unchanged. |

The guided page now has timed steps, explicit Emma/Kai role instructions, an evidence-page link and a same-chat proof step without a link that starts over. Redundant demo-header actions were removed after the narrow browser viewport showed them crowding the identity selector; the start action remains in the main card. Stale AI-cleanup and streaming descriptions are corrected. The admin overview clearly distinguishes historical benchmark scores from later frozen-runtime evidence. Documentation now leads with a short presenter path and an implemented architecture explanation.

## Local verification

The existing Proofbase Postgres and Redis containers were started without resetting the database. The worktree API ran on loopback port 8001 and the web app on 3001, leaving another local application's 3000/8000 services alone. A Windows cross-drive dependency junction initially prevented Next.js compilation; copying the existing dependency installation into the worktree resolved that local setup problem. No dependency versions changed.

Browser verification covered the project, People Operations handbook preview, correctly scoped chat, answer proof, Employee abstention/refusal, Kai Admin selection, and the evaluation evidence page. A successful optimized production build is served for the final local demo.

| Live question | Observed final behavior | End-to-end latency |
| --- | --- | ---: |
| Where does Northstar Analytics have offices? | Toronto, Montreal, New York; answer with handbook and remote-policy citations. | 11.082 s |
| What is Northstar's sabbatical policy? | `not_found`, no invented policy. | 3.956 s |
| What is the promotion calibration process? | `refuse_no_access` for Employee, no policy details in the answer. | 4.968 s |

These are three walkthrough checks, **not an accuracy estimate**. The extra remote-policy citation in the office answer remains inspectable; this pass does not establish that every citation is necessary. [Saved smoke observations](../../data/evaluation/portfolio-finish/smoke-check.json).

Verification completed:

- `python -m unittest scripts.test_portfolio_finish scripts.test_phase67_context_coverage scripts.test_current_eval_integrity` — 26 tests passed, including nine new focused cases.
- `node scripts/test_portfolio_identity.cjs` — five identity-request checks passed against the actual TypeScript module with mocked fetch.
- `python scripts/test_phase54_post_generation_validation.py` — passed, including claim/citation/fail-safe cases.
- `python scripts/test_phase58_abuse_controls.py` — passed; optional external Redis contract test not requested.
- API/new-script compilation and Next.js production build/type checks — passed. The local unrelated home-directory lockfile produces a non-fatal Next.js workspace-root warning.
- Phase 65, 66 and 68 saved-report `--check` commands and benchmark v1.1 validation — passed, with historical artifacts unchanged. These replay checks do not revalidate semantic judgments.
- Focused source, ledger and generated browser-bundle secret scan — zero findings; Git whitespace checks passed.

## Costs and retained evidence

Eleven SDK calls for the three live queries settled at an additional estimated **USD 0.00635410**. The conservative cumulative total is **USD 2.14328077**, within the existing USD 5 approval. The local verification wrapper uses a durable USD 0.50 incremental cap and no automatic SDK retries, retaining the historical ledger prefix. [Ledger](../../data/evaluation/portfolio-finish/api-ledger.json). This is a single-process demo guard, not a production billing control. UI generation-cost fields omit auxiliary assessment/validation calls; they are not the full verification spend.

Historical Phase 65 remains **33/60 automated protocol passes** with human review pending. Phase 68 remains a distinct 60-case dimension report with unresolved semantic grading disagreements, not a validated replacement overall score. The preserved source-inspected completeness figure 28/38 is provisional and not comparable overall accuracy. No historical answer, expected fact, source or grader judgment was rewritten for this finish.

## Deliberate stopping point

No new holdout, full benchmark rerun, evaluator v12 calibration, cloud deployment, new upload/indexing cycle, independent penetration test or human adjudication was performed. Generalization improvement is not claimed. Answers can still omit facts or over-abstain; graders can disagree with source inspection. Local demo identities, synthetic safety coverage and local file controls do not establish production readiness.

The README, timed walkthrough, presenter script, actual browser screenshots and architecture explanation are the portfolio deliverables. Further work is optional and requires a new scope; do not resume the deferred phase queue automatically.
