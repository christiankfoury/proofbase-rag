create extension if not exists "uuid-ossp";
create extension if not exists vector;

create table if not exists projects (
  id uuid primary key default uuid_generate_v4(),
  name text not null,
  description text not null default '',
  status text not null default 'active' check (status in ('active', 'paused', 'archived')),
  default_retrieval_profile text not null default 'vector-section',
  seeded_data_key text unique,
  quality_status text not null default 'project_evaluation_pending',
  quality_summary jsonb not null default '{}'::jsonb,
  created_at timestamptz not null default now(),
  updated_at timestamptz not null default now(),
  archived_at timestamptz
);

create index if not exists idx_projects_status on projects(status);
create index if not exists idx_projects_updated_at on projects(updated_at);

insert into projects (
  id, name, description, status, default_retrieval_profile,
  seeded_data_key, quality_status, quality_summary
)
values (
  '00000000-0000-0000-0000-000000000019',
  'Northstar Analytics',
  'Seeded workspace backed by the synthetic HR, IT/security, sales, manager, HR admin, and IT admin corpus.',
  'active',
  'vector-section',
  'northstar_synthetic',
  'global_baseline_measured',
  '{
    "label": "Global benchmark measured",
    "detail": "Uses existing global evaluation outputs. Project-scoped evaluation is planned for a later phase.",
    "permission_leakage_rate": 0.0,
    "known_open_issue": "MULTI-005 remains a documented source coverage miss."
  }'::jsonb
)
on conflict (seeded_data_key) do update set
  name = excluded.name,
  description = excluded.description,
  status = excluded.status,
  default_retrieval_profile = excluded.default_retrieval_profile,
  quality_status = excluded.quality_status,
  quality_summary = excluded.quality_summary,
  archived_at = null,
  updated_at = now();

create table if not exists project_departments (
  id uuid primary key default uuid_generate_v4(),
  project_id uuid not null references projects(id) on delete cascade,
  name text not null,
  icon text not null default 'building',
  color text not null default 'steel',
  description text not null default '',
  default_access_roles text[] not null default '{}',
  seeded_data_key text,
  status text not null default 'active' check (status in ('active', 'archived')),
  created_at timestamptz not null default now(),
  updated_at timestamptz not null default now(),
  archived_at timestamptz,
  unique (project_id, name),
  unique (project_id, seeded_data_key)
);

create index if not exists idx_project_departments_project on project_departments(project_id);
create index if not exists idx_project_departments_status on project_departments(status);

insert into project_departments (
  id, project_id, name, icon, color, description, default_access_roles, seeded_data_key
)
values
  (
    '00000000-0000-0000-0000-000000002001',
    '00000000-0000-0000-0000-000000000019',
    'People Operations',
    'people',
    'moss',
    'Employee-facing HR policies, benefits, PTO, and workplace guidance.',
    array['Employee', 'Manager', 'HR Admin'],
    'HR Public'
  ),
  (
    '00000000-0000-0000-0000-000000002002',
    '00000000-0000-0000-0000-000000000019',
    'HR Admin',
    'lock',
    'rust',
    'Restricted HR operations guidance for HR administrators.',
    array['HR Admin'],
    'HR Admin'
  ),
  (
    '00000000-0000-0000-0000-000000002003',
    '00000000-0000-0000-0000-000000000019',
    'IT and Security',
    'shield',
    'steel',
    'Employee-facing security, device, acceptable-use, and data-handling policies.',
    array['Employee', 'Manager', 'IT Admin'],
    'IT Public'
  ),
  (
    '00000000-0000-0000-0000-000000002004',
    '00000000-0000-0000-0000-000000000019',
    'IT Admin',
    'key',
    'rust',
    'Restricted privileged-access and incident-response guidance for IT administrators.',
    array['IT Admin'],
    'IT Admin'
  ),
  (
    '00000000-0000-0000-0000-000000002005',
    '00000000-0000-0000-0000-000000000019',
    'Sales',
    'chart',
    'moss',
    'Sales playbooks, product positioning, FAQs, and competitive guidance.',
    array['Sales Representative', 'Manager'],
    'Sales Enablement'
  ),
  (
    '00000000-0000-0000-0000-000000002006',
    '00000000-0000-0000-0000-000000000019',
    'Management',
    'briefcase',
    'steel',
    'Manager-only coaching, review, and promotion calibration guidance.',
    array['Manager', 'HR Admin'],
    'Manager Only'
  )
on conflict (project_id, seeded_data_key) do update set
  name = excluded.name,
  icon = excluded.icon,
  color = excluded.color,
  description = excluded.description,
  default_access_roles = excluded.default_access_roles,
  status = 'active',
  archived_at = null,
  updated_at = now();

