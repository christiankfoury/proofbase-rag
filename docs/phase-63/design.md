# Phase 63 Ongoing Adversarial Evaluation And Release Gates

## Goal

Make release decisions fail closed, provenance-bound, and honest about what local development evidence cannot prove. Existing sealed holdouts remain protected and unexecuted.

## Gate model

1. Run the deterministic check set for every change before merge or promotion.
2. On the documented cadence, run budgeted semantic development suites only with the explicit external-AI flag and a predeclared budget.
3. Freeze the candidate runtime before a release holdout is authored under separate custody.
4. Use a newly authored holdout once. Never use Phase 47-49 or Phase 55 sealed suites as development data, selectively rerun them, or tune against them.
5. Bind the decision to runtime commit, policy hash, corpus hash, suite/result hashes, models, prompt versions, sample sizes, failures, latency, cost, stability, and adjudication status.
6. Hard security failures block. Quality/budget misses require an explicit human decision and cannot silently promote.
7. Require human review of every automated security failure and at least 10%/11 passes.
8. Require verified rollback, production monitoring/on-call, hosted availability/cost evidence, and no open critical/high findings before production promotion.

## Current boundary

The current Phase 55 evidence is visible development evidence. It can demonstrate that the release engine works, but it cannot become a fresh release or generalization claim. Current production promotion is expected to remain blocked by human review, live monitoring/on-call, hosted availability, and `Independent validation required`.

No cloud resource, paid service, premium licence, Marketplace purchase, external AI call, or sealed-suite execution is needed to implement or verify this phase.
