from fastapi import FastAPI, HTTPException
from psycopg import Error as PsycopgError
from pydantic import BaseModel, Field

from apps.api.app.core.config import get_settings
from apps.api.app.generation.answer_generator import generate_answer, retrieved_chunks_payload
from apps.api.app.retrieval.config import default_retrieval_config
from apps.api.app.retrieval.retriever import retrieve_chunks


app = FastAPI(title="Enterprise Knowledge Agent API")


class QueryRequest(BaseModel):
    question: str = Field(..., min_length=1)
    user_role: str = "Employee"
    top_k: int | None = None
    retrieval_mode: str = "vector_only"
    chunking_strategy: str = "section_based"
    vector_weight: float = 0.5
    keyword_weight: float = 0.5


@app.get("/health")
def health() -> dict:
    return {"status": "ok"}


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
        chunks = retrieve_chunks(request.question, request.user_role, config)
        answer = generate_answer(request.question, chunks)
    except RuntimeError as exc:
        raise HTTPException(status_code=503, detail=str(exc)) from exc
    except PsycopgError as exc:
        raise HTTPException(status_code=503, detail="Database is not ready or the baseline schema has not been applied.") from exc
    except ValueError as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc
    return {
        "answer": answer["answer"],
        "behavior": answer["behavior"],
        "retrieval_mode": config.retrieval_mode,
        "chunking_strategy": config.chunking_strategy,
        "citations": answer["citations"],
        "retrieved_chunks": retrieved_chunks_payload(chunks),
    }
