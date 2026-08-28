import json
import uuid
from datetime import UTC, datetime
from pathlib import Path
from typing import Annotated

from fastapi import Depends, FastAPI, File, Form, Header, HTTPException, UploadFile
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import StreamingResponse
from psycopg import Error as PsycopgError
from pydantic import BaseModel, Field

from apps.api.app.audit.audit_logger import audit_summary as get_audit_summary
from apps.api.app.audit.audit_logger import list_audit_events, log_audit_event
from apps.api.app.auth.demo_auth import (
    DEMO_USER_HEADER,
    TENANT_HEADER,
    accessible_project_ids,
    list_demo_users,
    list_project_memberships,
    remove_project_membership,
    require_admin,
    require_project_editor,
    require_project_member,
    require_project_owner,
    resolve_demo_user,
    resolve_oidc_user,
    set_project_membership,
)
from apps.api.app.auth.oidc import LocalFixtureTokenVerifier, OidcValidationError, OidcVerifierConfig
from apps.api.app.auth.identity_store import token_is_revoked
from apps.api.app.auth.tenant_context import current_tenant_id, set_request_principal
from apps.api.app.core.config import get_settings
from apps.api.app.confidence.confidence_scorer import final_confidence
from apps.api.app.db.session import get_connection
from apps.api.app.feedback.feedback_store import feedback_summary as get_feedback_summary
from apps.api.app.feedback.feedback_store import list_feedback, submit_feedback
from apps.api.app.generation.answer_generator import (
    generate_answer,
    generate_answer_stream,
    repair_answer_once,
    retrieved_chunks_payload,
)
from apps.api.app.ingestion.pdf_extractor import extract_pdf_to_markdown
from apps.api.app.memory.context_builder import build_memory_context, memory_context_text
from apps.api.app.memory.query_rewriter import rewrite_followup_question
from apps.api.app.memory.session_store import (
    add_message,
    create_session,
    get_session,
    list_messages,
)
from apps.api.app.observability.logger import build_request_entry, log_request
from apps.api.app.observability.query_telemetry import (
    query_error_category,
    redacted_error_message,
    submit_query_telemetry,
)
from apps.api.app.observability.summary import compute_live_summary
from apps.api.app.observability.tracing import RequestTrace
from apps.api.app.permissions.access_control import unauthorized_chunks_reached_generation
from apps.api.app.projects.document_store import (
    approve_and_index_document,
    create_pending_review_document,
    get_project_document,
    list_project_documents,
    record_cleanup_metadata,
    record_cleanup_revert_metadata,
)
from apps.api.app.projects.markdown_cleanup import cleanup_uploaded_markdown, hash_markdown
from apps.api.app.projects.project_store import (
    archive_department,
    archive_project,
    get_department,
    get_project,
    list_projects,
)
from apps.api.app.projects.project_store import create_department as create_department_record
from apps.api.app.projects.project_store import create_project as create_project_record
from apps.api.app.projects.project_store import update_department as update_department_record
from apps.api.app.projects.project_store import update_project as update_project_record
from apps.api.app.reasoning.clarification import ClarificationDecision, clarification_answer
from apps.api.app.reasoning.evidence_assessment import (
    EvidenceAssessment,
    assess_evidence,
    evidence_generation_action,
    evidence_response_reason,
)
from apps.api.app.reasoning.defense_trace import build_defense_trace
from apps.api.app.reasoning.evidence_grouper import group_chunks_by_document
from apps.api.app.reasoning.multi_doc_detector import is_multi_document_question
from apps.api.app.reasoning.query_decomposer import retrieve_multi_doc
from apps.api.app.reasoning.request_assessment import (
    RequestAssessment,
    assess_request,
    assessment_response_decision,
)
from apps.api.app.reasoning.post_generation_validation import (
    PostGenerationValidation,
    can_prune_unsupported_citations,
    combine_validation_attempts,
    mark_citation_prune_repair,
    validate_candidate_answer,
)
from apps.api.app.retrieval.config import default_retrieval_config
from apps.api.app.retrieval.retriever import retrieve_chunks
from apps.api.app.review.review_store import create_review_decision, list_review_decisions

ROOT = Path(__file__).resolve().parents[3]
DASHBOARD_DATA_PATH = ROOT / "data/evaluation/dashboard-summary.json"
BENCHMARK_PATH = ROOT / "data/evaluation/benchmark-questions.json"
FAILED_QUESTIONS_PATH = ROOT / "data/evaluation/failed-questions/failed-questions.json"
PROMPT_EXPERIMENT_DIR = ROOT / "data/evaluation/prompt-experiments"
EXPANDED_BASELINE_DIR = ROOT / "data/evaluation/expanded-baseline"
MULTI_DOC_EVAL_PATH = ROOT / "data/evaluation/multi-doc-eval.json"
MAX_UPLOAD_BYTES = 10 * 1024 * 1024


def _cors_origins() -> list[str]:
    settings = get_settings()
    return [origin.strip() for origin in settings.cors_allowed_origins.split(",") if origin.strip()]


def _confidence_interpretation(response_type: str) -> str:
    if response_type in {"answer", "partial_answer"}:
        return "answer_support"
    return "response_behavior"


app = FastAPI(title="Proofbase API")
app.add_middleware(
    CORSMiddleware,
    allow_origins=_cors_origins(),
    allow_credentials=False,
    allow_methods=["*"],
    allow_headers=["*"],
)


class QueryRequest(BaseModel):
    question: str = Field(..., min_length=1)
    user_role: str = "Employee"
    session_id: str | None = None
    user_id: str | None = None
    top_k: int | None = None
    retrieval_mode: str = "vector_lexical_rerank"
    chunking_strategy: str = "section_based"
    vector_weight: float = 0.5
    keyword_weight: float = 0.5
    prompt_name: str = "answer_generation"
    prompt_version: str | None = None
    multi_doc_mode: str = Field("auto", pattern="^(auto|off|force)$")
    project_id: str | None = None
    department_id: str | None = None
    evaluation_excluded_document_prefixes: list[str] = Field(default_factory=list, max_length=10)


class CreateSessionRequest(BaseModel):
    user_role: str = "Employee"
    user_id: str | None = None


class FeedbackRequest(BaseModel):
    session_id: str | None = None
    message_id: str | None = None
    question: str = Field(..., min_length=1)
    answer: str = Field(..., min_length=1)
    response_type: str | None = None
    citations: list[dict] | None = None
    user_role: str = "Employee"
    rating: str = Field(..., pattern="^(thumbs_up|thumbs_down)$")
    user_comment: str | None = None
    feedback_category: str = "other"


class AlgorithmReviewRequest(BaseModel):
    profile_name: str = Field(..., min_length=1, max_length=120)
    decision: str = Field(..., pattern="^(review_only|candidate|rejected)$")
    question: str = Field(..., min_length=1)
    user_role: str = "Admin"
    reviewer_id: str | None = None
    primary_metric: str = Field("source_coverage", max_length=80)
    expected_sources: list[str] = Field(default_factory=list, max_length=20)
    notes: str = Field("", max_length=2000)
    result_summary: dict | None = None


class EvaluationReviewRequest(BaseModel):
    source_type: str = Field(..., pattern="^(failed_question|feedback)$")
    source_id: str = Field(..., min_length=1, max_length=120)
    question: str = Field(..., min_length=1)
    answer: str | None = None
    expected_answer: str | None = None
    expected_sources: list[str] = Field(default_factory=list, max_length=20)
    actual_citations: list[dict] = Field(default_factory=list, max_length=20)
    retrieved_chunks: list[dict] = Field(default_factory=list, max_length=20)
    answer_correctness: float = Field(..., ge=0, le=1)
    citation_correctness: float = Field(..., ge=0, le=1)
    decision: str = Field(..., pattern="^(needs_fix|evaluation_candidate|approved_reference|rejected)$")
    reviewer_role: str = "Evaluator"
    reviewer_id: str | None = None
    notes: str = Field("", max_length=2000)


class ApproveIndexRequest(BaseModel):
    reviewed_markdown: str | None = Field(None, max_length=2_000_000)


class CleanupMarkdownRequest(BaseModel):
    model: str | None = Field(None, min_length=1, max_length=120)


class ProjectCreateRequest(BaseModel):
    name: str = Field(..., min_length=1, max_length=120)
    description: str = Field("", max_length=1000)
    status: str = Field("active", pattern="^(active|paused)$")
    default_retrieval_profile: str = Field("vector-section", min_length=1, max_length=80)
    user_role: str = "Admin"
    user_id: str | None = None


class ProjectUpdateRequest(BaseModel):
    name: str | None = Field(None, min_length=1, max_length=120)
    description: str | None = Field(None, max_length=1000)
    status: str | None = Field(None, pattern="^(active|paused|archived)$")
    default_retrieval_profile: str | None = Field(None, min_length=1, max_length=80)
    user_role: str = "Admin"
    user_id: str | None = None


class ProjectMembershipUpdateRequest(BaseModel):
    membership_level: str = Field(..., pattern="^(viewer|contributor|owner)$")


class DepartmentCreateRequest(BaseModel):
    name: str = Field(..., min_length=1, max_length=120)
    icon: str = Field("building", pattern="^(people|shield|chart|briefcase|lock|key|building)$")
    color: str = Field("steel", pattern="^(moss|steel|rust|stone)$")
    description: str = Field("", max_length=1000)
    default_access_roles: list[str] = Field(default_factory=list, max_length=10)
    user_role: str = "Admin"
    user_id: str | None = None


class DepartmentUpdateRequest(BaseModel):
    name: str | None = Field(None, min_length=1, max_length=120)
    icon: str | None = Field(None, pattern="^(people|shield|chart|briefcase|lock|key|building)$")
    color: str | None = Field(None, pattern="^(moss|steel|rust|stone)$")
    description: str | None = Field(None, max_length=1000)
    default_access_roles: list[str] | None = Field(None, max_length=10)
    status: str | None = Field(None, pattern="^(active|archived)$")
    user_role: str = "Admin"
    user_id: str | None = None


def _validate_project_id(project_id: str) -> str:
    return _validate_uuid(project_id, "Project ID")


def _validate_uuid(value: str, label: str) -> str:
    try:
        uuid.UUID(value)
    except ValueError as exc:
        raise HTTPException(status_code=400, detail=f"{label} must be a valid UUID.") from exc
    return value


def _normalize_roles(roles: list[str] | None) -> list[str] | None:
    if roles is None:
        return None
    normalized = [role.strip() for role in roles if role.strip()]
    return list(dict.fromkeys(normalized))


def _safe_upload_name(filename: str | None) -> str:
    name = Path(filename or "upload.pdf").name
    stem = Path(name).stem or "upload"
    suffix = Path(name).suffix.lower() or ".pdf"
    safe_stem = "".join(char if char.isalnum() or char in {"-", "_"} else "-" for char in stem).strip("-")
    return f"{safe_stem or 'upload'}{suffix}"


