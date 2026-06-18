import json
import uuid
from datetime import UTC, datetime
from pathlib import Path

from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from psycopg import Error as PsycopgError
from pydantic import BaseModel, Field

from apps.api.app.audit.audit_logger import audit_summary as get_audit_summary
from apps.api.app.audit.audit_logger import list_audit_events, log_audit_event
from apps.api.app.core.config import get_settings
from apps.api.app.db.session import get_connection
from apps.api.app.feedback.feedback_store import feedback_summary as get_feedback_summary
from apps.api.app.feedback.feedback_store import list_feedback, submit_feedback
from apps.api.app.generation.answer_generator import generate_answer, retrieved_chunks_payload
from apps.api.app.memory.context_builder import build_memory_context, memory_context_text
from apps.api.app.memory.query_rewriter import rewrite_followup_question
from apps.api.app.memory.session_store import add_message, create_session, get_session, list_messages
from apps.api.app.observability.logger import build_request_entry, log_request
from apps.api.app.observability.summary import compute_live_summary
from apps.api.app.observability.tracing import RequestTrace
from apps.api.app.permissions.access_control import unauthorized_chunks_reached_generation
from apps.api.app.reasoning.evidence_grouper import group_chunks_by_document
from apps.api.app.reasoning.multi_doc_detector import is_multi_document_question
from apps.api.app.reasoning.query_decomposer import retrieve_multi_doc
from apps.api.app.retrieval.config import default_retrieval_config
from apps.api.app.retrieval.retriever import retrieve_chunks


ROOT = Path(__file__).resolve().parents[3]
DASHBOARD_DATA_PATH = ROOT / "data/evaluation/dashboard-summary.json"
BENCHMARK_PATH = ROOT / "data/evaluation/benchmark-questions.json"
FAILED_QUESTIONS_PATH = ROOT / "data/evaluation/failed-questions/failed-questions.json"
PROMPT_EXPERIMENT_DIR = ROOT / "data/evaluation/prompt-experiments"
MULTI_DOC_EVAL_PATH = ROOT / "data/evaluation/multi-doc-eval.json"


def _cors_origins() -> list[str]:
    settings = get_settings()
    return [origin.strip() for origin in settings.cors_allowed_origins.split(",") if origin.strip()]


app = FastAPI(title="Enterprise Knowledge Agent API")
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
    retrieval_mode: str = "vector_only"
    chunking_strategy: str = "section_based"
    vector_weight: float = 0.5
    keyword_weight: float = 0.5
    prompt_name: str = "answer_generation"
    prompt_version: str | None = None
    multi_doc_mode: str = Field("auto", pattern="^(auto|off|force)$")


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
        "documents",
        "document_versions",
        "chunks",
        "chunk_embeddings",
        "audit_logs",
        "chat_sessions",
        "chat_messages",
        "feedback",
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


@app.post("/chat/sessions")
def create_chat_session(request: CreateSessionRequest) -> dict:
    session_id = create_session(request.user_role, user_id=request.user_id)
    return {"session_id": session_id, "user_role": request.user_role}


@app.get("/evaluation/summary")
def evaluation_summary() -> dict:
    data = _load_dashboard_data()
    return {
        "generated_at": data["generated_at"],
        "overview": data["overview"],
        "run_count": len(data["runs"]),
        "failed_question_count": len(data["failed_questions"]),
        "notes": data["notes"],
    }


