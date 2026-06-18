"use client";

import { useState } from "react";
import { Badge, BadgeTone } from "@/components/Badge";
import { Card } from "@/components/Card";
import { QueryResponse, UserRole, queryRag } from "@/lib/api";
import { formatLabel } from "@/lib/dashboard";

const roles: UserRole[] = ["Employee", "Sales Representative", "Manager", "HR Admin"];

type RoleResult = {
  role: UserRole;
  result?: QueryResponse;
  error?: string;
};

function permissionResult(result?: QueryResponse): { text: string; tone: BadgeTone } {
  if (!result) return { text: "Not run", tone: "neutral" };
  if (result.permission_check.unauthorized_chunks_reached_generation) return { text: "Unsafe exposure", tone: "warn" };
  if (result.response_type === "refuse_no_access") return { text: "Blocked", tone: "info" };
  if (result.citations.length) return { text: "Answered with citations", tone: "good" };
  return { text: "Answered or not found", tone: "neutral" };
}

export function PermissionDemoClient() {
  const [question, setQuestion] = useState("What is the promotion calibration process?");
  const [results, setResults] = useState<RoleResult[]>(roles.map((role) => ({ role })));
  const [loading, setLoading] = useState(false);

  async function runAll() {
    setLoading(true);
    const nextResults: RoleResult[] = [];
    for (const role of roles) {
      try {
        const result = await queryRag({
          question,
          user_role: role,
          retrieval_mode: "vector_only",
          chunking_strategy: "section_based",
          multi_doc_mode: "off",
        });
        nextResults.push({ role, result });
      } catch (exc) {
        nextResults.push({ role, error: exc instanceof Error ? exc.message : "Query failed." });
      }
    }
    setResults(nextResults);
    setLoading(false);
  }

  return (
    <section className="space-y-5">
      <Card>
        <label className="text-sm font-semibold text-ink" htmlFor="permission-question">Question</label>
        <div className="mt-2 flex flex-col gap-3 md:flex-row">
          <input
            id="permission-question"
            value={question}
            onChange={(event) => setQuestion(event.target.value)}
            className="field min-w-0 flex-1"
          />
          <button type="button" onClick={runAll} disabled={loading} className="btn-primary">
            {loading ? "Running..." : "Run role comparison"}
          </button>
        </div>
        <p className="mt-3 text-sm text-stone-600">
          The default question uses promotion calibration because the current corpus supports the intended role contrast.
        </p>
      </Card>

      <div className="overflow-x-auto rounded-md border border-stone-300 bg-white shadow-card">
        <table className="data-table min-w-[980px]">
          <thead>
            <tr>
              <th>Role</th>
              <th>Response Type</th>
              <th>Answer Preview</th>
              <th className="text-right">Citations</th>
              <th>Unauthorized Chunks</th>
              <th>Permission Result</th>
            </tr>
          </thead>
          <tbody>
            {results.map(({ role, result, error }) => {
              const permission = permissionResult(result);
              const unauthorized = result?.permission_check.unauthorized_chunks_reached_generation;
              return (
                <tr key={role}>
                  <td className="whitespace-nowrap font-semibold text-ink">{role}</td>
                  <td className="whitespace-nowrap">{result ? formatLabel(result.response_type) : error ? "Error" : "Not run"}</td>
                  <td>
                    {error ? (
                      <span className="font-medium text-rust-dark">{error}</span>
                    ) : result?.answer ? (
                      `${result.answer.slice(0, 220)}${result.answer.length > 220 ? "..." : ""}`
                    ) : (
                      "Run the comparison."
                    )}
                  </td>
                  <td className="text-right">{result?.citations.length ?? "-"}</td>
                  <td className={unauthorized ? "font-semibold text-red-600" : ""}>{result ? String(unauthorized) : "-"}</td>
                  <td>
                    <Badge tone={permission.tone}>{permission.text}</Badge>
                  </td>
                </tr>
              );
            })}
          </tbody>
        </table>
      </div>
    </section>
  );
}
