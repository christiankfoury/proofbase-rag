# Runtime remediation and fresh measurement

1. Phase 67: repair confirmed context and retrieval mechanisms; verify on new
   development variants and existing local regressions; commit, review and push.
2. Phase 68 preparation: run bounded live development probes and inspect exact
   retrieved evidence and citations. Improve the evaluator against explicit
   challenge fixtures covering truthful statements of missing evidence, omissions,
   refusal without citations, correct not-found behavior, wrong-topic truth,
   stitched quotations and invalid/UTF-8-corrupted inputs. Preserve failed
   calibration attempts. No composite accuracy claim from an unreliable judge.
3. Only after development is finished, freeze runtime, evaluator, corpus,
   configuration and indexed data. Author and validate 60 new questions through
   separate context-isolated passes that cannot see prior questions or results.
   Verify overlap, seal hashes and publish author-plus-AI provenance. This is not
   independent human labeling.
4. Run each sealed case once, preserving raw answers, retrieved and cited chunks,
   provider usage, grader inputs/outputs and invalid judgments. Stop on custody,
   safety or budget failures. No selective retries, test tuning or silent removals.
5. Publish dimension-specific denominators, unresolved counts, source-linked
   agent review and reproducible results beside the unchanged historical results.
   Agent review is not human adjudication. A different question set is not a
   controlled before/after experiment; disclose that limitation.
6. Verify artifacts, commit, review and push. Report failure cases and remaining
   limitations even if the desired pass rate is not reached.

## Financial gate

The previously approved cumulative ceiling is USD 0.75; recorded spend is
USD 0.5687728, leaving USD 0.1812272. Phase 67 uses no external calls.
The user approved an increase to USD 2.00 on 2026-09-14. This allows at
most USD 1.4312272 additional estimated token cost. The earlier full evaluation
sequence used USD 0.446726 including interrupted/preflight work; this is planning
evidence, not a price or success guarantee for a new run.

Use a new ledger that preserves the complete previous call prefix
and explicitly records the changed authorized ceiling. Keep all old ledgers and
budget code frozen. Reserve cost before calls, price every model explicitly,
disable retries, and stop on unknown outcomes. Allocate at most USD 0.20 for live
development, USD 0.25 for evaluator calibration, and the remaining new allowance
for setup and one holdout run. Do not start the holdout without enough conservative
estimated headroom. Failure of calibration or budget sufficiency remains a gate,
not permission to weaken the evaluator or exceed the cap.
