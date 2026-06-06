import { Shell } from "@/components/Shell";
import { PermissionDemoClient } from "./PermissionDemoClient";

export default function PermissionDemoPage() {
  return (
    <Shell>
      <h2 className="text-3xl font-semibold">Permission Demo</h2>
      <p className="mt-3 max-w-3xl text-stone-700">
        Run the same role-sensitive question as multiple users and compare refusals, citations, and permission checks.
      </p>
      <div className="mt-6">
        <PermissionDemoClient />
      </div>
    </Shell>
  );
}
