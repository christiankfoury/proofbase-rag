# Phase 65 — fresh current-runtime measurement

Status: **interrupted — no full-suite percentage**. The one-shot run processed 58/60 cases, then the first upload fixture received HTTP 429 at approve/index. Case 59 never reached its query; case 60 was not started. No case was retried.

The planned suite has 60 cases across nine categories. A context-isolated agent authors the suite from the synthetic corpus and neutral contract; a separate agent checks labels before sealing. Neither role is a human reviewer. Runtime behavior and evaluator rules are frozen before authoring, and no tuning against the holdout is allowed.

The run will use the actual `/query` endpoint with local demo identities, a cloned local index, isolated logs/files and explicitly recorded call limits. This measures the frozen application under that evaluation configuration, not hosted production performance. The historical Phase 49 73.3% is a different experiment and cannot be used as a before/after baseline.

The app's conservative tenant daily admission allowance was exhausted. Eight preceding query requests (fresh-051 through fresh-058) also returned HTTP 429 and remain recorded as failures; they are not silently excluded. The final actual token-cost estimate, including calibration and the visible smoke, is **$0.237036**, below the separate $0.75 external API ceiling. Admission reservations and actual provider token charges are different measures.

There are 30 machine passes among the 58 processed cases, but the predeclared protocol prohibits turning this partial count into a full-suite rate. The saved artifacts include 39 answer-expected and 19 non-answer-expected processed cases; both rates remain null. Human review is pending. Do not present these partial results as current generalization accuracy or compare them with historical 73.3%.

Source/label validation covered 60 cases and 103 atomic required facts. The frozen Northstar index contains the 19 authored corpus documents plus three retained synthetic Phase 40 upload documents, two with indexed chunks. The broader cloned database has 32 documents across four projects; query scope remains Northstar. These additional fixture texts were verified against the known Phase 40 fixture script.

Saved verdict replay passed offline. The 21 local tests, source compilation and initial dashboard production build passed; final publication checks are recorded in the tracker. Model generation and semantic grading are not guaranteed to repeat. [Human-review packet](human-review-packet.md) preserves all 60 case slots and identifies missing responses.

Next experiment: preserve this entire run as interrupted. A test-only admission allowance sufficient for 60 requests can be declared before a new freeze while retaining the same $0.75 shared external API ceiling and unchanged app defaults. A new context-isolated author must create another suite; this run must never be resumed or cherry-picked.
