import { PageHeader } from "@/components/PageHeader";
import { Shell } from "@/components/Shell";
import { ProjectWorkspaceClient } from "./ProjectWorkspaceClient";

export default function ProjectsPage() {
  return (
    <Shell>
      <PageHeader
        title="Project Workspaces"
        description="Create and manage knowledge workspaces, review indexed coverage, and keep project quality status visible."
      />
      <ProjectWorkspaceClient />
    </Shell>
  );
}
