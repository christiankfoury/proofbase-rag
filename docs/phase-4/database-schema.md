# Database Schema Design

## Overview

Use PostgreSQL with pgvector. Use UUID primary keys for application tables. Natural IDs from the synthetic corpus, such as `HR-002`, are stored as external identifiers.

Required extensions:

```sql
create extension if not exists "uuid-ossp";
create extension if not exists vector;
```

These SQL examples are design references only. Do not create migration files in Phase 4.

## Users

Purpose: app users mapped from Clerk or Auth.js.

```sql
create table users (
  id uuid primary key default uuid_generate_v4(),
  external_auth_id text not null unique,
  email text not null unique,
  display_name text,
  is_active boolean not null default true,
  last_login_at timestamptz,
  created_at timestamptz not null default now(),
  updated_at timestamptz not null default now()
);
```

Indexes:

- unique `external_auth_id`
- unique `email`

## Roles

Purpose: canonical role list.

```sql
create table roles (
  id uuid primary key default uuid_generate_v4(),
  name text not null unique,
  description text,
  created_at timestamptz not null default now()
);
```

Seed roles:

- Employee
- Sales Representative
- Manager
- HR Admin
- IT Admin

## User Roles

Purpose: many-to-many role assignment.

```sql
create table user_roles (
  user_id uuid not null references users(id) on delete cascade,
  role_id uuid not null references roles(id) on delete cascade,
  assigned_by uuid references users(id),
  assigned_at timestamptz not null default now(),
  primary key (user_id, role_id)
);
```

## Documents

Purpose: stable logical document independent of versions.

```sql
create table documents (
  id uuid primary key default uuid_generate_v4(),
  external_document_id text not null unique,
  title text not null,
  department text not null,
  category text not null,
  source_type text not null,
  current_version_id uuid,
  status text not null default 'active',
  created_by uuid references users(id),
  created_at timestamptz not null default now(),
  updated_at timestamptz not null default now(),
  archived_at timestamptz
);

create index idx_documents_category on documents(category);
create index idx_documents_status on documents(status);
```

Notes:

- `external_document_id` stores values like `HR-002`.
- `current_version_id` should point to `document_versions.id` after both tables exist.

## Document Versions

Purpose: versioned source file, extracted text, metadata, and ingestion status.

```sql
create table document_versions (
  id uuid primary key default uuid_generate_v4(),
  document_id uuid not null references documents(id) on delete cascade,
  version_label text not null,
  effective_date date,
  owner text,
  review_cycle text,
  blob_uri text,
  content_hash text not null,
  extracted_text text,
  metadata_json jsonb not null default '{}'::jsonb,
  ingestion_status text not null default 'uploaded',
  indexed_at timestamptz,
  failed_at timestamptz,
  failure_reason text,
  created_at timestamptz not null default now(),
  unique (document_id, version_label)
);

create index idx_document_versions_status on document_versions(ingestion_status);
create index idx_document_versions_hash on document_versions(content_hash);
```

Ingestion statuses:

- `uploaded`
- `extracting`
- `chunking`
- `embedding`
- `indexed`
- `failed`
- `archived`

## Document Permissions

Purpose: document-level role access.

```sql
create table document_permissions (
  document_id uuid not null references documents(id) on delete cascade,
  role_id uuid not null references roles(id) on delete cascade,
  permission text not null default 'read',
  created_at timestamptz not null default now(),
  primary key (document_id, role_id)
);

create index idx_document_permissions_role on document_permissions(role_id);
```

Notes:

- Phase 5 supports `read` only.
- Chunks inherit document permissions.

## Chunks

Purpose: normalized retrievable text units with full-text search support.

```sql
create table chunks (
  id uuid primary key default uuid_generate_v4(),
  document_id uuid not null references documents(id) on delete cascade,
  document_version_id uuid not null references document_versions(id) on delete cascade,
  chunk_index integer not null,
  section_heading text,
  content text not null,
  content_hash text not null,
  token_count integer,
  chunking_strategy text not null,
  metadata_json jsonb not null default '{}'::jsonb,
  tsv tsvector generated always as (to_tsvector('english', content)) stored,
  created_at timestamptz not null default now(),
  unique (document_version_id, chunk_index)
);

create index idx_chunks_document on chunks(document_id);
create index idx_chunks_version_index on chunks(document_version_id, chunk_index);
create index idx_chunks_tsv on chunks using gin(tsv);
```

