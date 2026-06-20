import { API_BASE } from "@/lib/api";
import type { Citation, RetrievedChunk } from "@/lib/api";
import { demoAuthHeaders } from "@/lib/demoAuth";

export type ReviewDecision = "needs_fix" | "evaluation_candidate" | "approved_reference" | "rejected";
export type CorrectnessLabel = "1" | "0.5" | "0";

export type EvaluationReview = {
  id: string;
  source_type: "failed_question" | "feedback";
  source_id: string;
  question: string;
  answer?: string | null;
  expected_answer?: string | null;
  expected_sources: string[];
  actual_citations_json: Citation[];
  retrieved_chunks_json: RetrievedChunk[];
  answer_correctness: number;
  citation_correctness: number;
  decision: ReviewDecision;
  reviewer_role: string;
  reviewer_id?: string | null;
  notes: string;
  created_at: string;
};

async function reviewRequest<T>(path: string, options?: RequestInit): Promise<T> {
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
    throw new Error(detail || `Review request failed with ${response.status}`);
  }
  return response.json();
}

export async function createEvaluationReview(payload: {
  source_type: "failed_question" | "feedback";
  source_id: string;
  question: string;
  answer?: string | null;
  expected_answer?: string | null;
  expected_sources?: string[];
  actual_citations?: Citation[];
  retrieved_chunks?: RetrievedChunk[];
  answer_correctness: number;
  citation_correctness: number;
  decision: ReviewDecision;
  reviewer_role?: string;
  reviewer_id?: string | null;
  notes?: string;
}): Promise<EvaluationReview> {
  const result = await reviewRequest<{ review: EvaluationReview }>("/evaluation/reviews", {
    method: "POST",
    body: JSON.stringify({ reviewer_role: "Evaluator", notes: "", ...payload }),
  });
  return result.review;
}

export async function getEvaluationReviews(params: { source_type?: string; decision?: string; limit?: number } = {}): Promise<{
  reviews: EvaluationReview[];
  count: number;
}> {
  const search = new URLSearchParams();
  if (params.source_type) search.set("source_type", params.source_type);
  if (params.decision) search.set("decision", params.decision);
  if (params.limit) search.set("limit", String(params.limit));
  const query = search.toString() ? `?${search.toString()}` : "";
  return reviewRequest(`/evaluation/reviews${query}`, { cache: "no-store" });
}