create table if not exists documents (
  id uuid primary key default uuid_generate_v4(),
  project_id uuid references projects(id),
  department_id uuid references project_departments(id),
  external_document_id text not null unique,
  title text not null,
  department text not null,
  category text not null,
  source_type text not null default 'markdown',
  source_path text not null,
  access_roles text[] not null,
  sensitivity text not null default 'internal',
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

alter table documents
  add column if not exists sensitivity text not null default 'internal',
  add column if not exists project_id uuid references projects(id),
  add column if not exists department_id uuid references project_departments(id);

update documents
set project_id = '00000000-0000-0000-0000-000000000019'
where project_id is null
  and external_document_id ~ '^(HR|IT|SALES|MGR|HR-ADMIN|IT-ADMIN)-';

update documents d
set department_id = pd.id
from project_departments pd
where d.project_id = pd.project_id
  and d.category = pd.seeded_data_key
  and d.department_id is null;

create index if not exists idx_documents_project on documents(project_id);
create index if not exists idx_documents_department on documents(department_id);

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

create table if not exists ingestion_jobs (
  id uuid primary key default uuid_generate_v4(),
  project_id uuid references projects(id),
  department_id uuid references project_departments(id),
  document_id uuid references documents(id) on delete set null,
  document_version_id uuid references document_versions(id) on delete set null,
  source_file_name text not null,
  source_file_type text not null,
  status text not null default 'uploaded' check (
    status in ('uploaded', 'extracting', 'normalizing', 'pending_review', 'chunking', 'embedding', 'indexed', 'failed', 'skipped')
  ),
  stage text not null default 'uploaded',
  status_detail text not null default '',
  content_hash text,
  started_at timestamptz,
  completed_at timestamptz,
  failed_at timestamptz,
  error_message text,
  metadata_json jsonb not null default '{}'::jsonb,
  created_at timestamptz not null default now(),
  updated_at timestamptz not null default now(),
  unique (document_version_id)
);

create index if not exists idx_ingestion_jobs_project on ingestion_jobs(project_id);
create index if not exists idx_ingestion_jobs_department on ingestion_jobs(department_id);
create index if not exists idx_ingestion_jobs_status on ingestion_jobs(status);
create index if not exists idx_ingestion_jobs_created_at on ingestion_jobs(created_at);

alter table ingestion_jobs
  drop constraint if exists ingestion_jobs_status_check;

alter table ingestion_jobs
  add constraint ingestion_jobs_status_check
  check (status in ('uploaded', 'extracting', 'normalizing', 'pending_review', 'chunking', 'embedding', 'indexed', 'failed', 'skipped'));

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
  constraint chunks_version_strategy_index_key unique (document_version_id, chunking_strategy, chunk_index)
);

create index if not exists idx_chunks_document on chunks(document_id);
create index if not exists idx_chunks_version_index on chunks(document_version_id, chunk_index);
create index if not exists idx_chunks_strategy on chunks(chunking_strategy);
create index if not exists idx_chunks_tsv on chunks using gin(tsv);

alter table chunks
  drop constraint if exists chunks_document_version_id_chunk_index_key;

alter table chunks
  drop constraint if exists chunks_version_strategy_index_key;

alter table chunks
  add constraint chunks_version_strategy_index_key
  unique (document_version_id, chunking_strategy, chunk_index);

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
  retrieved_chunks_json jsonb not null default '[]'::jsonb,
  generated_answer text,
  retrieval_hit_score numeric(4,3),
  all_sources_hit_score numeric(4,3),
  expected_source_recall numeric(4,3),
  precision_at_k numeric(4,3),
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

alter table evaluation_results
  add column if not exists retrieved_chunks_json jsonb not null default '[]'::jsonb,
  add column if not exists all_sources_hit_score numeric(4,3),
  add column if not exists expected_source_recall numeric(4,3),
  add column if not exists precision_at_k numeric(4,3);

create table if not exists audit_logs (
  id uuid primary key default uuid_generate_v4(),
  user_id text,
  user_role text not null,
  action text not null,
  document_id text,
  resource_type text not null,
  outcome text not null,
  reason text,
  metadata_json jsonb not null default '{}'::jsonb,
  created_at timestamptz not null default now()
);

create index if not exists idx_audit_logs_user_role on audit_logs(user_role);
create index if not exists idx_audit_logs_action on audit_logs(action);
create index if not exists idx_audit_logs_document_id on audit_logs(document_id);
create index if not exists idx_audit_logs_created_at on audit_logs(created_at);

create table if not exists chat_sessions (
  id uuid primary key default uuid_generate_v4(),
  user_id text,
  user_role text not null,
  created_at timestamptz not null default now(),
  updated_at timestamptz not null default now()
);

create index if not exists idx_chat_sessions_user_role on chat_sessions(user_role);
create index if not exists idx_chat_sessions_updated_at on chat_sessions(updated_at);

create table if not exists chat_messages (
  id uuid primary key default uuid_generate_v4(),
  session_id uuid not null references chat_sessions(id) on delete cascade,
  role text not null,
  content text not null,
  response_type text,
  citations_json jsonb not null default '[]'::jsonb,
  confidence_json jsonb not null default '{}'::jsonb,
  metadata_json jsonb not null default '{}'::jsonb,
  created_at timestamptz not null default now()
);

create index if not exists idx_chat_messages_session_created on chat_messages(session_id, created_at);

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

create table if not exists feedback (
  id uuid primary key default uuid_generate_v4(),
  session_id uuid references chat_sessions(id) on delete set null,
  message_id uuid references chat_messages(id) on delete set null,
  question text not null,
  answer text not null,
  response_type text,
  citations_json jsonb not null default '[]'::jsonb,
  user_role text not null,
  rating text not null check (rating in ('thumbs_up', 'thumbs_down')),
  user_comment text,
  feedback_category text not null default 'other',
  created_at timestamptz not null default now()
);

create index if not exists idx_feedback_rating on feedback(rating);
create index if not exists idx_feedback_category on feedback(feedback_category);
create index if not exists idx_feedback_created_at on feedback(created_at);
