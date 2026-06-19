# Phase 24 Algorithm Quality Lab Design

## Goal

Phase 24 turns the old retrieval playground into a reviewable Algorithm Quality Lab for engineering-manager style evidence: named profiles, live comparisons, historical metrics, known failures, and explicit human review notes.

## Product Decision

The lab does not automatically run a full benchmark or promote a retrieval profile. A full evaluation run can call OpenAI many times, so this phase keeps expensive workflows manual and review-driven.

Instead, the lab combines:

- historical retrieval-only benchmark metrics from exported evaluation data
- one live shared question across named profiles
- reviewer-entered expected source documents
- live retrieved-source and citation-source coverage
- latency, confidence, cost, and permission leakage signals from real API output
- known failure buckets from exported failure data
- audit-backed review notes

## Named Profiles

The initial profiles are:

- `vector-section`: current default, historically strongest retrieval profile.
- `keyword-section`: fast lexical baseline.
- `hybrid-section-0.5`: vector and keyword blend.
- `multi-doc-forced`: forced query decomposition path for multi-source questions.

Only profiles with existing benchmark exports show historical metrics. Forced multi-doc appears as a live comparison profile but is not represented as a retrieval-only Phase 6 run.

## Review Gate

For one live question, the UI computes:

- retrieved-source coverage
- citation-source coverage
- final confidence
- response type
- total latency
- estimated cost
- unauthorized chunks reaching generation

A profile can be marked as a candidate for that question only by a reviewer. This is not a global promotion claim.

## Audit Event

`POST /evaluation/algorithm-reviews` accepts a review note and writes an `algorithm_profile_reviewed` audit event with:

- profile name
- decision
- primary metric
- question
- expected sources
- result summary
- reviewer notes

The review endpoint treats this audit event as the product record. It returns `503` if audit storage is unavailable instead of claiming the note was recorded.

## Limitations

- No benchmark run is launched from the UI.
- No profile is persisted as globally promoted.
- No reranker was added.
- Project-scoped benchmark sets are still future work.
- Live comparisons still call answer generation and require an OpenAI key.