@app.get("/evaluation/runs")
def evaluation_runs() -> dict:
    data = _load_dashboard_data()
    return {
        "runs": [
            {
                "run_id": run["run_id"],
                "run_name": run["run_name"],
                "phase": run["phase"],
                "run_type": run["run_type"],
                "timestamp": run["timestamp"],
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
def evaluation_run_detail(run_id: str) -> dict:
    data = _load_dashboard_data()
    for run in data["runs"]:
        if run["run_id"] == run_id:
            return run
    raise HTTPException(status_code=404, detail="Evaluation run not found.")


@app.get("/evaluation/runs/{run_id}/questions")
def evaluation_run_questions(run_id: str) -> dict:
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
def evaluation_compare() -> dict:
    data = _load_dashboard_data()
    return {
        "overview": data["overview"],
        "comparisons": data["comparisons"],
        "prompt_comparison": data.get("prompt_comparison", {}),
        "multi_doc_comparison": data.get("multi_doc_comparison", {}),
        "runs": data["runs"],
    }


@app.get("/evaluation/failed-questions")
def evaluation_failed_questions() -> dict:
    data = _load_dashboard_data()
    return {"failed_questions": data["failed_questions"]}


@app.get("/evaluation/failed-questions/enriched")
def evaluation_failed_questions_enriched() -> dict:
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


@app.post("/feedback")
def post_feedback(request: FeedbackRequest) -> dict:
    try:
        feedback_id = submit_feedback(
            session_id=request.session_id,
            message_id=request.message_id,
            question=request.question,
            answer=request.answer,
            response_type=request.response_type,
            citations=request.citations,
            user_role=request.user_role,
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
        user_role=request.user_role,
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
    rating: str | None = None,
    feedback_category: str | None = None,
    limit: int = 50,
) -> dict:
    items = list_feedback(rating=rating, feedback_category=feedback_category, limit=limit)
    return {"feedback": items, "count": len(items)}


@app.get("/feedback/summary")
def feedback_summary_route() -> dict:
    return get_feedback_summary()


@app.get("/observability/summary")
def observability_summary() -> dict:
    return compute_live_summary(limit=20)


@app.get("/observability/recent-requests")
def recent_requests_route(limit: int = 20) -> dict:
    return compute_live_summary(limit=limit)


@app.get("/audit/events")
def audit_events(
    action: str | None = None,
    outcome: str | None = None,
    limit: int = 20,
) -> dict:
    events = list_audit_events(action=action, outcome=outcome, limit=limit)
    return {"events": events, "count": len(events)}


@app.get("/audit/summary")
def audit_summary_route() -> dict:
    return get_audit_summary()


@app.post("/query")
def query(request: QueryRequest) -> dict:
    request_id = str(uuid.uuid4())
    request_timestamp = datetime.now(UTC).isoformat()
    trace = RequestTrace()
    chunks = []
    rewrite: dict = {"rewritten_question": request.question, "is_followup": False, "memory_used": False, "rewrite_strategy": None, "original_question": request.question}
    answer: dict = {}
    session_id = request.session_id

    settings = get_settings()
    config = default_retrieval_config(
        retrieval_mode=request.retrieval_mode,
        chunking_strategy=request.chunking_strategy,
        top_k=request.top_k or settings.default_top_k,
        vector_weight=request.vector_weight,
        keyword_weight=request.keyword_weight,
        run_name="api-query",
    )
    try:
        previous_turns = []
        if session_id:
            session = get_session(session_id)
            if not session:
                raise HTTPException(status_code=404, detail="Chat session not found.")
            previous_turns = list_messages(session_id)
        elif request.user_id:
            session_id = create_session(request.user_role, user_id=request.user_id)

        rewrite = rewrite_followup_question(request.question, previous_turns)
        memory_context = build_memory_context(previous_turns) if rewrite["memory_used"] else {}
        memory_text = memory_context_text(memory_context)
        retrieval_question = rewrite["rewritten_question"]

        trace.start("retrieval")
        multi_doc = request.multi_doc_mode == "force" or (
            request.multi_doc_mode == "auto" and is_multi_document_question(retrieval_question)
        )
        if multi_doc:
            chunks = retrieve_multi_doc(retrieval_question, request.user_role, config)
            grouped_docs = group_chunks_by_document(chunks)
        else:
            chunks = retrieve_chunks(retrieval_question, request.user_role, config)
            grouped_docs = None
        trace.stop("retrieval")

        trace.start("generation")
        answer = generate_answer(
            retrieval_question,
            chunks,
            user_role=request.user_role,
            memory_context=memory_text,
            original_question=request.question,
            prompt_name=request.prompt_name,
            prompt_version=request.prompt_version or ("v4" if multi_doc else None),
            multi_doc=multi_doc,
            grouped_docs=grouped_docs,
        )
        trace.stop("generation")
    except RuntimeError as exc:
        raise HTTPException(status_code=503, detail=str(exc)) from exc
    except PsycopgError as exc:
        raise HTTPException(status_code=503, detail="Database is not ready or the baseline schema has not been applied.") from exc
    except ValueError as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc

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
            user_role=request.user_role,
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
            user_role=request.user_role,
            session_id=session_id,
            question_truncated=request.question[:120],
            rewritten_question=rewrite.get("rewritten_question"),
            retrieval_mode=config.retrieval_mode,
            chunking_strategy=config.chunking_strategy,
            top_k=config.top_k,
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
        "retrieval_mode": config.retrieval_mode,
        "chunking_strategy": config.chunking_strategy,
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
            "user_role": request.user_role,
            "retrieved_chunks_count": len(chunks),
            "unauthorized_chunks_reached_generation": unauthorized_chunks_reached_generation(chunks, request.user_role),
        },
        "citations": answer["citations"],
        "retrieved_chunks": retrieved_chunks_payload(chunks),
    }
