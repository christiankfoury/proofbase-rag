import { demoAuthHeaders } from "@/lib/demoAuth";

export const API_BASE = process.env.NEXT_PUBLIC_API_BASE_URL ?? "http://127.0.0.1:8000";

export type UserRole = "Employee" | "Sales Representative" | "Manager" | "HR Admin" | "IT Admin";
export type RetrievalMode = "vector_only" | "keyword_only" | "hybrid";
export type MultiDocMode = "auto" | "off" | "force";

export type Citation = {
  document_id?: string;
  document_title?: string;
  section_heading?: string;
  chunk_id?: string;
  citation_text?: string;
  citation_type?: string;
  confidence?: number | null;
};

export type RetrievedChunk = {
  rank?: number | null;
  document_id: string;
  document_title: string;
  project_id?: string | null;
  department_id?: string | null;
  section_heading: string;
  chunk_id: string;
  score?: number | null;
  vector_score?: number | null;
  keyword_score?: number | null;
  hybrid_score?: number | null;
  retrieval_source?: string | null;
  access_roles?: string[] | null;
  sensitivity?: string | null;
  content_preview?: string;
};

export type QueryRequest = {
  question: string;
  user_role?: UserRole | string;
  session_id?: string | null;
  user_id?: string | null;
  top_k?: number | null;
  retrieval_mode?: RetrievalMode;
  chunking_strategy?: string;
  vector_weight?: number;
  keyword_weight?: number;
  prompt_name?: string;
  prompt_version?: string | null;
  multi_doc_mode?: MultiDocMode;
  project_id?: string | null;
  department_id?: string | null;
};

export type QueryResponse = {
  session_id: string | null;
  user_message_id: string | null;
  assistant_message_id: string | null;
  answer: string;
  behavior: string;
  response_type: string;
  retrieval_confidence: number;
  citation_confidence: number;
  answer_confidence: number;
  final_confidence: number;
  confidence_interpretation?: "answer_support" | "response_behavior";
  supported_claims: string[];
  unsupported_claims: string[];
  validation_notes: string;
  clarification_reason?: string | null;
  retrieval_mode: string;
  chunking_strategy: string;
  scope?: {
    project_id?: string | null;
    department_id?: string | null;
  };
  multi_doc_mode?: string;
  multi_doc_used?: boolean;
  prompt_name?: string | null;
  prompt_version?: string | null;
  model?: string | null;
  temperature?: number | null;
  input_cost_usd?: number | null;
  output_cost_usd?: number | null;
  estimated_cost_usd?: number | null;
  pricing_status?: string | null;
  retrieval_latency_ms?: number | null;
  generation_latency_ms?: number | null;
  total_latency_ms?: number | null;
  memory: {
    is_followup: boolean;
    memory_used: boolean;
    original_question: string;
    rewritten_question: string;
    rewrite_strategy?: string | null;
    previous_topic?: string | null;
  };
  permission_check: {
    user_role: string;
    retrieved_chunks_count: number;
    unauthorized_chunks_reached_generation: boolean;
  };
  citations: Citation[];
  retrieved_chunks: RetrievedChunk[];
};

export type RunQuestionRow = Record<string, unknown> & {
  question_id: string;
  question?: string;
  question_type?: string;
  expected_behavior?: string;
  expected_answer?: string;
  expected_source_document?: string[];
  actual_response_type?: string;
  actual_answer?: string;
  actual_citations?: Citation[];
  answer_accuracy?: number | null;
  citation_accuracy?: number | null;
  failure_type?: string | null;
  confidence?: number | null;
  final_confidence?: number | null;
  recommended_fix?: string | null;
  passed?: boolean;
};

export type RunQuestionResponse = {
  run: Record<string, unknown> | null;
  run_id: string;
  detail_available: boolean;
  detail_source: string | null;
  row_count: number;
  rows: RunQuestionRow[];
  message: string | null;
};

export type EnrichedFailure = {
  phase: string;
  question_id: string;
  expected_behavior?: string;
  actual_response_type?: string;
  failure_type: string;
  citation_confidence?: number | null;
  answer_confidence?: number | null;
  recommended_fix?: string;
  question?: string;
  question_type?: string;
  user_role?: string;
  expected_answer?: string;
  expected_source_document?: string[];
  expected_source_section_or_quote?: Array<Record<string, unknown>>;
  actual_answer?: string;
  actual_citations?: Citation[];
  actual_citation_documents?: string[];
  citation_failure_categories?: string[];
  citation_failure_labels?: string[];
  missing_citation_documents?: string[];
  unexpected_citation_documents?: string[];
  restricted_citation_documents?: string[];
  retrieved_documents?: string[];
  retrieved_chunks?: RetrievedChunk[];
  confidence?: number | null;
  known_open_issue?: boolean;
  known_open_issue_note?: string | null;
};

async function requestJson<T>(path: string, options?: RequestInit): Promise<T> {
  const response = await fetch(`${API_BASE}${path}`, {
    ...options,
    headers: {
      "Content-Type": "application/json",
      ...demoAuthHeaders(),
      ...(options?.headers ?? {}),
    },
  });
  if (!response.ok) {
    const detail = await response.text();
    throw new Error(detail || `Request failed with ${response.status}`);
  }
  return response.json();
}

