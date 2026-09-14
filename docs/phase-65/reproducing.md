# Reproducing the fresh evaluation evidence

The saved-record check needs the repository and Python dependencies, but no database or API key:

```powershell
python scripts/report_fresh_eval.py --check
python -m unittest scripts.test_fresh_eval scripts.test_fresh_report scripts.test_evaluation_evidence
```

It validates the runtime/evaluator source hashes, suite/validation custody hashes, case identities, deterministic verdict contracts, aggregate denominators, ledger totals and durable-record hashes. It does **not** independently rejudge model-generated semantic labels. The expected facts, exact source quotes, raw responses, retrieved authorized evidence and model judgments are available for inspection in `data/evaluation/fresh-current`. The separate human packet links each case to that evidence.

The freeze records the measured source commit, normalized code/corpus hashes, database table hashes (including vectors and access policies), relevant settings, Python and dependency versions. JSON custody artifacts use raw-byte hashes and disable Git line-ending conversion. Runtime files normalize CRLF to LF for portable checks. These fingerprints establish consistency with the committed artifacts, not third-party attestation.

The seal records the suite's unexecuted state at sealing time and stays immutable. The run manifest records whether execution later completed or was interrupted. Grader citation IDs C1, C2, etc. refer to the ordered raw response citations; the response itself is preserved without those added grading labels.

The execution command is intentionally one-shot:

```powershell
python scripts/run_fresh_eval.py --preflight
python scripts/run_fresh_eval.py --allow-external-ai
```

These commands will refuse a changed frozen environment or an existing run directory. Do not remove completed or interrupted evidence to bypass that refusal. A fresh repeat requires a separately named protocol/run and appropriately documented authorization; once the questions have been examined, they are no longer unseen. Do not selectively rerun failures or describe a repeated suite as fresh generalization.

The original run uses an isolated clone called `proofbase_eval_phase65` of the local synthetic demo database. `scripts/fresh_eval_environment.py --prepare` creates a new clone only if that name does not already exist. It never drops or replaces a database. Exact original database row IDs and vectors may differ from a newly seeded installation, so a new installation cannot claim to reproduce the old runtime merely by passing the same question strings. Inspect the saved evidence offline instead.

The harness caps chat output at 2048 tokens and disables SDK retries and external telemetry delivery. The grader has a separate 1800-token limit and a pinned model snapshot. Runtime model aliases, provider nondeterminism and latency remain limitations. The shared $0.75 API ledger covers calibration, the visible development smoke, embeddings, application model calls and grading. It is a conservative token-cost accounting control, not a provider invoice or cloud-infrastructure budget.

The target was at least 80% automated full-response passes with zero recorded permission/scope/memory violations. Every expected material fact must be correct and every factual claim supported by its exact cited passage. Unknowns and malformed grades fail; interrupted runs have no full-suite percentage. Report expected-answer and expected-non-answer denominators separately. Do not compare the percentage directly to Phase 49's historical 73.3%: the questions, runtime and evaluator differ.

Human review requires a named person to fill in all decisions, timestamps and reasons. Agent-authored calibration, separate agent authoring and separate agent validation do not establish independent human review or inter-rater agreement.

The `preflight-rejected-v1` folder contains an earlier **unexecuted** draft and freeze. It was replaced after a code-review finding in the grader input envelope. It contributes no cases or outcomes to the current run. The correction and passing version-4 calibration are documented in Phase 64; the final authoring pass starts after that correction is frozen.
