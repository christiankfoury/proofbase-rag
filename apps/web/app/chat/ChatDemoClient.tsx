"use client";

import Link from "next/link";
import { FormEvent, ReactNode, useEffect, useMemo, useRef, useState } from "react";
import {
  BookOpen,
  Brain,
  CheckCircle2,
  Clipboard,
  Copy,
  FileText,
  Gauge,
  History,
  Layers3,
  MessageSquare,
  MousePointerClick,
  PanelRightOpen,
  RefreshCcw,
  Search,
  Send,
  Settings2,
  ShieldCheck,
  SlidersHorizontal,
  Sparkles,
  ThumbsDown,
  ThumbsUp,
  X,
} from "lucide-react";
import { useSearchParams } from "next/navigation";
import { Badge } from "@/components/Badge";
import { CitationTable, RetrievedContext } from "@/components/QueryResultPanel";
import {
  MultiDocMode,
  QueryResponse,
  RetrievalMode,
  UserRole,
  createChatSession,
  queryRag,
  queryRagStream,
  submitFeedback,
} from "@/lib/api";
import { formatMetric } from "@/lib/dashboard";
import { DEMO_USER_CHANGED_EVENT, fetchCurrentDemoUser, fetchDemoUsers, setSelectedDemoUserId, syncDemoUserCookie } from "@/lib/demoAuth";
import type { DemoUser } from "@/lib/demoAuth";
import { fetchProject, fetchProjects, type Project } from "@/lib/projects";

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
    tone: "bg-moss-soft text-moss-dark border-moss/30",
  },
  {
    label: "Missing info",
    role: "Employee" as UserRole,
    question: "What is Northstar's sabbatical policy?",
    intent: "Shows not_found instead of inventing a policy.",
    multiDocMode: "auto" as MultiDocMode,
    tone: "bg-stone-100 text-stone-800 border-stone-300",
  },
  {
    label: "Restricted",
    role: "Employee" as UserRole,
    question: "What is the promotion calibration process?",
    intent: "Shows permission refusal for an Employee.",
    multiDocMode: "auto" as MultiDocMode,
    tone: "bg-rust-soft text-rust-dark border-rust/30",
  },
  {
    label: "Manager access",
    role: "Manager" as UserRole,
    question: "What is the promotion calibration process?",
    intent: "Shows role-sensitive access when allowed by the corpus.",
    multiDocMode: "auto" as MultiDocMode,
    tone: "bg-steel-soft text-steel-dark border-steel/30",
  },
  {
    label: "Multi-doc",
    role: "Employee" as UserRole,
    question: "If I work remotely, what approval and device security expectations apply?",
    intent: "Shows synthesis across HR and IT documents.",
    multiDocMode: "force" as MultiDocMode,
    tone: "bg-amber-50 text-amber-900 border-amber-200",
  },
  {
    label: "Known failure",
    role: "Sales Representative" as UserRole,
    question: "How should I position Northstar against BI tools while avoiding prohibited claims?",
    intent: "Shows the MULTI-005 open retrieval issue honestly.",
    multiDocMode: "force" as MultiDocMode,
    tone: "bg-rose-50 text-rose-900 border-rose-200",
  },
];

type ChatMessage = {
  id: string;
  role: "user" | "assistant" | "system";
  content: string;
  question?: string;
  response?: QueryResponse;
  responseType?: string;
  status?: "pending" | "streaming" | "done" | "error";
  statusText?: string;
};

type EvidenceToggles = {
  citations: boolean;
  retrievedContext: boolean;
  metrics: boolean;
  validation: boolean;
  feedback: boolean;
};

function makeId(prefix: string) {
  const random = typeof crypto !== "undefined" && "randomUUID" in crypto ? crypto.randomUUID() : Math.random().toString(36).slice(2);
  return `${prefix}-${random}`;
}

function formatMode(value: string) {
  return value.replaceAll("_", " ");
}

function formatLatency(value: number | null | undefined) {
  if (value === null || value === undefined) return "pending";
  if (value >= 1000) return `${(value / 1000).toFixed(1)}s`;
  return `${Math.round(value)} ms`;
}

function formatUsd(value: number | null | undefined) {
  if (value === null || value === undefined) return "pending";
  return `$${value.toFixed(6)}`;
}

function shortId(value: string | null | undefined, fallback = "global") {
  return value ? value.slice(0, 8) : fallback;
}

function IconButton({
  label,
  children,
  onClick,
  disabled = false,
}: {
  label: string;
  children: ReactNode;
  onClick: () => void;
  disabled?: boolean;
}) {
  return (
    <button
      type="button"
      onClick={onClick}
      disabled={disabled}
      title={label}
      aria-label={label}
      className="inline-flex h-10 w-10 items-center justify-center rounded-md border border-stone-300 bg-white text-stone-700 shadow-sm transition-colors hover:border-moss hover:text-ink disabled:cursor-not-allowed disabled:opacity-50 focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-moss"
    >
      {children}
    </button>
  );
}

function SettingSection({ icon, title, children, tone = "text-moss" }: { icon: ReactNode; title: string; children: ReactNode; tone?: string }) {
  return (
    <section className="rounded-md border border-stone-200 bg-white p-4 shadow-sm">
      <div className="mb-3 flex items-center gap-2">
        <span className={`inline-flex h-8 w-8 items-center justify-center rounded-md bg-stone-100 ${tone}`}>{icon}</span>
        <h3 className="text-sm font-semibold text-ink">{title}</h3>
      </div>
      {children}
    </section>
  );
}

function ToggleRow({ label, checked, onChange }: { label: string; checked: boolean; onChange: (checked: boolean) => void }) {
  return (
    <label className="flex cursor-pointer items-center justify-between gap-3 rounded-md border border-stone-200 bg-stone-50 px-3 py-2 text-sm text-stone-700">
      <span>{label}</span>
      <input type="checkbox" checked={checked} onChange={(event) => onChange(event.target.checked)} className="h-4 w-4 accent-moss" />
    </label>
  );
}

