# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Running the App

```bash
# Windows: double-click start_server.bat, or:
pip install -r requirements.txt
python app.py
# Serves on http://127.0.0.1:5050 via Waitress (4 threads)
# Port override: set TW_PORT env var
```

The batch file auto-kills any process on port 5050 and clears `__pycache__/` before starting. Verify with `GET /api/health`.

There are no tests, linter, or build step.

## Architecture

Single-process Flask app served by Waitress (production WSGI, no reloader). SQLite database (`testwatch.db`) in the project root. Vanilla JS frontend with Chart.js for statistics.

### Backend (app.py + models.py)

- **Database connections** use Flask's `g` context: `get_db()` returns a per-request connection, `close_db()` runs as teardown. Never call `db.close()` manually in route handlers.
- **Schema migrations** are inline in `init_db()` using `ALTER TABLE` with column-existence checks. `init_db()` is safe to call on every startup. Never use DROP TABLE or destructive schema changes — **existing data in testwatch.db must be preserved**.
- **All API responses** under `/api/` get no-cache headers via `@after_request`.
- **Error handler** catches all exceptions and returns JSON `{"error": "..."}`.
- **Source fingerprint** (`_source_fingerprint()`) hashes app.py + models.py for change detection.

### Frontend (templates/ + static/)

- **Jinja2 templates** extend `base.html`. Each page has inline `<script>` blocks.
- **`fetchJson(url, opts)`** in stopwatch.html is an error-safe fetch wrapper: returns `[]` on GET failure, `{ok: false}` on POST/PUT failure. Prevents page crashes on network errors.
- **localStorage keys**: `tw_session` (full stopwatch state as JSON), `tw_prep_scenario` (preparation page selection). Stopwatch state is independent from other pages.
- **`_activateGeneration` counter** in stopwatch.html prevents race conditions when `activateSession()` is called concurrently (e.g., auto-restore vs user click).
- **session-bar.js** is an IIFE loaded on every page. It polls `tw_session` from localStorage every 500ms to show the running timer, and checks `/api/version` every 30s for server changes.

### Data Model

`scenarios` → `ranks` (test steps, with jira_key for linking) → `time_entries` (timed activities within a session). `workstreams` are assigned to ranks. `activity_types` are the categories for time entries.

Scenarios have both `name` (Jira ID, e.g., "FSMTEST-57421") and `display_name` (readable, e.g., "91.5 YUC Sale"). The API returns a computed `label` field that prefers display_name.

### CSV Import (POST /api/import-csv)

Parses semicolon-separated Jira Xray test execution exports. Expects columns: "Test Key", "Status", "Executed By". Filename becomes scenario name. Jira key prefix (e.g., "OFCON" from "OFCON-1234") auto-creates workstreams. **Upsert logic**: existing ranks matched by `jira_key` within the scenario are updated, not duplicated.

## Key Constraints

- **Data preservation is critical.** The user has real testing session data. All schema changes must be additive (ALTER TABLE ADD COLUMN). Never drop tables, delete the DB, or reset data.
- **Do not git push unless explicitly asked.** Commit locally when asked, but pushing requires explicit user instruction.
- **Stopwatch persistence.** The running stopwatch must survive navigation to any other page. State is stored in localStorage and restored on return. Do not clear `tw_session` unless the session is explicitly ended.
