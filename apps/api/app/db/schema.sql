create extension if not exists "uuid-ossp";
create extension if not exists vector;

create table if not exists tenants (
  id uuid primary key default uuid_generate_v4(),
  name text not null,
  slug text not null unique,
  status text not null default 'active' check (status in ('active', 'suspended', 'archived')),
  data_classification text not null default 'internal',
  retention_policy_key text not null default 'tenant_configured',
  is_demo boolean not null default false,
  created_at timestamptz not null default now(),
  updated_at timestamptz not null default now()
);

insert into tenants (id, name, slug, status, is_demo)
values ('00000000-0000-0000-0000-000000002801', 'Northstar Analytics Demo', 'northstar-demo', 'active', true)
on conflict (id) do update set
  name = excluded.name,
  slug = excluded.slug,
  status = excluded.status,
  is_demo = excluded.is_demo,
  updated_at = now();

create table if not exists demo_users (
  id uuid primary key default uuid_generate_v4(),
  display_name text not null,
  email text not null unique,
  business_role text not null,
  is_admin boolean not null default false,
  status text not null default 'active' check (status in ('active', 'disabled')),
  created_at timestamptz not null default now(),
  updated_at timestamptz not null default now()
);

create index if not exists idx_demo_users_status on demo_users(status);
create index if not exists idx_demo_users_role on demo_users(business_role);

insert into demo_users (id, display_name, email, business_role, is_admin)
values
  ('00000000-0000-0000-0000-000000002701', 'Emma Employee', 'employee@northstar.example', 'Employee', false),
  ('00000000-0000-0000-0000-000000002702', 'Sam Sales', 'sales@northstar.example', 'Sales Representative', false),
  ('00000000-0000-0000-0000-000000002703', 'Mina Manager', 'manager@northstar.example', 'Manager', false),
  ('00000000-0000-0000-0000-000000002704', 'Harper HR Admin', 'hr-admin@northstar.example', 'HR Admin', false),
  ('00000000-0000-0000-0000-000000002705', 'Ira IT Admin', 'it-admin@northstar.example', 'IT Admin', false),
  ('00000000-0000-0000-0000-000000002706', 'Kai Admin', 'admin@northstar.example', 'Admin', true),
  ('00000000-0000-0000-0000-000000002707', 'Gus Guest', 'guest@external.example', 'Employee', false)
on conflict (id) do update set
  display_name = excluded.display_name,
  email = excluded.email,
  business_role = excluded.business_role,
  is_admin = excluded.is_admin,
  status = 'active',
  updated_at = now();

create table if not exists tenant_memberships (
  id uuid primary key default uuid_generate_v4(),
  tenant_id uuid not null references tenants(id) on delete cascade,
  user_id uuid not null references demo_users(id) on delete cascade,
  tenant_role text not null default 'member' check (tenant_role in ('member', 'admin', 'owner')),
  status text not null default 'active' check (status in ('invited', 'active', 'disabled', 'removed')),
  provisioned_by text not null default 'administrator',
  disabled_at timestamptz,
  created_at timestamptz not null default now(),
  updated_at timestamptz not null default now(),
  unique (tenant_id, user_id)
);

create index if not exists idx_tenant_memberships_user on tenant_memberships(user_id, status);

insert into tenant_memberships (tenant_id, user_id, tenant_role, status, provisioned_by)
select
  '00000000-0000-0000-0000-000000002801'::uuid,
  id,
  case when is_admin then 'owner' else 'member' end,
  'active',
  'seeded_demo'
from demo_users
on conflict (tenant_id, user_id) do update set
  tenant_role = excluded.tenant_role,
  status = excluded.status,
  provisioned_by = excluded.provisioned_by,
  disabled_at = null,
  updated_at = now();

create table if not exists external_identities (
  id uuid primary key default uuid_generate_v4(),
  user_id uuid not null references demo_users(id) on delete cascade,
  issuer text not null,
  subject text not null,
  status text not null default 'active' check (status in ('active', 'revoked')),
  last_authenticated_at timestamptz,
  created_at timestamptz not null default now(),
  updated_at timestamptz not null default now(),
  unique (issuer, subject)
);

