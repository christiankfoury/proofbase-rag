import Link from "next/link";
import {
  BookOpen,
  Brain,
  CheckCircle2,
  Database,
  FileText,
  Gauge,
  GitBranch,
  LockKeyhole,
  MessageSquare,
  Search,
  ShieldCheck,
  Sparkles,
} from "lucide-react";
import { Badge } from "@/components/Badge";
import { Card } from "@/components/Card";
import { PageHeader } from "@/components/PageHeader";
import { SectionHeading } from "@/components/SectionHeading";
import { Shell } from "@/components/Shell";

const mentalModel = [
  {
    title: "Ask a scoped question",
    detail: "The app starts with the user's question, selected project, optional department, and signed-in demo role.",
    icon: MessageSquare,
    tone: "moss",
  },
  {
    title: "Find allowed evidence",
    detail: "Retrieval searches indexed chunks while applying project, department, and role filters before generation.",
    icon: Search,
    tone: "steel",
  },
  {
    title: "Answer from context",
    detail: "The model receives only retrieved context and returns structured JSON with response type and citations.",
    icon: Sparkles,
    tone: "rust",
  },
  {
    title: "Validate the proof",
    detail: "The backend checks citations against retrieved chunks and returns confidence, evidence, latency, and logs.",
    icon: CheckCircle2,
    tone: "moss",
  },
];

const currentDefaults = [
  {
    label: "Chunking",
    value: "section_based",
    detail: "Markdown documents are split by section headings so citations map to readable policy sections.",
  },
  {
    label: "Chat default retrieval",
    value: "vector_lexical_rerank",
    detail: "The App chat defaults to vector search with lexical reranking over section-based chunks.",
  },
  {
    label: "Multi-doc mode",
    value: "auto",
    detail: "The API can detect some multi-document questions and retrieve evidence across planned subqueries.",
  },
  {
    label: "Measured reference",
    value: "vector_lexical_rerank",
    detail: "The strongest measured retrieval reference adds lexical reranking to vector candidates.",
  },
];

const glossary = [
  ["RAG", "Retrieval-augmented generation: find relevant evidence first, then ask the model to answer from that evidence."],
  ["Chunk", "A smaller searchable section of a document, stored with source metadata and an embedding."],
  ["Embedding", "A numeric representation of text meaning used for semantic vector search."],
  ["Vector search", "Search that compares the question embedding to stored chunk embeddings."],
  ["Keyword search", "PostgreSQL full-text search over exact words and policy terms."],
  ["Hybrid search", "A retrieval mode that merges vector and keyword candidates with weighted scores."],
  ["Reranking", "A second ranking step that reorders retrieved candidates using extra scoring logic."],
  ["Top-k", "The number of chunks returned to generation."],
  ["Citation", "A structured pointer to the document, section, chunk ID, and support text behind a claim."],
  ["Confidence", "A heuristic score built from retrieval quality, citation support, and answer support."],
  ["Memory", "Previous chat turns used to rewrite follow-up questions, not as source evidence."],
  ["Permission leakage", "A restricted source appearing in retrieved chunks or citations for a role that should not access it."],
  ["Multi-document", "A question that needs evidence from more than one source document."],
];