def current_demo_user(
    x_demo_user_id: Annotated[str | None, Header(alias=DEMO_USER_HEADER)] = None,
    x_tenant_id: Annotated[str | None, Header(alias=TENANT_HEADER)] = None,
    authorization: Annotated[str | None, Header(alias="Authorization")] = None,
) -> dict:
    settings = get_settings()
    if settings.auth_mode == "local_demo":
        try:
            selected_tenant_id = str(uuid.UUID(x_tenant_id or settings.default_demo_tenant_id))
            selected_user_id = str(uuid.UUID(x_demo_user_id or settings.default_demo_user_id))
        except (ValueError, AttributeError) as exc:
            raise HTTPException(status_code=400, detail="Identity selections must be valid UUIDs.") from exc
        set_request_principal(tenant_id=selected_tenant_id, user_id=selected_user_id)
        user = resolve_demo_user(selected_user_id, selected_tenant_id)
        set_request_principal(tenant_id=user["tenant_id"], user_id=user["id"])
        return user
    if x_demo_user_id is not None:
        raise HTTPException(status_code=400, detail="Demo identity headers are disabled outside local demo mode.")
    if settings.auth_mode == "oidc":
        raise HTTPException(status_code=503, detail="The hosted OIDC provider adapter is not connected.")
    if not authorization or not authorization.startswith("Bearer "):
        raise HTTPException(status_code=401, detail="A bearer token is required.")
    if not x_tenant_id:
        raise HTTPException(status_code=400, detail="X-Tenant-Id is required for multi-tenant requests.")
    try:
        selected_tenant_id = str(uuid.UUID(x_tenant_id))
    except (ValueError, AttributeError) as exc:
        raise HTTPException(status_code=400, detail="X-Tenant-Id must be a valid UUID.") from exc
    verifier = LocalFixtureTokenVerifier(
        OidcVerifierConfig(
            issuer=settings.oidc_issuer,
            audience=settings.oidc_audience,
            local_signing_secret=settings.oidc_local_signing_secret,
        )
    )
    try:
        bearer_token = authorization.removeprefix("Bearer ").strip()
        claims = verifier.verify(bearer_token)
        token_id = claims.get("jti")
        if isinstance(token_id, str) and token_is_revoked(issuer=claims["iss"], token_id=token_id):
            raise OidcValidationError("Bearer token is revoked.")
    except OidcValidationError as exc:
        raise HTTPException(status_code=401, detail=str(exc)) from exc
    tenant_ids = claims.get("tenant_ids")
    if not isinstance(tenant_ids, list) or selected_tenant_id not in tenant_ids:
        raise HTTPException(status_code=403, detail="The token does not authorize the selected tenant.")
    try:
        set_request_principal(tenant_id=selected_tenant_id, user_id=claims["sub"])
        user = resolve_oidc_user(issuer=claims["iss"], subject=claims["sub"], tenant_id=selected_tenant_id)
        set_request_principal(tenant_id=user["tenant_id"], user_id=user["id"])
        return user
    except PsycopgError as exc:
        raise HTTPException(status_code=503, detail="OIDC identity mapping is unavailable.") from exc


def current_admin_user(user: Annotated[dict, Depends(current_demo_user)]) -> dict:
    require_admin(user)
    return user


def _effective_query_role(requested_role: str, user: dict, *, project_scoped: bool) -> str:
    if project_scoped:
        return user["business_role"]
    if user["is_admin"]:
        return requested_role or user["business_role"]
    return user["business_role"]


def _evaluation_excluded_document_prefixes(request: QueryRequest, user: dict) -> tuple[str, ...]:
    prefixes = tuple(dict.fromkeys(prefix.strip() for prefix in request.evaluation_excluded_document_prefixes if prefix.strip()))
    if prefixes and not user["is_admin"]:
        raise HTTPException(status_code=403, detail="Evaluation document exclusions are restricted to admin users.")
    return prefixes


def _load_dashboard_data() -> dict:
    if not DASHBOARD_DATA_PATH.exists():
        raise HTTPException(
            status_code=404,
            detail="Evaluation dashboard data not found. Run `python scripts/export_dashboard_data.py` first.",
        )
    try:
        return json.loads(DASHBOARD_DATA_PATH.read_text(encoding="utf-8"))
    except json.JSONDecodeError as exc:
        raise HTTPException(status_code=500, detail="Evaluation dashboard data is not valid JSON.") from exc


def _read_json_file(path: Path, default):
    if not path.exists():
        return default
    try:
        return json.loads(path.read_text(encoding="utf-8"))
    except json.JSONDecodeError as exc:
        raise HTTPException(status_code=500, detail=f"{path.name} is not valid JSON.") from exc


def _load_benchmark_by_id() -> dict[str, dict]:
    benchmark = _read_json_file(BENCHMARK_PATH, {"questions": []})
    return {
        question["question_id"]: question
        for question in benchmark.get("questions", [])
        if isinstance(question, dict) and question.get("question_id")
    }


def _load_failed_items() -> list[dict]:
    return _read_json_file(FAILED_QUESTIONS_PATH, [])


def _load_run_rows(run_id: str) -> tuple[list[dict], str | None]:
    prompt_path = PROMPT_EXPERIMENT_DIR / f"{run_id}.json"
    if prompt_path.exists():
        payload = _read_json_file(prompt_path, {})
        return payload.get("rows") or [], "prompt_experiment"

    expanded_path = EXPANDED_BASELINE_DIR / f"{run_id}.json"
    if expanded_path.exists():
        payload = _read_json_file(expanded_path, {})
        return payload.get("rows") or [], "expanded_baseline"

    if run_id in {"multi-doc-baseline", "multi-doc", "multi-doc-eval"} and MULTI_DOC_EVAL_PATH.exists():
        payload = _read_json_file(MULTI_DOC_EVAL_PATH, {})
        mode = "baseline" if run_id == "multi-doc-baseline" else "multi_doc"
        return payload.get(mode, {}).get("rows") or [], "multi_doc_eval"

    return [], None


def _dashboard_run(run_id: str) -> dict | None:
    data = _load_dashboard_data()
    return next((run for run in data["runs"] if run["run_id"] == run_id), None)


def _normalize_citation_documents(citations: list[dict] | None) -> list[str]:
    if not citations:
        return []
    return list(dict.fromkeys(str(citation.get("document_id")) for citation in citations if citation.get("document_id")))


def _enrich_eval_row(row: dict, benchmark_by_id: dict[str, dict], failed_by_id: dict[str, dict]) -> dict:
    question_id = row.get("question_id")
    benchmark = benchmark_by_id.get(question_id, {})
    failure = failed_by_id.get(question_id, {})
    citations = row.get("citations") or []
    return {
        **row,
        "question": row.get("question") or benchmark.get("question"),
        "question_type": row.get("question_type") or benchmark.get("question_type"),
        "user_role": row.get("user_role") or benchmark.get("user_role"),
        "expected_behavior": row.get("expected_behavior") or benchmark.get("expected_behavior"),
        "expected_answer": benchmark.get("expected_answer"),
        "expected_source_document": benchmark.get("expected_source_document"),
        "expected_source_section_or_quote": benchmark.get("expected_source_section_or_quote"),
        "actual_response_type": row.get("actual_response_type") or row.get("response_type"),
        "actual_answer": row.get("actual_answer") or row.get("answer"),
        "actual_citations": citations,
        "actual_citation_documents": _normalize_citation_documents(citations),
        "failure_type": failure.get("failure_type"),
        "recommended_fix": failure.get("recommended_fix"),
        "passed": not failure,
    }


@app.get("/health")
def health() -> dict:
    return {"status": "ok"}


@app.get("/ready")
def ready() -> dict:
    required_tables = [
        "projects",
        "tenants",
        "tenant_memberships",
        "external_identities",
        "auth_sessions",
        "project_departments",
        "documents",
        "document_versions",
        "ingestion_jobs",
        "chunks",
        "chunk_embeddings",
        "audit_logs",
        "chat_sessions",
        "chat_messages",
        "feedback",
        "evaluation_reviews",
    ]
    try:
        with get_connection() as conn:
            vector_extension = conn.execute(
                "select exists(select 1 from pg_extension where extname = 'vector') as exists"
            ).fetchone()["exists"]
            table_rows = conn.execute(
                """
                select table_name
                from information_schema.tables
                where table_schema = 'public'
                  and table_name = any(%s)
                """,
                (required_tables,),
            ).fetchall()
            existing_tables = {row["table_name"] for row in table_rows}
            missing_tables = sorted(set(required_tables) - existing_tables)
            if missing_tables:
                raise HTTPException(
                    status_code=503,
                    detail={
                        "status": "not_ready",
                        "database": "connected",
                        "schema": "missing_tables",
                        "missing_tables": missing_tables,
                    },
                )
            if not vector_extension:
                raise HTTPException(
                    status_code=503,
                    detail={
                        "status": "not_ready",
                        "database": "connected",
                        "schema": "pgvector_missing",
                    },
                )
            document_count = conn.execute("select count(*) as count from documents").fetchone()["count"]
            chunk_count = conn.execute("select count(*) as count from chunks").fetchone()["count"]
    except HTTPException:
        raise
    except PsycopgError as exc:
        raise HTTPException(
            status_code=503,
            detail={"status": "not_ready", "database": "unavailable", "reason": str(exc)},
        ) from exc

    return {
        "status": "ready",
        "database": "connected",
        "schema": "ok",
        "pgvector": "enabled",
        "document_count": document_count,
        "chunk_count": chunk_count,
    }


@app.get("/auth/demo-users")
def demo_users_route() -> dict:
    if get_settings().auth_mode != "local_demo":
        raise HTTPException(status_code=404, detail="Demo identities are disabled.")
    try:
        users = list_demo_users()
    except PsycopgError as exc:
        raise HTTPException(status_code=503, detail="Demo auth schema is not ready.") from exc
    return {"users": users, "count": len(users), "auth_mode": "local_demo"}


@app.get("/auth/me")
def auth_me_route(user: Annotated[dict, Depends(current_demo_user)]) -> dict:
    return {"user": user, "auth_mode": get_settings().auth_mode}


@app.post("/chat/sessions")
def create_chat_session(request: CreateSessionRequest, user: Annotated[dict, Depends(current_demo_user)]) -> dict:
    effective_role = _effective_query_role(request.user_role, user, project_scoped=False)
    session_id = create_session(effective_role, user_id=user["id"])
    return {"session_id": session_id, "user_role": effective_role, "user_id": user["id"]}


@app.get("/evaluation/summary")
def evaluation_summary(user: Annotated[dict, Depends(current_admin_user)]) -> dict:
    data = _load_dashboard_data()
    return {
        "generated_at": data["generated_at"],
        "overview": data["overview"],
        "benchmark_context": data.get("benchmark_context", {}),
        "regression_scorecard": data.get("regression_scorecard", {}),
        "phase33_precision_readiness": data.get("phase33_precision_readiness", {}),
        "independent_evaluation": data.get("independent_evaluation", {}),
        "run_count": len(data["runs"]),
        "failed_question_count": len(data["failed_questions"]),
        "notes": data["notes"],
    }


@app.get("/evaluation/runs")
def evaluation_runs(user: Annotated[dict, Depends(current_admin_user)]) -> dict:
    data = _load_dashboard_data()
    return {
        "runs": [
            {
                "run_id": run["run_id"],
                "run_name": run["run_name"],
                "phase": run["phase"],
                "run_type": run["run_type"],
                "timestamp": run["timestamp"],
                "run_timestamp": run.get("run_timestamp") or run.get("timestamp"),
                "sample_size": run.get("sample_size") or run.get("total_questions"),
                "passed_count": run.get("passed_count"),
                "failed_count": run.get("failed_count"),
                "benchmark_version": run.get("benchmark_version"),
                "category_breakdown": run.get("category_breakdown"),
                "retrieval_mode": run.get("retrieval_mode"),
                "chunking_strategy": run.get("chunking_strategy"),
                "top_k": run.get("top_k"),
                "metrics": run["metrics"],
                "failed_question_count": len(run.get("failed_questions") or []),
            }
            for run in data["runs"]
        ]
    }


@app.get("/evaluation/runs/{run_id}")
def evaluation_run_detail(run_id: str, user: Annotated[dict, Depends(current_admin_user)]) -> dict:
    data = _load_dashboard_data()
    for run in data["runs"]:
        if run["run_id"] == run_id:
            return run
    raise HTTPException(status_code=404, detail="Evaluation run not found.")


@app.get("/evaluation/runs/{run_id}/questions")
def evaluation_run_questions(run_id: str, user: Annotated[dict, Depends(current_admin_user)]) -> dict:
    run = _dashboard_run(run_id)
    rows, detail_source = _load_run_rows(run_id)
    benchmark_by_id = _load_benchmark_by_id()
    failed_by_id = {item["question_id"]: item for item in _load_failed_items() if item.get("question_id")}
    enriched_rows = [_enrich_eval_row(row, benchmark_by_id, failed_by_id) for row in rows]
    if not run and not enriched_rows:
        raise HTTPException(status_code=404, detail="Evaluation run not found.")
    return {
        "run": run,
        "run_id": run_id,
        "detail_available": bool(enriched_rows),
        "detail_source": detail_source,
        "row_count": len(enriched_rows),
        "rows": enriched_rows,
        "message": None if enriched_rows else "Detailed per-question rows are not available for this run.",
    }