function SegmentedControl<T extends string>({
  value,
  options,
  onChange,
}: {
  value: T;
  options: T[];
  onChange: (value: T) => void;
}) {
  return (
    <div className="grid grid-cols-3 overflow-hidden rounded-md border border-stone-300 bg-stone-100 p-1">
      {options.map((option) => (
        <button
          key={option}
          type="button"
          onClick={() => onChange(option)}
          className={`rounded px-2 py-2 text-xs font-semibold capitalize transition-colors ${
            value === option ? "bg-white text-ink shadow-sm" : "text-stone-600 hover:text-ink"
          }`}
        >
          {formatMode(option)}
        </button>
      ))}
    </div>
  );
}

function TypingDots() {
  return (
    <span className="inline-flex items-center gap-1" aria-label="Assistant is typing">
      <span className="h-2 w-2 animate-pulse rounded-full bg-stone-500" />
      <span className="h-2 w-2 animate-pulse rounded-full bg-stone-500 [animation-delay:120ms]" />
      <span className="h-2 w-2 animate-pulse rounded-full bg-stone-500 [animation-delay:240ms]" />
    </span>
  );
}

function MetricTile({ label, value }: { label: string; value: string | number | null | undefined }) {
  return (
    <div className="rounded-md border border-stone-200 bg-white p-3">
      <p className="text-2xs font-semibold uppercase tracking-wide text-stone-500">{label}</p>
      <p className="mt-1 text-sm font-semibold text-ink">{formatMetric(value)}</p>
    </div>
  );
}

function confidenceInterpretation(result: QueryResponse): string {
  if (result.confidence_interpretation === "response_behavior") {
    return "This confidence describes whether the system chose the right behavior, such as answering, refusing, or asking for clarification.";
  }
  return "This confidence describes how strongly the answer is supported by retrieved and cited evidence.";
}

function ProofSummary({ result }: { result: QueryResponse }) {
  return (
    <section className="rounded-md border border-moss bg-white p-4">
      <div className="flex flex-wrap items-start justify-between gap-3">
        <div>
          <p className="text-xs font-semibold uppercase tracking-wide text-moss-dark">Why this answer?</p>
          <h3 className="mt-1 text-lg font-semibold text-ink">Answer proof</h3>
        </div>
        <Badge tone={result.permission_check.unauthorized_chunks_reached_generation ? "warn" : "good"}>
          {result.permission_check.unauthorized_chunks_reached_generation ? "Permission issue" : "Permission-filtered"}
        </Badge>
      </div>
      <div className="mt-4 grid gap-3 md:grid-cols-2 xl:grid-cols-4">
        <div className="rounded border border-stone-200 bg-stone-50 p-3">
          <p className="text-xs font-semibold uppercase tracking-wide text-stone-500">Scope</p>
          <p className="mt-1 text-sm font-semibold text-ink">
            {shortId(result.scope?.project_id)} / {shortId(result.scope?.department_id, "all departments")}
          </p>
          <p className="mt-1 text-xs text-stone-600">Applied before generation.</p>
        </div>
        <div className="rounded border border-stone-200 bg-stone-50 p-3">
          <p className="text-xs font-semibold uppercase tracking-wide text-stone-500">Role</p>
          <p className="mt-1 text-sm font-semibold text-ink">{result.permission_check.user_role}</p>
          <p className="mt-1 text-xs text-stone-600">
            {result.permission_check.unauthorized_chunks_reached_generation ? "Review permission safety." : "No unauthorized chunks reached generation."}
          </p>
        </div>
        <div className="rounded border border-stone-200 bg-stone-50 p-3">
          <p className="text-xs font-semibold uppercase tracking-wide text-stone-500">Citations</p>
          <p className="mt-1 text-sm font-semibold text-ink">{result.citations.length}</p>
          <p className="mt-1 text-xs text-stone-600">{result.retrieved_chunks.length} retrieved snippets available.</p>
        </div>
        <div className="rounded border border-stone-200 bg-stone-50 p-3">
          <p className="text-xs font-semibold uppercase tracking-wide text-stone-500">Confidence</p>
          <p className="mt-1 text-sm font-semibold text-ink">{formatMetric(result.final_confidence)}</p>
          <p className="mt-1 text-xs text-stone-600">{confidenceInterpretation(result)}</p>
        </div>
      </div>
      {result.clarification_reason ? (
        <div className="mt-4 rounded border border-steel/30 bg-steel/10 p-3">
          <p className="text-xs font-semibold uppercase tracking-wide text-stone-500">Clarification reason</p>
          <p className="mt-1 text-sm font-semibold text-ink">{formatMode(result.clarification_reason)}</p>
        </div>
      ) : null}
      <div className="mt-4 flex flex-wrap gap-2">
        <Link href="/dev-admin/runs" className="btn-secondary btn-sm">
          Evaluation runs
        </Link>
        <Link href="/dev-admin/permission-safety" className="btn-secondary btn-sm">
          Permission safety
        </Link>
        <Link href="/dev-admin/observability" className="btn-secondary btn-sm">
          Observability
        </Link>
        <Link href="/dev-admin/audit" className="btn-secondary btn-sm">
          Audit log
        </Link>
      </div>
    </section>
  );
}

