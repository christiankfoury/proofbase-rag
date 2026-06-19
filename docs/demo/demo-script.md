# Enterprise Knowledge Agent Demo Script

This five-minute demo is designed for recruiters and engineering interviewers. Lead with the App side, then move into Dev/Admin proof for quality, permissions, failures, and operations.

## Setup

Start the Docker stack:

```powershell
docker compose up --build
```

Initialize and ingest:

```powershell
docker compose run --rm api python scripts/setup_db.py
docker compose run --rm api python scripts/ingest_markdown.py --apply-schema --chunking-strategy section_based
```

Open:

- App: `http://localhost:3000`
- API health: `http://localhost:8000/health`
- API readiness: `http://localhost:8000/ready`

If port `3000` is busy, set `WEB_PORT=3001` and open `http://localhost:3001`.

## Scene 1: App Home And Demo Path

Open: `/`

Point out:

- The first screen is a product workspace, not a metrics wall.
- The four-step demo path goes from project workspace to department knowledge, scoped assistant, and Dev/Admin proof.
- The App side is intentionally separate from Dev/Admin evaluation and operations.

Expected takeaway:

> This is presented as an internal knowledge product with measurable engineering controls behind it.

## Scene 2: Project Workspace

Open: `/projects`

Select the seeded `Northstar Analytics` project.

Point out:

- Projects are durable knowledge workspaces.
- The seeded project maps the synthetic enterprise corpus into departments.
- Workspace quality and document coverage are visible before asking questions.

Expected behavior:

- `Northstar Analytics` appears as seeded demo data.
- The project detail page shows departments, document counts, and project-scoped assistant entry points.

## Scene 3: Department Document Library

Open a seeded department, for example:

`/projects/00000000-0000-0000-0000-000000000019/departments/00000000-0000-0000-0000-000000002001`

Point out:

- Department workspaces have icons, descriptions, access defaults, and document inventories.
- Indexed corpus documents show roles, status, active version metadata, and extracted Markdown preview.
- PDF upload creates reviewable Markdown, but uploaded files are not indexed until a future approval/indexing step.

Expected behavior:

- The document library shows seeded indexed documents.
- The upload form and review status make ingestion limits explicit.

## Scene 4: Scoped Assistant With Citations

Open: `/chat`

Use:

- Project: `Northstar Analytics`
- Department: `All departments`
- Role: `Employee`
- Question: `Where does Northstar Analytics have offices?`

Expected behavior:

- The response type is `answer`.
- The answer cites an HR source such as `HR-001`.
- Confidence, latency, citations, and retrieved context are visible.

Point out:

- Retrieval is scoped to the selected project.
- Citations are structured evidence, not decorative footnotes.
- Retrieved context is shown for engineering review.

## Scene 5: Safe Refusal And Role Contrast

In `/chat`, ask as `Employee`:

```text
What is the promotion calibration process?
```

Expected behavior:

- The system refuses because the employee role should not access manager-only guidance.
- Restricted chunks do not reach generation.

Then open `/dev-admin/permission-demo` and run the same question across roles.

Point out:

- Permission filtering happens before generation.
- The same question can have different valid outcomes by role.
- Permission evaluation reports zero leakage in the benchmark artifacts.

## Scene 6: Missing Information And Memory

In `/chat`, ask:

```text
What is Northstar's sabbatical policy?
```

Expected behavior:

- The assistant returns a missing-information response instead of inventing a policy.

Then use the memory scenario button or ask the vacation question followed by:

```text
Can I carry any unused days into next year?
```

Point out:

- Memory helps rewrite follow-up questions.
- Memory is not treated as source evidence; retrieved documents remain the source of truth.

## Scene 7: Algorithm Quality Lab

Open: `/dev-admin/retrieval-playground`

Use:

- Question: `If I work remotely, what approval and device security expectations apply?`
- Role: `Employee`

Point out:

- Named profiles compare vector, keyword, hybrid, and multi-document behavior.
- Results include source coverage, citation coverage, latency, cost signals, and known failure visibility.
- Review notes are audit-backed; profile promotion is not automatic.

## Scene 8: Failed Question And Human Review

Open: `/dev-admin/failed-questions`

Expand a known failure such as `MULTI-005`.

Point out:

- The UI keeps expected answer, actual answer, expected sources, actual citations, root cause, and suggested fix together.
- Evaluators can label answer correctness and citation correctness independently.
- Saving a review creates a candidate or needs-fix decision, but it does not mutate benchmark JSON automatically.

Optional: open `/dev-admin/feedback` and show the same review workflow for negative user feedback.

## Closing Pitch

End with:

> The project shows the enterprise AI loop end to end: organize knowledge, scope retrieval, answer with citations, enforce permissions before generation, measure quality, inspect failures, collect human review, and keep limitations visible.

## Honest Limitations To Mention

- The corpus is synthetic.
- Querying requires a configured `OPENAI_API_KEY`.
- `/chat` is a demo UI, not production authentication.
- Uploaded PDFs are extracted for review, but approval/indexing for those uploads is future work.
- Azure deployment is documented as ready work, not claimed as completed.
- Project-scoped benchmarks and automatic candidate promotion remain future work.
