"use client";

import { useState } from "react";
import { QueryResponse, UserRole, queryRag } from "@/lib/api";
import { formatLabel } from "@/lib/dashboard";

const roles: UserRole[] = ["Employee", "Sales Representative", "Manager", "HR Admin"];

type RoleResult = {
  role: UserRole;
  result?: QueryResponse;
  error?: string;
};

function permissionResult(result?: QueryResponse): string {
  if (!result) return "not run";
  if (result.permission_check.unauthorized_chunks_reached_generation) return "unsafe exposure";
  if (result.response_type === "refuse_no_access") return "blocked";
  if (result.citations.length) return "answered with citations";
  return "answered or not found";
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
      <div className="rounded-md border border-stone-300 bg-white p-5">
        <label className="text-sm font-semibold" htmlFor="permission-question">Question</label>
        <div className="mt-2 flex flex-col gap-3 md:flex-row">
          <input
            id="permission-question"
            value={question}
            onChange={(event) => setQuestion(event.target.value)}
            className="min-w-0 flex-1 rounded border border-stone-300 px-3 py-2"
          />
          <button type="button" onClick={runAll} disabled={loading} className="rounded bg-ink px-4 py-2 font-semibold text-white disabled:opacity-60">
            {loading ? "Running..." : "Run role comparison"}
          </button>
        </div>
        <p className="mt-3 text-sm text-stone-600">
          The default question uses promotion calibration because the current corpus supports the intended role contrast.
        </p>
      </div>

      <div className="overflow-x-auto rounded-md border border-stone-300 bg-white">
        <table className="w-full min-w-[980px] text-left text-sm">
          <thead className="bg-stone-100 text-stone-700">
            <tr>
              <th className="p-3">Role</th>
              <th className="p-3">Response Type</th>
              <th className="p-3">Answer Preview</th>
              <th className="p-3 text-right">Citations</th>
              <th className="p-3">Unauthorized Chunks</th>
              <th className="p-3">Permission Result</th>
            </tr>
          </thead>
          <tbody>
            {results.map(({ role, result, error }) => (
              <tr key={role} className="border-t border-stone-200 align-top">
                <td className="whitespace-nowrap p-3 font-semibold">{role}</td>
                <td className="whitespace-nowrap p-3">{result ? formatLabel(result.response_type) : error ? "Error" : "Not run"}</td>
                <td className="p-3">
                  {error ? <span className="text-rust">{error}</span> : result?.answer ? `${result.answer.slice(0, 220)}${result.answer.length > 220 ? "..." : ""}` : "Run the comparison."}
                </td>
                <td className="p-3 text-right">{result?.citations.length ?? "-"}</td>
                <td className="p-3">{result ? String(result.permission_check.unauthorized_chunks_reached_generation) : "-"}</td>
                <td className="p-3">{permissionResult(result)}</td>
              </tr>
            ))}
          </tbody>
        </table>
      </div>
    </section>
  );
}
