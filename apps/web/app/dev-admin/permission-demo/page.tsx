import { PageHeader } from "@/components/PageHeader";
import { Shell } from "@/components/Shell";
import { PermissionDemoClient } from "./PermissionDemoClient";

export default function PermissionDemoPage() {
  return (
    <Shell>
      <PageHeader
        title="Permission Demo"
        description="Admin-only simulation: run the same role-sensitive question as multiple users and compare refusals, citations, and permission checks."
      />
      <PermissionDemoClient />
    </Shell>
  );
}
