import json
import uuid
from datetime import UTC, datetime
from pathlib import Path

from fastapi import FastAPI, HTTPException
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


app = FastAPI(title="Enterprise Knowledge Agent API")

ROOT = Path(__file__).resolve().parents[3]
DASHBOARD_DATA_PATH = ROOT / "data/evaluation/dashboard-summary.json"


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
        multi_doc = is_multi_document_question(retrieval_question)
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
        "prompt_name": answer.get("prompt_name"),
        "prompt_version": answer.get("prompt_version"),
        "model": answer.get("model"),
        "temperature": answer.get("temperature"),
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
