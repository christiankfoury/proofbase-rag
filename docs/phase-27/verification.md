# Phase 27 Verification

## Commands Run

```powershell
python -m compileall apps scripts
python -c "import apps.api.app.main as m; print(m.app.title)"
python scripts/setup_db.py
docker compose config --quiet
python -c "from apps.api.app.auth.demo_auth import list_demo_users; users=list_demo_users(); print(len(users)); print([(u['display_name'], u['business_role'], u['is_admin'], len(u['memberships'])) for u in users])"
npm run build
```

## API Smoke Checks

FastAPI `TestClient` checks passed:

- `GET /auth/demo-users` returned `200`.
- `GET /auth/me` for Emma Employee returned `200`.
- Emma Employee could open seeded Northstar Analytics project data.
- Gus Guest received `403` for Northstar Analytics project data.
- Emma Employee received `403` for Dev/Admin evaluation summary.
- Kai Knowledge Manager received `200` for Dev/Admin evaluation summary.

## Role Derivation Smoke Check

An in-process `/query` smoke test monkeypatched retrieval and generation to avoid OpenAI calls and request-log writes.

Result:

- Request header: Emma Employee.
- Request body attempted `user_role: HR Admin`.
- Request body included seeded Northstar project scope.
- API retrieved and returned permission context as `Employee`.

## Notes

- `python scripts/setup_db.py` applied schema idempotently and reported existing corpus counts: 14 documents and 160 chunks.
- `docker compose config --quiet` completed, with Docker warning that the local user Docker config file was not readable. Compose config validation still exited successfully.
- `npm run build` completed successfully.
- No OpenAI-backed live query was run during this verification pass.
- Runtime request log changes were not intentionally included in Phase 27.
