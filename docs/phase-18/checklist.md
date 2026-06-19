# Phase 18 Checklist

## App Surface

- [x] Make `/` the App Home.
- [x] Keep `/chat` as the working assistant route.
- [x] Use Assistant First positioning on the App Home.
- [x] Show Projects, Departments, Documents, and Algorithm Verification as planned next capabilities.
- [x] Avoid fake project data, mock CRUD, upload flows, or new backend models.

## Dev/Admin Surface

- [x] Move evaluation and operations pages under `/dev-admin`.
- [x] Preserve the previous metrics overview at `/dev-admin`.
- [x] Move run comparison to `/dev-admin/runs`.
- [x] Move run detail to `/dev-admin/evaluation/runs/[run_id]`.
- [x] Move failed questions to `/dev-admin/failed-questions`.
- [x] Move retrieval playground to `/dev-admin/retrieval-playground`.
- [x] Move permission demo to `/dev-admin/permission-demo`.
- [x] Move multi-doc to `/dev-admin/multi-doc`.
- [x] Move observability to `/dev-admin/observability`.
- [x] Move feedback to `/dev-admin/feedback`.
- [x] Move audit logs to `/dev-admin/audit`.
- [x] Move deep evaluation pages under `/dev-admin`.
- [x] Do not add redirects for old Dev/Admin URLs.

## Layout And Navigation

- [x] Replace flat top navigation with grouped sidebar navigation.
- [x] Add App, Dev/Admin, and Deep Evaluation navigation groups.
- [x] Update metadata away from evaluation-only wording.
- [x] Preserve existing visual language without a full redesign.

## Documentation

- [x] Add Phase 18 navigation design notes.
- [x] Update README route list.
- [x] Update interactive demo route list.
- [x] Update screenshot and final cleanup route checks.

## Verification

- [x] Run `cd apps/web; npm run build`.
- [x] Manually verify `/`.
- [x] Manually verify `/chat`.
- [x] Manually verify `/dev-admin/runs`.
- [x] Manually verify `/dev-admin/evaluation/runs/phase11-answer-generation-v1`.
- [x] Manually verify `/dev-admin/failed-questions`.
- [x] Manually verify `/dev-admin/retrieval-playground`.
- [x] Manually verify `/dev-admin/observability`.