const modules = [
  {
    title: "Ingestion and chunking",
    icon: FileText,
    summary: "Documents become reviewable, searchable chunks.",
    detail: "Seeded Markdown and approved uploaded documents are normalized, split into chunks, embedded, and stored with document, version, project, department, and access-role metadata.",
  },
  {
    title: "Retrieval and ranking",
    icon: Search,
    summary: "The app chooses candidate chunks.",
    detail: "Retrieval can use vector search, keyword search, hybrid scoring, or vector plus lexical reranking. The App currently sends section-based chunking and vector + lexical rerank retrieval by default.",
  },
  {
    title: "Permission filtering",
    icon: LockKeyhole,
    summary: "Unsafe evidence is filtered before generation.",
    detail: "Project, department, document status, indexed-version status, and role overlap are applied before retrieved chunks are sent to the answer generator.",
  },
  {
    title: "Generation",
    icon: Sparkles,
    summary: "The model answers from retrieved context.",
    detail: "The answer prompt requires structured JSON, response types, citations, no unsupported guesses, and clarification for ambiguous questions.",
  },
  {
    title: "Citation validation",
    icon: ShieldCheck,
    summary: "Citations must match retrieved chunks.",
    detail: "The backend matches model citations to retrieved chunk IDs or source metadata, can backfill supporting citations, and flags weak support.",
  },
  {
    title: "Confidence and evaluation",
    icon: Gauge,
    summary: "Quality is scored and compared.",
    detail: "Confidence is heuristic. Promotion decisions should use exported benchmark runs for retrieval, answer quality, memory, and permission safety.",
  },
  {
    title: "Memory",
    icon: Brain,
    summary: "Memory clarifies follow-ups only.",
    detail: "Previous turns can rewrite a vague follow-up into a standalone question. They do not become source evidence and cannot bypass permissions.",
  },
  {
    title: "Multi-document orchestration",
    icon: GitBranch,
    summary: "Some questions need multiple sources.",
    detail: "The system can detect cross-domain questions, decompose them into subqueries, retrieve per source need, group evidence by document, and use a multi-document prompt.",
  },
];

const proofSteps = [
  {
    title: "Candidate chunks",
    detail: "The system first identifies likely source chunks from active, indexed documents.",
    width: "lg:w-full",
    tone: "steel",
  },
  {
    title: "Role-filtered chunks",
    detail: "Project, department, and access-role filters decide what may reach generation.",
    width: "lg:w-11/12",
    tone: "moss",
  },
  {
    title: "Generated answer",
    detail: "The model answers only from the retrieved context and declares a response type.",
    width: "lg:w-10/12",
    tone: "rust",
  },
  {
    title: "Validated citations",
    detail: "Returned citations are checked against the retrieved chunks and scored for support.",
    width: "lg:w-9/12",
    tone: "moss",
  },
];

const proofLinks = [
  ["Ask the assistant", "/chat"],
  ["Open projects", "/projects"],
  ["Quality lab", "/dev-admin/retrieval-playground"],
  ["Run comparison", "/dev-admin/runs"],
  ["Permission safety", "/dev-admin/permission-safety"],
  ["Memory evaluation", "/dev-admin/memory-evaluation"],
];

const toneStyles = {
  moss: {
    badge: "border-moss bg-moss-soft text-moss-dark",
    panel: "border-moss bg-moss-soft/50",
  },
  steel: {
    badge: "border-steel bg-steel-soft text-steel-dark",
    panel: "border-steel bg-steel-soft/60",
  },
  rust: {
    badge: "border-rust bg-rust-soft text-rust-dark",
    panel: "border-rust bg-rust-soft/60",
  },
} as const;

function toneKey(tone: string) {
  return tone as keyof typeof toneStyles;
}

