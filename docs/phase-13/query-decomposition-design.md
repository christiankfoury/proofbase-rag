# Phase 13: Query Decomposition Design

## Approach

Lightweight LLM-based decomposition using one GPT-4.1-mini call per multi-doc question.

## Function

```python
def decompose_question(question: str, model: str = "gpt-4.1-mini") -> list[str]
```

**System prompt:**
> You are a search query decomposer for an enterprise knowledge assistant. Given a question that requires information from multiple source documents, generate 2 to 3 specific search queries — one per required document domain. Return only a valid JSON array of query strings, nothing else.

**Example:**

Input:
> "If I work remotely, what approval and device security expectations apply?"

Output:
```json
["What is the manager approval process for remote work?", "What device security rules apply to remote workers?"]
```

## Fallback

Any exception (JSON parse failure, API timeout, rate limit) returns `[question]` — the original question as a single-element list. This ensures the multi-doc retrieval path always produces results even if decomposition fails.

## Usage

`decompose_question()` is called inside `retrieve_multi_doc()`. It is not exposed directly to `main.py`. The routing decision (is_multi_document_question) and the retrieval orchestration (retrieve_multi_doc) are the public API.

## Why LLM vs Heuristic for Decomposition

Heuristic detection (is_multi_document_question) is sufficient to identify that a question needs multiple documents. But generating the right subqueries for each domain requires understanding the question's intent — a small LLM call is more reliable than hand-coded rewrite rules for this task.

The decomposition call is cheap (short prompt, single completion, temperature=0) and only fires when multi-doc is detected.

## Cost Implications

One extra GPT-4.1-mini call per detected multi-doc question. At roughly 100-200 input tokens per decomposition call, this adds minimal cost to what is already an LLM-heavy operation.