insert into external_identities (user_id, issuer, subject, status)
select id, 'https://identity.local.proofbase.invalid', 'northstar:' || id::text, 'active'
from demo_users
on conflict (issuer, subject) do update set
  user_id = excluded.user_id,
  status = excluded.status,
  updated_at = now();

create table if not exists auth_sessions (
  id uuid primary key default uuid_generate_v4(),
  user_id uuid not null references demo_users(id) on delete cascade,
  tenant_id uuid not null references tenants(id) on delete cascade,
  provider_session_id text,
  refresh_token_ciphertext text,
  csrf_token_hash text not null,
  auth_time timestamptz not null,
  last_seen_at timestamptz not null,
  idle_expires_at timestamptz not null,
  absolute_expires_at timestamptz not null,
  mfa_satisfied boolean not null default false,
  status text not null default 'active' check (status in ('active', 'revoked', 'expired')),
  revoked_at timestamptz,
  created_at timestamptz not null default now()
);

create index if not exists idx_auth_sessions_principal on auth_sessions(tenant_id, user_id, status);

create table if not exists oidc_authorization_transactions (
  id uuid primary key default uuid_generate_v4(),
  state_hash text not null unique,
  nonce_hash text not null,
  return_path text not null default '/',
  expires_at timestamptz not null,
  consumed_at timestamptz,
  created_at timestamptz not null default now()
);

create table if not exists revoked_oidc_tokens (
  issuer text not null,
  token_id_hash text not null,
  expires_at timestamptz not null,
  revoked_at timestamptz not null default now(),
  reason_code text not null default 'session_revoked',
  primary key (issuer, token_id_hash)
);

