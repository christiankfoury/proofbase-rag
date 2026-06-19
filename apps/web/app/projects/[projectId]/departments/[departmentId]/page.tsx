import { PageHeader } from "@/components/PageHeader";
import { Shell } from "@/components/Shell";
import { DepartmentDetailClient } from "./DepartmentDetailClient";

export default async function DepartmentDetailPage({
  params,
}: {
  params: Promise<{ projectId: string; departmentId: string }>;
}) {
  const resolvedParams = await params;
  return (
    <Shell>
      <PageHeader
        title="Department Workspace"
        description="Department detail shows icon, access defaults, document coverage, and editable workspace settings."
      />
      <DepartmentDetailClient projectId={resolvedParams.projectId} departmentId={resolvedParams.departmentId} />
    </Shell>
  );
}
