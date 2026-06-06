import { Shell } from "@/components/Shell";
import { RetrievalPlaygroundClient } from "./RetrievalPlaygroundClient";

export default function RetrievalPlaygroundPage() {
  return (
    <Shell>
      <h2 className="text-3xl font-semibold">Retrieval Playground</h2>
      <p className="mt-3 max-w-3xl text-stone-700">
        Compare vector, keyword, hybrid, and forced multi-document query paths using the same question and real API output.
      </p>
      <div className="mt-6">
        <RetrievalPlaygroundClient />
      </div>
    </Shell>
  );
}