create table if not exists projects (
  id uuid primary key default uuid_generate_v4(),
  tenant_id uuid not null references tenants(id),
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
  id, tenant_id, name, description, status, default_retrieval_profile,
  seeded_data_key, quality_status, quality_summary
)
values (
  '00000000-0000-0000-0000-000000000019',
  '00000000-0000-0000-0000-000000002801',
  'Northstar Analytics',
  'Seeded workspace backed by the synthetic HR, IT/security, sales, manager, finance, legal, engineering, support, operations, HR admin, and IT admin corpus.',
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

create table if not exists project_memberships (
  id uuid primary key default uuid_generate_v4(),
  tenant_id uuid not null references tenants(id),
  project_id uuid not null references projects(id) on delete cascade,
  user_id uuid not null references demo_users(id) on delete cascade,
  membership_level text not null check (membership_level in ('viewer', 'contributor', 'owner')),
  created_at timestamptz not null default now(),
  updated_at timestamptz not null default now(),
  unique (project_id, user_id)
);

create index if not exists idx_project_memberships_project on project_memberships(project_id);
create index if not exists idx_project_memberships_user on project_memberships(user_id);

insert into project_memberships (tenant_id, project_id, user_id, membership_level)
values
  ('00000000-0000-0000-0000-000000002801', '00000000-0000-0000-0000-000000000019', '00000000-0000-0000-0000-000000002701', 'viewer'),
  ('00000000-0000-0000-0000-000000002801', '00000000-0000-0000-0000-000000000019', '00000000-0000-0000-0000-000000002702', 'viewer'),
  ('00000000-0000-0000-0000-000000002801', '00000000-0000-0000-0000-000000000019', '00000000-0000-0000-0000-000000002703', 'viewer'),
  ('00000000-0000-0000-0000-000000002801', '00000000-0000-0000-0000-000000000019', '00000000-0000-0000-0000-000000002704', 'viewer'),
  ('00000000-0000-0000-0000-000000002801', '00000000-0000-0000-0000-000000000019', '00000000-0000-0000-0000-000000002705', 'viewer'),
  ('00000000-0000-0000-0000-000000002801', '00000000-0000-0000-0000-000000000019', '00000000-0000-0000-0000-000000002706', 'owner')
on conflict (project_id, user_id) do update set
  membership_level = excluded.membership_level,
  updated_at = now();

create table if not exists project_departments (
  id uuid primary key default uuid_generate_v4(),
  tenant_id uuid not null references tenants(id),
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
  id, tenant_id, project_id, name, icon, color, description, default_access_roles, seeded_data_key
)
values
  (
    '00000000-0000-0000-0000-000000002001',
    '00000000-0000-0000-0000-000000002801',
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
    '00000000-0000-0000-0000-000000002801',
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
    '00000000-0000-0000-0000-000000002801',
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
    '00000000-0000-0000-0000-000000002801',
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
    '00000000-0000-0000-0000-000000002801',
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
    '00000000-0000-0000-0000-000000002801',
    '00000000-0000-0000-0000-000000000019',
    'Management',
    'briefcase',
    'steel',
    'Manager-only coaching, review, and promotion calibration guidance.',
    array['Manager', 'HR Admin'],
    'Manager Only'
  ),
  (
    '00000000-0000-0000-0000-000000002007',
    '00000000-0000-0000-0000-000000002801',
    '00000000-0000-0000-0000-000000000019',
    'Finance',
    'building',
    'steel',
    'Expense, reimbursement, procurement, and spend-approval guidance.',
    array['Employee', 'Sales Representative', 'Manager', 'HR Admin', 'IT Admin'],
    'Finance'
  ),
  (
    '00000000-0000-0000-0000-000000002008',
    '00000000-0000-0000-0000-000000002801',
    '00000000-0000-0000-0000-000000000019',
    'Legal',
    'lock',
    'rust',
    'Restricted legal operations guidance for contracts, NDAs, retention, and legal holds.',
    array['Sales Representative', 'Manager', 'HR Admin', 'IT Admin'],
    'Legal'
  ),
  (
    '00000000-0000-0000-0000-000000002009',
    '00000000-0000-0000-0000-000000002801',
    '00000000-0000-0000-0000-000000000019',
    'Engineering',
    'key',
    'steel',
    'Restricted engineering operations guidance for deployments, on-call, incidents, and API standards.',
    array['Manager', 'IT Admin'],
    'Engineering'
  ),
  (
    '00000000-0000-0000-0000-000000002010',
    '00000000-0000-0000-0000-000000002801',
    '00000000-0000-0000-0000-000000000019',
    'Support',
    'briefcase',
    'moss',
    'Restricted customer-support escalation, SLA, refund, and handoff guidance.',
    array['Sales Representative', 'Manager'],
    'Support'
  ),
  (
    '00000000-0000-0000-0000-000000002011',
    '00000000-0000-0000-0000-000000002801',
    '00000000-0000-0000-0000-000000000019',
    'Operations',
    'building',
    'stone',
    'Vendor onboarding, travel booking, equipment request, and operations exception guidance.',
    array['Employee', 'Manager', 'HR Admin', 'IT Admin'],
    'Operations'
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

create table if not exists evaluation_reviews (
  id uuid primary key default uuid_generate_v4(),
  source_type text not null check (source_type in ('failed_question', 'feedback')),
  source_id text not null,
  question text not null,
  answer text,
  expected_answer text,
  expected_sources text[] not null default '{}',
  actual_citations_json jsonb not null default '[]'::jsonb,
  retrieved_chunks_json jsonb not null default '[]'::jsonb,
  answer_correctness numeric(3, 2) not null check (answer_correctness in (0, 0.5, 1)),
  citation_correctness numeric(3, 2) not null check (citation_correctness in (0, 0.5, 1)),
  decision text not null check (decision in ('needs_fix', 'evaluation_candidate', 'approved_reference', 'rejected')),
  reviewer_role text not null default 'Evaluator',
  reviewer_id text,
  notes text not null default '',
  created_at timestamptz not null default now()
);

create index if not exists idx_evaluation_reviews_source on evaluation_reviews(source_type, source_id);
create index if not exists idx_evaluation_reviews_decision on evaluation_reviews(decision);
create index if not exists idx_evaluation_reviews_created_at on evaluation_reviews(created_at);

-- Phase 56 tenant ownership backfill. Platform benchmark rows intentionally keep
-- a null tenant_id; tenant-scoped evaluation rows must provide one when created.
alter table projects add column if not exists tenant_id uuid references tenants(id);
update projects set tenant_id = '00000000-0000-0000-0000-000000002801'::uuid where tenant_id is null;
alter table projects alter column tenant_id set not null;
create index if not exists idx_projects_tenant on projects(tenant_id, status);

alter table project_departments add column if not exists tenant_id uuid references tenants(id);
update project_departments pd set tenant_id = p.tenant_id from projects p
where pd.project_id = p.id and pd.tenant_id is null;
alter table project_departments alter column tenant_id set not null;
create index if not exists idx_project_departments_tenant on project_departments(tenant_id, project_id);

alter table project_memberships add column if not exists tenant_id uuid references tenants(id);
update project_memberships pm set tenant_id = p.tenant_id from projects p
where pm.project_id = p.id and pm.tenant_id is null;
alter table project_memberships alter column tenant_id set not null;
create index if not exists idx_project_memberships_tenant on project_memberships(tenant_id, user_id);

alter table documents add column if not exists tenant_id uuid references tenants(id);
update documents d set tenant_id = p.tenant_id from projects p
where d.project_id = p.id and d.tenant_id is null;
alter table documents alter column tenant_id set not null;
create index if not exists idx_documents_tenant on documents(tenant_id, project_id);

alter table document_versions add column if not exists tenant_id uuid references tenants(id);
update document_versions dv set tenant_id = d.tenant_id from documents d
where dv.document_id = d.id and dv.tenant_id is null;
alter table document_versions alter column tenant_id set not null;
create index if not exists idx_document_versions_tenant on document_versions(tenant_id, document_id);

alter table ingestion_jobs add column if not exists tenant_id uuid references tenants(id);
update ingestion_jobs ij set tenant_id = p.tenant_id from projects p
where ij.project_id = p.id and ij.tenant_id is null;
alter table ingestion_jobs alter column tenant_id set not null;
create index if not exists idx_ingestion_jobs_tenant on ingestion_jobs(tenant_id, status);

alter table chunks add column if not exists tenant_id uuid references tenants(id);
update chunks c set tenant_id = d.tenant_id from documents d
where c.document_id = d.id and c.tenant_id is null;
alter table chunks alter column tenant_id set not null;
create index if not exists idx_chunks_tenant on chunks(tenant_id, document_id);

alter table chunk_embeddings add column if not exists tenant_id uuid references tenants(id);
update chunk_embeddings ce set tenant_id = c.tenant_id from chunks c
where ce.chunk_id = c.id and ce.tenant_id is null;
alter table chunk_embeddings alter column tenant_id set not null;
create index if not exists idx_chunk_embeddings_tenant on chunk_embeddings(tenant_id, chunk_id);

alter table chat_sessions add column if not exists tenant_id uuid references tenants(id);
update chat_sessions set tenant_id = '00000000-0000-0000-0000-000000002801'::uuid where tenant_id is null;
alter table chat_sessions alter column tenant_id set not null;
create index if not exists idx_chat_sessions_tenant on chat_sessions(tenant_id, updated_at);

alter table chat_messages add column if not exists tenant_id uuid references tenants(id);
update chat_messages cm set tenant_id = cs.tenant_id from chat_sessions cs
where cm.session_id = cs.id and cm.tenant_id is null;
alter table chat_messages alter column tenant_id set not null;
create index if not exists idx_chat_messages_tenant on chat_messages(tenant_id, session_id);

alter table feedback add column if not exists tenant_id uuid references tenants(id);
update feedback f set tenant_id = cs.tenant_id from chat_sessions cs
where f.session_id = cs.id and f.tenant_id is null;
update feedback set tenant_id = '00000000-0000-0000-0000-000000002801'::uuid where tenant_id is null;
alter table feedback alter column tenant_id set not null;
create index if not exists idx_feedback_tenant on feedback(tenant_id, created_at);

alter table audit_logs add column if not exists tenant_id uuid references tenants(id);
update audit_logs set tenant_id = '00000000-0000-0000-0000-000000002801'::uuid where tenant_id is null;
alter table audit_logs alter column tenant_id set not null;
create index if not exists idx_audit_logs_tenant on audit_logs(tenant_id, created_at);

alter table evaluation_questions add column if not exists tenant_id uuid references tenants(id);
alter table evaluation_runs add column if not exists tenant_id uuid references tenants(id);
alter table evaluation_results add column if not exists tenant_id uuid references tenants(id);
alter table evaluation_reviews add column if not exists tenant_id uuid references tenants(id);
create index if not exists idx_evaluation_runs_tenant on evaluation_runs(tenant_id, started_at);
create index if not exists idx_evaluation_results_tenant on evaluation_results(tenant_id, evaluation_run_id);
create index if not exists idx_evaluation_reviews_tenant on evaluation_reviews(tenant_id, created_at);

-- Phase 57 runtime authorization: migrations stay owned by the schema owner;
-- application transactions assume this non-bypass role.
do $$
begin
  if not exists (select 1 from pg_roles where rolname = 'proofbase_runtime') then
    create role proofbase_runtime nologin nosuperuser nocreatedb nocreaterole noinherit nobypassrls;
  else
    alter role proofbase_runtime nologin nosuperuser nocreatedb nocreaterole noinherit nobypassrls;
  end if;
end
$$;

create unique index if not exists uq_projects_tenant_id_id on projects(tenant_id, id);
create unique index if not exists uq_departments_tenant_id_id on project_departments(tenant_id, id);
create unique index if not exists uq_documents_tenant_id_id on documents(tenant_id, id);
create unique index if not exists uq_document_versions_tenant_id_id on document_versions(tenant_id, id);
create unique index if not exists uq_chunks_tenant_id_id on chunks(tenant_id, id);
create unique index if not exists uq_chat_sessions_tenant_id_id on chat_sessions(tenant_id, id);
create unique index if not exists uq_chat_messages_tenant_id_id on chat_messages(tenant_id, id);
create unique index if not exists uq_evaluation_runs_tenant_id_id on evaluation_runs(tenant_id, id);

do $$
begin
  if not exists (select 1 from pg_constraint where conname = 'departments_tenant_project_fk') then
    alter table project_departments add constraint departments_tenant_project_fk foreign key (tenant_id, project_id) references projects(tenant_id, id);
  end if;
  if not exists (select 1 from pg_constraint where conname = 'memberships_tenant_project_fk') then
    alter table project_memberships add constraint memberships_tenant_project_fk foreign key (tenant_id, project_id) references projects(tenant_id, id);
  end if;
  if not exists (select 1 from pg_constraint where conname = 'documents_tenant_project_fk') then
    alter table documents add constraint documents_tenant_project_fk foreign key (tenant_id, project_id) references projects(tenant_id, id);
  end if;
  if not exists (select 1 from pg_constraint where conname = 'documents_tenant_department_fk') then
    alter table documents add constraint documents_tenant_department_fk foreign key (tenant_id, department_id) references project_departments(tenant_id, id);
  end if;
  if not exists (select 1 from pg_constraint where conname = 'versions_tenant_document_fk') then
    alter table document_versions add constraint versions_tenant_document_fk foreign key (tenant_id, document_id) references documents(tenant_id, id);
  end if;
  if not exists (select 1 from pg_constraint where conname = 'jobs_tenant_project_fk') then
    alter table ingestion_jobs add constraint jobs_tenant_project_fk foreign key (tenant_id, project_id) references projects(tenant_id, id);
  end if;
  if not exists (select 1 from pg_constraint where conname = 'jobs_tenant_department_fk') then
    alter table ingestion_jobs add constraint jobs_tenant_department_fk foreign key (tenant_id, department_id) references project_departments(tenant_id, id);
  end if;
  if not exists (select 1 from pg_constraint where conname = 'jobs_tenant_document_fk') then
    alter table ingestion_jobs add constraint jobs_tenant_document_fk foreign key (tenant_id, document_id) references documents(tenant_id, id);
  end if;
  if not exists (select 1 from pg_constraint where conname = 'jobs_tenant_version_fk') then
    alter table ingestion_jobs add constraint jobs_tenant_version_fk foreign key (tenant_id, document_version_id) references document_versions(tenant_id, id);
  end if;
  if not exists (select 1 from pg_constraint where conname = 'chunks_tenant_document_fk') then
    alter table chunks add constraint chunks_tenant_document_fk foreign key (tenant_id, document_id) references documents(tenant_id, id);
  end if;
  if not exists (select 1 from pg_constraint where conname = 'chunks_tenant_version_fk') then
    alter table chunks add constraint chunks_tenant_version_fk foreign key (tenant_id, document_version_id) references document_versions(tenant_id, id);
  end if;
  if not exists (select 1 from pg_constraint where conname = 'embeddings_tenant_chunk_fk') then
    alter table chunk_embeddings add constraint embeddings_tenant_chunk_fk foreign key (tenant_id, chunk_id) references chunks(tenant_id, id);
  end if;
  if not exists (select 1 from pg_constraint where conname = 'messages_tenant_session_fk') then
    alter table chat_messages add constraint messages_tenant_session_fk foreign key (tenant_id, session_id) references chat_sessions(tenant_id, id);
  end if;
  if not exists (select 1 from pg_constraint where conname = 'feedback_tenant_session_fk') then
    alter table feedback add constraint feedback_tenant_session_fk foreign key (tenant_id, session_id) references chat_sessions(tenant_id, id);
  end if;
  if not exists (select 1 from pg_constraint where conname = 'feedback_tenant_message_fk') then
    alter table feedback add constraint feedback_tenant_message_fk foreign key (tenant_id, message_id) references chat_messages(tenant_id, id);
  end if;
  if not exists (select 1 from pg_constraint where conname = 'results_tenant_run_fk') then
    alter table evaluation_results add constraint results_tenant_run_fk foreign key (tenant_id, evaluation_run_id) references evaluation_runs(tenant_id, id);
  end if;
end
$$;

create or replace function proofbase_current_tenant_id() returns uuid
language sql stable as $$
  select nullif(current_setting('app.tenant_id', true), '')::uuid
$$;

create or replace function proofbase_platform_admin() returns boolean
language sql stable as $$
  select coalesce(nullif(current_setting('app.platform_admin', true), '')::boolean, false)
$$;

-- Phase 59 local secure-file lifecycle. Objects remain quarantined and
-- tenant-scoped; hosted object storage and malware scanning are external gates.
create table if not exists file_objects (
  id uuid primary key default uuid_generate_v4(),
  tenant_id uuid not null references tenants(id),
  project_id uuid not null references projects(id),
  department_id uuid not null references project_departments(id),
  document_id uuid references documents(id) on delete set null,
  document_version_id uuid references document_versions(id) on delete set null,
  storage_key text not null unique,
  original_name_hash text not null,
  declared_mime text not null,
  detected_mime text not null,
  size_bytes bigint not null check (size_bytes >= 0 and size_bytes <= 10485760),
  content_sha256 text not null,
  lifecycle_state text not null check (lifecycle_state in ('quarantined', 'scanning', 'clean', 'rejected', 'deleted')),
  scanner_name text,
  scanner_verdict text,
  page_count integer check (page_count is null or page_count between 1 and 100),
  rejection_reason text,
  data_classification text not null check (data_classification = 'non_sensitive'),
  legal_hold boolean not null default false,
  retention_expires_at timestamptz not null,
  deleted_at timestamptz,
  created_at timestamptz not null default now(),
  updated_at timestamptz not null default now()
);

create unique index if not exists uq_file_objects_tenant_id_id on file_objects(tenant_id, id);
create unique index if not exists uq_file_objects_active_content
  on file_objects(tenant_id, project_id, department_id, content_sha256)
  where lifecycle_state not in ('rejected', 'deleted');
create index if not exists idx_file_objects_retention on file_objects(lifecycle_state, retention_expires_at)
  where legal_hold = false and lifecycle_state <> 'deleted';

alter table ingestion_jobs add column if not exists file_object_id uuid;

do $$
begin
  if not exists (select 1 from pg_constraint where conname = 'file_objects_tenant_project_fk') then
    alter table file_objects add constraint file_objects_tenant_project_fk foreign key (tenant_id, project_id) references projects(tenant_id, id);
  end if;
  if not exists (select 1 from pg_constraint where conname = 'file_objects_tenant_department_fk') then
    alter table file_objects add constraint file_objects_tenant_department_fk foreign key (tenant_id, department_id) references project_departments(tenant_id, id);
  end if;
  if not exists (select 1 from pg_constraint where conname = 'file_objects_tenant_document_fk') then
    alter table file_objects add constraint file_objects_tenant_document_fk foreign key (tenant_id, document_id) references documents(tenant_id, id);
  end if;
  if not exists (select 1 from pg_constraint where conname = 'file_objects_tenant_version_fk') then
    alter table file_objects add constraint file_objects_tenant_version_fk foreign key (tenant_id, document_version_id) references document_versions(tenant_id, id);
  end if;
  if not exists (select 1 from pg_constraint where conname = 'jobs_tenant_file_object_fk') then
    alter table ingestion_jobs add constraint jobs_tenant_file_object_fk foreign key (tenant_id, file_object_id) references file_objects(tenant_id, id);
  end if;
end
$$;

alter table file_objects enable row level security;
alter table file_objects force row level security;
drop policy if exists tenant_isolation on file_objects;
create policy tenant_isolation on file_objects
  using (tenant_id = proofbase_current_tenant_id() or proofbase_platform_admin())
  with check (tenant_id = proofbase_current_tenant_id() or proofbase_platform_admin());

grant select, insert, update, delete on file_objects to proofbase_runtime;

grant usage on schema public to proofbase_runtime;
grant select, insert, update, delete on all tables in schema public to proofbase_runtime;
grant usage, select on all sequences in schema public to proofbase_runtime;
alter default privileges in schema public grant select, insert, update, delete on tables to proofbase_runtime;
alter default privileges in schema public grant usage, select on sequences to proofbase_runtime;

create or replace function proofbase_current_tenant_id() returns uuid
language sql stable as $$
  select nullif(current_setting('app.tenant_id', true), '')::uuid
$$;

create or replace function proofbase_platform_admin() returns boolean
language sql stable as $$
  select coalesce(nullif(current_setting('app.platform_admin', true), '')::boolean, false)
$$;

alter table tenants enable row level security;
alter table tenants force row level security;
drop policy if exists tenant_isolation on tenants;
create policy tenant_isolation on tenants
  using (id = proofbase_current_tenant_id() or proofbase_platform_admin())
  with check (id = proofbase_current_tenant_id() or proofbase_platform_admin());

alter table demo_users enable row level security;
alter table demo_users force row level security;
drop policy if exists tenant_isolation on demo_users;
create policy tenant_isolation on demo_users using (
  proofbase_platform_admin() or exists (
    select 1 from tenant_memberships tm
    where tm.user_id = demo_users.id and tm.tenant_id = proofbase_current_tenant_id()
  )
);

alter table external_identities enable row level security;
alter table external_identities force row level security;
drop policy if exists tenant_isolation on external_identities;
create policy tenant_isolation on external_identities using (
  proofbase_platform_admin() or exists (
    select 1 from tenant_memberships tm
    where tm.user_id = external_identities.user_id and tm.tenant_id = proofbase_current_tenant_id()
  )
);

do $$
declare protected_table text;
begin
  foreach protected_table in array array[
    'tenant_memberships', 'auth_sessions', 'projects', 'project_memberships',
    'project_departments', 'documents', 'document_versions', 'ingestion_jobs',
    'chunks', 'chunk_embeddings', 'chat_sessions', 'chat_messages', 'feedback', 'audit_logs'
  ]
  loop
    execute format('alter table %I enable row level security', protected_table);
    execute format('alter table %I force row level security', protected_table);
    execute format('drop policy if exists tenant_isolation on %I', protected_table);
    execute format(
      'create policy tenant_isolation on %I using (tenant_id = proofbase_current_tenant_id() or proofbase_platform_admin()) with check (tenant_id = proofbase_current_tenant_id() or proofbase_platform_admin())',
      protected_table
    );
  end loop;
end
$$;

do $$
declare evaluation_table text;
begin
  foreach evaluation_table in array array[
    'evaluation_questions', 'evaluation_runs', 'evaluation_results', 'evaluation_reviews'
  ]
  loop
    execute format('alter table %I enable row level security', evaluation_table);
    execute format('alter table %I force row level security', evaluation_table);
    execute format('drop policy if exists tenant_isolation on %I', evaluation_table);
    execute format(
      'create policy tenant_isolation on %I using (tenant_id = proofbase_current_tenant_id() or tenant_id is null) with check (tenant_id = proofbase_current_tenant_id() or (tenant_id is null and proofbase_platform_admin()))',
      evaluation_table
    );
  end loop;
end
$$;
