# End-To-End Flow

This document follows a user question through the live API path. The main entry points are `POST /query` and `POST /query/stream` in `apps/api/app/main.py`.

## One Request In Plain English

1. The API receives the question, requested retrieval settings, optional session ID, and optional project or department scope.
2. If a project scope is present, the API verifies the demo user is a member of that project.
3. The API chooses the effective role. For project-scoped App queries, it uses the signed-in demo user's business role instead of trusting the request body.
4. If a chat session exists, previous messages are loaded and used only to detect and rewrite follow-up questions.
5. Deterministic request guards run first. Every remaining request receives a strict-schema semantic assessment that can continue, clarify, block, or fail safely, but cannot grant access.
6. Only a continued request reaches retrieval, which runs against Postgres with project, department, and role filters.
7. Multi-document mode may decompose the question into subqueries and merge results.
8. A permission-aware evidence assessment sees only those authorized chunks and decides whether the request is answerable, partially answerable, unsupported, conflicting, or temporarily unverifiable.
9. Only `answer` or `partial_answer` proceeds to ordinary generation. Missing evidence returns not found, conflicts request clarification, and assessment failures stop safely.
10. Generation either returns a deterministic policy response, a no-access/not-found response, or calls OpenAI with a prompt version and authorized retrieved context.
11. Citations are matched to retrieved chunks, optionally backfilled from retrieved chunks, then validated.
12. Confidence scores, citations, retrieved chunk previews, request- and evidence-assessment metadata, memory metadata, and permission checks are returned.
13. The request is logged for observability. Guarded requests, permission-filtered retrieval, evidence conflicts, and assessment failures are audit logged.

## Request Flow Diagram

```mermaid
sequenceDiagram
  participant Web as Web/App or Dev/Admin
  participant API as FastAPI
  participant Memory as Memory rewrite
  participant Assess as Request assessor
  participant Retriever as Retriever
  participant DB as Postgres + pgvector
  participant Evidence as Evidence assessor
  participant Gen as Answer generator
  participant OpenAI as OpenAI chat

  Web->>API: POST /query
  API->>API: Validate project/department scope
  API->>API: Derive effective role
  API->>Memory: Load session turns and rewrite if follow-up
  API->>Assess: Current request + minimal reference context
  alt Block, clarify, or assessment unavailable
    Assess-->>API: Safe routing response; no retrieval
    API-->>Web: Clarify/block/fail-safe response
  else Continue
    Assess-->>API: Continue (no authorization authority)
  API->>Retriever: Retrieve with role and scope
  Retriever->>DB: Query indexed active documents only
  DB-->>Retriever: Allowed chunks
  Retriever-->>API: RetrievedChunk list
  API->>Evidence: Rewritten request + authorized chunks only
  alt Missing, conflicting, or assessment unavailable
    Evidence-->>API: Not found, clarify, or fail safely
    API-->>Web: Safe non-generation response
  else Sufficient or partial
    Evidence-->>API: Answer action + authorized support metadata
  API->>Gen: Generate from permission-filtered chunks
  Gen->>Gen: Check unauthorized chunks again
  alt Policy/no chunks
    Gen-->>API: Refusal, clarify, or not-found
  else Model answer
    Gen->>OpenAI: Prompt + retrieved context
    OpenAI-->>Gen: Structured JSON answer
    Gen->>Gen: Validate citations and confidence
    Gen-->>API: Answer payload
  end
  API-->>Web: Answer, citations, confidence, metadata
  end
  end
```

## Scope And Role Selection

The request schema allows:

| Field | Meaning |
| --- | --- |
| `project_id` | Optional project boundary for App-side scoped RAG. |
| `department_id` | Optional strict department boundary. It requires `project_id`. |
| `user_role` | Requested role. It is honored for admin/global use more than App-scoped use. |
| `retrieval_mode` | `vector_only`, `keyword_only`, `hybrid`, or `vector_lexical_rerank`. |
| `top_k` | Number of final chunks requested. |
| `multi_doc_mode` | `auto`, `off`, or `force`. |
| `prompt_version` | Optional prompt override. |

In App-scoped requests, `apps/api/app/main.py` calls project membership checks before retrieval and derives the role from the authenticated demo user. Department scope is strict: if supplied, retrievers add `d.department_id = %s::uuid`.

## Memory Step

Memory is not evidence. It is a preprocessing aid:

1. `list_messages` loads recent session messages.
2. `rewrite_followup_question` checks whether the current question looks like a follow-up.
3. If it is a follow-up, the system creates a standalone retrieval question.
4. `memory_context_text` provides a small prompt note with previous topic and cited source IDs.
5. The answer must still cite currently retrieved chunks.

This is why prior assistant answers can help resolve "it" or "that", but they are not trusted as proof.

## Request Assessment Step

`apps/api/app/reasoning/request_assessment.py` runs after identity and project membership resolution but before retrieval. Existing deterministic guards remain fast paths. In the default `semantic_all_remaining` mode, every other request is classified with the versioned `request_assessment` prompt and the strict `request_assessment.v1` schema.

The model receives only the current request, at most two recent user turns, and an application-derived standalone question for reference resolution. It does not receive the effective role, project or department authorization, source documents, retrieved chunks, secrets, or tool permissions. Its output can narrow the path to `continue`, `clarify`, `block`, or `temporary_unavailable`; it cannot expand scope. Invalid schema, refusal, timeout, missing credentials, or provider failure returns a fail-safe response before retrieval.

