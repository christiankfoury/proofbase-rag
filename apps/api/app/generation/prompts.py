from apps.api.app.retrieval.types import RetrievedChunk
from apps.api.app.prompts.prompt_registry import get_prompt


ANSWER_SYSTEM_PROMPT = get_prompt("answer_generation", "v1").content


def format_context(chunks: list[RetrievedChunk]) -> str:
    blocks = []
    for chunk in chunks:
        blocks.append(
            "\n".join(
                [
                    f"Document ID: {chunk.document_id}",
                    f"Title: {chunk.document_title}",
                    f"Section: {chunk.section_heading}",
                    f"Chunk ID: {chunk.chunk_id}",
                    f"Rank: {chunk.rank}",
                    f"Retrieval Score: {chunk.score:.4f}",
                    "Content:",
                    chunk.content,
                ]
            )
        )
    return "\n\n---\n\n".join(blocks)


def build_answer_user_prompt(
    question: str,
    chunks: list[RetrievedChunk],
    memory_context: str | None = None,
    original_question: str | None = None,
) -> str:
    parts = []
    if original_question and original_question != question:
        parts.append(f"Original user question:\n{original_question}")
        parts.append(f"Standalone retrieval question:\n{question}")
    else:
        parts.append(f"Question:\n{question}")
    if memory_context:
        parts.append(f"Conversation memory for query clarification only:\n{memory_context}")
    parts.append(f"Retrieved context:\n{format_context(chunks)}")
    return "\n\n".join(parts)
