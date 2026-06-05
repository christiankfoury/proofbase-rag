import { Shell } from "@/components/Shell";
import { formatMetric, getDashboardData } from "@/lib/dashboard";

export default async function FailedQuestionsPage() {
  const data = await getDashboardData();

  return (
    <Shell>
      <h2 className="text-3xl font-semibold">Failed Questions</h2>
      <p className="mt-3 max-w-3xl text-stone-700">
        These failures are the next improvement backlog. They are exported from the Phase 7 and Phase 9 failed-question reports.
      </p>
      <div className="mt-6 overflow-x-auto rounded-md border border-stone-300 bg-white">
        <table className="w-full min-w-[960px] text-left text-sm">
          <thead className="bg-stone-100">
            <tr>
              <th className="p-3">Question</th>
              <th className="p-3">Phase</th>
              <th className="p-3">Failure</th>
              <th className="p-3">Actual</th>
              <th className="p-3 text-right">Citation Conf</th>
              <th className="p-3 text-right">Answer Conf</th>
              <th className="p-3">Recommended Fix</th>
            </tr>
          </thead>
          <tbody>
            {data.failed_questions.map((item) => (
              <tr key={`${item.phase}-${item.question_id}`} className="border-t border-stone-200">
                <td className="p-3 font-medium">{item.question_id}</td>
                <td className="p-3">{item.phase}</td>
                <td className="p-3">{item.failure_type}</td>
                <td className="p-3">{item.actual_response_type ?? "n/a"}</td>
                <td className="p-3 text-right">{formatMetric(item.citation_confidence)}</td>
                <td className="p-3 text-right">{formatMetric(item.answer_confidence)}</td>
                <td className="p-3">{item.recommended_fix}</td>
              </tr>
            ))}
          </tbody>
        </table>
      </div>
    </Shell>
  );
}
