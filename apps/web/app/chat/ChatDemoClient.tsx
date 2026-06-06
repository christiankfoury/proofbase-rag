"use client";

import { FormEvent, useState } from "react";
import { QueryResultPanel } from "@/components/QueryResultPanel";
import {
  MultiDocMode,
  QueryResponse,
  RetrievalMode,
  UserRole,
  createChatSession,
  queryRag,
  submitFeedback,
} from "@/lib/api";

const roles: UserRole[] = ["Employee", "Sales Representative", "Manager", "HR Admin", "IT Admin"];
const retrievalModes: RetrievalMode[] = ["vector_only", "keyword_only", "hybrid"];
const promptVersions = ["default", "v1", "v2", "v3", "v4"];
const multiDocModes: MultiDocMode[] = ["auto", "off", "force"];

const presets = [
  {
    label: "HR factual",
    role: "Employee" as UserRole,
    question: "Where does Northstar Analytics have offices?",
    intent: "Shows a normal answer with HR citation.",
    multiDocMode: "auto" as MultiDocMode,
  },
  {
    label: "Missing info",
    role: "Employee" as UserRole,
    question: "What is Northstar's sabbatical policy?",
    intent: "Shows not_found instead of inventing a policy.",
    multiDocMode: "auto" as MultiDocMode,
  },
  {
    label: "Restricted",
    role: "Employee" as UserRole,
    question: "What is the promotion calibration process?",
    intent: "Shows permission refusal for an Employee.",
    multiDocMode: "auto" as MultiDocMode,
  },
  {
    label: "Manager access",
    role: "Manager" as UserRole,
    question: "What is the promotion calibration process?",
    intent: "Shows role-sensitive access when allowed by the corpus.",
    multiDocMode: "auto" as MultiDocMode,
  },
  {
    label: "Multi-doc",
    role: "Employee" as UserRole,
    question: "If I work remotely, what approval and device security expectations apply?",
    intent: "Shows synthesis across HR and IT documents.",
    multiDocMode: "force" as MultiDocMode,
  },
  {
    label: "Known failure",
    role: "Sales Representative" as UserRole,
    question: "How should I position Northstar against BI tools while avoiding prohibited claims?",
    intent: "Shows the MULTI-005 open retrieval issue honestly.",
    multiDocMode: "force" as MultiDocMode,
  },
];

