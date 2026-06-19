import type { Citation } from "@/lib/api";

const API_BASE = process.env.NEXT_PUBLIC_API_BASE_URL ?? "http://127.0.0.1:8000";

export type FeedbackItem = {
  feedback_id: string;
  session_id: string | null;
  message_id: string | null;
  question: string;
  answer: string;
  response_type: string | null;
  citations_json: Citation[];
  user_role: string;
  rating: "thumbs_up" | "thumbs_down";
  user_comment: string | null;
  feedback_category: string;
  created_at: string;
};

export type FeedbackSummary = {
  total: number;
  thumbs_up: number;
  thumbs_down: number;
  negative_category_breakdown: Record<string, number>;
};

export type RequestLogEntry = {
  request_id: string;
  timestamp: string;
  user_role: string;
  session_id: string | null;
  question: string;
  rewritten_question: string | null;
  retrieval_mode: string;
  response_type: string | null;
  final_confidence: number | null;
  total_latency_ms: number | null;
  retrieval_latency_ms: number | null;
  generation_latency_ms: number | null;
  prompt_version: string | null;
  input_tokens: number | null;
  output_tokens: number | null;
  estimated_cost_usd?: number | null;
  pricing_status?: string | null;
  error: string | null;
};

export type ObservabilitySummary = {
  generated_at?: string;
  total_requests?: number;
  avg_total_latency_ms: number | null;
  avg_retrieval_latency_ms: number | null;
  avg_generation_latency_ms: number | null;
  avg_final_confidence: number | null;
  avg_input_tokens: number | null;
  avg_output_tokens: number | null;
  estimated_cost: number | null;
  total_estimated_cost_usd?: number | null;
  avg_estimated_cost_usd?: number | null;
  recent_requests?: RequestLogEntry[];
  status?: string;
  message?: string;
};

export type AuditEvent = {
  id: string;
  user_id: string | null;
  user_role: string;
  action: string;
  document_id: string | null;
  resource_type: string;
  outcome: string;
  reason: string | null;
  metadata_json: Record<string, unknown>;
  created_at: string;
};

export type AuditSummary = {
  counts_by_action: Record<string, number>;
};

export async function getFeedbackSummary(): Promise<FeedbackSummary> {
  const res = await fetch(`${API_BASE}/feedback/summary`, { cache: "no-store" });
  if (!res.ok) return { total: 0, thumbs_up: 0, thumbs_down: 0, negative_category_breakdown: {} };
  return res.json();
}

export async function getFeedback(params?: {
  rating?: string;
  feedback_category?: string;
  limit?: number;
}): Promise<{ feedback: FeedbackItem[]; count: number }> {
  const url = new URL(`${API_BASE}/feedback`);
  if (params?.rating) url.searchParams.set("rating", params.rating);
  if (params?.feedback_category) url.searchParams.set("feedback_category", params.feedback_category);
  if (params?.limit) url.searchParams.set("limit", String(params.limit));
  const res = await fetch(url.toString(), { cache: "no-store" });
  if (!res.ok) return { feedback: [], count: 0 };
  return res.json();
}

export async function getObservabilitySummary(): Promise<ObservabilitySummary> {
  const res = await fetch(`${API_BASE}/observability/summary`, { cache: "no-store" });
  if (!res.ok) {
    return {
      avg_total_latency_ms: null,
      avg_retrieval_latency_ms: null,
      avg_generation_latency_ms: null,
      avg_final_confidence: null,
      avg_input_tokens: null,
      avg_output_tokens: null,
      estimated_cost: null,
      total_estimated_cost_usd: null,
      avg_estimated_cost_usd: null,
      status: "unavailable",
    };
  }
  return res.json();
}

export async function getAuditEvents(params?: {
  action?: string;
  outcome?: string;
  limit?: number;
}): Promise<{ events: AuditEvent[]; count: number }> {
  const url = new URL(`${API_BASE}/audit/events`);
  if (params?.action) url.searchParams.set("action", params.action);
  if (params?.outcome) url.searchParams.set("outcome", params.outcome);
  if (params?.limit) url.searchParams.set("limit", String(params.limit));
  const res = await fetch(url.toString(), { cache: "no-store" });
  if (!res.ok) return { events: [], count: 0 };
  return res.json();
}

export async function getAuditSummary(): Promise<AuditSummary> {
  const res = await fetch(`${API_BASE}/audit/summary`, { cache: "no-store" });
  if (!res.ok) return { counts_by_action: {} };
  return res.json();
}
