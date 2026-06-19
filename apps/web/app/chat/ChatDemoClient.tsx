"use client";

import { FormEvent, useEffect, useState } from "react";
import { EmptyState } from "@/components/EmptyState";
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
import { fetchProject, fetchProjects, type Project } from "@/lib/projects";

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
  const [projects, setProjects] = useState<Project[]>([]);
  const [selectedProjectId, setSelectedProjectId] = useState("");
  const [selectedProject, setSelectedProject] = useState<Project | null>(null);
  const [selectedDepartmentId, setSelectedDepartmentId] = useState("");
  const [scopeLoading, setScopeLoading] = useState(false);
  const [result, setResult] = useState<QueryResponse | null>(null);
  const [transcript, setTranscript] = useState<Array<{ question: string; response_type: string; answer: string }>>([]);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [feedbackRating, setFeedbackRating] = useState<"thumbs_up" | "thumbs_down">("thumbs_up");
  const [feedbackCategory, setFeedbackCategory] = useState("correctness");
  const [feedbackComment, setFeedbackComment] = useState("");
  const [feedbackStatus, setFeedbackStatus] = useState<string | null>(null);
  const departments = selectedProject?.departments ?? [];
  const queryDisabled = loading || scopeLoading || !selectedProjectId;

  useEffect(() => {
    let cancelled = false;
    fetchProjects()
      .then((items) => {
        if (cancelled) return;
        setProjects(items);
        setSelectedProjectId((current) => current || items.find((item) => item.seeded_data_key)?.id || items[0]?.id || "");
      })
      .catch((exc) => {
        if (!cancelled) setError(exc instanceof Error ? exc.message : "Project list failed.");
      });
    return () => {
      cancelled = true;
    };
  }, []);

  useEffect(() => {
    if (!selectedProjectId) {
      setSelectedProject(null);
      setSelectedDepartmentId("");
      return;
    }

    let cancelled = false;
    setScopeLoading(true);
    fetchProject(selectedProjectId)
      .then((project) => {
        if (cancelled) return;
        setSelectedProject(project);
        setSelectedDepartmentId((current) =>
          current && project.departments?.some((department) => department.id === current) ? current : ""
        );
      })
      .catch((exc) => {
        if (!cancelled) setError(exc instanceof Error ? exc.message : "Project detail failed.");
      })
      .finally(() => {
        if (!cancelled) setScopeLoading(false);
      });
    return () => {
      cancelled = true;
    };
  }, [selectedProjectId]);

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
        project_id: selectedProjectId || null,
        department_id: selectedDepartmentId || null,
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
        project_id: selectedProjectId || null,
        department_id: selectedDepartmentId || null,
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
        project_id: selectedProjectId || null,
        department_id: selectedDepartmentId || null,
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
    <div className="grid gap-6 xl:grid-cols-[420px_minmax(0,1fr)] 2xl:grid-cols-[460px_minmax(0,1fr)] 2xl:gap-8">
      <aside className="card space-y-6 xl:sticky xl:top-8 xl:self-start">
        <form onSubmit={onSubmit} className="space-y-4">
          <div className="grid gap-3 md:grid-cols-2 xl:grid-cols-1">
            <div>
              <label className="text-sm font-semibold text-ink" htmlFor="project">Project</label>
              <select
                id="project"
                value={selectedProjectId}
                onChange={(event) => {
                  setSelectedProjectId(event.target.value);
                  setSelectedDepartmentId("");
                }}
                className="field mt-1 w-full"
                disabled={scopeLoading && !projects.length}
              >
                {projects.length ? null : <option value="">No projects loaded</option>}
                {projects.map((project) => (
                  <option key={project.id} value={project.id}>{project.name}</option>
                ))}
              </select>
            </div>
            <div>
              <label className="text-sm font-semibold text-ink" htmlFor="department">Department</label>
              <select
                id="department"
                value={selectedDepartmentId}
                onChange={(event) => setSelectedDepartmentId(event.target.value)}
                className="field mt-1 w-full"
                disabled={!selectedProjectId || scopeLoading}
              >
                <option value="">All departments</option>
                {departments.map((department) => (
                  <option key={department.id} value={department.id}>{department.name}</option>
                ))}
              </select>
            </div>
          </div>
          <div>
            <label className="text-sm font-semibold text-ink" htmlFor="role">Role</label>
            <select id="role" value={role} onChange={(event) => setRole(event.target.value as UserRole)} className="field mt-1 w-full">
              {roles.map((item) => <option key={item}>{item}</option>)}
            </select>
          </div>
          <div>
            <label className="text-sm font-semibold text-ink" htmlFor="question">Question</label>
            <textarea
              id="question"
              value={question}
              onChange={(event) => setQuestion(event.target.value)}
              rows={5}
              className="field mt-1 w-full"
            />
          </div>
          <div className="grid gap-3 md:grid-cols-3 xl:grid-cols-1">
            <div>
              <label className="text-sm font-semibold text-ink" htmlFor="retrieval">Retrieval</label>
              <select id="retrieval" value={retrievalMode} onChange={(event) => setRetrievalMode(event.target.value as RetrievalMode)} className="field mt-1 w-full">
                {retrievalModes.map((item) => <option key={item} value={item}>{item.replaceAll("_", " ")}</option>)}
              </select>
            </div>
            <div>
              <label className="text-sm font-semibold text-ink" htmlFor="prompt">Prompt</label>
              <select id="prompt" value={promptVersion} onChange={(event) => setPromptVersion(event.target.value)} className="field mt-1 w-full">
                {promptVersions.map((item) => <option key={item}>{item}</option>)}
              </select>
            </div>
            <div>
              <label className="text-sm font-semibold text-ink" htmlFor="multi-doc">Multi-doc</label>
              <select id="multi-doc" value={multiDocMode} onChange={(event) => setMultiDocMode(event.target.value as MultiDocMode)} className="field mt-1 w-full">
                {multiDocModes.map((item) => <option key={item}>{item}</option>)}
              </select>
            </div>
          </div>
          <button type="submit" disabled={queryDisabled} className="btn-primary w-full">
            {loading ? "Running..." : "Submit query"}
          </button>
        </form>

        <section>
          <h3 className="text-xs font-semibold uppercase tracking-wide text-stone-500">Demo Presets</h3>
          <div className="mt-3 space-y-2">
            {presets.map((preset) => (
              <button
                key={preset.label}
                type="button"
                onClick={() => {
                  setRole(preset.role);
                  setQuestion(preset.question);
                  setRetrievalMode("vector_only");
                  setMultiDocMode(preset.multiDocMode);
                  setSelectedDepartmentId("");
                }}
                className="w-full rounded border border-stone-300 px-3 py-2 text-left text-sm transition-colors hover:border-moss hover:bg-moss-soft focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-moss"
              >
                <span className="font-semibold text-ink">{preset.label}</span>
                <span className="mt-1 block text-xs text-stone-600">{preset.intent}</span>
              </button>
            ))}
            <button
              type="button"
              onClick={runMemoryScenario}
              disabled={queryDisabled}
              className="w-full rounded border border-steel px-3 py-2 text-left text-sm font-semibold text-steel-dark transition-colors hover:bg-steel-soft disabled:opacity-60 focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-steel"
            >
              Run memory follow-up scenario
            </button>
          </div>
        </section>

        {transcript.length ? (
          <section>
            <h3 className="text-xs font-semibold uppercase tracking-wide text-stone-500">Recent Turns</h3>
            <div className="mt-3 space-y-2">
              {transcript.map((turn, index) => (
                <div key={`${turn.question}-${index}`} className="rounded border border-stone-200 bg-stone-50 p-3 text-xs">
                  <p className="font-semibold text-ink">{turn.question}</p>
                  <p className="mt-1 text-stone-600">{turn.response_type}</p>
                </div>
              ))}
            </div>
          </section>
        ) : null}
      </aside>

      <section className="space-y-5">
        {error ? (
          <div className="rounded-md border border-rust bg-rust-soft p-4 text-sm font-medium text-rust-dark">{error}</div>
        ) : null}
        {result ? (
          <QueryResultPanel result={result} />
        ) : (
          <EmptyState>Run a preset or submit a question to inspect the live response.</EmptyState>
        )}

        {result ? (
          <div className="card">
            <h3 className="text-lg font-semibold text-ink">Submit Feedback</h3>
            <div className="mt-3 grid gap-3 md:grid-cols-3">
              <select value={feedbackRating} onChange={(event) => setFeedbackRating(event.target.value as "thumbs_up" | "thumbs_down")} className="field">
                <option value="thumbs_up">Thumbs up</option>
                <option value="thumbs_down">Thumbs down</option>
              </select>
              <select value={feedbackCategory} onChange={(event) => setFeedbackCategory(event.target.value)} className="field">
                <option value="correctness">Correctness</option>
                <option value="citation">Citation</option>
                <option value="permissions">Permissions</option>
                <option value="missing_info">Missing info</option>
                <option value="other">Other</option>
              </select>
              <button type="button" onClick={sendFeedback} className="btn-accent">Submit feedback</button>
            </div>
            <textarea value={feedbackComment} onChange={(event) => setFeedbackComment(event.target.value)} rows={3} className="field mt-3 w-full" placeholder="Optional comment" />
            {feedbackStatus ? <p className="mt-2 text-sm text-stone-700">{feedbackStatus}</p> : null}
          </div>
        ) : null}
      </section>
    </div>
  );
}
