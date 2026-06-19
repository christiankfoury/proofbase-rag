import { PageHeader } from "@/components/PageHeader";
import { Shell } from "@/components/Shell";
import { ProjectWorkspaceClient } from "../ProjectWorkspaceClient";

export default async function ProjectDetailPage({ params }: { params: Promise<{ projectId: string }> }) {
  const resolvedParams = await params;
  return (
    <Shell>
      <PageHeader
        title="Project Workspace"
        description="Project home shows document coverage, quality status, recent activity, and workspace settings."
      />
      <ProjectWorkspaceClient initialProjectId={resolvedParams.projectId} />
    </Shell>
  );
}
