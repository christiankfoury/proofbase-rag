# API Design

## Principles

- FastAPI backend.
- Authenticated routes by default.
- Backend enforces authorization; frontend checks are not sufficient.
- Request and response bodies are implementation-oriented but not code.

## Documents

| Method | Path | Purpose | Required Role |
|---|---|---|---|
| POST | `/documents/upload` | Upload a document and start ingestion | HR Admin or IT Admin |
| GET | `/documents` | List documents visible to current user | Authenticated |
| GET | `/documents/{document_id}` | Get document metadata and versions | User must have access |
| PATCH | `/documents/{document_id}` | Update document metadata | HR Admin or IT Admin |
| POST | `/documents/{document_id}/archive` | Archive a document | HR Admin or IT Admin |

Upload request:

```json
{
  "file": "multipart-file",
  "metadata": {
    "department": "People Operations",
    "category": "HR Public",
    "access_roles": ["Employee", "Manager"]
  }
}
```

Document response:

```json
{
  "id": "uuid",
  "external_document_id": "HR-002",
  "title": "PTO and Leave Policy",
  "status": "indexed",
  "current_version": "1.0",
  "permissions": ["Employee", "Sales Representative", "Manager", "HR Admin", "IT Admin"]
}
```

## Chat

| Method | Path | Purpose | Required Role |
|---|---|---|---|
| POST | `/chat/sessions` | Create a chat session | Authenticated |
| POST | `/chat/sessions/{session_id}/messages` | Ask a question | Authenticated |
| GET | `/chat/sessions/{session_id}/messages` | Get chat history | Session owner or admin |

Ask request:

```json
{
  "message": "How many vacation days do I get?",
  "retrieval_mode": "vector_only",
  "top_k": 5
}
```

Ask response:

```json
{
  "answer_run_id": "uuid",
  "answer": "Full-time employees receive 20 paid vacation days per calendar year.",
  "behavior": "answer",
  "citations": [
    {
      "document_id": "HR-002",
      "document_title": "PTO and Leave Policy",
      "section_heading": "Vacation Entitlement",
      "chunk_id": "uuid",
      "confidence_score": 0.0
    }
  ],
  "metrics": {
    "latency_ms": 0,
    "input_tokens": 0,
    "output_tokens": 0,
    "estimated_cost_usd": 0.0
  }
}
```

Use zero placeholders until implementation records real values.

## Evaluation

| Method | Path | Purpose | Required Role |
|---|---|---|---|
| POST | `/evaluation/questions/import` | Import benchmark questions | Admin |
| POST | `/evaluation/runs` | Start evaluation run | Admin |
| GET | `/evaluation/runs` | List evaluation runs | Admin or demo viewer |
| GET | `/evaluation/runs/{run_id}` | Get run details | Admin or demo viewer |
| GET | `/evaluation/runs/compare` | Compare evaluation runs | Admin or demo viewer |

Start run request:

```json
{
  "run_name": "baseline-vector-only",
  "retrieval_mode": "vector_only",
  "chunking_strategy": "section_based",
  "top_k": 5,
  "prompt_version": "answer_v1",
  "model": "gpt-4.1-mini"
}
```

## Admin

| Method | Path | Purpose | Required Role |
|---|---|---|---|
| GET | `/admin/users` | List users | Admin |
| POST | `/admin/users/{user_id}/roles` | Assign roles | Admin |
| PATCH | `/admin/documents/{document_id}/permissions` | Manage document permissions | Admin |
| GET | `/admin/audit-logs` | View audit logs | Admin |

## Feedback

| Method | Path | Purpose | Required Role |
|---|---|---|---|
| POST | `/feedback` | Submit feedback on an answer | Authenticated |
| GET | `/feedback` | List feedback | Admin or demo viewer |

Feedback request:

```json
{
  "answer_run_id": "uuid",
  "rating": 4,
  "label": "helpful",
  "comment": "Answer was correct and citation was useful."
}
```

## Frontend Pages

| Page | Purpose | Main Components | API Data | Demonstrated Value |
|---|---|---|---|---|
| Project overview | Explain architecture and measured improvement | Architecture cards, version timeline, metrics summary | Evaluation summaries | Shows production framing |
| Chat | Ask role-aware questions | Chat panel, role badge, citations, feedback | Chat endpoints | Shows permission-aware RAG |
| Document upload/admin | Upload and monitor ingestion | Upload form, status table, permission editor | Document endpoints | Shows enterprise ingestion |
| Document detail | Inspect metadata, versions, chunks | Metadata panel, chunk list, permissions | Document detail | Shows normalized storage |
| Evaluation dashboard | Compare benchmark runs | Metric cards, run table, charts | Evaluation endpoints | Shows measurable improvement |
| Evaluation run detail | Inspect per-question failures | Question table, retrieved chunks, answer/citation view | Run detail | Shows engineering rigor |
| Failed questions | Debug weak cases | Filters by failure type | Evaluation results | Shows iteration workflow |
| Prompt versions | Manage prompt history | Prompt list, active version, change notes | Prompt endpoints later | Shows prompt experiment tracking |
| Access control | Manage roles and document access | User table, role editor, permission matrix | Admin endpoints | Shows RBAC design |
| Audit logs | Review sensitive actions | Log table, filters | Audit endpoint | Shows security posture |