export async function queryRag(payload: QueryRequest): Promise<QueryResponse> {
  return requestJson<QueryResponse>("/query", {
    method: "POST",
    body: JSON.stringify(payload),
  });
}

export type QueryStreamHandlers = {
  onStatus?: (status: string, message?: string) => void;
  onDelta?: (delta: string) => void;
  onMetadata?: (response: QueryResponse) => void;
};

function parseSseBlock(block: string): { event: string; data: unknown } | null {
  const lines = block.split(/\r?\n/);
  let event = "message";
  const dataLines: string[] = [];
  for (const line of lines) {
    if (line.startsWith("event:")) event = line.slice("event:".length).trim();
    if (line.startsWith("data:")) dataLines.push(line.slice("data:".length).trimStart());
  }
  if (!dataLines.length) return null;
  try {
    return { event, data: JSON.parse(dataLines.join("\n")) };
  } catch {
    return null;
  }
}

export async function queryRagStream(payload: QueryRequest, handlers: QueryStreamHandlers = {}): Promise<QueryResponse> {
  const response = await fetch(`${API_BASE}/query/stream`, {
    method: "POST",
    body: JSON.stringify(payload),
    headers: {
      "Content-Type": "application/json",
      Accept: "text/event-stream",
      ...demoAuthHeaders(),
    },
  });
  if (!response.ok) {
    const detail = await response.text();
    throw new Error(detail || `Request failed with ${response.status}`);
  }
  if (!response.body) throw new Error("Streaming response is unavailable.");

  const reader = response.body.getReader();
  const decoder = new TextDecoder();
  let buffer = "";
  let finalResponse: QueryResponse | null = null;
  let streamError: string | null = null;

  function consume(block: string) {
    const parsed = parseSseBlock(block);
    if (!parsed) return;
    const data = parsed.data as Record<string, unknown>;
    if (parsed.event === "status") {
      handlers.onStatus?.(String(data.status ?? "status"), typeof data.message === "string" ? data.message : undefined);
    } else if (parsed.event === "answer_delta") {
      const delta = typeof data.delta === "string" ? data.delta : "";
      if (delta) handlers.onDelta?.(delta);
    } else if (parsed.event === "metadata") {
      finalResponse = data as QueryResponse;
      handlers.onMetadata?.(finalResponse);
    } else if (parsed.event === "error") {
      streamError = typeof data.message === "string" ? data.message : "Streaming query failed.";
    }
  }

  while (true) {
    const { done, value } = await reader.read();
    buffer += decoder.decode(value ?? new Uint8Array(), { stream: !done });
    const blocks = buffer.split(/\r?\n\r?\n/);
    buffer = blocks.pop() ?? "";
    blocks.forEach(consume);
    if (done) break;
  }
  if (buffer.trim()) consume(buffer);
  if (streamError) throw new Error(streamError);
  if (!finalResponse) throw new Error("Streaming query ended before final metadata arrived.");
  return finalResponse;
}

export async function createChatSession(payload: { user_role?: string; user_id?: string | null } = {}): Promise<{ session_id: string; user_role: string; user_id?: string }> {
  return requestJson("/chat/sessions", {
    method: "POST",
    body: JSON.stringify(payload),
  });
}

export async function submitFeedback(payload: {
  session_id?: string | null;
  message_id?: string | null;
  question: string;
  answer: string;
  response_type?: string | null;
  citations?: Citation[];
  user_role?: string;
  rating: "thumbs_up" | "thumbs_down";
  user_comment?: string | null;
  feedback_category?: string;
}): Promise<{ feedback_id: string; status: string }> {
  return requestJson("/feedback", {
    method: "POST",
    body: JSON.stringify({ feedback_category: "other", ...payload }),
  });
}

export async function getRunQuestions(runId: string, headers: HeadersInit = {}): Promise<RunQuestionResponse> {
  const response = await fetch(`${API_BASE}/evaluation/runs/${encodeURIComponent(runId)}/questions`, {
    cache: "no-store",
    headers: {
      "Content-Type": "application/json",
      ...demoAuthHeaders(),
      ...headers,
    },
  });
  if (!response.ok) {
    return {
      run: null,
      run_id: runId,
      detail_available: false,
      detail_source: null,
      row_count: 0,
      rows: [],
      message: "Run details are unavailable for the selected demo user.",
    };
  }
  return response.json();
}

export async function getEnrichedFailures(headers: HeadersInit = {}): Promise<{ failed_questions: EnrichedFailure[]; count: number }> {
  const response = await fetch(`${API_BASE}/evaluation/failed-questions/enriched`, {
    cache: "no-store",
    headers: {
      "Content-Type": "application/json",
      ...demoAuthHeaders(),
      ...headers,
    },
  });
  if (!response.ok) return { failed_questions: [], count: 0 };
  return response.json();
}

export async function submitAlgorithmReview(payload: {
  profile_name: string;
  decision: "review_only" | "candidate" | "rejected";
  question: string;
  user_role: string;
  reviewer_id?: string | null;
  primary_metric?: string;
  expected_sources?: string[];
  notes?: string;
  result_summary?: Record<string, unknown>;
}): Promise<{ review_id: string; status: string; audit_action: string; decision: string }> {
  return requestJson("/evaluation/algorithm-reviews", {
    method: "POST",
    body: JSON.stringify({ primary_metric: "source_coverage", expected_sources: [], notes: "", ...payload }),
  });
}