A small trusted contract check prevents a clear information request from being mislabeled merely because its subject may be sensitive, restricted, or absent. That normalization still leads only to the ordinary permission-filtered retrieval path and is exposed as `normalization_reason` metadata. It cannot grant access or insert evidence.

## Retrieval Step

The normal dispatch lives in `apps/api/app/retrieval/retriever.py`.

| Mode | Implementation |
| --- | --- |
| `vector_only` | Embeds the query, searches `chunk_embeddings`, returns nearest chunks. |
| `keyword_only` | Builds a PostgreSQL full-text query and ranks by `ts_rank_cd`. |
| `hybrid` | Runs vector and keyword retrieval separately, normalizes scores, merges, and sorts. |
| `vector_lexical_rerank` | Runs vector retrieval over a larger allowed candidate set, then reranks by vector score plus lexical overlap. |

Every retriever filters by:

- document status `active`
- document version status `indexed`
- chunking strategy
- project and department scope, when supplied
- role overlap via `d.access_roles && %s`

## Evidence Sufficiency Step

Before generation, `apps/api/app/reasoning/evidence_assessment.py` runs only after retrieval has applied identity, project, department, document-role, active-version, and chunk filters. Empty evidence and missing required source coverage use deterministic fast paths; unresolved cases use the versioned strict-schema semantic assessor.

The assessor receives the normalized request, bounded Phase 52 routing fields, and authorized chunks. It receives no role, membership, hidden candidate, filtered document ID, secret, tool authority, or memory text. Application code validates or removes every model-authored chunk reference against the authorized input allowlist and derives duplicated action/source metadata deterministically. This normalization cannot add evidence or authorization.

An `answer` or `partial_answer` action preserves the complete permission-filtered retrieval set for generation; semantic support IDs explain the assessment but are not a second retriever. `not_found`, unresolved conflict, timeout, schema failure, or provider failure stops before ordinary generation.

## Generation Step

The answer generator first checks for unsafe state:

- If any retrieved chunk is not accessible to the current role, it returns `refuse_no_access` and logs an audit event.
- If no chunks exist, it returns `not_found` unless the expected behavior explicitly asks for no-access.
- If deterministic policy patterns match, it can return `not_found`, `refuse_no_access`, `clarify`, or a direct supported answer without calling OpenAI.
- Otherwise, it builds a prompt from the selected prompt version and the retrieved context.

The default active prompt is chosen by `get_prompt("answer_generation", version)`. If no version is supplied, the active prompt file is used. Phase 38's strongest answer-quality run explicitly used prompt `v8`.

## Post-Generation Validation Step

`apps/api/app/reasoning/post_generation_validation.py` checks generated `answer` and `partial_answer` candidates before candidate text is returned. Streaming generation is buffered until this step completes, so a rejected pre-repair answer is not emitted as deltas.

The validator receives the question, candidate, candidate citations, and the same permission-filtered chunks supplied to generation. It checks exact numbers, money, dates, percentages, and durations deterministically, then uses a strict-schema semantic pass for claim entailment, negation, exceptions, roles/approvals, conflicts, citation-to-claim support, and source-instruction following. Application code removes non-authorized model references and downgrades inconsistent support; a normalization is recorded and cannot silently become acceptance.

At most one regeneration is allowed. `repair_answer_once` uses the identical authorized chunks and performs no retrieval. If a second validation still finds unsupported material, the response keeps only typed supported claims and their supporting authorized citations as a partial answer; when no safe supported subset exists, it returns not found. Exact mismatches and source-instruction compliance are never copied into a partial fallback.

## Response Payload

The API response includes:

| Field | Purpose |
| --- | --- |
| `answer` | Natural-language answer. |
| `response_type` | Structured type: `answer`, `partial_answer`, `not_found`, `refuse_no_access`, or `clarify`. |
| `behavior` | Evaluation behavior derived from response type. |
| `citations` | Validated citations pointing to retrieved chunks. |
| `retrieved_chunks` | Chunk metadata and content previews, not full chunk text. |
| `memory` | Follow-up detection and rewrite metadata. |
| `request_assessment` | Typed intent/risk/action, route, safe reason codes, normalization, model, prompt, latency, token, and estimated-cost metadata. |
| `evidence_assessment` | Post-permission answerability, required facts/source coverage, conflicts, action, authorized support IDs, normalization, model, prompt, latency, tokens, and estimated cost. It is null when request assessment stops before retrieval. |
| `post_generation_validation` | Claim/citation checks, exact literals, source-instruction outcome, bounded reason codes, repair count, normalization, route/status, latency, tokens, and estimated cost. It is null when a request stops before generation. |
| `permission_check` | Effective role and whether unauthorized chunks reached generation. |
| `confidence` fields | Retrieval, citation, answer, and final confidence. |
| `scope` | Project and department scope used by retrieval. |

## Important Boundary

The answer generator's context comes from `RetrievedChunk` objects returned by the retriever. That means the main permission boundary is before generation, not after generation.

The code also logs retrieved chunk IDs and document IDs for observability, but it does not need to log full source text to prove which evidence was used.
