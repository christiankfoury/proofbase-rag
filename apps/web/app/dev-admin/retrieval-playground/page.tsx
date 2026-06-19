import { PageHeader } from "@/components/PageHeader";
import { Shell } from "@/components/Shell";
import { RetrievalPlaygroundClient } from "./RetrievalPlaygroundClient";

export default function RetrievalPlaygroundPage() {
  return (
    <Shell>
      <PageHeader
        title="Retrieval Playground"
        description="Compare vector, keyword, hybrid, and forced multi-document query paths using the same question and real API output."
      />
      <RetrievalPlaygroundClient />
    </Shell>
  );
}