## Chunk Embeddings

Purpose: vector representation for pgvector similarity search.

```sql
create table chunk_embeddings (
  id uuid primary key default uuid_generate_v4(),
  chunk_id uuid not null references chunks(id) on delete cascade,
  embedding_model text not null,
  embedding vector(1536) not null,
  created_at timestamptz not null default now(),
  unique (chunk_id, embedding_model)
);

create index idx_chunk_embeddings_vector
  on chunk_embeddings using hnsw (embedding vector_cosine_ops);
```

Notes:

- `vector(1536)` assumes the first embedding model uses 1536 dimensions.
- If the model changes dimension, use a new table or dimension-compatible migration.

## Chat Sessions

Purpose: user conversations.

```sql
create table chat_sessions (
  id uuid primary key default uuid_generate_v4(),
  user_id uuid not null references users(id),
  title text,
  created_at timestamptz not null default now(),
  updated_at timestamptz not null default now(),
  archived_at timestamptz
);
```

## Chat Messages

Purpose: chat turns.

```sql
create table chat_messages (
  id uuid primary key default uuid_generate_v4(),
  session_id uuid not null references chat_sessions(id) on delete cascade,
  role text not null,
  content text not null,
  metadata_json jsonb not null default '{}'::jsonb,
  created_at timestamptz not null default now()
);

create index idx_chat_messages_session_created on chat_messages(session_id, created_at);
```

## Prompts

Purpose: prompt families.

```sql
create table prompts (
  id uuid primary key default uuid_generate_v4(),
  name text not null unique,
  prompt_type text not null,
  description text,
  created_at timestamptz not null default now()
);
```

Prompt types:

- `answer_generation`
- `query_rewriting`
- `citation_validation`
- `evaluation_judge`
- `refusal_policy`

## Prompt Versions

Purpose: versioned prompt content and model settings.

```sql
create table prompt_versions (
  id uuid primary key default uuid_generate_v4(),
  prompt_id uuid not null references prompts(id) on delete cascade,
  version text not null,
  content text not null,
  model text not null,
  temperature numeric(3,2) not null default 0.2,
  is_active boolean not null default false,
  change_notes text,
  created_by uuid references users(id),
  created_at timestamptz not null default now(),
  unique (prompt_id, version)
);

create index idx_prompt_versions_active on prompt_versions(prompt_id, is_active);
```

## Retrieval Runs

Purpose: every retrieval attempt.

```sql
create table retrieval_runs (
  id uuid primary key default uuid_generate_v4(),
  session_id uuid references chat_sessions(id),
  message_id uuid references chat_messages(id),
  user_id uuid references users(id),
  retrieval_mode text not null,
  query text not null,
  rewritten_query text,
  top_k integer not null,
  filters_json jsonb not null default '{}'::jsonb,
  latency_ms integer,
  created_at timestamptz not null default now()
);
```

Retrieval modes:

- `vector_only`
- `keyword_only`
- `hybrid`
- `hybrid_rerank`

## Retrieved Chunks

Purpose: ranked chunks returned by retrieval.

```sql
create table retrieved_chunks (
  id uuid primary key default uuid_generate_v4(),
  retrieval_run_id uuid not null references retrieval_runs(id) on delete cascade,
  chunk_id uuid not null references chunks(id),
  rank integer not null,
  vector_score numeric,
  keyword_score numeric,
  hybrid_score numeric,
  rerank_score numeric,
  was_allowed boolean not null default true
);

create index idx_retrieved_chunks_run_rank on retrieved_chunks(retrieval_run_id, rank);
```

## Answer Runs

Purpose: answer generation attempts.

```sql
create table answer_runs (
  id uuid primary key default uuid_generate_v4(),
  session_id uuid references chat_sessions(id),
  message_id uuid references chat_messages(id),
  retrieval_run_id uuid references retrieval_runs(id),
  prompt_version_id uuid references prompt_versions(id),
  model text not null,
  answer_text text not null,
  expected_behavior text,
  refusal_reason text,
  latency_ms integer,
  input_tokens integer,
  output_tokens integer,
  estimated_cost_usd numeric(12,6),
  created_at timestamptz not null default now()
);
```

