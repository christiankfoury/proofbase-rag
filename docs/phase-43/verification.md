# Phase 43 Verification

Generated during Phase 43 implementation.

## Local Checks

- Passed: `python scripts/test_phase43_markdown_cleanup.py`
- Passed: `python scripts/test_phase40_upload_indexing.py`
- Passed: `python -m compileall apps/api/app scripts`
- Passed with known local Docker config warning: `docker compose config --quiet`
- Passed with established Windows workaround after sandbox `EPERM`: `cd apps/web; $env:NEXT_DIST_DIR='.next-codex-build'; $env:NEXT_TELEMETRY_DISABLED='1'; npm run build`

## OpenAI-Backed Checks

- Passed dry-run guard: `python scripts/run_phase40_upload_e2e.py --dry-run`
- Attempted but blocked by missing local credentials: `python scripts/run_phase40_upload_e2e.py --allow-external-ai`
  - Result: approve/index returned `503` with `OPENAI_API_KEY is required for embedding generation`.
  - Credential check confirmed `OPENAI_API_KEY`, `settings.openai_api_key`, and `settings.openai_api_key_file` were unavailable to the verification process.
  - No live OpenAI-backed pass is claimed for Phase 43.

## Expected Behavior

- Non-editor users are rejected before the cleanup service can call OpenAI.
- Indexed documents are rejected before cleanup.
- Cleanup returns a review draft and keeps the document pending review with zero chunks.
- Cleanup metadata updates `metadata_json` only; approval/index remains responsible for replacing reviewed Markdown and creating chunks/embeddings.
- Empty or unsafe cleanup output is rejected.
