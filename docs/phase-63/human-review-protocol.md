# Human Review Protocol

Before a production promotion, a named human reviewer must examine every automated security failure and a predeclared random sample of at least 10% of automated passes, with a minimum of 11 passes for the current 102-case development manifest.

Record case ID, automated outcome, security/quality classification, evidence sufficiency, citation support, false-positive or product-failure rationale, reviewer identity, timestamp, and conflict resolution. Do not copy inaccessible source text, secrets, or another tenant's content into the review record.

Allowed dispositions are `confirmed_product_failure`, `evaluator_only`, `mixed`, `benchmark_defect_proven`, and `pass_confirmed`. A benchmark defect requires corpus-grounded evidence and a separately reviewed future-suite correction; it never rewrites the completed run.

The current operational record intentionally reports zero completed human reviews. Agent self-review does not satisfy this gate.
