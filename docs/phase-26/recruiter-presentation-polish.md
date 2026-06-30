# Phase 26 Recruiter Presentation Polish

## Goal

Phase 26 aligns the product first impression, demo script, README, screenshots, and case study around one story:

> Proofbase is an App-side project knowledge workspace with Dev/Admin evidence for quality, safety, failures, and operations.

## Presentation Sequence

The preferred five-minute sequence is:

1. App Home
2. `Northstar Analytics` project workspace
3. Department document library
4. Scoped assistant answer with citations and retrieved context
5. Algorithm Quality Lab comparison
6. Failed-question or feedback human review

This keeps the demo recruiter-friendly while giving engineering managers direct access to the evidence layer.

## App-Side Changes

The App Home now exposes a four-step route path:

- open projects
- inspect department knowledge
- ask with project and department scope
- prove controls in Dev/Admin

The copy emphasizes implemented features:

- project workspaces
- department document libraries
- PDF-to-Markdown extraction review
- project- and department-scoped assistant retrieval
- citations, confidence, latency, retrieved context, and feedback

It also states the important limitation: uploaded PDF approval and indexing remain future work.

## Dev/Admin Changes

The Dev/Admin overview now frames itself as the proof layer behind the App demo. It highlights:

- Algorithm Quality Lab
- failed-question inspection
- permission safety

The page continues to show benchmark metrics and known tradeoffs rather than replacing them with marketing claims.

## Documentation Changes

Updated materials:

- `README.md`
- `docs/demo/demo-script.md`
- `docs/demo/interactive-demo-guide.md`
- `docs/demo/screenshots-checklist.md`
- `docs/demo/final-cleanup-checklist.md`
- `docs/demo/portfolio-case-study.md`
- `docs/roadmap/progress.md`

## Limitations Kept Visible

- The corpus is synthetic.
- `/chat` now uses local demo auth, but it is still not production authentication or SSO.
- Uploaded PDFs are extracted for review only; approval, chunking, embeddings, and indexing are not implemented.
- Human review decisions are persisted, but approved candidates are not automatically exported into benchmark JSON.
- Project-scoped benchmark runs remain future work.
- Azure deployment is documented as ready work, not claimed as completed.
