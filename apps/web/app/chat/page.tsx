import { PageHeader } from "@/components/PageHeader";
import { Shell } from "@/components/Shell";
import { ChatDemoClient } from "./ChatDemoClient";

export default function ChatDemoPage() {
  return (
    <Shell>
      <PageHeader
        title="Chat Demo"
        description="Ask the enterprise RAG API live from a selected project or department, switch demo roles, inspect citations and retrieved context, and submit feedback. This is a recruiter demo UI, not production authentication."
      />
      <ChatDemoClient />
    </Shell>
  );
}
