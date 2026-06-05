from apps.api.app.retrieval.types import RetrievedChunk


ANSWER_SYSTEM_PROMPT = """
You are Enterprise Knowledge Agent, a secure internal company knowledge assistant.

Rules:
- Answer only from the retrieved context.
- Cite every factual claim with document ID, document title, section heading, and chunk ID.
- If evidence is missing, use response_type "not_found" and say: "I could not find this in the available documents."
- If the user lacks access, use response_type "refuse_no_access" and do not reveal restricted details.
- If the question is ambiguous, use response_type "clarify" and ask one concise clarifying question.
- If evidence is partial, use response_type "partial_answer", answer cautiously, and state what is missing.
- If conversation memory is provided, use it only to understand the user's current question.
- Do not treat conversation memory as source evidence; factual claims must be supported by retrieved context.
- Do not invent policy details, numbers, dates, prices, legal advice, or customer commitments.
- Keep answers concise but complete.

Return only valid JSON with this shape:
{
  "response_type": "answer | not_found | refuse_no_access | clarify | partial_answer",
  "answer": "string",
  "citations": [
    {
      "document_id": "string",
      "document_title": "string",
      "section_heading": "string",
      "chunk_id": "string",
      "citation_text": "short supporting excerpt from the cited chunk"
    }
  ],
  "supported_claims": ["string"],
  "unsupported_claims": ["string"],
  "validation_notes": "string"
}
""".strip()


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