@app.get("/evaluation/compare")
def evaluation_compare(user: Annotated[dict, Depends(current_admin_user)]) -> dict:
    data = _load_dashboard_data()
    return {
        "overview": data["overview"],
        "benchmark_context": data.get("benchmark_context", {}),
        "comparisons": data["comparisons"],
        "regression_scorecard": data.get("regression_scorecard", {}),
        "prompt_comparison": data.get("prompt_comparison", {}),
        "multi_doc_comparison": data.get("multi_doc_comparison", {}),
        "phase33_precision_readiness": data.get("phase33_precision_readiness", {}),
        "independent_evaluation": data.get("independent_evaluation", {}),
        "runs": data["runs"],
    }


@app.get("/evaluation/failed-questions")
def evaluation_failed_questions(user: Annotated[dict, Depends(current_admin_user)]) -> dict:
    data = _load_dashboard_data()
    return {"failed_questions": data["failed_questions"]}


@app.get("/evaluation/failed-questions/enriched")
def evaluation_failed_questions_enriched(user: Annotated[dict, Depends(current_admin_user)]) -> dict:
    data = _load_dashboard_data()
    current_run_id = data.get("overview", {}).get("current_answer_run_id")
    benchmark_by_id = _load_benchmark_by_id()
    failed_items = _load_failed_items()
    detailed_rows: dict[str, dict] = {}
    run_ids = [
        run_id
        for run_id in (current_run_id, "phase11-answer-generation-v3", "phase11-answer-generation-v1")
        if run_id
    ]
    for run_id in dict.fromkeys(run_ids):
        rows, _ = _load_run_rows(run_id)
        for row in rows:
            if row.get("question_id") and row["question_id"] not in detailed_rows:
                detailed_rows[row["question_id"]] = row

    failures = []
    for item in failed_items:
        question_id = item.get("question_id")
        benchmark = benchmark_by_id.get(question_id, {})
        row = detailed_rows.get(question_id, {})
        citations = row.get("citations") or item.get("actual_citations") or []
        failures.append(
            {
                **item,
                "question": benchmark.get("question"),
                "question_type": benchmark.get("question_type"),
                "user_role": benchmark.get("user_role"),
                "expected_answer": benchmark.get("expected_answer"),
                "expected_source_document": benchmark.get("expected_source_document"),
                "expected_source_section_or_quote": benchmark.get("expected_source_section_or_quote"),
                "actual_answer": row.get("answer"),
                "actual_citations": citations,
                "actual_citation_documents": _normalize_citation_documents(citations),
                "retrieved_documents": row.get("retrieved_documents") or row.get("retrieved_document_ids") or [],
                "retrieved_chunks": row.get("retrieved_chunks") or [],
                "confidence": row.get("final_confidence") or item.get("answer_confidence"),
                "known_open_issue": question_id == "MULTI-005",
                "known_open_issue_note": (
                    "Known Phase 13 open issue: MULTI-005 still fails because SALES-002 is missed during retrieval."
                    if question_id == "MULTI-005"
                    else None
                ),
            }
        )
    return {"failed_questions": failures, "count": len(failures)}


@app.post("/evaluation/algorithm-reviews", status_code=201)
def algorithm_review_route(request: AlgorithmReviewRequest, user: Annotated[dict, Depends(current_admin_user)]) -> dict:
    review_id = str(uuid.uuid4())
    recorded = log_audit_event(
        action="algorithm_profile_reviewed",
        user_role=user["business_role"],
        user_id=user["id"],
        resource_type="retrieval_profile",
        document_id=request.profile_name,
        outcome=request.decision,
        reason=request.primary_metric,
        metadata={
            "review_id": review_id,
            "profile_name": request.profile_name,
            "question": request.question,
            "expected_sources": request.expected_sources,
            "notes": request.notes,
            "result_summary": request.result_summary or {},
        },
    )
    if not recorded:
        raise HTTPException(status_code=503, detail="Audit log storage is unavailable; review note was not recorded.")
    return {
        "review_id": review_id,
        "status": "recorded",
        "audit_action": "algorithm_profile_reviewed",
        "decision": request.decision,
    }


@app.post("/evaluation/reviews", status_code=201)
def create_evaluation_review_route(request: EvaluationReviewRequest, user: Annotated[dict, Depends(current_admin_user)]) -> dict:
    if request.answer_correctness not in {0, 0.5, 1} or request.citation_correctness not in {0, 0.5, 1}:
        raise HTTPException(status_code=400, detail="Correctness labels must be 0, 0.5, or 1.")
    try:
        review = create_review_decision(
            source_type=request.source_type,
            source_id=request.source_id,
            question=request.question,
            answer=request.answer,
            expected_answer=request.expected_answer,
            expected_sources=request.expected_sources,
            actual_citations=request.actual_citations,
            retrieved_chunks=request.retrieved_chunks,
            answer_correctness=request.answer_correctness,
            citation_correctness=request.citation_correctness,
            decision=request.decision,
            reviewer_role=user["business_role"],
            reviewer_id=user["id"],
            notes=request.notes,
        )
    except PsycopgError as exc:
        raise HTTPException(status_code=503, detail="Database error saving evaluation review.") from exc
    log_audit_event(
        action="evaluation_review_saved",
        user_role=user["business_role"],
        user_id=user["id"],
        resource_type="evaluation_review",
        document_id=review["id"],
        outcome=request.decision,
        reason=request.source_type,
        metadata={
            "review_id": review["id"],
            "source_type": request.source_type,
            "source_id": request.source_id,
            "answer_correctness": request.answer_correctness,
            "citation_correctness": request.citation_correctness,
        },
    )
    return {"review": review, "status": "saved"}


@app.get("/evaluation/reviews")
def evaluation_reviews_route(
    user: Annotated[dict, Depends(current_admin_user)],
    source_type: str | None = None,
    source_id: str | None = None,
    decision: str | None = None,
    limit: int = 50,
) -> dict:
    try:
        reviews = list_review_decisions(source_type=source_type, source_id=source_id, decision=decision, limit=limit)
    except PsycopgError as exc:
        raise HTTPException(status_code=503, detail="Database error loading evaluation reviews.") from exc
    return {"reviews": reviews, "count": len(reviews)}


@app.post("/feedback")
def post_feedback(request: FeedbackRequest, user: Annotated[dict, Depends(current_demo_user)]) -> dict:
    effective_role = user["business_role"]
    try:
        feedback_id = submit_feedback(
            session_id=request.session_id,
            message_id=request.message_id,
            question=request.question,
            answer=request.answer,
            response_type=request.response_type,
            citations=request.citations,
            user_role=effective_role,
            rating=request.rating,
            user_comment=request.user_comment,
            feedback_category=request.feedback_category,
        )
    except ValueError as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc
    except PsycopgError as exc:
        raise HTTPException(status_code=503, detail="Database error saving feedback.") from exc
    log_audit_event(
        action="feedback_submitted",
        user_role=effective_role,
        user_id=user["id"],
        resource_type="feedback",
        outcome="success",
        metadata={
            "feedback_id": feedback_id,
            "rating": request.rating,
            "feedback_category": request.feedback_category,
        },
    )
    return {"feedback_id": feedback_id, "status": "submitted"}


@app.get("/feedback")
def get_feedback(
    user: Annotated[dict, Depends(current_admin_user)],
    rating: str | None = None,
    feedback_category: str | None = None,
    limit: int = 50,
) -> dict:
    items = list_feedback(rating=rating, feedback_category=feedback_category, limit=limit)
    return {"feedback": items, "count": len(items)}


@app.get("/feedback/summary")
def feedback_summary_route(user: Annotated[dict, Depends(current_admin_user)]) -> dict:
    return get_feedback_summary()


@app.get("/observability/summary")
def observability_summary(user: Annotated[dict, Depends(current_admin_user)]) -> dict:
    return compute_live_summary(limit=20)


@app.get("/observability/recent-requests")
def recent_requests_route(user: Annotated[dict, Depends(current_admin_user)], limit: int = 20) -> dict:
    return compute_live_summary(limit=limit)


@app.get("/audit/events")
def audit_events(
    user: Annotated[dict, Depends(current_admin_user)],
    action: str | None = None,
    outcome: str | None = None,
    limit: int = 20,
) -> dict:
    events = list_audit_events(action=action, outcome=outcome, limit=limit)
    return {"events": events, "count": len(events)}


@app.get("/audit/summary")
def audit_summary_route(user: Annotated[dict, Depends(current_admin_user)]) -> dict:
    return get_audit_summary()


@app.get("/projects")
def projects_route(user: Annotated[dict, Depends(current_demo_user)], include_archived: bool = False) -> dict:
    try:
        projects = list_projects(tenant_id=user["tenant_id"], include_archived=include_archived)
    except PsycopgError as exc:
        raise HTTPException(status_code=503, detail="Database is not ready or the project schema has not been applied.") from exc
    allowed_project_ids = accessible_project_ids(user)
    if allowed_project_ids is not None:
        projects = [project for project in projects if project["id"] in allowed_project_ids]
    return {"projects": projects, "count": len(projects)}


@app.post("/projects", status_code=201)
def create_project_route(request: ProjectCreateRequest, user: Annotated[dict, Depends(current_admin_user)]) -> dict:
    name = request.name.strip()
    description = request.description.strip()
    default_retrieval_profile = request.default_retrieval_profile.strip()
    if not name:
        raise HTTPException(status_code=400, detail="Project name is required.")
    if not default_retrieval_profile:
        raise HTTPException(status_code=400, detail="Default retrieval profile is required.")
    try:
        project = create_project_record(
            tenant_id=user["tenant_id"],
            created_by_user_id=user["id"],
            name=name,
            description=description,
            status=request.status,
            default_retrieval_profile=default_retrieval_profile,
        )
    except ValueError as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc
    except PsycopgError as exc:
        raise HTTPException(status_code=503, detail="Database error creating project.") from exc

    log_audit_event(
        action="project_created",
        user_role=user["business_role"],
        user_id=user["id"],
        resource_type="project",
        document_id=project["id"],
        outcome="success",
        metadata={"project_id": project["id"], "project_name": project["name"], "status": project["status"]},
    )
    return {"project": project}


@app.get("/projects/{project_id}")
def project_detail_route(project_id: str, user: Annotated[dict, Depends(current_demo_user)], include_archived: bool = False) -> dict:
    project_id = _validate_project_id(project_id)
    require_project_member(user, project_id)
    try:
        project = get_project(project_id, include_archived=include_archived)
    except PsycopgError as exc:
        raise HTTPException(status_code=503, detail="Database error loading project.") from exc
    if not project:
        raise HTTPException(status_code=404, detail="Project not found.")
    return {"project": project}


@app.get("/projects/{project_id}/memberships")
def project_memberships_route(project_id: str, user: Annotated[dict, Depends(current_demo_user)]) -> dict:
    project_id = _validate_project_id(project_id)
    require_project_owner(user, project_id)
    try:
        if not get_project(project_id):
            raise HTTPException(status_code=404, detail="Project not found.")
        memberships = list_project_memberships(project_id)
    except HTTPException:
        raise
    except PsycopgError as exc:
        raise HTTPException(status_code=503, detail="Database error loading project memberships.") from exc
    return {"memberships": memberships, "count": len(memberships)}


@app.put("/projects/{project_id}/memberships/{user_id}")
def update_project_membership_route(
    project_id: str,
    user_id: str,
    request: ProjectMembershipUpdateRequest,
    user: Annotated[dict, Depends(current_demo_user)],
) -> dict:
    project_id = _validate_project_id(project_id)
    user_id = _validate_uuid(user_id, "Demo user ID")
    require_project_owner(user, project_id)
    try:
        membership = set_project_membership(project_id, user_id, request.membership_level)
    except ValueError as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc
    except PsycopgError as exc:
        raise HTTPException(status_code=503, detail="Database error saving project membership.") from exc
    if not membership:
        raise HTTPException(status_code=404, detail="Active project or assignable demo user not found.")

    log_audit_event(
        action="project_membership_updated",
        user_role=user["business_role"],
        user_id=user["id"],
        resource_type="project",
        document_id=project_id,
        outcome="success",
        reason=request.membership_level,
        metadata={
            "project_id": project_id,
            "member_user_id": user_id,
            "membership_level": request.membership_level,
        },
    )
    return {"membership": membership, "status": "saved"}


