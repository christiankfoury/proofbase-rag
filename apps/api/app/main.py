from fastapi import FastAPI, HTTPException
from psycopg import Error as PsycopgError
from pydantic import BaseModel, Field

from apps.api.app.core.config import get_settings
from apps.api.app.generation.answer_generator import generate_answer, retrieved_chunks_payload
from apps.api.app.memory.context_builder import build_memory_context, memory_context_text
from apps.api.app.memory.query_rewriter import rewrite_followup_question
from apps.api.app.memory.session_store import add_message, create_session, get_session, list_messages
from apps.api.app.permissions.access_control import unauthorized_chunks_reached_generation
from apps.api.app.retrieval.config import default_retrieval_config
from apps.api.app.retrieval.retriever import retrieve_chunks


app = FastAPI(title="Enterprise Knowledge Agent API")


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


class CreateSessionRequest(BaseModel):
    user_role: str = "Employee"
    user_id: str | None = None


@app.get("/health")
def health() -> dict:
    return {"status": "ok"}


@app.post("/chat/sessions")
def create_chat_session(request: CreateSessionRequest) -> dict:
    session_id = create_session(request.user_role, user_id=request.user_id)
    return {"session_id": session_id, "user_role": request.user_role}


@app.post("/query")
def query(request: QueryRequest) -> dict:
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
        session_id = request.session_id
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
        chunks = retrieve_chunks(retrieval_question, request.user_role, config)
        answer = generate_answer(
            retrieval_question,
            chunks,
            user_role=request.user_role,
            memory_context=memory_text,
            original_question=request.question,
        )
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