## Citations

Purpose: answer-to-source links.

```sql
create table citations (
  id uuid primary key default uuid_generate_v4(),
  answer_run_id uuid not null references answer_runs(id) on delete cascade,
  chunk_id uuid references chunks(id),
  document_id uuid references documents(id),
  document_version_id uuid references document_versions(id),
  section_heading text,
  quote text,
  confidence_score numeric(4,3),
  validation_status text not null default 'pending',
  created_at timestamptz not null default now()
);

create index idx_citations_answer on citations(answer_run_id);
create index idx_citations_chunk on citations(chunk_id);
create index idx_citations_document on citations(document_id);
```

## Evaluation Questions

Purpose: imported benchmark questions.

```sql
create table evaluation_questions (
  id uuid primary key default uuid_generate_v4(),
  question_id text not null,
  question_type text not null,
  difficulty text not null,
  user_role text not null,
  question text not null,
  previous_turns_json jsonb not null default '[]'::jsonb,
  expected_behavior text not null,
  expected_answer text not null,
  expected_sources_json jsonb not null default '[]'::jsonb,
  allowed_documents_json jsonb not null default '[]'::jsonb,
  evaluation_notes text,
  benchmark_version text not null,
  unique (benchmark_version, question_id)
);

create index idx_evaluation_questions_type on evaluation_questions(question_type);
```

## Evaluation Runs

Purpose: benchmark run metadata.

```sql
create table evaluation_runs (
  id uuid primary key default uuid_generate_v4(),
  run_name text not null,
  config_json jsonb not null,
  retrieval_mode text not null,
  chunking_strategy text not null,
  top_k integer not null,
  prompt_version_id uuid references prompt_versions(id),
  model text not null,
  started_by uuid references users(id),
  started_at timestamptz not null default now(),
  completed_at timestamptz,
  status text not null default 'running'
);
```

## Evaluation Results

Purpose: per-question benchmark results.

```sql
create table evaluation_results (
  id uuid primary key default uuid_generate_v4(),
  evaluation_run_id uuid not null references evaluation_runs(id) on delete cascade,
  evaluation_question_id uuid not null references evaluation_questions(id),
  retrieval_run_id uuid references retrieval_runs(id),
  answer_run_id uuid references answer_runs(id),
  retrieval_hit_score numeric(4,3),
  precision_at_k numeric(4,3),
  recall_at_k numeric(4,3),
  mrr numeric(4,3),
  answer_accuracy numeric(4,3),
  citation_accuracy numeric(4,3),
  faithfulness numeric(4,3),
  hallucination_score numeric(4,3),
  refusal_accuracy numeric(4,3),
  permission_leakage numeric(4,3),
  latency_ms integer,
  token_usage integer,
  estimated_cost_usd numeric(12,6),
  notes text
);

create index idx_evaluation_results_run on evaluation_results(evaluation_run_id);
create index idx_evaluation_results_question on evaluation_results(evaluation_question_id);
```

## Feedback

Purpose: user feedback on answers.

```sql
create table feedback (
  id uuid primary key default uuid_generate_v4(),
  answer_run_id uuid not null references answer_runs(id) on delete cascade,
  user_id uuid references users(id),
  rating integer,
  label text,
  comment text,
  created_at timestamptz not null default now()
);
```

## Audit Logs

Purpose: sensitive action logs.

```sql
create table audit_logs (
  id uuid primary key default uuid_generate_v4(),
  actor_user_id uuid references users(id),
  action text not null,
  resource_type text not null,
  resource_id text,
  metadata_json jsonb not null default '{}'::jsonb,
  request_id text,
  created_at timestamptz not null default now()
);

create index idx_audit_logs_actor on audit_logs(actor_user_id);
create index idx_audit_logs_action on audit_logs(action);
create index idx_audit_logs_resource on audit_logs(resource_type, resource_id);
create index idx_audit_logs_created on audit_logs(created_at);
```

Audit examples:

- `document_uploaded`
- `document_archived`
- `document_permissions_updated`
- `user_role_assigned`
- `restricted_query_refused`
- `evaluation_run_started`