@app.delete("/projects/{project_id}/memberships/{user_id}")
def delete_project_membership_route(
    project_id: str,
    user_id: str,
    user: Annotated[dict, Depends(current_demo_user)],
) -> dict:
    project_id = _validate_project_id(project_id)
    user_id = _validate_uuid(user_id, "Demo user ID")
    require_project_owner(user, project_id)
    try:
        removed = remove_project_membership(project_id, user_id)
    except PsycopgError as exc:
        raise HTTPException(status_code=503, detail="Database error removing project membership.") from exc
    if not removed:
        raise HTTPException(status_code=404, detail="Project membership not found.")

    log_audit_event(
        action="project_membership_removed",
        user_role=user["business_role"],
        user_id=user["id"],
        resource_type="project",
        document_id=project_id,
        outcome="success",
        reason="access_removed",
        metadata={"project_id": project_id, "member_user_id": user_id},
    )
    return {"status": "removed", "user_id": user_id}


@app.get("/projects/{project_id}/documents")
def project_documents_route(
    project_id: str,
    user: Annotated[dict, Depends(current_demo_user)],
    department_id: str | None = None,
    include_archived: bool = False,
) -> dict:
    project_id = _validate_project_id(project_id)
    require_project_member(user, project_id)
    if department_id is not None:
        department_id = _validate_project_id(department_id)
    try:
        if not get_project(project_id, include_archived=include_archived):
            raise HTTPException(status_code=404, detail="Project not found.")
        documents = list_project_documents(
            project_id,
            department_id=department_id,
            include_archived=include_archived,
        )
    except HTTPException:
        raise
    except PsycopgError as exc:
        raise HTTPException(status_code=503, detail="Database error loading project documents.") from exc
    return {"documents": documents, "count": len(documents)}


@app.post("/projects/{project_id}/departments", status_code=201)
def create_department_route(project_id: str, request: DepartmentCreateRequest, user: Annotated[dict, Depends(current_demo_user)]) -> dict:
    project_id = _validate_project_id(project_id)
    require_project_editor(user, project_id)
    name = request.name.strip()
    description = request.description.strip()
    default_access_roles = _normalize_roles(request.default_access_roles) or []
    if not name:
        raise HTTPException(status_code=400, detail="Department name is required.")
    try:
        if not get_project(project_id):
            raise HTTPException(status_code=404, detail="Project not found.")
        department = create_department_record(
            project_id=project_id,
            name=name,
            icon=request.icon,
            color=request.color,
            description=description,
            default_access_roles=default_access_roles,
        )
    except HTTPException:
        raise
    except ValueError as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc
    except PsycopgError as exc:
        raise HTTPException(status_code=503, detail="Database error creating department.") from exc

    log_audit_event(
        action="department_created",
        user_role=user["business_role"],
        user_id=user["id"],
        resource_type="department",
        document_id=department["id"],
        outcome="success",
        metadata={"project_id": project_id, "department_id": department["id"], "department_name": department["name"]},
    )
    return {"department": department}


@app.get("/projects/{project_id}/departments/{department_id}/documents")
def department_documents_route(
    project_id: str,
    department_id: str,
    user: Annotated[dict, Depends(current_demo_user)],
    include_archived: bool = False,
) -> dict:
    project_id = _validate_project_id(project_id)
    department_id = _validate_project_id(department_id)
    require_project_member(user, project_id)
    try:
        if not get_department(project_id, department_id, include_archived=include_archived):
            raise HTTPException(status_code=404, detail="Department not found.")
        documents = list_project_documents(
            project_id,
            department_id=department_id,
            include_archived=include_archived,
        )
    except HTTPException:
        raise
    except PsycopgError as exc:
        raise HTTPException(status_code=503, detail="Database error loading department documents.") from exc
    return {"documents": documents, "count": len(documents)}


@app.get("/projects/{project_id}/departments/{department_id}/documents/{document_id}")
def department_document_detail_route(
    project_id: str,
    department_id: str,
    document_id: str,
    user: Annotated[dict, Depends(current_demo_user)],
) -> dict:
    project_id = _validate_project_id(project_id)
    department_id = _validate_project_id(department_id)
    document_id = _validate_project_id(document_id)
    require_project_member(user, project_id)
    try:
        if not get_department(project_id, department_id, include_archived=True):
            raise HTTPException(status_code=404, detail="Department not found.")
        document = get_project_document(
            project_id=project_id,
            department_id=department_id,
            document_id=document_id,
            include_archived=True,
        )
    except HTTPException:
        raise
    except PsycopgError as exc:
        raise HTTPException(status_code=503, detail="Database error loading department document.") from exc
    if not document:
        raise HTTPException(status_code=404, detail="Document not found.")
    return {"document": document}


@app.post("/projects/{project_id}/departments/{department_id}/documents/upload", status_code=201)
async def upload_department_document_route(
    project_id: str,
    department_id: str,
    user: Annotated[dict, Depends(current_demo_user)],
    file: UploadFile = File(...),
    title: str | None = Form(None),
    access_roles: str | None = Form(None),
    restricted: bool = Form(False),
) -> dict:
    project_id = _validate_project_id(project_id)
    department_id = _validate_project_id(department_id)
    require_project_editor(user, project_id)
    safe_name = _safe_upload_name(file.filename)
    if not safe_name.lower().endswith(".pdf"):
        raise HTTPException(status_code=400, detail="Only PDF uploads are supported in this phase.")

    raw_bytes = await file.read()
    if len(raw_bytes) > MAX_UPLOAD_BYTES:
        raise HTTPException(status_code=413, detail="PDF uploads are limited to 10 MB in the local demo.")
    if not raw_bytes.startswith(b"%PDF"):
        raise HTTPException(status_code=400, detail="Uploaded file is not a valid PDF.")

    settings = get_settings()
    upload_id = str(uuid.uuid4())
    relative_path = (
        Path(settings.upload_storage_dir)
        / user["tenant_id"]
        / project_id
        / department_id
        / f"{upload_id}-{safe_name}"
    )
    storage_path = ROOT / relative_path
    storage_path.parent.mkdir(parents=True, exist_ok=True)
    storage_path.write_bytes(raw_bytes)

    document_title = (title or Path(safe_name).stem.replace("-", " ")).strip()
    external_document_id = f"UPLOAD-{upload_id[:8].upper()}"

    try:
        department = get_department(project_id, department_id)
        if not department:
            storage_path.unlink(missing_ok=True)
            raise HTTPException(status_code=404, detail="Department not found.")
        roles = _normalize_roles(access_roles.split(",")) if access_roles else list(department["default_access_roles"])
        if not roles:
            roles = ["Employee"]
        extraction = extract_pdf_to_markdown(storage_path, title=document_title)
        document = create_pending_review_document(
            project_id=project_id,
            department=department,
            external_document_id=external_document_id,
            title=document_title,
            source_path=str(relative_path).replace("\\", "/"),
            source_file_name=safe_name,
            source_file_type="pdf",
            raw_file_bytes=raw_bytes,
            access_roles=roles,
            restricted=restricted,
            extracted_markdown=extraction.markdown,
            extraction_metadata={
                "extractor": "pypdf",
                "page_count": extraction.page_count,
                "pages_with_text": extraction.pages_with_text,
                "extraction_confidence": extraction.confidence,
                "warnings": extraction.warnings,
                "review_required": True,
            },
        )
    except HTTPException:
        raise
    except PsycopgError as exc:
        storage_path.unlink(missing_ok=True)
        raise HTTPException(status_code=503, detail="Database error saving extracted document.") from exc
    except Exception as exc:
        storage_path.unlink(missing_ok=True)
        raise HTTPException(status_code=400, detail=f"PDF extraction failed: {exc}") from exc

    log_audit_event(
        action="document_uploaded_for_review",
        user_role=user["business_role"],
        user_id=user["id"],
        resource_type="document",
        document_id=document["external_document_id"],
        outcome="success",
        reason="pending_review",
        metadata={
            "project_id": project_id,
            "department_id": department_id,
            "document_id": document["id"],
            "external_document_id": document["external_document_id"],
            "source_file_name": safe_name,
            "ingestion_status": document["version"]["ingestion_status"],
        },
    )
    return {
        "document": document,
        "status": "pending_review",
        "message": "PDF extracted to Markdown for review. No chunks or embeddings were created.",
    }


@app.post("/projects/{project_id}/departments/{department_id}/documents/{document_id}/approve-index")
def approve_department_document_route(
    project_id: str,
    department_id: str,
    document_id: str,
    user: Annotated[dict, Depends(current_demo_user)],
    request: ApproveIndexRequest | None = None,
) -> dict:
    project_id = _validate_project_id(project_id)
    department_id = _validate_project_id(department_id)
    document_id = _validate_project_id(document_id)
    require_project_editor(user, project_id)
    cleanup_review_metadata: dict | None = None
    try:
        if not get_department(project_id, department_id):
            raise HTTPException(status_code=404, detail="Department not found.")
        current_document = get_project_document(
            project_id=project_id,
            department_id=department_id,
            document_id=document_id,
            include_archived=False,
        )
        if current_document:
            cleanup_metadata = (current_document.get("version", {}).get("metadata") or {}).get("ai_cleanup")
            if isinstance(cleanup_metadata, dict) and request and request.reviewed_markdown is not None:
                reviewed_hash = hash_markdown(request.reviewed_markdown.strip())
                cleanup_review_metadata = {
                    "approved_after_cleanup": True,
                    "reviewer_edited_after_cleanup": reviewed_hash != cleanup_metadata.get("cleaned_content_hash"),
                    "approved_content_hash": reviewed_hash,
                    "cleanup_cleaned_content_hash": cleanup_metadata.get("cleaned_content_hash"),
                    "cleanup_model": cleanup_metadata.get("model"),
                }
        document = approve_and_index_document(
            project_id=project_id,
            department_id=department_id,
            document_id=document_id,
            reviewed_markdown=request.reviewed_markdown if request else None,
        )
    except HTTPException:
        raise
    except ValueError as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc
    except RuntimeError as exc:
        raise HTTPException(status_code=503, detail=str(exc)) from exc
    except PsycopgError as exc:
        raise HTTPException(status_code=503, detail="Database error indexing approved document.") from exc
    if not document:
        raise HTTPException(status_code=404, detail="Document not found.")

    log_audit_event(
        action="document_approved_for_indexing",
        user_role=user["business_role"],
        user_id=user["id"],
        resource_type="document",
        document_id=document["external_document_id"],
        outcome=document["version"]["ingestion_status"],
        reason="human_review_approved",
        metadata={
            "project_id": project_id,
            "department_id": department_id,
            "document_id": document["id"],
            "external_document_id": document["external_document_id"],
            "chunk_count": document["chunk_count"],
            "ingestion_status": document["version"]["ingestion_status"],
            "ai_cleanup_review": cleanup_review_metadata,
        },
    )
    if cleanup_review_metadata:
        log_audit_event(
            action="document_markdown_cleanup_approved_indexed",
            user_role=user["business_role"],
            user_id=user["id"],
            resource_type="document",
            document_id=document["external_document_id"],
            outcome=document["version"]["ingestion_status"],
            reason="approved_indexed_after_cleanup",
            metadata={
                "project_id": project_id,
                "department_id": department_id,
                "document_id": document["id"],
                "external_document_id": document["external_document_id"],
                "chunk_count": document["chunk_count"],
                **cleanup_review_metadata,
            },
        )
    return {
        "document": document,
        "status": document["version"]["ingestion_status"],
        "message": "Approved document was indexed for scoped retrieval.",
    }


