# Phase 20 Department Workspace Design

## Goal

Phase 20 makes departments project-local knowledge areas. This gives the seeded Northstar workspace recognizable business sections and gives new projects a way to organize knowledge before upload and project-scoped retrieval arrive.

## Seeded Department Mapping

The existing corpus uses broad `department` metadata and more specific `category` metadata. Phase 20 maps seeded departments by category so restricted admin knowledge remains visible as separate workspaces:

| Corpus category | Department workspace |
|---|---|
| `HR Public` | People Operations |
| `HR Admin` | HR Admin |
| `IT Public` | IT and Security |
| `IT Admin` | IT Admin |
| `Sales Enablement` | Sales |
| `Manager Only` | Management |

This preserves the original document metadata while giving the App side a cleaner product model.

## Data Model

`project_departments` stores:

- `project_id`
- `name`
- `icon`
- `color`
- `description`
- `default_access_roles`
- `seeded_data_key`
- `status`
- timestamps and `archived_at`

`documents.department_id` links indexed documents to departments. Retrieval still ignores this field until project/department-scoped RAG is implemented.

## API

| Method | Route | Purpose |
|---|---|---|
| `POST` | `/projects/{project_id}/departments` | Create a department. |
| `GET` | `/projects/{project_id}/departments/{department_id}` | Load department detail. |
| `PATCH` | `/projects/{project_id}/departments/{department_id}` | Update department metadata. |
| `DELETE` | `/projects/{project_id}/departments/{department_id}` | Soft archive a department. |

Project detail responses now include department metadata and coverage counts.

## Product Boundaries

Department defaults do not yet enforce retrieval access. They are durable planning metadata for document organization and future permission management. Existing role filtering still happens at the document/chunk retrieval layer before generation.

Department-scoped assistant and document lists are planned for later phases.
