import { Shell } from "@/components/Shell";
import { ChatDemoClient } from "./ChatDemoClient";

export default function ChatDemoPage() {
  return (
    <Shell>
      <h2 className="text-3xl font-semibold">Chat Demo</h2>
      <p className="mt-3 max-w-3xl text-stone-700">
        Ask the enterprise RAG API live, switch demo roles, inspect citations and retrieved context, and submit feedback.
        This is a recruiter demo UI, not production authentication.
      </p>
      <div className="mt-6">
        <ChatDemoClient />
      </div>
    </Shell>
  );
}
