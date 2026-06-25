import { PageHeader } from "@/components/PageHeader";
import { Shell } from "@/components/Shell";
import { ChatDemoClient } from "./ChatDemoClient";

export default function ChatDemoPage() {
  return (
    <Shell>
      <PageHeader title="Chat Demo" />
      <ChatDemoClient />
    </Shell>
  );
}
