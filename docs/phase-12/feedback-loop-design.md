# Phase 12: Feedback Loop Design

## Feedback Table Schema

Stored in PostgreSQL alongside the existing chat_sessions and chat_messages tables.

```sql
feedback (
  id uuid primary key,
  session_id uuid references chat_sessions(id) on delete set null,
  message_id uuid references chat_messages(id) on delete set null,
  question text not null,
  answer text not null,
  response_type text,
  citations_json jsonb not null default '[]',
  user_role text not null,
  rating text not null check (rating in ('thumbs_up', 'thumbs_down')),
  user_comment text,
  feedback_category text not null default 'other',
  created_at timestamptz not null default now()
)
```

## API Contract

| Method | Route | Description |
|--------|-------|-------------|
| POST | /feedback | Submit a feedback item |
| GET | /feedback | List feedback (filters: rating, feedback_category, limit) |
| GET | /feedback/summary | Aggregate counts and category breakdown |

### POST /feedback request body

```json
{
  "session_id": "uuid or null",
  "message_id": "uuid or null",
  "question": "What is the vacation policy?",
  "answer": "Employees receive 15 days...",
  "response_type": "answer",
  "citations": [],
  "user_role": "Employee",
  "rating": "thumbs_down",
  "user_comment": "The answer is missing the carry-over policy.",
  "feedback_category": "incorrect_answer"
}
```

## Feedback Categories

| Category | Description |
|----------|-------------|
| correct | Answer was accurate and well-cited |
| incorrect_answer | Factually wrong |
| missing_citation | Cited fewer sources than expected |
| wrong_citation | Cited the wrong document/section |
| hallucination | Answer included content not in retrieved docs |
| refused_incorrectly | Refused a question the user should be allowed to ask |
| should_have_refused | Answered a restricted question it should have refused |
| not_found_incorrectly | Said not found when the answer exists |
| permission_issue | Role-based access problem |
| unclear_answer | Answer was confusing or incomplete |
| other | Anything else |

## Audit Integration

Every POST /feedback call logs a `feedback_submitted` event to `audit_logs` with:
- `rating`, `feedback_category`, `feedback_id` in metadata
- `resource_type = "feedback"`, `outcome = "success"`
