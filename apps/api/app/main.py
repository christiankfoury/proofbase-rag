from fastapi import FastAPI
from pydantic import BaseModel, Field

from apps.api.app.core.config import get_settings
from apps.api.app.generation.answer_generator import generate_answer, retrieved_chunks_payload
from apps.api.app.retrieval.vector_retriever import retrieve_chunks


app = FastAPI(title="Enterprise Knowledge Agent API")


class QueryRequest(BaseModel):
    question: str = Field(..., min_length=1)
    user_role: str = "Employee"
    top_k: int | None = None


@app.get("/health")
def health() -> dict:
    return {"status": "ok"}


@app.post("/query")
def query(request: QueryRequest) -> dict:
    settings = get_settings()
    top_k = request.top_k or settings.default_top_k
    chunks = retrieve_chunks(request.question, request.user_role, top_k)
    answer = generate_answer(request.question, chunks)
    return {
        "answer": answer["answer"],
        "behavior": answer["behavior"],
        "citations": answer["citations"],
        "retrieved_chunks": retrieved_chunks_payload(chunks),
    }