export function ChatDemoClient() {
  const [role, setRole] = useState<UserRole>("Employee");
  const [question, setQuestion] = useState("Where does Northstar Analytics have offices?");
  const [retrievalMode, setRetrievalMode] = useState<RetrievalMode>("vector_only");
  const [promptVersion, setPromptVersion] = useState("default");
  const [multiDocMode, setMultiDocMode] = useState<MultiDocMode>("auto");
  const [sessionId, setSessionId] = useState<string | null>(null);
  const [result, setResult] = useState<QueryResponse | null>(null);
  const [transcript, setTranscript] = useState<Array<{ question: string; response_type: string; answer: string }>>([]);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [feedbackRating, setFeedbackRating] = useState<"thumbs_up" | "thumbs_down">("thumbs_up");
  const [feedbackCategory, setFeedbackCategory] = useState("correctness");
  const [feedbackComment, setFeedbackComment] = useState("");
  const [feedbackStatus, setFeedbackStatus] = useState<string | null>(null);

  async function runQuery(nextQuestion = question, nextSessionId = sessionId) {
    setLoading(true);
    setError(null);
    setFeedbackStatus(null);
    try {
      const response = await queryRag({
        question: nextQuestion,
        user_role: role,
        session_id: nextSessionId,
        retrieval_mode: retrievalMode,
        chunking_strategy: "section_based",
        prompt_version: promptVersion === "default" ? null : promptVersion,
        multi_doc_mode: multiDocMode,
      });
      setSessionId(response.session_id);
      setResult(response);
      setTranscript((items) => [...items, { question: nextQuestion, response_type: response.response_type, answer: response.answer }].slice(-5));
      return response;
    } catch (exc) {
      setError(exc instanceof Error ? exc.message : "Query failed.");
      return null;
    } finally {
      setLoading(false);
    }
  }

  async function onSubmit(event: FormEvent) {
    event.preventDefault();
    await runQuery();
  }

  async function runMemoryScenario() {
    setLoading(true);
    setError(null);
    setFeedbackStatus(null);
    try {
      const session = await createChatSession({ user_role: role });
      setSessionId(session.session_id);
      await queryRag({
        question: "How many vacation days do full-time employees receive?",
        user_role: role,
        session_id: session.session_id,
        retrieval_mode: retrievalMode,
        chunking_strategy: "section_based",
        multi_doc_mode: "off",
      });
      const followup = "Can I carry any unused days into next year?";
      const response = await queryRag({
        question: followup,
        user_role: role,
        session_id: session.session_id,
        retrieval_mode: retrievalMode,
        chunking_strategy: "section_based",
        prompt_version: promptVersion === "default" ? null : promptVersion,
        multi_doc_mode: "off",
      });
      setQuestion(followup);
      setResult(response);
      setTranscript([
        { question: "How many vacation days do full-time employees receive?", response_type: "context", answer: "Seeded memory turn." },
        { question: followup, response_type: response.response_type, answer: response.answer },
      ]);
    } catch (exc) {
      setError(exc instanceof Error ? exc.message : "Memory scenario failed.");
    } finally {
      setLoading(false);
    }
  }

  async function sendFeedback() {
    if (!result) return;
    setFeedbackStatus(null);
    try {
      const response = await submitFeedback({
        session_id: result.session_id,
        message_id: result.assistant_message_id,
        question,
        answer: result.answer,
        response_type: result.response_type,
        citations: result.citations,
        user_role: role,
        rating: feedbackRating,
        feedback_category: feedbackCategory,
        user_comment: feedbackComment,
      });
      setFeedbackStatus(`Feedback submitted: ${response.feedback_id}`);
      setFeedbackComment("");
    } catch (exc) {
      setFeedbackStatus(exc instanceof Error ? exc.message : "Feedback failed.");
    }
  }

  return (
    <div className="grid gap-6 xl:grid-cols-[380px_1fr]">
      <aside className="space-y-5 rounded-md border border-stone-300 bg-white p-5">
        <form onSubmit={onSubmit} className="space-y-4">
          <div>
            <label className="text-sm font-semibold" htmlFor="role">Role</label>
            <select id="role" value={role} onChange={(event) => setRole(event.target.value as UserRole)} className="mt-1 w-full rounded border border-stone-300 px-3 py-2">
              {roles.map((item) => <option key={item}>{item}</option>)}
            </select>
          </div>
          <div>
            <label className="text-sm font-semibold" htmlFor="question">Question</label>
            <textarea
              id="question"
              value={question}
              onChange={(event) => setQuestion(event.target.value)}
              rows={5}
              className="mt-1 w-full rounded border border-stone-300 px-3 py-2"
            />
          </div>
          <div className="grid gap-3 md:grid-cols-3 xl:grid-cols-1">
            <div>
              <label className="text-sm font-semibold" htmlFor="retrieval">Retrieval</label>
              <select id="retrieval" value={retrievalMode} onChange={(event) => setRetrievalMode(event.target.value as RetrievalMode)} className="mt-1 w-full rounded border border-stone-300 px-3 py-2">
                {retrievalModes.map((item) => <option key={item} value={item}>{item.replaceAll("_", " ")}</option>)}
              </select>
            </div>
            <div>
              <label className="text-sm font-semibold" htmlFor="prompt">Prompt</label>
              <select id="prompt" value={promptVersion} onChange={(event) => setPromptVersion(event.target.value)} className="mt-1 w-full rounded border border-stone-300 px-3 py-2">
                {promptVersions.map((item) => <option key={item}>{item}</option>)}
              </select>
            </div>
            <div>
              <label className="text-sm font-semibold" htmlFor="multi-doc">Multi-doc</label>
              <select id="multi-doc" value={multiDocMode} onChange={(event) => setMultiDocMode(event.target.value as MultiDocMode)} className="mt-1 w-full rounded border border-stone-300 px-3 py-2">
                {multiDocModes.map((item) => <option key={item}>{item}</option>)}
              </select>
            </div>
          </div>
          <button type="submit" disabled={loading} className="w-full rounded bg-ink px-4 py-2 font-semibold text-white disabled:opacity-60">
            {loading ? "Running..." : "Submit query"}
          </button>
        </form>

        <section>
          <h3 className="font-semibold">Demo Presets</h3>
          <div className="mt-3 space-y-2">
            {presets.map((preset) => (
              <button
                key={preset.label}
                type="button"
                onClick={() => {
                  setRole(preset.role);
                  setQuestion(preset.question);
                  setMultiDocMode(preset.multiDocMode);
                }}
                className="w-full rounded border border-stone-300 px-3 py-2 text-left text-sm hover:border-moss"
              >
                <span className="font-semibold">{preset.label}</span>
                <span className="mt-1 block text-xs text-stone-600">{preset.intent}</span>
              </button>
            ))}
            <button type="button" onClick={runMemoryScenario} disabled={loading} className="w-full rounded border border-steel px-3 py-2 text-left text-sm font-semibold text-steel disabled:opacity-60">
              Run memory follow-up scenario
            </button>
          </div>
        </section>

        {transcript.length ? (
          <section>
            <h3 className="font-semibold">Recent Turns</h3>
            <div className="mt-3 space-y-2">
              {transcript.map((turn, index) => (
                <div key={`${turn.question}-${index}`} className="rounded border border-stone-200 p-3 text-xs">
                  <p className="font-semibold">{turn.question}</p>
                  <p className="mt-1 text-stone-600">{turn.response_type}</p>
                </div>
              ))}
            </div>
          </section>
        ) : null}
      </aside>

      <section className="space-y-5">
        {error ? <div className="rounded-md border border-rust bg-orange-50 p-4 text-sm text-rust">{error}</div> : null}
        {result ? <QueryResultPanel result={result} /> : <div className="rounded-md border border-stone-300 bg-white p-8 text-stone-700">Run a preset or submit a question to inspect the live response.</div>}

        {result ? (
          <section className="rounded-md border border-stone-300 bg-white p-5">
            <h3 className="text-lg font-semibold">Submit Feedback</h3>
            <div className="mt-3 grid gap-3 md:grid-cols-3">
              <select value={feedbackRating} onChange={(event) => setFeedbackRating(event.target.value as "thumbs_up" | "thumbs_down")} className="rounded border border-stone-300 px-3 py-2">
                <option value="thumbs_up">Thumbs up</option>
                <option value="thumbs_down">Thumbs down</option>
              </select>
              <select value={feedbackCategory} onChange={(event) => setFeedbackCategory(event.target.value)} className="rounded border border-stone-300 px-3 py-2">
                <option value="correctness">Correctness</option>
                <option value="citation">Citation</option>
                <option value="permissions">Permissions</option>
                <option value="missing_info">Missing info</option>
                <option value="other">Other</option>
              </select>
              <button type="button" onClick={sendFeedback} className="rounded bg-moss px-4 py-2 font-semibold text-white">Submit feedback</button>
            </div>
            <textarea value={feedbackComment} onChange={(event) => setFeedbackComment(event.target.value)} rows={3} className="mt-3 w-full rounded border border-stone-300 px-3 py-2" placeholder="Optional comment" />
            {feedbackStatus ? <p className="mt-2 text-sm text-stone-700">{feedbackStatus}</p> : null}
          </section>
        ) : null}
      </section>
    </div>
  );
}
