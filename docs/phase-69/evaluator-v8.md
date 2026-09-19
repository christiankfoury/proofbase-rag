# Phase 69: v8 evaluator correction

V7's failed calibration and portable replay were committed, reviewed and pushed
as `9a0c395` and `2dabfc3`. Main aligned with origin/main; unrelated request-log
edits remain preserved. V7 source and evidence are frozen.

V8 uses separate contract, transport and calibration files. Claims have an explicit
`factual` or `speech_act` kind. Speech acts must have unknown evidence statuses and
empty references, and are excluded from factual/citation denominators. Appended
policy claims still require assessment. Exact answer spans and all existing
reference, completeness, permission/safety and uncertainty rules remain enforced.

The reviewer receives a deterministic projection of the actual proposed dimension
labels as well as raw inputs and candidate details. Its instructions explicitly
distinguish a correctly detected answer failure from an incorrect grader label.
Agreeing with a correct failure or unresolved label is appropriate; disagreement
remains unresolved. Three deliberately wrong candidate probes retain their original
labels and data, testing omissions and internal inconsistency. No expectations
were changed following model execution.

The v7 accounting implementation is reused, including complete historical-prefix
protection, USD 5 authorization, pre-call reservations, zero retries and unknown
outcome stopping. The v8 full-attempt bound is **USD 2.921800** against **USD
3.65143408** remaining before execution. The larger reservation includes longer
instructions and the explicit candidate-label projection. Actual charges will be
recorded separately. The v8 runner also snapshots the ledger at attempt completion.

Six new local test methods pass, including unchanged visible challenge outcomes,
speech-act contracts, explicit negative review labels, projection/reducer agreement,
conservative review cost bounds and recorded three-call execution with a test double.
The four frozen v7 replay tests also pass. These are implementation checks, not a
semantic-validation claim. Next is one complete live development calibration,
followed by evidence inspection and honest publication regardless of outcome.