export default function AlgorithmGuidePage() {
  return (
    <Shell>
      <PageHeader
        title="Algorithm Guide"
        description={
          <p className="text-lg text-stone-800">
            A plain-English map of how the assistant finds evidence, keeps restricted content out of generation, and returns cited answers with proof.
          </p>
        }
        actions={
          <>
            <Link href="/chat" className="btn-primary">
              Ask the assistant
            </Link>
            <Link href="/dev-admin/retrieval-playground" className="btn-secondary">
              Open quality lab
            </Link>
          </>
        }
      />

      <div className="grid gap-6">
        <Card tone="good" className="overflow-hidden">
          <div className="flex flex-col gap-4 lg:flex-row lg:items-start lg:justify-between">
            <div className="max-w-4xl">
              <p className="badge-good">Simple mental model</p>
              <h2 className="mt-3 text-2xl font-semibold text-ink">Question, evidence, answer, proof</h2>
              <p className="mt-3 text-stone-700">
                The app does not ask the model to answer from memory alone. It first searches the knowledge workspace for allowed evidence, then asks the model to answer only from that evidence.
              </p>
            </div>
            <Badge tone="solid" className="shrink-0">RAG overview</Badge>
          </div>

          <div className="mt-6 grid gap-3 lg:grid-cols-4">
            {mentalModel.map((step, index) => {
              const Icon = step.icon;
              const styles = toneStyles[toneKey(step.tone)];
              return (
                <article key={step.title} className={`rounded-md border p-4 ${styles.panel}`}>
                  <div className="flex items-center justify-between gap-3">
                    <span className={`inline-flex h-10 w-10 items-center justify-center rounded border bg-white ${styles.badge}`}>
                      <Icon className="h-5 w-5" aria-hidden="true" />
                    </span>
                    <span className="text-sm font-semibold text-stone-500">{String(index + 1).padStart(2, "0")}</span>
                  </div>
                  <h3 className="mt-4 font-semibold text-ink">{step.title}</h3>
                  <p className="mt-2 text-sm leading-6 text-stone-700">{step.detail}</p>
                </article>
              );
            })}
          </div>
        </Card>

        <Card>
          <SectionHeading
            title="End-To-End Flow"
            description="The graph shows the normal request path from user question to validated answer."
          />
          <div className="grid gap-3 lg:grid-cols-[1fr_1fr_1fr_1fr_1fr]">
            {[
              ["User question", "Project, department, and signed-in role shape the request.", MessageSquare],
              ["Memory rewrite", "Follow-up questions may become standalone search queries.", Brain],
              ["Retrieval", "Postgres and pgvector return matching indexed chunks.", Database],
              ["Generation", "The model answers from permission-filtered context.", Sparkles],
              ["Validation", "Citations, confidence, logs, and evidence are returned.", ShieldCheck],
            ].map(([title, detail, Icon], index) => {
              const StepIcon = Icon as typeof MessageSquare;
              return (
                <div key={title as string} className="relative rounded-md border border-stone-300 bg-white p-4 shadow-card">
                  <div className="flex items-start gap-3">
                    <span className="inline-flex h-9 w-9 shrink-0 items-center justify-center rounded border border-moss bg-moss-soft text-moss-dark">
                      <StepIcon className="h-4 w-4" aria-hidden="true" />
                    </span>
                    <div>
                      <p className="text-xs font-semibold uppercase tracking-wide text-stone-500">Step {index + 1}</p>
                      <h3 className="mt-1 font-semibold text-ink">{title as string}</h3>
                    </div>
                  </div>
                  <p className="mt-3 text-sm leading-6 text-stone-700">{detail as string}</p>
                </div>
              );
            })}
          </div>
        </Card>

        <Card tone="good">
          <SectionHeading
            title="What The App Uses Today"
            description="These are current implementation facts, not future claims."
          />
          <div className="grid gap-3 md:grid-cols-2 xl:grid-cols-4">
            {currentDefaults.map((item) => (
              <article key={item.label} className="rounded-md border border-moss bg-white p-4 shadow-card">
                <p className="text-xs font-semibold uppercase tracking-wide text-stone-500">{item.label}</p>
                <p className="mt-2 break-words font-mono text-lg font-semibold text-moss-dark">{item.value}</p>
                <p className="mt-2 text-sm leading-6 text-stone-700">{item.detail}</p>
              </article>
            ))}
          </div>
        </Card>

        <Card>
          <SectionHeading
            title="Term Glossary"
            description="Short definitions for the words used across chat, proof panels, and Dev/Admin pages."
          />
          <div className="grid gap-3 md:grid-cols-2 xl:grid-cols-3">
            {glossary.map(([term, definition]) => (
              <article key={term} className="rounded-md border border-stone-300 bg-stone-50 p-4">
                <h3 className="font-semibold text-ink">{term}</h3>
                <p className="mt-2 text-sm leading-6 text-stone-700">{definition}</p>
              </article>
            ))}
          </div>
        </Card>

        <Card tone="good">
          <div className="flex flex-col gap-4 lg:flex-row lg:items-start lg:justify-between">
            <SectionHeading
              title="Algorithm Modules"
              description="Each module has a beginner summary and a deeper implementation note."
              className="mb-0"
            />
            <Badge tone="good" className="shrink-0">Deeper detail</Badge>
          </div>
          <div className="mt-5 grid gap-3 md:grid-cols-2">
            {modules.map((item) => {
              const Icon = item.icon;
              return (
                <details key={item.title} className="group rounded-md border border-stone-300 bg-white p-4 shadow-card">
                  <summary className="flex cursor-pointer list-none items-start gap-3">
                    <span className="inline-flex h-10 w-10 shrink-0 items-center justify-center rounded border border-moss bg-moss-soft text-moss-dark">
                      <Icon className="h-5 w-5" aria-hidden="true" />
                    </span>
                    <span className="min-w-0 flex-1">
                      <span className="block font-semibold text-ink">{item.title}</span>
                      <span className="mt-1 block text-sm leading-6 text-stone-700">{item.summary}</span>
                    </span>
                    <span className="ml-auto rounded border border-stone-300 px-2 py-1 text-xs font-semibold text-stone-600 group-open:bg-moss-soft group-open:text-moss-dark">
                      More
                    </span>
                  </summary>
                  <p className="mt-4 border-t border-stone-200 pt-4 text-sm leading-6 text-stone-700">{item.detail}</p>
                </details>
              );
            })}
          </div>
        </Card>

        <Card>
          <div className="grid gap-6 xl:grid-cols-[0.9fr_1.1fr] xl:items-start">
            <div>
              <p className="badge-good">Safety funnel</p>
              <h2 className="mt-3 text-2xl font-semibold text-ink">Why restricted evidence stays out</h2>
              <p className="mt-3 text-stone-700">
                The permission boundary is before generation. Candidate evidence may exist in the database, but only chunks matching the signed-in role and selected scope can be sent to the model.
              </p>
              <div className="mt-5 grid gap-3 sm:grid-cols-2">
                <div className="rounded-md border border-stone-300 bg-stone-50 p-4">
                  <p className="font-semibold text-ink">Memory boundary</p>
                  <p className="mt-2 text-sm leading-6 text-stone-700">Previous turns can clarify a follow-up question, but they are not cited as source evidence.</p>
                </div>
                <div className="rounded-md border border-stone-300 bg-stone-50 p-4">
                  <p className="font-semibold text-ink">Citation boundary</p>
                  <p className="mt-2 text-sm leading-6 text-stone-700">Citations must point back to retrieved chunks that survived the filters.</p>
                </div>
              </div>
            </div>
            <div className="flex flex-col items-center gap-3">
              {proofSteps.map((step, index) => {
                const styles = toneStyles[toneKey(step.tone)];
                return (
                  <article key={step.title} className={`w-full ${step.width} rounded-md border p-4 shadow-card ${styles.panel}`}>
                    <div className="flex items-center justify-between gap-4">
                      <h3 className="font-semibold text-ink">{step.title}</h3>
                      <span className={`rounded border px-2 py-1 text-xs font-semibold uppercase tracking-wide ${styles.badge}`}>
                        {index + 1}
                      </span>
                    </div>
                    <p className="mt-2 text-sm leading-6 text-stone-700">{step.detail}</p>
                  </article>
                );
              })}
            </div>
          </div>
        </Card>

        <Card tone="good">
          <div className="grid gap-5 lg:grid-cols-[1fr_1fr] lg:items-start">
            <div>
              <p className="badge-good">Measured changes only</p>
              <h2 className="mt-3 text-2xl font-semibold text-ink">How improvements are chosen</h2>
              <p className="mt-3 text-stone-700">
                New retrieval, chunking, prompt, memory, or multi-document behavior should be promoted only after benchmark evidence shows the change improved quality without weakening permission safety.
              </p>
              <p className="mt-3 text-sm leading-6 text-stone-700">
                That is why experimental ideas, like new chunking algorithms, belong in Dev/Admin comparison first instead of silently changing the App default.
              </p>
            </div>
            <div className="grid gap-3 sm:grid-cols-2">
              {proofLinks.map(([label, href]) => (
                <Link key={href} href={href} className="btn-secondary justify-start">
                  <BookOpen className="h-4 w-4" aria-hidden="true" />
                  {label}
                </Link>
              ))}
            </div>
          </div>
        </Card>
      </div>
    </Shell>
  );
}