@app.post("/projects/{project_id}/departments/{department_id}/documents/{document_id}/cleanup-markdown")
def cleanup_department_document_markdown_route(
    project_id: str,
    department_id: str,
    document_id: str,
    user: Annotated[dict, Depends(current_demo_user)],
    request: CleanupMarkdownRequest | None = None,
) -> dict:
    project_id = _validate_project_id(project_id)
    department_id = _validate_project_id(department_id)
    document_id = _validate_project_id(document_id)
    require_project_editor(user, project_id)
    document = None
    try:
        if not get_department(project_id, department_id):
            raise HTTPException(status_code=404, detail="Department not found.")
        document = get_project_document(
            project_id=project_id,
            department_id=department_id,
            document_id=document_id,
            include_archived=False,
        )
        if not document:
            raise HTTPException(status_code=404, detail="Document not found.")
        if document["version"]["ingestion_status"] not in {"pending_review", "failed"}:
            raise HTTPException(status_code=400, detail="Only pending-review or failed documents can be cleaned up.")

        log_audit_event(
            action="document_markdown_cleanup_requested",
            user_role=user["business_role"],
            user_id=user["id"],
            resource_type="document",
            document_id=document["external_document_id"],
            outcome="requested",
            reason="explicit_editor_action",
            metadata={
                "project_id": project_id,
                "department_id": department_id,
                "document_id": document["id"],
                "external_document_id": document["external_document_id"],
                "source_content_hash": hash_markdown(document.get("review_markdown") or document.get("markdown_preview") or ""),
            },
        )
        cleanup = cleanup_uploaded_markdown(
            document=document,
            requested_by=user["id"],
            model=request.model if request else None,
        )
        updated_document = record_cleanup_metadata(
            project_id=project_id,
            department_id=department_id,
            document_id=document_id,
            cleanup_metadata=cleanup["metadata"],
        )
    except HTTPException:
        raise
    except ValueError as exc:
        if document:
            log_audit_event(
                action="document_markdown_cleanup_failed",
                user_role=user["business_role"],
                user_id=user["id"],
                resource_type="document",
                document_id=document["external_document_id"],
                outcome="failed",
                reason=str(exc),
                metadata={"project_id": project_id, "department_id": department_id, "document_id": document["id"]},
            )
        raise HTTPException(status_code=400, detail=str(exc)) from exc
    except RuntimeError as exc:
        if document:
            log_audit_event(
                action="document_markdown_cleanup_failed",
                user_role=user["business_role"],
                user_id=user["id"],
                resource_type="document",
                document_id=document["external_document_id"],
                outcome="failed",
                reason=str(exc),
                metadata={"project_id": project_id, "department_id": department_id, "document_id": document["id"]},
            )
        raise HTTPException(status_code=503, detail=str(exc)) from exc
    except PsycopgError as exc:
        if document:
            log_audit_event(
                action="document_markdown_cleanup_failed",
                user_role=user["business_role"],
                user_id=user["id"],
                resource_type="document",
                document_id=document["external_document_id"],
                outcome="failed",
                reason="database_error_saving_cleanup_metadata",
                metadata={"project_id": project_id, "department_id": department_id, "document_id": document["id"]},
            )
        raise HTTPException(status_code=503, detail="Database error saving cleanup metadata.") from exc
    if not updated_document:
        raise HTTPException(status_code=404, detail="Document not found.")

    metadata = cleanup["metadata"]
    log_audit_event(
        action="document_markdown_cleanup_succeeded",
        user_role=user["business_role"],
        user_id=user["id"],
        resource_type="document",
        document_id=updated_document["external_document_id"],
        outcome="draft_returned_not_indexed",
        reason="explicit_editor_action",
        metadata={
            "project_id": project_id,
            "department_id": department_id,
            "document_id": updated_document["id"],
            "external_document_id": updated_document["external_document_id"],
            "model": metadata["model"],
            "source_content_hash": metadata["source_content_hash"],
            "cleaned_content_hash": metadata["cleaned_content_hash"],
            "estimated_cost_usd": metadata["estimated_cost_usd"],
        },
    )
    return {
        "cleaned_markdown": cleanup["cleaned_markdown"],
        "document": updated_document,
        "model": metadata["model"],
        "input_tokens": metadata["input_tokens"],
        "output_tokens": metadata["output_tokens"],
        "input_cost_usd": metadata["input_cost_usd"],
        "output_cost_usd": metadata["output_cost_usd"],
        "estimated_cost_usd": metadata["estimated_cost_usd"],
        "pricing_status": metadata["pricing_status"],
        "source_content_hash": metadata["source_content_hash"],
        "cleaned_content_hash": metadata["cleaned_content_hash"],
        "cleanup_timestamp": metadata["cleanup_timestamp"],
    }


@app.post("/projects/{project_id}/departments/{department_id}/documents/{document_id}/cleanup-markdown/revert")
def revert_department_document_cleanup_route(
    project_id: str,
    department_id: str,
    document_id: str,
    user: Annotated[dict, Depends(current_demo_user)],
) -> dict:
    project_id = _validate_project_id(project_id)
    department_id = _validate_project_id(department_id)
    document_id = _validate_project_id(document_id)
    require_project_editor(user, project_id)
    try:
        if not get_department(project_id, department_id):
            raise HTTPException(status_code=404, detail="Department not found.")
        document = record_cleanup_revert_metadata(
            project_id=project_id,
            department_id=department_id,
            document_id=document_id,
            reverted_by=user["id"],
        )
    except HTTPException:
        raise
    except ValueError as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc
    except PsycopgError as exc:
        raise HTTPException(status_code=503, detail="Database error saving cleanup revert metadata.") from exc
    if not document:
        raise HTTPException(status_code=404, detail="Document not found.")

    log_audit_event(
        action="document_markdown_cleanup_reverted",
        user_role=user["business_role"],
        user_id=user["id"],
        resource_type="document",
        document_id=document["external_document_id"],
        outcome="reverted",
        reason="editor_reverted_to_deterministic_extraction",
        metadata={
            "project_id": project_id,
            "department_id": department_id,
            "document_id": document["id"],
            "external_document_id": document["external_document_id"],
            "source_content_hash": hash_markdown(document.get("review_markdown") or document.get("markdown_preview") or ""),
        },
    )
    return {"document": document, "status": "reverted"}


@app.get("/projects/{project_id}/departments/{department_id}")
def department_detail_route(
    project_id: str,
    department_id: str,
    user: Annotated[dict, Depends(current_demo_user)],
    include_archived: bool = False,
) -> dict:
    project_id = _validate_project_id(project_id)
    department_id = _validate_project_id(department_id)
    require_project_member(user, project_id)
    try:
        department = get_department(project_id, department_id, include_archived=include_archived)
    except PsycopgError as exc:
        raise HTTPException(status_code=503, detail="Database error loading department.") from exc
    if not department:
        raise HTTPException(status_code=404, detail="Department not found.")
    return {"department": department}


@app.patch("/projects/{project_id}/departments/{department_id}")
def update_department_route(
    project_id: str,
    department_id: str,
    request: DepartmentUpdateRequest,
    user: Annotated[dict, Depends(current_demo_user)],
) -> dict:
    project_id = _validate_project_id(project_id)
    department_id = _validate_project_id(department_id)
    require_project_editor(user, project_id)
    updates = request.model_dump(exclude={"user_role", "user_id"}, exclude_unset=True)
    if "name" in updates and updates["name"] is not None:
        updates["name"] = updates["name"].strip()
        if not updates["name"]:
            raise HTTPException(status_code=400, detail="Department name is required.")
    if "description" in updates and updates["description"] is not None:
        updates["description"] = updates["description"].strip()
    if "default_access_roles" in updates:
        updates["default_access_roles"] = _normalize_roles(updates["default_access_roles"])
    try:
        department = update_department_record(project_id, department_id, **updates)
    except ValueError as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc
    except PsycopgError as exc:
        raise HTTPException(status_code=503, detail="Database error updating department.") from exc
    if not department:
        raise HTTPException(status_code=404, detail="Department not found.")

    log_audit_event(
        action="department_updated",
        user_role=user["business_role"],
        user_id=user["id"],
        resource_type="department",
        document_id=department["id"],
        outcome="success",
        metadata={
            "project_id": project_id,
            "department_id": department["id"],
            "changed_fields": sorted(updates.keys()),
        },
    )
    return {"department": department}


@app.delete("/projects/{project_id}/departments/{department_id}")
def archive_department_route(
    project_id: str,
    department_id: str,
    user: Annotated[dict, Depends(current_demo_user)],
) -> dict:
    project_id = _validate_project_id(project_id)
    department_id = _validate_project_id(department_id)
    require_project_editor(user, project_id)
    try:
        department = archive_department(project_id, department_id)
    except PsycopgError as exc:
        raise HTTPException(status_code=503, detail="Database error archiving department.") from exc
    if not department:
        raise HTTPException(status_code=404, detail="Department not found.")

    log_audit_event(
        action="department_archived",
        user_role=user["business_role"],
        user_id=user["id"],
        resource_type="department",
        document_id=department["id"],
        outcome="success",
        reason="soft_delete",
        metadata={"project_id": project_id, "department_id": department["id"], "department_name": department["name"]},
    )
    return {"department": department, "status": "archived"}


@app.patch("/projects/{project_id}")
def update_project_route(project_id: str, request: ProjectUpdateRequest, user: Annotated[dict, Depends(current_demo_user)]) -> dict:
    project_id = _validate_project_id(project_id)
    require_project_editor(user, project_id)
    updates = request.model_dump(exclude={"user_role", "user_id"}, exclude_unset=True)
    if "name" in updates and updates["name"] is not None:
        updates["name"] = updates["name"].strip()
        if not updates["name"]:
            raise HTTPException(status_code=400, detail="Project name is required.")
    if "description" in updates and updates["description"] is not None:
        updates["description"] = updates["description"].strip()
    if "default_retrieval_profile" in updates and updates["default_retrieval_profile"] is not None:
        updates["default_retrieval_profile"] = updates["default_retrieval_profile"].strip()
        if not updates["default_retrieval_profile"]:
            raise HTTPException(status_code=400, detail="Default retrieval profile is required.")
    try:
        project = update_project_record(project_id, **updates)
    except ValueError as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc
    except PsycopgError as exc:
        raise HTTPException(status_code=503, detail="Database error updating project.") from exc
    if not project:
        raise HTTPException(status_code=404, detail="Project not found.")

    log_audit_event(
        action="project_updated",
        user_role=user["business_role"],
        user_id=user["id"],
        resource_type="project",
        document_id=project["id"],
        outcome="success",
        metadata={"project_id": project["id"], "changed_fields": sorted(updates.keys())},
    )
    return {"project": project}


@app.delete("/projects/{project_id}")
def archive_project_route(project_id: str, user: Annotated[dict, Depends(current_demo_user)]) -> dict:
    project_id = _validate_project_id(project_id)
    require_project_editor(user, project_id)
    try:
        project = archive_project(project_id)
    except PsycopgError as exc:
        raise HTTPException(status_code=503, detail="Database error archiving project.") from exc
    if not project:
        raise HTTPException(status_code=404, detail="Project not found.")

    log_audit_event(
        action="project_archived",
        user_role=user["business_role"],
        user_id=user["id"],
        resource_type="project",
        document_id=project["id"],
        outcome="success",
        reason="soft_delete",
        metadata={"project_id": project["id"], "project_name": project["name"]},
    )
    return {"project": project, "status": "archived"}


