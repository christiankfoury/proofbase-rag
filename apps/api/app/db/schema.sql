create extension if not exists "uuid-ossp";
create extension if not exists vector;

create table if not exists documents (
  id uuid primary key default uuid_generate_v4(),
  external_document_id text not null unique,
  title text not null,
  department text not null,
  category text not null,
  source_type text not null default 'markdown',
  source_path text not null,
  access_roles text[] not null,
  restricted boolean not null default false,
  status text not null default 'active',
  current_version_id uuid,
  created_at timestamptz not null default now(),
  updated_at timestamptz not null default now(),
  archived_at timestamptz
);

create index if not exists idx_documents_category on documents(category);
create index if not exists idx_documents_status on documents(status);
create index if not exists idx_documents_access_roles on documents using gin(access_roles);

create table if not exists document_versions (
  id uuid primary key default uuid_generate_v4(),
  document_id uuid not null references documents(id) on delete cascade,
  version_label text not null,
  effective_date date,
  owner text,
  review_cycle text,
  content_hash text not null,
  extracted_text text not null,
  metadata_json jsonb not null default '{}'::jsonb,
  ingestion_status text not null default 'indexed',
  indexed_at timestamptz,
  failed_at timestamptz,
  failure_reason text,
  created_at timestamptz not null default now(),
  unique (document_id, version_label)
);

create index if not exists idx_document_versions_status on document_versions(ingestion_status);
create index if not exists idx_document_versions_hash on document_versions(content_hash);

alter table documents
  drop constraint if exists documents_current_version_fk;

alter table documents
  add constraint documents_current_version_fk
  foreign key (current_version_id) references document_versions(id);

create table if not exists chunks (
  id uuid primary key default uuid_generate_v4(),
  document_id uuid not null references documents(id) on delete cascade,
  document_version_id uuid not null references document_versions(id) on delete cascade,
  chunk_index integer not null,
  section_heading text not null,
  content text not null,
  content_hash text not null,
  token_count integer,
  chunking_strategy text not null default 'section_based',
  metadata_json jsonb not null default '{}'::jsonb,
  tsv tsvector generated always as (to_tsvector('english', content)) stored,
  created_at timestamptz not null default now(),
  unique (document_version_id, chunk_index)
);

create index if not exists idx_chunks_document on chunks(document_id);
create index if not exists idx_chunks_version_index on chunks(document_version_id, chunk_index);
create index if not exists idx_chunks_tsv on chunks using gin(tsv);

create table if not exists chunk_embeddings (
  id uuid primary key default uuid_generate_v4(),
  chunk_id uuid not null references chunks(id) on delete cascade,
  embedding_model text not null,
  embedding vector(1536) not null,
  created_at timestamptz not null default now(),
  unique (chunk_id, embedding_model)
);

create index if not exists idx_chunk_embeddings_vector
  on chunk_embeddings using hnsw (embedding vector_cosine_ops);

create table if not exists prompts (
  id uuid primary key default uuid_generate_v4(),
  name text not null unique,
  prompt_type text not null,
  description text,
  created_at timestamptz not null default now()
);

create table if not exists prompt_versions (
  id uuid primary key default uuid_generate_v4(),
  prompt_id uuid not null references prompts(id) on delete cascade,
  version text not null,
  content text not null,
  model text not null,
  temperature numeric(3,2) not null default 0.2,
  is_active boolean not null default false,
  change_notes text,
  created_at timestamptz not null default now(),
  unique (prompt_id, version)
);

create index if not exists idx_prompt_versions_active on prompt_versions(prompt_id, is_active);

create table if not exists evaluation_questions (
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

create index if not exists idx_evaluation_questions_type on evaluation_questions(question_type);

create table if not exists evaluation_runs (
  id uuid primary key default uuid_generate_v4(),
  run_name text not null,
  config_json jsonb not null,
  retrieval_mode text not null,
  chunking_strategy text not null,
  top_k integer not null,
  model text not null,
  started_at timestamptz not null default now(),
  completed_at timestamptz,
  status text not null default 'running'
);

create table if not exists evaluation_results (
  id uuid primary key default uuid_generate_v4(),
  evaluation_run_id uuid not null references evaluation_runs(id) on delete cascade,
  question_id text not null,
  question_type text not null,
  user_role text not null,
  expected_behavior text not null,
  generated_behavior text,
  expected_source_documents text[] not null default '{}',
  retrieved_source_documents text[] not null default '{}',
  generated_answer text,
  retrieval_hit_score numeric(4,3),
  mrr numeric(4,3),
  citation_source_match numeric(4,3),
  behavior_match numeric(4,3),
  answer_accuracy text not null default 'pending',
  faithfulness text not null default 'pending',
  hallucination_rate text not null default 'pending',
  latency_ms integer,
  notes text
);

create index if not exists idx_evaluation_results_run on evaluation_results(evaluation_run_id);
create index if not exists idx_evaluation_results_question_id on evaluation_results(question_id);

insert into prompts (name, prompt_type, description)
values ('enterprise_answer', 'answer_generation', 'Baseline grounded answer prompt with citations and refusal behavior.')
on conflict (name) do nothing;

insert into prompt_versions (prompt_id, version, content, model, temperature, is_active, change_notes)
select
  p.id,
  'answer_v1',
  'Answer only from the provided context. If the context does not support the answer, say the information was not found in the available documents. Include concise citations using document ID, title, and section.',
  'gpt-4.1-mini',
  0.2,
  true,
  'Initial Phase 5 baseline prompt.'
from prompts p
where p.name = 'enterprise_answer'
on conflict (prompt_id, version) do nothing;
