# Evaluator v9 preparation

V8 remains frozen and failed. V9 keeps the original rubric and independently
validated expectations, removes speech acts from factual-claim records, and
clarifies not-found/access/generic refusal distinctions. Review receives explicit
derived labels and the completeness-dependent response-behavior formula.
Reviewer probes now record exact agreement as well as required-error detection.

The evaluator alone uses pinned `gpt-5.4-mini-2026-03-17`, low reasoning, with
4096 completion tokens per call (reasoning included). No temperature parameter.
Official model documentation checked 2026-09-19:
https://developers.openai.com/api/docs/models/gpt-5.4-mini
Pricing uses USD 0.75/M input and USD 4.50/M completion tokens, ignoring possible
cache discounts conservatively. No tools, retries, or background execution.

V9 has a separate transport and continuation writer which validates the complete
frozen v8 call prefix and preserves the historical budget provenance. Unknown
outcomes retain their reservation and block calls. Whole calibration bound:
USD 2.21678925 against USD 3.46333208 remaining before execution. No application
model change, application call or fresh holdout is included.

Readiness requires all 24 development judgments and all three exact audit sets
to agree, no invalid grade, and independent source inspection without unresolved
semantic findings. Even then these are visible development checks, not a claim
of general grader accuracy; new separate-context validation is needed before
application measurement. No human adjudication is inferred.

Verification: five new tests pass for unchanged rubric, complete prefix custody,
reasoning-token accounting, unknown-outcome blocking and whole-case bounds.
Both historical calibration reports still replay.