def _query_response_payload(
    request: QueryRequest,
    session_id: str | None,
    user_message_id: str | None,
    assistant_message_id: str | None,
    answer: dict,
    rewrite: dict,
    config,
    chunks: list,
    trace: RequestTrace,
    multi_doc: bool,
    effective_role: str,
    request_assessment: RequestAssessment,
    evidence_assessment: EvidenceAssessment | None,
) -> dict:
    defense_trace = build_defense_trace(
        request_assessment=request_assessment,
        evidence_assessment=evidence_assessment,
        post_generation_validation=answer.get("post_generation_validation"),
        answer=answer,
        authorized_chunks=chunks,
        effective_role=effective_role,
        generation_latency_ms=trace.generation_latency_ms,
    )
    return {
        "session_id": session_id,
        "user_message_id": user_message_id,
        "assistant_message_id": assistant_message_id,
        "answer": answer["answer"],
        "behavior": answer["behavior"],
        "response_type": answer["response_type"],
        "retrieval_confidence": answer["retrieval_confidence"],
        "citation_confidence": answer["citation_confidence"],
        "answer_confidence": answer["answer_confidence"],
        "final_confidence": answer["final_confidence"],
        "confidence_interpretation": _confidence_interpretation(answer["response_type"]),
        "supported_claims": answer["supported_claims"],
        "unsupported_claims": answer["unsupported_claims"],
        "validation_notes": answer["validation_notes"],
        "clarification_reason": answer.get("clarification_reason"),
        "request_assessment": request_assessment.model_dump(mode="json"),
        "evidence_assessment": evidence_assessment.model_dump(mode="json") if evidence_assessment else None,
        "post_generation_validation": answer.get("post_generation_validation"),
        "defense_trace": defense_trace.model_dump(mode="json"),
        "retrieval_mode": config.retrieval_mode,
        "chunking_strategy": config.chunking_strategy,
        "scope": {
            "project_id": config.project_id,
            "department_id": config.department_id,
        },
        "multi_doc_mode": request.multi_doc_mode,
        "multi_doc_used": multi_doc,
        "prompt_name": answer.get("prompt_name"),
        "prompt_version": answer.get("prompt_version"),
        "model": answer.get("model"),
        "temperature": answer.get("temperature"),
        "input_cost_usd": answer.get("input_cost_usd"),
        "output_cost_usd": answer.get("output_cost_usd"),
        "estimated_cost_usd": answer.get("estimated_cost_usd"),
        "pricing_status": answer.get("pricing_status"),
        "retrieval_latency_ms": trace.retrieval_latency_ms,
        "generation_latency_ms": trace.generation_latency_ms,
        "total_latency_ms": trace.total_latency_ms,
        "memory": {
            "is_followup": rewrite["is_followup"],
            "memory_used": rewrite["memory_used"],
            "original_question": rewrite["original_question"],
            "rewritten_question": rewrite["rewritten_question"],
            "rewrite_strategy": rewrite["rewrite_strategy"],
            "previous_topic": rewrite.get("previous_topic"),
        },
        "permission_check": {
            "user_role": effective_role,
            "retrieved_chunks_count": len(chunks),
            "unauthorized_chunks_reached_generation": unauthorized_chunks_reached_generation(chunks, effective_role),
        },
        "citations": answer["citations"],
        "retrieved_chunks": retrieved_chunks_payload(chunks),
    }


def _assess_before_retrieval(
    request: QueryRequest,
    *,
    project_id: str | None,
    department_id: str | None,
    rewrite: dict,
    effective_role: str,
    user_id: str | None,
    previous_turns: list[dict],
) -> tuple[RequestAssessment, dict | None]:
    assessment = assess_request(
        request.question,
        project_id=project_id,
        department_id=department_id,
        has_memory=bool(rewrite.get("memory_used")),
        rewritten_question=rewrite.get("rewritten_question"),
        previous_turns=previous_turns,
    )
    decision = assessment_response_decision(assessment)
    if assessment.recommended_action == "block":
        log_audit_event(
            action="user_prompt_override_blocked",
            user_role=effective_role,
            user_id=user_id,
            resource_type="query",
            outcome="blocked",
            reason=assessment.response_reason,
            metadata={
                "project_id": project_id,
                "department_id": department_id,
                "assessment_route": assessment.route,
                "reason_codes": list(assessment.reason_codes),
            },
        )
    elif assessment.status == "failed_safe":
        log_audit_event(
            action="request_assessment_failed_safe",
            user_role=effective_role,
            user_id=user_id,
            resource_type="query",
            outcome="blocked",
            reason=assessment.response_reason,
            metadata={
                "project_id": project_id,
                "department_id": department_id,
                "assessment_route": assessment.route,
                "reason_codes": list(assessment.reason_codes),
            },
        )
    return assessment, clarification_answer(decision) if decision else None


def _assess_after_retrieval(
    question: str,
    *,
    request_assessment: RequestAssessment,
    chunks: list,
    multi_doc: bool,
    effective_role: str,
    user_id: str | None,
    project_id: str | None,
    department_id: str | None,
) -> EvidenceAssessment:
    assessment = assess_evidence(
        question,
        request_assessment=request_assessment,
        authorized_chunks=chunks,
        multi_document=multi_doc,
    )
    if assessment.recommended_action in {"clarify", "temporary_unavailable"}:
        log_audit_event(
            action=(
                "evidence_assessment_failed_safe"
                if assessment.status == "failed_safe"
                else "authorized_evidence_conflict_detected"
            ),
            user_role=effective_role,
            user_id=user_id,
            resource_type="query",
            outcome="blocked",
            reason=evidence_response_reason(assessment),
            metadata={
                "project_id": project_id,
                "department_id": department_id,
                "assessment_route": assessment.route,
                "recommended_action": assessment.recommended_action,
                "reason_codes": list(assessment.reason_codes),
                "authorized_chunk_count": len(chunks),
            },
        )
    return assessment


def _evidence_stop_answer(assessment: EvidenceAssessment) -> dict | None:
    if assessment.recommended_action == "clarify":
        return clarification_answer(
            ClarificationDecision(
                reason="authorized_evidence_conflicting",
                question=(
                    "The accessible sources conflict on a material part of this request. "
                    "Which applicable policy, version, or time period should I use?"
                ),
            )
        )
    if assessment.recommended_action == "temporary_unavailable":
        return clarification_answer(
            ClarificationDecision(
                reason="evidence_assessment_unavailable",
                question=(
                    "I can’t safely verify whether the available evidence is sufficient right now, "
                    "so I haven’t generated an answer. Please try again."
                ),
            )
        )
    return None


def _evidence_generation_chunks(chunks: list, assessment: EvidenceAssessment) -> list:
    if assessment.recommended_action not in {"answer", "partial_answer"}:
        return []
    return list(chunks)


def _validate_generated_answer(
    question: str,
    *,
    answer: dict,
    authorized_chunks: list,
    effective_role: str,
    user_id: str | None,
    project_id: str | None,
    department_id: str | None,
    memory_context: str | None,
    original_question: str,
    prompt_name: str,
    prompt_version: str | None,
    multi_doc: bool,
    evidence_action: str | None,
) -> tuple[dict, PostGenerationValidation]:
    code_authored = answer.get("input_tokens") == 0 and answer.get("output_tokens") == 0
    first = validate_candidate_answer(
        question,
        candidate=answer,
        authorized_chunks=authorized_chunks,
        code_authored=code_authored,
    )
    final_answer = answer
    final_validation = first
    if can_prune_unsupported_citations(first):
        supported_citation_ids = {
            check.citation_chunk_id for check in first.citation_checks if check.supports_claims
        }
        final_answer = dict(answer)
        final_answer["citations"] = [
            citation
            for citation in (answer.get("citations") or [])
            if citation.get("chunk_id") in supported_citation_ids
        ]
        final_validation = mark_citation_prune_repair(first)
    elif first.action == "repair":
        try:
            repaired = repair_answer_once(
                question,
                authorized_chunks,
                candidate=answer,
                validation_reason_codes=list(first.reason_codes),
                user_role=effective_role,
                memory_context=memory_context,
                original_question=original_question,
                prompt_name=prompt_name,
                prompt_version=prompt_version,
                multi_doc=multi_doc,
                grouped_docs=group_chunks_by_document(authorized_chunks) if multi_doc else None,
                evidence_action=evidence_action,
            )
        except Exception:
            final_validation = first.model_copy(
                update={
                    "action": "downgrade",
                    "status": "failed_safe",
                    "repair_count": 1,
                    "reason_codes": list(dict.fromkeys([
                        *first.reason_codes,
                        "validator_service_error",
                        "repair_failed",
                    ])),
                }
            )
            final_answer = _validation_safe_downgrade(answer, final_validation, authorized_chunks)
        else:
            second = validate_candidate_answer(
                question,
                candidate=repaired,
                authorized_chunks=authorized_chunks,
                repair_count=1,
            )
            final_validation = combine_validation_attempts(first, second)
            if second.action == "accept":
                final_answer = _combine_generation_attempts(answer, repaired)
            else:
                final_answer = _validation_safe_downgrade(repaired, final_validation, authorized_chunks)
    elif first.action == "downgrade":
        final_answer = _validation_safe_downgrade(answer, final_validation, authorized_chunks)

    final_answer["post_generation_validation"] = final_validation.model_dump(mode="json")
    if first.action != "accept" or final_validation.status == "failed_safe":
        log_audit_event(
            action=("post_generation_validation_repaired" if final_validation.action == "accept" else "post_generation_validation_downgraded"),
            user_role=effective_role,
            user_id=user_id,
            resource_type="query",
            outcome="allowed" if final_validation.action == "accept" else "blocked",
            reason=final_validation.reason_codes[-1],
            metadata={
                "project_id": project_id,
                "department_id": department_id,
                "validation_route": final_validation.route,
                "validation_status": final_validation.status,
                "reason_codes": list(final_validation.reason_codes),
                "repair_count": final_validation.repair_count,
                "authorized_chunk_count": len(authorized_chunks),
            },
        )
    return final_answer, final_validation


def _combine_generation_attempts(first: dict, second: dict) -> dict:
    combined = dict(second)
    for key in ("input_tokens", "output_tokens", "input_cost_usd", "output_cost_usd", "estimated_cost_usd"):
        left = first.get(key)
        right = second.get(key)
        combined[key] = None if left is None and right is None else (left or 0) + (right or 0)
    combined["generation_attempt_count"] = 2
    return combined


def _validation_safe_downgrade(
    answer: dict,
    validation: PostGenerationValidation | None = None,
    authorized_chunks: list | None = None,
) -> dict:
    downgraded = dict(answer)
    supported_claims = [
        claim.claim_text
        for claim in (validation.claims if validation else [])
        if claim.support_status == "supported"
    ]
    supported_citation_ids = {
        check.citation_chunk_id
        for check in (validation.citation_checks if validation else [])
        if check.supports_claims
    }
    if supported_claims and validation and not validation.source_instruction_followed:
        citations = [
            citation
            for citation in (answer.get("citations") or [])
            if citation.get("chunk_id") in supported_citation_ids
        ]
        citation_scores = [float(citation.get("confidence") or 0.0) for citation in citations]
        citation_confidence = (
            round(sum(citation_scores) / len(citation_scores), 3)
            if citation_scores
            else 0.0
        )
        downgraded.update(
            {
                "answer": "Based on limited supporting evidence, " + " ".join(dict.fromkeys(supported_claims)),
                "response_type": "partial_answer",
                "behavior": "answer",
                "citations": citations,
                "supported_claims": list(dict.fromkeys(supported_claims)),
                "unsupported_claims": [],
                "validation_notes": "Only claims that passed post-generation validation are included.",
                **final_confidence("partial_answer", authorized_chunks or [], citation_confidence, []),
            }
        )
        return downgraded
    downgraded.update(
        {
            "answer": "I could not safely validate an answer from the available documents.",
            "response_type": "not_found",
            "behavior": "say_not_found",
            "citations": [],
            "supported_claims": [],
            "unsupported_claims": [],
            "citation_confidence": 0.0,
            "answer_confidence": 0.0,
            "confidence_label": "low",
            "validation_notes": "Post-generation validation did not pass within the one-repair limit.",
            **final_confidence("not_found", [], 0.0, []),
        }
    )
    return downgraded


