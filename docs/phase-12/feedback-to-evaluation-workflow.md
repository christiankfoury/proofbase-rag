# Phase 12: Feedback-to-Evaluation Workflow

## Overview

Negative feedback from real queries can surface answer quality problems that the benchmark does not yet cover. This workflow converts thumbs-down feedback into candidate benchmark questions for human review.

**Important:** Candidates are never automatically added to `benchmark-questions.json`. Human review is required at every step.

## Step-by-Step

### 1. Collect Feedback

Users submit feedback via `POST /feedback` with `rating: "thumbs_down"` and a meaningful `feedback_category` (e.g. `hallucination`, `wrong_citation`, `not_found_incorrectly`).

### 2. Export Candidates

```bash
python scripts/export_feedback_candidates.py
```

This reads all `thumbs_down` feedback from the database and writes candidates to:

```
data/evaluation/feedback-candidates.json
```

Each candidate includes:

```json
{
  "original_question": "What is the parental leave policy for adoptive parents?",
  "bad_answer": "Parental leave applies only to birth parents.",
  "user_comment": "Adoptive parents are also eligible per the HR policy.",
  "feedback_category": "incorrect_answer",
  "suggested_question_type": "answer_quality",
  "needs_human_review": true,
  "source_session_id": "...",
  "feedback_id": "...",
  "created_at": "..."
}
```

### 3. Human Review

Open `data/evaluation/feedback-candidates.json` and for each candidate:

- Verify the question is answerable from the synthetic document corpus
- Confirm the `suggested_question_type` is correct
- Write the `expected_behavior` (e.g. `answer`, `not_found`, `refuse_no_access`)
- Identify `expected_source_document` and `expected_source_section_or_quote`
- Assign a unique `question_id` following the existing convention (e.g. `FEED-001`)

### 4. Add to Benchmark

After review, manually copy the validated question into `data/evaluation/benchmark-questions.json` following the existing schema. Do not bulk-import — review each question individually.

### 5. Re-run Evaluation

```bash
python scripts/run_prompt_experiment.py --prompt-version all
python scripts/compare_prompt_versions.py
python scripts/export_dashboard_data.py
```

## Guardrails

- `needs_human_review: true` is always set by the export script and cannot be overridden
- The export script never writes to `benchmark-questions.json`
- Only `thumbs_down` + negative categories are exported (not `correct` or `other`)
