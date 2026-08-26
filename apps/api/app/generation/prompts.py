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


def format_context_grouped(grouped_docs: list[dict]) -> str:
    sections = []
    for group in grouped_docs:
        header = f"=== Document: {group['document_id']} — {group['document_title']} ==="
        chunk_blocks = []
        for chunk in group["chunks"]:
            chunk_blocks.append(
                "\n".join(
                    [
                        f"[Section: {chunk.section_heading}]",
                        f"Chunk ID: {chunk.chunk_id}",
                        f"Score: {chunk.score:.4f}",
                        "Content:",
                        chunk.content,
                    ]
                )
            )
        sections.append(header + "\n\n" + "\n\n".join(chunk_blocks))
    return "\n\n".join(sections)


def build_multi_doc_user_prompt(
    question: str,
    grouped_docs: list[dict],
    memory_context: str | None = None,
    original_question: str | None = None,
    evidence_action: str | None = None,
) -> str:
    parts = []
    if original_question and original_question != question:
        parts.append(f"Original user question:\n{original_question}")
        parts.append(f"Standalone retrieval question:\n{question}")
    else:
        parts.append(f"Question:\n{question}")
    if memory_context:
        parts.append(f"Conversation memory for query clarification only:\n{memory_context}")
    if evidence_action == "partial_answer":
        parts.append(
            "Evidence sufficiency control: only a supported subset is available. "
            "Answer only that supported subset, state generically what remains unsupported, "
            "and return response_type `partial_answer`."
        )
    parts.append(f"Retrieved context (grouped by document):\n{format_context_grouped(grouped_docs)}")
    return "\n\n".join(parts)


def build_answer_user_prompt(
    question: str,
    chunks: list[RetrievedChunk],
    memory_context: str | None = None,
    original_question: str | None = None,
    evidence_action: str | None = None,
) -> str:
    parts = []
    if original_question and original_question != question:
        parts.append(f"Original user question:\n{original_question}")
        parts.append(f"Standalone retrieval question:\n{question}")
    else:
        parts.append(f"Question:\n{question}")
    if memory_context:
        parts.append(f"Conversation memory for query clarification only:\n{memory_context}")
    if evidence_action == "partial_answer":
        parts.append(
            "Evidence sufficiency control: only a supported subset is available. "
            "Answer only that supported subset, state generically what remains unsupported, "
            "and return response_type `partial_answer`."
        )
    parts.append(f"Retrieved context:\n{format_context(chunks)}")
    return "\n\n".join(parts)