@app.post("/query/stream")
def query_stream(request: QueryRequest, user: Annotated[dict, Depends(current_demo_user)]) -> StreamingResponse:
    def events():
        request_id = str(uuid.uuid4())
        request_timestamp = datetime.now(UTC).isoformat()
        trace = RequestTrace()
        chunks = []
        config = None
        effective_role = request.user_role
        multi_doc = False
        rewrite: dict = {
            "rewritten_question": request.question,
            "is_followup": False,
            "memory_used": False,
            "rewrite_strategy": None,
            "original_question": request.question,
        }
        answer: dict = {}
        request_assessment: RequestAssessment | None = None
        evidence_assessment: EvidenceAssessment | None = None
        session_id = request.session_id

        def submit_failure_telemetry(exc: BaseException) -> None:
            trace.finish()
            submit_query_telemetry(
                request_id=request_id,
                request=request,
                operation_type="rag_query_stream",
                status="failed",
                config=config,
                answer=answer,
                trace=trace,
                chunks=chunks,
                error_category=query_error_category(exc),
                error_message_redacted=redacted_error_message(exc),
            )

        try:
            yield _sse("status", {"status": "request_started", "message": "Preparing scoped query."})
            project_id = _validate_project_id(request.project_id) if request.project_id else None
            department_id = _validate_project_id(request.department_id) if request.department_id else None
            if department_id and not project_id:
                raise ValueError("Department scope requires a project scope.")
            if project_id:
                require_project_member(user, project_id)
            effective_role = _effective_query_role(request.user_role, user, project_scoped=bool(project_id))
            excluded_document_prefixes = _evaluation_excluded_document_prefixes(request, user)

            settings = get_settings()
            config = default_retrieval_config(
                retrieval_mode=request.retrieval_mode,
                chunking_strategy=request.chunking_strategy,
                top_k=request.top_k or settings.default_top_k,
                vector_weight=request.vector_weight,
                keyword_weight=request.keyword_weight,
                run_name="api-query-stream",
                project_id=project_id,
                department_id=department_id,
                excluded_document_prefixes=excluded_document_prefixes,
            )

            if project_id:
                project = get_project(project_id)
                if not project:
                    raise HTTPException(status_code=404, detail="Project not found.")
                if department_id and not get_department(project_id, department_id):
                    raise HTTPException(status_code=404, detail="Department not found.")

            previous_turns = []
            if session_id:
                session = get_session(session_id)
                if not session:
                    raise HTTPException(status_code=404, detail="Chat session not found.")
                if session.get("tenant_id") != user["tenant_id"]:
                    raise HTTPException(status_code=404, detail="Chat session not found.")
                if session.get("user_id") and session["user_id"] != user["id"]:
                    raise HTTPException(status_code=403, detail="Chat session belongs to another demo user.")
                previous_turns = list_messages(session_id)
            elif request.user_id:
                session_id = create_session(effective_role, user_id=user["id"])

            yield _sse("status", {"status": "memory_started", "message": "Checking conversation memory."})
            rewrite = rewrite_followup_question(request.question, previous_turns)
            memory_context = build_memory_context(previous_turns) if rewrite["memory_used"] else {}
            memory_text = memory_context_text(memory_context)
            retrieval_question = rewrite["rewritten_question"]
            yield _sse("status", {"status": "assessment_started", "message": "Assessing request intent and safety."})
            request_assessment, clarification = _assess_before_retrieval(
                request,
                project_id=project_id,
                department_id=department_id,
                rewrite=rewrite,
                effective_role=effective_role,
                user_id=user.get("id"),
                previous_turns=previous_turns,
            )
            yield _sse(
                "status",
                {
                    "status": "assessment_complete",
                    "message": f"Request assessment recommended {request_assessment.recommended_action}.",
                    "route": request_assessment.route,
                    "recommended_action": request_assessment.recommended_action,
                    "reason_codes": list(request_assessment.reason_codes),
                },
            )

            if clarification:
                answer = clarification
                grouped_docs = None
                multi_doc = False
            else:
                trace.start("retrieval")
                yield _sse("status", {"status": "retrieval_started", "message": "Retrieving permission-filtered context."})
                multi_doc = request.multi_doc_mode == "force" or (
                    request.multi_doc_mode == "auto" and is_multi_document_question(retrieval_question)
                )
                if multi_doc:
                    chunks = retrieve_multi_doc(retrieval_question, effective_role, config)
                    grouped_docs = group_chunks_by_document(chunks)
                else:
                    chunks = retrieve_chunks(retrieval_question, effective_role, config)
                    grouped_docs = None
                trace.stop("retrieval")
                yield _sse(
                    "status",
                    {
                        "status": "retrieval_complete",
                        "message": f"Retrieved {len(chunks)} accessible chunks.",
                        "chunk_count": len(chunks),
                    },
                )

                yield _sse(
                    "status",
                    {"status": "evidence_assessment_started", "message": "Checking accessible evidence sufficiency."},
                )
                evidence_assessment = _assess_after_retrieval(
                    retrieval_question,
                    request_assessment=request_assessment,
                    chunks=chunks,
                    multi_doc=multi_doc,
                    effective_role=effective_role,
                    user_id=user.get("id"),
                    project_id=project_id,
                    department_id=department_id,
                )
                yield _sse(
                    "status",
                    {
                        "status": "evidence_assessment_complete",
                        "message": f"Evidence assessment recommended {evidence_assessment.recommended_action}.",
                        "route": evidence_assessment.route,
                        "recommended_action": evidence_assessment.recommended_action,
                        "reason_codes": list(evidence_assessment.reason_codes),
                    },
                )
                answer = _evidence_stop_answer(evidence_assessment) or {}
                generation_chunks = _evidence_generation_chunks(chunks, evidence_assessment)
                if evidence_assessment.recommended_action == "not_found":
                    answer = generate_answer(
                        retrieval_question,
                        [],
                        user_role=effective_role,
                        prompt_name=request.prompt_name,
                        prompt_version=request.prompt_version or ("v4" if multi_doc else None),
                    )
                elif not answer:
                    trace.start("generation")
                    yield _sse("status", {"status": "generation_started", "message": "Generating answer."})
                    generation_grouped_docs = group_chunks_by_document(generation_chunks) if multi_doc else None
                    for generation_event in generate_answer_stream(
                        retrieval_question,
                        generation_chunks,
                        user_role=effective_role,
                        memory_context=memory_text,
                        original_question=request.question,
                        prompt_name=request.prompt_name,
                        prompt_version=request.prompt_version or ("v4" if multi_doc else None),
                        multi_doc=multi_doc,
                        grouped_docs=generation_grouped_docs,
                        evidence_action=evidence_generation_action(evidence_assessment),
                    ):
                        event_type = generation_event.get("type")
                        if event_type == "status":
                            yield _sse(
                                "status",
                                {
                                    "status": generation_event.get("status", "generation_status"),
                                    "message": generation_event.get("message", "Generation status updated."),
                                },
                            )
                        elif event_type == "final":
                            answer = generation_event["answer"]
                    trace.stop("generation")
                yield _sse(
                    "status",
                    {"status": "post_generation_validation_started", "message": "Validating generated claims and citations."},
                )
                answer, post_validation = _validate_generated_answer(
                    retrieval_question,
                    answer=answer,
                    authorized_chunks=generation_chunks,
                    effective_role=effective_role,
                    user_id=user.get("id"),
                    project_id=project_id,
                    department_id=department_id,
                    memory_context=memory_text,
                    original_question=request.question,
                    prompt_name=request.prompt_name,
                    prompt_version=request.prompt_version or ("v4" if multi_doc else None),
                    multi_doc=multi_doc,
                    evidence_action=evidence_generation_action(evidence_assessment),
                )
                yield _sse(
                    "status",
                    {
                        "status": "post_generation_validation_complete",
                        "message": f"Post-generation validation recommended {post_validation.action}.",
                        "action": post_validation.action,
                        "reason_codes": list(post_validation.reason_codes),
                        "repair_count": post_validation.repair_count,
                    },
                )
                yield _sse("answer_delta", {"delta": answer["answer"]})
            if not answer:
                raise RuntimeError("Streaming generation did not return a final answer.")
            if request_assessment is None:
                raise RuntimeError("Streaming query did not return a request assessment.")

            user_message_id = None
            assistant_message_id = None
            if session_id:
                user_message_id = add_message(
                    session_id=session_id,
                    role="user",
                    content=request.question,
                    metadata={
                        "rewritten_question": rewrite["rewritten_question"],
                        "is_followup": rewrite["is_followup"],
                        "memory_used": rewrite["memory_used"],
                    },
                )
                assistant_message_id = add_message(
                    session_id=session_id,
                    role="assistant",
                    content=answer["answer"],
                    response_type=answer["response_type"],
                    citations=answer["citations"],
                    confidence={
                        "retrieval_confidence": answer["retrieval_confidence"],
                        "citation_confidence": answer["citation_confidence"],
                        "answer_confidence": answer["answer_confidence"],
                        "final_confidence": answer["final_confidence"],
                    },
                    metadata={
                        "original_question": request.question,
                        "rewritten_question": rewrite["rewritten_question"],
                        "memory_used": rewrite["memory_used"],
                        "user_message_id": user_message_id,
                    },
                )

            if request.prompt_version and request.prompt_version != "v1":
                log_audit_event(
                    action="prompt_version_changed",
                    user_role=effective_role,
                    user_id=user["id"],
                    resource_type="generation",
                    outcome="success",
                    reason="non_default_prompt_version_requested",
                    metadata={"prompt_version": answer.get("prompt_version")},
                )

            trace.finish()
            log_request(
                build_request_entry(
                    request_id=request_id,
                    timestamp=request_timestamp,
                    tenant_id=user.get("tenant_id") or str(current_tenant_id()),
                    user_role=effective_role,
                    session_id=session_id,
                    question_truncated=request.question[:120],
                    rewritten_question=rewrite.get("rewritten_question"),
                    retrieval_mode=config.retrieval_mode,
                    chunking_strategy=config.chunking_strategy,
                    top_k=config.top_k,
                    project_id=config.project_id,
                    department_id=config.department_id,
                    retrieved_chunk_ids=[c.chunk_id for c in chunks],
                    retrieved_document_ids=list(dict.fromkeys(c.document_id for c in chunks)),
                    response_type=answer.get("response_type"),
                    citation_count=len(answer.get("citations") or []),
                    final_confidence=answer.get("final_confidence"),
                    retrieval_latency_ms=trace.retrieval_latency_ms,
                    generation_latency_ms=trace.generation_latency_ms,
                    total_latency_ms=trace.total_latency_ms,
                    prompt_version=answer.get("prompt_version"),
                    model=answer.get("model"),
                    input_tokens=answer.get("input_tokens"),
                    output_tokens=answer.get("output_tokens"),
                    input_cost_usd=answer.get("input_cost_usd"),
                    output_cost_usd=answer.get("output_cost_usd"),
                    estimated_cost_usd=answer.get("estimated_cost_usd"),
                    pricing_status=answer.get("pricing_status"),
                    error=None,
                )
            )
            submit_query_telemetry(
                request_id=request_id,
                request=request,
                operation_type="rag_query_stream",
                status="succeeded",
                config=config,
                answer=answer,
                trace=trace,
                chunks=chunks,
            )
            payload = _query_response_payload(
                request=request,
                session_id=session_id,
                user_message_id=user_message_id,
                assistant_message_id=assistant_message_id,
                answer=answer,
                rewrite=rewrite,
                config=config,
                chunks=chunks,
                trace=trace,
                multi_doc=multi_doc,
                effective_role=effective_role,
                request_assessment=request_assessment,
                evidence_assessment=evidence_assessment,
            )
            yield _sse("metadata", payload)
            yield _sse("complete", {"status": "complete"})
        except HTTPException as exc:
            submit_failure_telemetry(exc)
            detail = exc.detail if isinstance(exc.detail, str) else "Streaming query failed."
            yield _sse("error", {"status_code": exc.status_code, "message": detail})
        except RuntimeError as exc:
            submit_failure_telemetry(exc)
            yield _sse("error", {"status_code": 503, "message": str(exc)})
        except PsycopgError as exc:
            submit_failure_telemetry(exc)
            yield _sse("error", {"status_code": 503, "message": "Database is not ready or the baseline schema has not been applied."})
        except ValueError as exc:
            submit_failure_telemetry(exc)
            yield _sse("error", {"status_code": 400, "message": str(exc)})

    return StreamingResponse(events(), media_type="text/event-stream")


