# Five-minute presenter script

Use the [interactive demo guide](interactive-demo-guide.md) for setup, exact clicks, expected behavior and recovery.

**0:00 — Workspace.** “Proofbase is an internal knowledge assistant. Northstar Analytics is a synthetic company, organized into projects and departments.”

**0:45 — Source.** “Here is the actual Employee Handbook. Documents must be indexed to become searchable. Uploads and optional AI cleanup remain reviewable until an editor approves indexing.”

**1:30 — Question.** “As Emma Employee, I will ask where the company has offices, scoped to People Operations.” Send once and wait for the final response.

**2:30 — Proof.** “The answer names Toronto, Montreal and New York. Here is its handbook citation and the retrieved passage. The displayed role and scope explain which evidence was available. Confidence is a support signal, not a guarantee.” Stay in the same chat and open Why this answer?

**3:30 — Evidence and limits.** Switch to Kai Admin and open Dev/Admin’s evaluation methodology page. “The application records evaluations and failures. The earlier separate 60-case run passed 33 automated protocol checks; the newer run has unresolved grading judgments and no validated overall score. These results are preserved, not replaced by a perfect demo score.”

**4:30 — Close.** “This version is a finished portfolio demonstration of the workflow and its engineering tradeoffs. It still has answer-completeness and evaluator limitations, and local demo identity is not production SSO.”

Answer deeper questions using the [architecture explanation](architecture-diagram.md), [evaluation reviewer guide](../evaluation/README.md), and [per-case measured answers](../phase-68/case-review.md). Do not call automated or agent review independent human validation.