function EvidencePanel({
  message,
  toggles,
  feedbackRating,
  feedbackCategory,
  feedbackComment,
  feedbackStatus,
  onRatingChange,
  onCategoryChange,
  onCommentChange,
  onFeedback,
}: {
  message: ChatMessage;
  toggles: EvidenceToggles;
  feedbackRating: "thumbs_up" | "thumbs_down";
  feedbackCategory: string;
  feedbackComment: string;
  feedbackStatus: string | null;
  onRatingChange: (value: "thumbs_up" | "thumbs_down") => void;
  onCategoryChange: (value: string) => void;
  onCommentChange: (value: string) => void;
  onFeedback: (message: ChatMessage) => void;
}) {
  const result = message.response;
  if (!result) return null;

  return (
    <div className="mt-4 space-y-4 rounded-md border border-stone-200 bg-stone-50 p-4">
      <ProofSummary result={result} />

      {toggles.metrics ? (
        <section>
          <div className="mb-2 flex items-center gap-2 text-sm font-semibold text-ink">
            <Gauge className="h-4 w-4 text-steel" />
            Metrics
          </div>
          <div className="grid gap-2 sm:grid-cols-2 lg:grid-cols-4">
            <MetricTile label="Final confidence" value={result.final_confidence} />
            <MetricTile label="Retrieval" value={result.retrieval_confidence} />
            <MetricTile label="Citation" value={result.citation_confidence} />
            <MetricTile label="Answer" value={result.answer_confidence} />
            <MetricTile label="Retrieval latency" value={formatLatency(result.retrieval_latency_ms)} />
            <MetricTile label="Generation latency" value={formatLatency(result.generation_latency_ms)} />
            <MetricTile label="Total latency" value={formatLatency(result.total_latency_ms)} />
            <MetricTile label="Estimated cost" value={formatUsd(result.estimated_cost_usd)} />
          </div>
          <div className="mt-3 flex flex-wrap items-center gap-2 text-xs text-stone-600">
            <Badge tone={result.permission_check.unauthorized_chunks_reached_generation ? "warn" : "good"}>
              {result.permission_check.unauthorized_chunks_reached_generation ? "Leakage detected" : "No permission leakage"}
            </Badge>
            <span>Role: {result.permission_check.user_role}</span>
            <span>Chunks: {result.permission_check.retrieved_chunks_count}</span>
            <span>Scope: {shortId(result.scope?.project_id)} / {shortId(result.scope?.department_id, "all")}</span>
          </div>
        </section>
      ) : null}

      {toggles.citations ? (
        <section>
          <div className="mb-2 flex items-center gap-2 text-sm font-semibold text-ink">
            <FileText className="h-4 w-4 text-moss" />
            Citations
          </div>
          <CitationTable citations={result.citations} />
        </section>
      ) : null}

      {toggles.validation ? (
        <section className="grid gap-3 lg:grid-cols-2">
          <div className="rounded-md border border-stone-200 bg-white p-3">
            <div className="mb-2 flex items-center gap-2 text-sm font-semibold text-ink">
              <CheckCircle2 className="h-4 w-4 text-moss" />
              Supported Claims
            </div>
            <ul className="list-disc space-y-1 pl-5 text-sm text-stone-700">
              {result.supported_claims.length ? result.supported_claims.map((claim) => <li key={claim}>{claim}</li>) : <li>No supported claims returned.</li>}
            </ul>
          </div>
          <div className="rounded-md border border-stone-200 bg-white p-3">
            <div className="mb-2 flex items-center gap-2 text-sm font-semibold text-ink">
              <ShieldCheck className="h-4 w-4 text-rust" />
              Validation Notes
            </div>
            <p className="text-sm leading-6 text-stone-700">{result.validation_notes || "No validation notes returned."}</p>
            {result.unsupported_claims.length ? (
              <ul className="mt-2 list-disc space-y-1 pl-5 text-sm text-stone-700">
                {result.unsupported_claims.map((claim) => <li key={claim}>{claim}</li>)}
              </ul>
            ) : null}
          </div>
        </section>
      ) : null}

      {toggles.retrievedContext ? (
        <section>
          <div className="mb-2 flex items-center gap-2 text-sm font-semibold text-ink">
            <BookOpen className="h-4 w-4 text-steel" />
            Retrieved Context
          </div>
          <RetrievedContext chunks={result.retrieved_chunks} />
        </section>
      ) : null}

      {toggles.feedback ? (
        <section className="rounded-md border border-stone-200 bg-white p-3">
          <div className="mb-3 flex items-center gap-2 text-sm font-semibold text-ink">
            <MessageSquare className="h-4 w-4 text-moss" />
            Feedback
          </div>
          <div className="grid gap-3 md:grid-cols-[160px_1fr_auto]">
            <select value={feedbackRating} onChange={(event) => onRatingChange(event.target.value as "thumbs_up" | "thumbs_down")} className="field">
              <option value="thumbs_up">Thumbs up</option>
              <option value="thumbs_down">Thumbs down</option>
            </select>
            <select value={feedbackCategory} onChange={(event) => onCategoryChange(event.target.value)} className="field">
              <option value="correctness">Correctness</option>
              <option value="citation">Citation</option>
              <option value="permissions">Permissions</option>
              <option value="missing_info">Missing info</option>
              <option value="other">Other</option>
            </select>
            <button type="button" onClick={() => onFeedback(message)} className="btn-accent inline-flex items-center justify-center gap-2">
              {feedbackRating === "thumbs_up" ? <ThumbsUp className="h-4 w-4" /> : <ThumbsDown className="h-4 w-4" />}
              Submit
            </button>
          </div>
          <textarea value={feedbackComment} onChange={(event) => onCommentChange(event.target.value)} rows={3} className="field mt-3 w-full" placeholder="Optional comment" />
          {feedbackStatus ? <p className="mt-2 text-sm text-stone-700">{feedbackStatus}</p> : null}
        </section>
      ) : null}
    </div>
  );
}