def _sse(event: str, data: dict) -> str:
    return f"event: {event}\ndata: {json.dumps(data, default=str)}\n\n"


@app.post("/query")
def query(request: QueryRequest, user: Annotated[dict, Depends(current_demo_user)]) -> dict:
    request_id = str(uuid.uuid4())
    request_timestamp = datetime.now(UTC).isoformat()
    trace = RequestTrace()
    chunks = []
    rewrite: dict = {"rewritten_question": request.question, "is_followup": False, "memory_used": False, "rewrite_strategy": None, "original_question": request.question}
    answer: dict = {}
    request_assessment: RequestAssessment | None = None
    evidence_assessment: EvidenceAssessment | None = None
    session_id = request.session_id
    project_id = _validate_project_id(request.project_id) if request.project_id else None
    department_id = _validate_project_id(request.department_id) if request.department_id else None
    if department_id and not project_id:
        raise HTTPException(status_code=400, detail="Department scope requires a project scope.")
    if project_id:
        require_project_member(user, project_id)
    effective_role = _effective_query_role(request.user_role, user, project_scoped=bool(project_id))
    excluded_document_prefixes = _evaluation_excluded_document_prefixes(request, user)

    settings = get_settings()
    config = default_retrieval_config(
        retrieval_mode=request.retrieval_mode,
        chunking_strategy=request.chunking_strategy,
        top_k=request.top_k or settings.default_top_k,
        vector_weight=request.vector_weight,
        keyword_weight=request.keyword_weight,
        run_name="api-query",
        project_id=project_id,
        department_id=department_id,
        excluded_document_prefixes=excluded_document_prefixes,
    )

    def submit_failure_telemetry(exc: BaseException) -> None:
        trace.finish()
        submit_query_telemetry(
            request_id=request_id,
            request=request,
            operation_type="rag_query",
            status="failed",
            config=config,
            answer=answer,
            trace=trace,
            chunks=chunks,
            error_category=query_error_category(exc),
            error_message_redacted=redacted_error_message(exc),
        )

    try:
        if project_id:
            project = get_project(project_id)
            if not project:
                raise HTTPException(status_code=404, detail="Project not found.")
            if department_id and not get_department(project_id, department_id):
                raise HTTPException(status_code=404, detail="Department not found.")

        previous_turns = []
        if session_id:
            session = get_session(session_id)
            if not session:
                raise HTTPException(status_code=404, detail="Chat session not found.")
            if session.get("tenant_id") != user["tenant_id"]:
                raise HTTPException(status_code=404, detail="Chat session not found.")
            if session.get("user_id") and session["user_id"] != user["id"]:
                raise HTTPException(status_code=403, detail="Chat session belongs to another demo user.")
            previous_turns = list_messages(session_id)
        elif request.user_id:
            session_id = create_session(effective_role, user_id=user["id"])

        rewrite = rewrite_followup_question(request.question, previous_turns)
        memory_context = build_memory_context(previous_turns) if rewrite["memory_used"] else {}
        memory_text = memory_context_text(memory_context)
        retrieval_question = rewrite["rewritten_question"]
        request_assessment, clarification = _assess_before_retrieval(
            request,
            project_id=project_id,
            department_id=department_id,
            rewrite=rewrite,
            effective_role=effective_role,
            user_id=user.get("id"),
            previous_turns=previous_turns,
        )

        if clarification:
            answer = clarification
            grouped_docs = None
            multi_doc = False
        else:
            trace.start("retrieval")
            multi_doc = request.multi_doc_mode == "force" or (
                request.multi_doc_mode == "auto" and is_multi_document_question(retrieval_question)
            )
            if multi_doc:
                chunks = retrieve_multi_doc(retrieval_question, effective_role, config)
                grouped_docs = group_chunks_by_document(chunks)
            else:
                chunks = retrieve_chunks(retrieval_question, effective_role, config)
                grouped_docs = None
            trace.stop("retrieval")

            evidence_assessment = _assess_after_retrieval(
                retrieval_question,
                request_assessment=request_assessment,
                chunks=chunks,
                multi_doc=multi_doc,
                effective_role=effective_role,
                user_id=user.get("id"),
                project_id=project_id,
                department_id=department_id,
            )
            answer = _evidence_stop_answer(evidence_assessment) or {}
            generation_chunks = _evidence_generation_chunks(chunks, evidence_assessment)
            if evidence_assessment.recommended_action == "not_found":
                answer = generate_answer(
                    retrieval_question,
                    [],
                    user_role=effective_role,
                    prompt_name=request.prompt_name,
                    prompt_version=request.prompt_version or ("v4" if multi_doc else None),
                )
            elif not answer:
                trace.start("generation")
                generation_grouped_docs = group_chunks_by_document(generation_chunks) if multi_doc else None
                answer = generate_answer(
                    retrieval_question,
                    generation_chunks,
                    user_role=effective_role,
                    memory_context=memory_text,
                    original_question=request.question,
                    prompt_name=request.prompt_name,
                    prompt_version=request.prompt_version or ("v4" if multi_doc else None),
                    multi_doc=multi_doc,
                    grouped_docs=generation_grouped_docs,
                    evidence_action=evidence_generation_action(evidence_assessment),
                )
                trace.stop("generation")
            answer, _post_validation = _validate_generated_answer(
                retrieval_question,
                answer=answer,
                authorized_chunks=generation_chunks,
                effective_role=effective_role,
                user_id=user.get("id"),
                project_id=project_id,
                department_id=department_id,
                memory_context=memory_text,
                original_question=request.question,
                prompt_name=request.prompt_name,
                prompt_version=request.prompt_version or ("v4" if multi_doc else None),
                multi_doc=multi_doc,
                evidence_action=evidence_generation_action(evidence_assessment),
            )
    except HTTPException as exc:
        submit_failure_telemetry(exc)
        raise
    except RuntimeError as exc:
        submit_failure_telemetry(exc)
        raise HTTPException(status_code=503, detail=str(exc)) from exc
    except PsycopgError as exc:
        submit_failure_telemetry(exc)
        raise HTTPException(status_code=503, detail="Database is not ready or the baseline schema has not been applied.") from exc
    except ValueError as exc:
        submit_failure_telemetry(exc)
        raise HTTPException(status_code=400, detail=str(exc)) from exc

    user_message_id = None
    assistant_message_id = None
    if request_assessment is None:
        raise HTTPException(status_code=503, detail="Request assessment did not complete.")
    if session_id:
        user_message_id = add_message(
            session_id=session_id,
            role="user",
            content=request.question,
            metadata={
                "rewritten_question": rewrite["rewritten_question"],
                "is_followup": rewrite["is_followup"],
                "memory_used": rewrite["memory_used"],
            },
        )
        assistant_message_id = add_message(
            session_id=session_id,
            role="assistant",
            content=answer["answer"],
            response_type=answer["response_type"],
            citations=answer["citations"],
            confidence={
                "retrieval_confidence": answer["retrieval_confidence"],
                "citation_confidence": answer["citation_confidence"],
                "answer_confidence": answer["answer_confidence"],
                "final_confidence": answer["final_confidence"],
            },
            metadata={
                "original_question": request.question,
                "rewritten_question": rewrite["rewritten_question"],
                "memory_used": rewrite["memory_used"],
                "user_message_id": user_message_id,
            },
        )

    if request.prompt_version and request.prompt_version != "v1":
        log_audit_event(
            action="prompt_version_changed",
            user_role=effective_role,
            user_id=user["id"],
            resource_type="generation",
            outcome="success",
            reason="non_default_prompt_version_requested",
            metadata={"prompt_version": answer.get("prompt_version")},
        )

    trace.finish()
    log_request(
        build_request_entry(
            request_id=request_id,
            timestamp=request_timestamp,
            tenant_id=user.get("tenant_id") or str(current_tenant_id()),
            user_role=effective_role,
            session_id=session_id,
            question_truncated=request.question[:120],
            rewritten_question=rewrite.get("rewritten_question"),
            retrieval_mode=config.retrieval_mode,
            chunking_strategy=config.chunking_strategy,
            top_k=config.top_k,
            project_id=config.project_id,
            department_id=config.department_id,
            retrieved_chunk_ids=[c.chunk_id for c in chunks],
            retrieved_document_ids=list(dict.fromkeys(c.document_id for c in chunks)),
            response_type=answer.get("response_type"),
            citation_count=len(answer.get("citations") or []),
            final_confidence=answer.get("final_confidence"),
            retrieval_latency_ms=trace.retrieval_latency_ms,
            generation_latency_ms=trace.generation_latency_ms,
            total_latency_ms=trace.total_latency_ms,
            prompt_version=answer.get("prompt_version"),
            model=answer.get("model"),
            input_tokens=answer.get("input_tokens"),
            output_tokens=answer.get("output_tokens"),
            input_cost_usd=answer.get("input_cost_usd"),
            output_cost_usd=answer.get("output_cost_usd"),
            estimated_cost_usd=answer.get("estimated_cost_usd"),
            pricing_status=answer.get("pricing_status"),
            error=None,
        )
    )
    submit_query_telemetry(
        request_id=request_id,
        request=request,
        operation_type="rag_query",
        status="succeeded",
        config=config,
        answer=answer,
        trace=trace,
        chunks=chunks,
    )

    defense_trace = build_defense_trace(
        request_assessment=request_assessment,
        evidence_assessment=evidence_assessment,
        post_generation_validation=answer.get("post_generation_validation"),
        answer=answer,
        authorized_chunks=chunks,
        effective_role=effective_role,
        generation_latency_ms=trace.generation_latency_ms,
    )
    return {
        "session_id": session_id,
        "user_message_id": user_message_id,
        "assistant_message_id": assistant_message_id,
        "answer": answer["answer"],
        "behavior": answer["behavior"],
        "response_type": answer["response_type"],
        "retrieval_confidence": answer["retrieval_confidence"],
        "citation_confidence": answer["citation_confidence"],
        "answer_confidence": answer["answer_confidence"],
        "final_confidence": answer["final_confidence"],
        "supported_claims": answer["supported_claims"],
        "unsupported_claims": answer["unsupported_claims"],
        "validation_notes": answer["validation_notes"],
        "clarification_reason": answer.get("clarification_reason"),
        "request_assessment": request_assessment.model_dump(mode="json"),
        "evidence_assessment": evidence_assessment.model_dump(mode="json") if evidence_assessment else None,
        "post_generation_validation": answer.get("post_generation_validation"),
        "defense_trace": defense_trace.model_dump(mode="json"),
        "retrieval_mode": config.retrieval_mode,
        "chunking_strategy": config.chunking_strategy,
        "scope": {
            "project_id": config.project_id,
            "department_id": config.department_id,
        },
        "multi_doc_mode": request.multi_doc_mode,
        "multi_doc_used": multi_doc,
        "prompt_name": answer.get("prompt_name"),
        "prompt_version": answer.get("prompt_version"),
        "model": answer.get("model"),
        "temperature": answer.get("temperature"),
        "input_cost_usd": answer.get("input_cost_usd"),
        "output_cost_usd": answer.get("output_cost_usd"),
        "estimated_cost_usd": answer.get("estimated_cost_usd"),
        "pricing_status": answer.get("pricing_status"),
        "retrieval_latency_ms": trace.retrieval_latency_ms,
        "generation_latency_ms": trace.generation_latency_ms,
        "total_latency_ms": trace.total_latency_ms,
        "memory": {
            "is_followup": rewrite["is_followup"],
            "memory_used": rewrite["memory_used"],
            "original_question": rewrite["original_question"],
            "rewritten_question": rewrite["rewritten_question"],
            "rewrite_strategy": rewrite["rewrite_strategy"],
            "previous_topic": rewrite.get("previous_topic"),
        },
        "permission_check": {
            "user_role": effective_role,
            "retrieved_chunks_count": len(chunks),
            "unauthorized_chunks_reached_generation": unauthorized_chunks_reached_generation(chunks, effective_role),
        },
        "citations": answer["citations"],
        "retrieved_chunks": retrieved_chunks_payload(chunks),
    }