export function ChatDemoClient() {
  const searchParams = useSearchParams();
  const [demoUsers, setDemoUsers] = useState<DemoUser[]>([]);
  const [currentUser, setCurrentUser] = useState<DemoUser | null>(null);
  const [identityLoading, setIdentityLoading] = useState(true);
  const [question, setQuestion] = useState("Where does Northstar Analytics have offices?");
  const [retrievalMode, setRetrievalMode] = useState<RetrievalMode>("vector_only");
  const [promptVersion, setPromptVersion] = useState("default");
  const [multiDocMode, setMultiDocMode] = useState<MultiDocMode>("auto");
  const [sessionId, setSessionId] = useState<string | null>(null);
  const [projects, setProjects] = useState<Project[]>([]);
  const [projectsLoading, setProjectsLoading] = useState(true);
  const [selectedProjectId, setSelectedProjectId] = useState("");
  const [selectedProject, setSelectedProject] = useState<Project | null>(null);
  const [selectedDepartmentId, setSelectedDepartmentId] = useState("");
  const [requestedScope, setRequestedScope] = useState<{ projectId: string; departmentId: string; applied: boolean } | null>(null);
  const [scopeRequestVersion, setScopeRequestVersion] = useState(0);
  const [scopeNotice, setScopeNotice] = useState<string | null>(null);
  const [scopeLoading, setScopeLoading] = useState(false);
  const [messages, setMessages] = useState<ChatMessage[]>([]);
  const [settingsOpen, setSettingsOpen] = useState(false);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [feedbackRating, setFeedbackRating] = useState<"thumbs_up" | "thumbs_down">("thumbs_up");
  const [feedbackCategory, setFeedbackCategory] = useState("correctness");
  const [feedbackComment, setFeedbackComment] = useState("");
  const [feedbackStatus, setFeedbackStatus] = useState<string | null>(null);
  const [toggles, setToggles] = useState<EvidenceToggles>({
    citations: true,
    retrievedContext: false,
    metrics: true,
    validation: true,
    feedback: true,
  });

  const revealTimer = useRef<number | null>(null);
  const transcriptRef = useRef<HTMLDivElement | null>(null);
  const requestedDepartmentId = useRef("");
  const departments = selectedProject?.departments ?? [];
  const selectedDepartment = departments.find((department) => department.id === selectedDepartmentId) ?? null;
  const scopeLabel = `${selectedProject?.name ?? "Loading project"} / ${selectedDepartment?.name ?? "All departments"}`;
  const queryDisabled = loading || scopeLoading || !selectedProjectId || !question.trim();
  const role = currentUser?.business_role ?? "Employee";
  const identityName = currentUser?.display_name ?? (identityLoading ? "Loading demo user" : "Demo identity unavailable");
  const identityBadge = currentUser ? role : identityLoading ? "Loading" : "API offline";
  const identityBadgeTone = currentUser || identityLoading ? "neutral" : "warn";
  const identityDetail = currentUser
    ? `${role} - derived server-side from local demo auth`
    : identityLoading
      ? "Waiting for local demo auth."
      : "Start the API to load the selected demo user.";
  const latestResultMessage = useMemo(() => [...messages].reverse().find((message) => message.response), [messages]);

  useEffect(() => {
    return () => {
      if (revealTimer.current) window.clearInterval(revealTimer.current);
    };
  }, []);

  useEffect(() => {
    transcriptRef.current?.scrollTo({ top: transcriptRef.current.scrollHeight, behavior: "smooth" });
  }, [messages]);

  useEffect(() => {
    let cancelled = false;

    async function loadIdentity() {
      setIdentityLoading(true);
      try {
        syncDemoUserCookie();
        const [users, user] = await Promise.all([fetchDemoUsers(), fetchCurrentDemoUser()]);
        if (cancelled) return;
        setDemoUsers(users);
        setCurrentUser(user);
      } catch (exc) {
        if (!cancelled) setError(exc instanceof Error ? exc.message : "Demo identity failed.");
      } finally {
        if (!cancelled) setIdentityLoading(false);
      }
    }

    loadIdentity();
    window.addEventListener(DEMO_USER_CHANGED_EVENT, loadIdentity);
    window.addEventListener("storage", loadIdentity);
    return () => {
      cancelled = true;
      window.removeEventListener(DEMO_USER_CHANGED_EVENT, loadIdentity);
      window.removeEventListener("storage", loadIdentity);
    };
  }, []);

  useEffect(() => {
    let cancelled = false;
    setProjectsLoading(true);
    const requestedProjectId = searchParams.get("project") ?? "";
    requestedDepartmentId.current = searchParams.get("department") ?? "";
    const requestedQuestion = searchParams.get("question") ?? "";
    if (requestedQuestion) setQuestion(requestedQuestion);
    setRequestedScope(
      requestedProjectId || requestedDepartmentId.current
        ? { projectId: requestedProjectId, departmentId: requestedDepartmentId.current, applied: false }
        : null
    );
    if (requestedProjectId || requestedDepartmentId.current) {
      setScopeRequestVersion((current) => current + 1);
    }
    fetchProjects()
      .then((items) => {
        if (cancelled) return;
        setProjects(items);
        const requestedProject = items.find((item) => item.id === requestedProjectId);
        setSelectedProjectId((current) =>
          requestedProject?.id || current || items.find((item) => item.seeded_data_key)?.id || items[0]?.id || ""
        );
      })
      .catch((exc) => {
        if (!cancelled) setError(exc instanceof Error ? exc.message : "Project list failed.");
      })
      .finally(() => {
        if (!cancelled) setProjectsLoading(false);
      });
    return () => {
      cancelled = true;
    };
  }, [searchParams]);

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
        const pendingDepartmentId = requestedDepartmentId.current;
        const requestedDepartment = pendingDepartmentId
          ? project.departments?.find((department) => department.id === pendingDepartmentId)
          : null;
        setSelectedDepartmentId((current) => {
          if (pendingDepartmentId) return requestedDepartment?.id ?? "";
          return current && project.departments?.some((department) => department.id === current) ? current : "";
        });
        if (requestedScope && !requestedScope.applied && requestedScope.projectId && requestedScope.projectId !== selectedProjectId) {
          setScopeNotice("The requested project was not available, so chat opened the default project.");
          setRequestedScope((current) => (current ? { ...current, applied: true } : current));
        } else if (requestedScope && !requestedScope.applied && pendingDepartmentId && requestedDepartment) {
          setScopeNotice(null);
          setRequestedScope((current) => (current ? { ...current, applied: true } : current));
        } else if (requestedScope && !requestedScope.applied && pendingDepartmentId) {
          setScopeNotice("The URL requested a department that is not available in this project, so chat is using all departments.");
          setRequestedScope((current) => (current ? { ...current, applied: true } : current));
        } else if (requestedScope && !requestedScope.applied && requestedScope.projectId) {
          setScopeNotice(null);
          setRequestedScope((current) => (current ? { ...current, applied: true } : current));
        }
        requestedDepartmentId.current = "";
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
  }, [scopeRequestVersion, selectedProjectId]);

  function setToggle(key: keyof EvidenceToggles, checked: boolean) {
    setToggles((current) => ({ ...current, [key]: checked }));
  }

  function revealAssistantAnswer(messageId: string, answer: string) {
    if (revealTimer.current) window.clearInterval(revealTimer.current);
    let cursor = 0;
    const step = Math.max(2, Math.ceil(answer.length / 110));
    revealTimer.current = window.setInterval(() => {
      cursor = Math.min(answer.length, cursor + step);
      setMessages((items) =>
        items.map((message) =>
          message.id === messageId
            ? {
                ...message,
                content: answer.slice(0, cursor),
                status: cursor >= answer.length ? "done" : "streaming",
              }
            : message
        )
      );
      if (cursor >= answer.length && revealTimer.current) {
        window.clearInterval(revealTimer.current);
        revealTimer.current = null;
      }
    }, 18);
  }

  function appendPendingTurn(nextQuestion: string) {
    const userMessage: ChatMessage = {
      id: makeId("user"),
      role: "user",
      content: nextQuestion,
    };
    const assistantMessage: ChatMessage = {
      id: makeId("assistant"),
      role: "assistant",
      content: "",
      question: nextQuestion,
      status: "pending",
      statusText: "Preparing request...",
    };
    setMessages((items) => [...items, userMessage, assistantMessage]);
    return assistantMessage.id;
  }

  async function runQuery(nextQuestion = question, nextSessionId = sessionId, options: { appendTurn?: boolean } = {}) {
    const trimmedQuestion = nextQuestion.trim();
    if (!trimmedQuestion || !selectedProjectId) return null;
    const assistantMessageId = options.appendTurn === false ? null : appendPendingTurn(trimmedQuestion);
    setLoading(true);
    setError(null);
    setFeedbackStatus(null);
    let sawDelta = false;
    try {
      const payload = {
        question: trimmedQuestion,
        session_id: nextSessionId,
        retrieval_mode: retrievalMode,
        chunking_strategy: "section_based",
        prompt_version: promptVersion === "default" ? null : promptVersion,
        multi_doc_mode: multiDocMode,
        project_id: selectedProjectId || null,
        department_id: selectedDepartmentId || null,
      };
      const response = await queryRagStream(payload, {
        onStatus: (_status, message) => {
          if (!assistantMessageId || !message) return;
          setMessages((items) =>
            items.map((item) =>
              item.id === assistantMessageId && item.status === "pending"
                ? {
                    ...item,
                    statusText: message,
                  }
                : item
            )
          );
        },
        onDelta: (delta) => {
          sawDelta = true;
          if (!assistantMessageId) return;
          setMessages((items) =>
            items.map((item) =>
              item.id === assistantMessageId
                ? {
                    ...item,
                    content: `${item.content}${delta}`,
                    status: "streaming",
                    statusText: undefined,
                  }
                : item
            )
          );
        },
        onMetadata: (metadata) => {
          setSessionId(metadata.session_id);
          if (!assistantMessageId) return;
          setMessages((items) =>
            items.map((message) =>
              message.id === assistantMessageId
                ? {
                    ...message,
                    content: metadata.answer,
                    response: metadata,
                    responseType: metadata.response_type,
                    status: "done",
                    statusText: undefined,
                  }
                : message
            )
          );
        },
      });
      setSessionId(response.session_id);
      return response;
    } catch (exc) {
      if (!sawDelta) {
        try {
          const response = await queryRag({
            question: trimmedQuestion,
            session_id: nextSessionId,
            retrieval_mode: retrievalMode,
            chunking_strategy: "section_based",
            prompt_version: promptVersion === "default" ? null : promptVersion,
            multi_doc_mode: multiDocMode,
            project_id: selectedProjectId || null,
            department_id: selectedDepartmentId || null,
          });
          setSessionId(response.session_id);
          if (assistantMessageId) {
            setMessages((items) =>
              items.map((message) =>
                message.id === assistantMessageId
                  ? {
                      ...message,
                      content: "",
                      response,
                      responseType: response.response_type,
                      status: "streaming",
                      statusText: undefined,
                    }
                  : message
              )
            );
            revealAssistantAnswer(assistantMessageId, response.answer);
          }
          return response;
        } catch (fallbackExc) {
          exc = fallbackExc;
        }
      }
      const message = exc instanceof Error ? exc.message : "Query failed.";
      setError(message);
      if (assistantMessageId) {
        setMessages((items) =>
          items.map((item) =>
            item.id === assistantMessageId
              ? {
                  ...item,
                  content: item.content ? `${item.content}\n\n${message}` : message,
                  status: "error",
                  responseType: "error",
                  statusText: undefined,
                }
              : item
          )
        );
      }
      return null;
    } finally {
      setLoading(false);
    }
  }

  async function onSubmit(event: FormEvent) {
    event.preventDefault();
    const submittedQuestion = question.trim();
    if (!submittedQuestion) return;
    setQuestion("");
    await runQuery(submittedQuestion);
  }

  async function runMemoryScenario() {
    if (!selectedProjectId) return;
    setLoading(true);
    setError(null);
    setFeedbackStatus(null);
    const firstQuestion = "How many vacation days do full-time employees receive?";
    const followup = "Can I carry any unused days into next year?";
    const assistantMessageId = appendPendingTurn(followup);
    setMessages((items) => [
      ...items.slice(0, -2),
      {
        id: makeId("system"),
        role: "system",
        content: "Memory scenario: a hidden first turn asks about vacation days, then the visible follow-up is rewritten with session memory.",
      },
      ...items.slice(-2),
    ]);
    try {
      const session = await createChatSession();
      setSessionId(session.session_id);
      await queryRag({
        question: firstQuestion,
        session_id: session.session_id,
        retrieval_mode: retrievalMode,
        chunking_strategy: "section_based",
        multi_doc_mode: "off",
        project_id: selectedProjectId || null,
        department_id: selectedDepartmentId || null,
      });
      const response = await queryRag({
        question: followup,
        session_id: session.session_id,
        retrieval_mode: retrievalMode,
        chunking_strategy: "section_based",
        prompt_version: promptVersion === "default" ? null : promptVersion,
        multi_doc_mode: "off",
        project_id: selectedProjectId || null,
        department_id: selectedDepartmentId || null,
      });
      setQuestion("");
      setMessages((items) =>
        items.map((message) =>
          message.id === assistantMessageId
            ? {
                ...message,
                content: "",
                response,
                responseType: response.response_type,
                status: "streaming",
              }
            : message
        )
      );
      revealAssistantAnswer(assistantMessageId, response.answer);
    } catch (exc) {
      const message = exc instanceof Error ? exc.message : "Memory scenario failed.";
      setError(message);
      setMessages((items) =>
        items.map((item) =>
          item.id === assistantMessageId
            ? {
                ...item,
                content: message,
                status: "error",
                responseType: "error",
              }
            : item
        )
      );
    } finally {
      setLoading(false);
    }
  }

  async function sendFeedback(message: ChatMessage) {
    if (!message.response) return;
    setFeedbackStatus(null);
    try {
      const response = await submitFeedback({
        session_id: message.response.session_id,
        message_id: message.response.assistant_message_id,
        question: message.question ?? "",
        answer: message.response.answer,
        response_type: message.response.response_type,
        citations: message.response.citations,
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

  function applyPreset(preset: (typeof presets)[number]) {
    const matchingUser = demoUsers.find((user) => user.business_role === preset.role);
    if (matchingUser) setSelectedDemoUserId(matchingUser.id);
    setQuestion(preset.question);
    setRetrievalMode("vector_only");
    setMultiDocMode(preset.multiDocMode);
    setSelectedDepartmentId("");
    setSettingsOpen(false);
  }

  function resetChat() {
    if (revealTimer.current) window.clearInterval(revealTimer.current);
    revealTimer.current = null;
    setMessages([]);
    setSessionId(null);
    setError(null);
    setFeedbackStatus(null);
    setQuestion("Where does Northstar Analytics have offices?");
  }

  async function copyAnswer(message: ChatMessage) {
    if (!message.response?.answer) return;
    await navigator.clipboard.writeText(message.response.answer);
  }

  return (
    <div
      data-testid="chat-interface"
      className="relative left-1/2 -my-5 flex h-[calc(100dvh-57px)] w-[100vw] -translate-x-1/2 flex-col overflow-hidden bg-stone-50"
    >
      <header className="z-20 shrink-0 border-b border-stone-200 bg-white/95 px-4 py-3 backdrop-blur md:px-6 xl:px-8 2xl:px-10">
        <div className="flex items-center justify-between gap-3">
          <div className="min-w-0">
            <div className="flex min-w-0 items-center gap-2">
              <span className="inline-flex h-9 w-9 items-center justify-center rounded-md bg-moss-soft text-moss-dark">
                <Sparkles className="h-5 w-5" />
              </span>
              <div className="min-w-0">
                <h2 className="truncate text-base font-semibold text-ink">Northstar assistant</h2>
                <p className="truncate text-xs text-stone-600">
                  {scopeLabel}
                </p>
              </div>
            </div>
          </div>
          <div className="flex max-w-[52vw] shrink-0 items-center gap-2 overflow-x-auto pb-1 md:max-w-none">
            <Badge tone={identityBadgeTone}>{identityBadge}</Badge>
            <IconButton label="New chat" onClick={resetChat}>
              <RefreshCcw className="h-4 w-4" />
            </IconButton>
            <IconButton label="Run memory scenario" onClick={runMemoryScenario} disabled={loading || !selectedProjectId}>
              <History className="h-4 w-4" />
            </IconButton>
            <IconButton label="Copy latest answer" onClick={() => latestResultMessage && copyAnswer(latestResultMessage)} disabled={!latestResultMessage}>
              <Clipboard className="h-4 w-4" />
            </IconButton>
            <IconButton label="Open settings" onClick={() => setSettingsOpen(true)}>
              <Settings2 className="h-4 w-4" />
            </IconButton>
          </div>
        </div>
      </header>

      <main ref={transcriptRef} data-testid="chat-transcript" className="min-h-0 flex-1 overflow-y-auto px-4 py-6 md:px-6 xl:px-8 2xl:px-10">
        <div className="mx-auto flex max-w-4xl flex-col gap-5">
          {scopeNotice ? (
            <div className="rounded-md border border-rust bg-rust-soft p-3 text-sm text-rust-dark">
              <span className="font-semibold">Scope note:</span> {scopeNotice}
            </div>
          ) : null}
          {messages.length === 0 ? (
            <section className="rounded-md border border-stone-200 bg-white p-6 shadow-sm">
              <div className="flex items-start gap-4">
                <span className="inline-flex h-12 w-12 shrink-0 items-center justify-center rounded-md bg-steel-soft text-steel-dark">
                  <MessageSquare className="h-6 w-6" />
                </span>
                <div>
                  <h3 className="text-xl font-semibold text-ink">Ask a project-scoped knowledge question.</h3>
                  <p className="mt-2 max-w-2xl text-sm leading-6 text-stone-700">
                    The demo still uses the live enterprise RAG API, permission-filtered retrieval, citations, validation, metrics, and feedback. The response text is revealed gradually after the completed `/query` response returns.
                  </p>
                </div>
              </div>
              <div className="mt-5 grid gap-2 sm:grid-cols-2 lg:grid-cols-3">
                {presets.slice(0, 6).map((preset) => (
                  <button
                    key={preset.label}
                    type="button"
                    onClick={() => applyPreset(preset)}
                    className={`group rounded-md border px-3 py-3 text-left transition-[border-color,filter] hover:border-ink/40 hover:brightness-95 focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-moss ${preset.tone}`}
                    aria-label={`Insert question: ${preset.question}`}
                  >
                    <span className="flex items-center justify-between gap-3">
                      <span className="text-sm font-semibold">{preset.label}</span>
                      <span className="inline-flex h-8 w-8 shrink-0 items-center justify-center rounded-full bg-white/80 shadow-sm ring-1 ring-black/10">
                        <MousePointerClick className="h-4 w-4" aria-hidden="true" />
                      </span>
                    </span>
                    <span className="mt-1 block text-xs leading-5 opacity-80">{preset.intent}</span>
                  </button>
                ))}
              </div>
            </section>
          ) : null}

          {messages.map((message) => (
            <article
              key={message.id}
              className={`flex ${message.role === "user" ? "justify-end" : message.role === "system" ? "justify-center" : "justify-start"}`}
            >
              {message.role === "system" ? (
                <div className="max-w-2xl rounded-full border border-stone-200 bg-white px-4 py-2 text-center text-xs text-stone-600 shadow-sm">{message.content}</div>
              ) : (
                <div
                  className={`max-w-[88%] rounded-2xl px-4 py-3 shadow-sm md:max-w-[78%] ${
                    message.role === "user"
                      ? "rounded-br-md bg-ink text-white"
                      : message.status === "error"
                        ? "rounded-bl-md border border-rust bg-rust-soft text-rust-dark"
                        : "rounded-bl-md border border-stone-200 bg-white text-stone-800"
                  }`}
                >
                  {message.role === "assistant" ? (
                    <div className="mb-2 flex flex-wrap items-center gap-2">
                      <span className="inline-flex h-7 w-7 items-center justify-center rounded-md bg-moss-soft text-moss-dark">
                        <Brain className="h-4 w-4" />
                      </span>
                      <span className="text-xs font-semibold uppercase tracking-wide text-stone-500">Assistant</span>
                      {message.responseType ? <Badge tone={message.status === "error" ? "warn" : "neutral"}>{formatMode(message.responseType)}</Badge> : null}
                      {message.status === "streaming" ? <Badge tone="good">revealing</Badge> : null}
                    </div>
                  ) : null}
                  <div className="whitespace-pre-wrap text-sm leading-7">
                    {message.status === "pending" ? (
                      <span className="inline-flex items-center gap-2 text-stone-600">
                        <span>{message.statusText ?? "Thinking..."}</span>
                        <TypingDots />
                      </span>
                    ) : (
                      message.content
                    )}
                    {message.status === "streaming" ? <span className="ml-1 inline-block h-4 w-1 animate-pulse bg-stone-500 align-middle" /> : null}
                  </div>
                  {message.role === "assistant" && message.response ? (
                    <div className="mt-3 flex flex-wrap gap-2">
                      <button
                        type="button"
                        onClick={() =>
                          setToggles((current) => ({
                            ...current,
                            citations: true,
                            retrievedContext: true,
                            metrics: true,
                            validation: true,
                          }))
                        }
                        className="inline-flex items-center gap-2 rounded-md border border-moss bg-moss-soft px-2.5 py-1.5 text-xs font-semibold text-moss-dark hover:border-moss-dark hover:text-ink focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-moss"
                      >
                        <ShieldCheck className="h-3.5 w-3.5" />
                        Why this answer?
                      </button>
                      <button
                        type="button"
                        onClick={() => copyAnswer(message)}
                        className="inline-flex items-center gap-2 rounded-md border border-stone-200 bg-white px-2.5 py-1.5 text-xs font-semibold text-stone-700 hover:border-moss hover:text-ink focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-moss"
                      >
                        <Copy className="h-3.5 w-3.5" />
                        Copy
                      </button>
                      <button
                        type="button"
                        onClick={() => setToggle("citations", !toggles.citations)}
                        className="inline-flex items-center gap-2 rounded-md border border-stone-200 bg-white px-2.5 py-1.5 text-xs font-semibold text-stone-700 hover:border-moss hover:text-ink focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-moss"
                      >
                        <FileText className="h-3.5 w-3.5" />
                        Citations
                      </button>
                      <button
                        type="button"
                        onClick={() => setToggle("retrievedContext", !toggles.retrievedContext)}
                        className="inline-flex items-center gap-2 rounded-md border border-stone-200 bg-white px-2.5 py-1.5 text-xs font-semibold text-stone-700 hover:border-moss hover:text-ink focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-moss"
                      >
                        <BookOpen className="h-3.5 w-3.5" />
                        Sources
                      </button>
                      <button
                        type="button"
                        onClick={() => setToggle("metrics", !toggles.metrics)}
                        className="inline-flex items-center gap-2 rounded-md border border-stone-200 bg-white px-2.5 py-1.5 text-xs font-semibold text-stone-700 hover:border-moss hover:text-ink focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-moss"
                      >
                        <Gauge className="h-3.5 w-3.5" />
                        Metrics
                      </button>
                    </div>
                  ) : null}
                  {message.role === "assistant" ? (
                    <EvidencePanel
                      message={message}
                      toggles={toggles}
                      feedbackRating={feedbackRating}
                      feedbackCategory={feedbackCategory}
                      feedbackComment={feedbackComment}
                      feedbackStatus={feedbackStatus}
                      onRatingChange={setFeedbackRating}
                      onCategoryChange={setFeedbackCategory}
                      onCommentChange={setFeedbackComment}
                      onFeedback={sendFeedback}
                    />
                  ) : null}
                </div>
              )}
            </article>
          ))}

          {error ? <div className="rounded-md border border-rust bg-rust-soft p-4 text-sm font-medium text-rust-dark">{error}</div> : null}
        </div>
      </main>

      <form onSubmit={onSubmit} className="z-20 shrink-0 bg-stone-50 px-4 pb-5 pt-2 md:px-6 xl:px-8 2xl:px-10">
        <div className="mx-auto max-w-4xl">
          <div className="mb-2 flex flex-nowrap gap-2 overflow-x-auto pb-1">
            {presets.slice(0, 4).map((preset) => (
              <button
                key={preset.label}
                type="button"
                onClick={() => applyPreset(preset)}
                className="inline-flex shrink-0 items-center gap-1.5 rounded-full border border-stone-300 bg-white px-3 py-1.5 text-xs font-semibold text-stone-700 transition-colors hover:border-moss hover:text-ink focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-moss"
                aria-label={`Insert question: ${preset.question}`}
              >
                <MousePointerClick className="h-3.5 w-3.5" aria-hidden="true" />
                {preset.label}
              </button>
            ))}
          </div>
          <div className="flex items-end gap-3 rounded-md border border-stone-300 bg-white p-2 shadow-sm focus-within:ring-2 focus-within:ring-moss">
            <textarea
              value={question}
              onChange={(event) => setQuestion(event.target.value)}
              rows={1}
              className="min-h-10 max-h-28 flex-1 resize-none border-0 bg-transparent px-2 py-2 text-sm leading-6 text-ink outline-none"
              placeholder="Ask about policies, permissions, sales guidance, or cross-document expectations..."
            />
            <button type="submit" disabled={queryDisabled} className="btn-primary inline-flex h-11 w-11 shrink-0 items-center justify-center px-0" aria-label="Send message">
              <Send className="h-4 w-4" />
            </button>
          </div>
          <p className="mt-2 truncate text-xs text-stone-500">
            Retrieval: {formatMode(retrievalMode)} / Prompt: {promptVersion} / Multi-doc: {multiDocMode}
            {latestResultMessage?.response ? ` / Last confidence: ${formatMetric(latestResultMessage.response.final_confidence)}` : ""}
          </p>
        </div>
      </form>

      {settingsOpen ? (
        <div className="fixed inset-0 z-40 bg-ink/30" onClick={() => setSettingsOpen(false)} aria-hidden="true" />
      ) : null}
      <aside
        className={`fixed right-0 top-0 z-50 h-full w-full max-w-[440px] transform overflow-y-auto border-l border-stone-300 bg-stone-50 p-5 shadow-2xl transition-transform duration-200 ${
          settingsOpen ? "translate-x-0" : "translate-x-full"
        }`}
        aria-hidden={!settingsOpen}
      >
        <div className="mb-5 flex items-center justify-between gap-3">
          <div>
            <p className="text-xs font-semibold uppercase tracking-wide text-stone-500">Chat controls</p>
            <h2 className="text-xl font-semibold text-ink">Settings</h2>
          </div>
          <IconButton label="Close settings" onClick={() => setSettingsOpen(false)}>
            <X className="h-4 w-4" />
          </IconButton>
        </div>

        <div className="space-y-4">
          <SettingSection icon={<SlidersHorizontal className="h-4 w-4" />} title="Identity & Scope" tone="text-steel">
            <div className="space-y-3">
              <div>
                <label className="text-xs font-semibold text-stone-600" htmlFor="project">Project</label>
                <select
                  id="project"
                  value={selectedProjectId}
                  onChange={(event) => {
                    setSelectedProjectId(event.target.value);
                    setSelectedDepartmentId("");
                    setRequestedScope(null);
                    setScopeNotice(null);
                  }}
                  className="field mt-1 w-full"
                  disabled={scopeLoading && !projects.length}
                >
                  {projects.length ? null : <option value="">{projectsLoading ? "Loading projects" : "No projects loaded"}</option>}
                  {projects.map((project) => (
                    <option key={project.id} value={project.id}>{project.name}</option>
                  ))}
                </select>
              </div>
              <div>
                <label className="text-xs font-semibold text-stone-600" htmlFor="department">Department</label>
                <select
                  id="department"
                  value={selectedDepartmentId}
                  onChange={(event) => {
                    setSelectedDepartmentId(event.target.value);
                    setRequestedScope(null);
                    setScopeNotice(null);
                  }}
                  className="field mt-1 w-full"
                  disabled={!selectedProjectId || scopeLoading}
                >
                  <option value="">All departments</option>
                  {departments.map((department) => (
                    <option key={department.id} value={department.id}>{department.name}</option>
                  ))}
                </select>
              </div>
              <div className="rounded-md border border-stone-200 bg-stone-50 p-3 text-sm text-stone-700">
                <p className="font-semibold text-ink">{identityName}</p>
                <p className="mt-1 text-xs">{identityDetail}</p>
              </div>
            </div>
          </SettingSection>

          <SettingSection icon={<Search className="h-4 w-4" />} title="Retrieval" tone="text-moss">
            <SegmentedControl value={retrievalMode} options={retrievalModes} onChange={setRetrievalMode} />
          </SettingSection>

          <SettingSection icon={<Sparkles className="h-4 w-4" />} title="Generation" tone="text-rust">
            <div className="space-y-3">
              <div>
                <label className="text-xs font-semibold text-stone-600" htmlFor="prompt">Prompt version</label>
                <select id="prompt" value={promptVersion} onChange={(event) => setPromptVersion(event.target.value)} className="field mt-1 w-full">
                  {promptVersions.map((item) => <option key={item}>{item}</option>)}
                </select>
              </div>
              <div>
                <p className="mb-1 text-xs font-semibold text-stone-600">Multi-doc mode</p>
                <SegmentedControl value={multiDocMode} options={multiDocModes} onChange={setMultiDocMode} />
              </div>
            </div>
          </SettingSection>

          <SettingSection icon={<Layers3 className="h-4 w-4" />} title="Demo Presets" tone="text-steel">
            <div className="grid gap-2">
              {presets.map((preset) => (
                <button
                  key={preset.label}
                  type="button"
                  onClick={() => applyPreset(preset)}
                  className={`group rounded-md border px-3 py-3 text-left transition-[border-color,filter] hover:border-ink/40 hover:brightness-95 focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-moss ${preset.tone}`}
                  aria-label={`Insert question: ${preset.question}`}
                >
                  <span className="flex items-center justify-between gap-3">
                    <span className="text-sm font-semibold">{preset.label}</span>
                    <span className="inline-flex h-8 w-8 shrink-0 items-center justify-center rounded-full bg-white/80 shadow-sm ring-1 ring-black/10">
                      <MousePointerClick className="h-4 w-4" aria-hidden="true" />
                    </span>
                  </span>
                  <span className="mt-1 block text-xs leading-5 opacity-80">{preset.intent}</span>
                </button>
              ))}
              <button
                type="button"
                onClick={runMemoryScenario}
                disabled={loading || !selectedProjectId}
                className="inline-flex items-center justify-center gap-2 rounded-md border border-steel bg-white px-3 py-2 text-sm font-semibold text-steel-dark transition-colors hover:bg-steel-soft disabled:opacity-60 focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-steel"
              >
                <History className="h-4 w-4" />
                Run memory follow-up
              </button>
            </div>
          </SettingSection>

          <SettingSection icon={<PanelRightOpen className="h-4 w-4" />} title="Evidence Display" tone="text-moss">
            <div className="space-y-2">
              <ToggleRow label="Citations" checked={toggles.citations} onChange={(checked) => setToggle("citations", checked)} />
              <ToggleRow label="Retrieved context" checked={toggles.retrievedContext} onChange={(checked) => setToggle("retrievedContext", checked)} />
              <ToggleRow label="Metrics" checked={toggles.metrics} onChange={(checked) => setToggle("metrics", checked)} />
              <ToggleRow label="Validation notes" checked={toggles.validation} onChange={(checked) => setToggle("validation", checked)} />
              <ToggleRow label="Feedback" checked={toggles.feedback} onChange={(checked) => setToggle("feedback", checked)} />
            </div>
          </SettingSection>
        </div>
      </aside>
    </div>
  );
}
