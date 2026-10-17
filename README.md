# Smart Parking Management System

SPMS is a CSE703095 Requirements Engineering course project using FastAPI, SQLite, React, Vite and shadcn/ui. Sprint 1 is implemented: login with roles, LPR gate events, entry/exit sessions, manual entry and barrier with audit log, and slot availability.

## Quick start

Install Python 3.13, uv, Node.js 22 (with npm) and Git. From the repository root, run these commands on separate lines in PowerShell or Git Bash:

```text
uv sync --directory backend
cd frontend
npm install
cd ..
```

Start the backend and frontend in separate terminals:

```text
npm run dev:be
```

```text
npm run dev:fe
```

Open `http://localhost:5173`. The backend serves `GET http://localhost:8000/api/health` with `{"status":"ok"}`; Vite proxies `/api` to the backend. The shell shows the API as offline if the backend is unavailable.

Run all checks from the root:

```text
npm run check
```

This runs Ruff and pytest in `backend/`, then ESLint, `tsc -b` and Vite build in `frontend/`. Root `check:be` and `check:fe` scripts are available for focused checks. If PowerShell blocks `npm.ps1`, replace `npm` with `npm.cmd`; the command arguments stay the same.

## Demo users and mock devices

Demo logins: `admin/admin123`, `attendant/attendant123`, `driver/driver123`. With the backend running (`npm run dev:be`), mock devices run from the repository root:

```text
uv run --directory backend python mocks/lpr.py 30A-123.45 --gate IN-1 --confidence 0.95
uv run --directory backend python mocks/lpr.py 30A-123.45 --gate OUT-1
uv run --directory backend python mocks/sensor.py T1-A-05 --occupied
uv run --directory backend python mocks/sensor.py T1-A-05 --free
```

`--confidence 0.6` makes the Gate page ask for manual entry. Add `--url http://localhost:PORT` if the backend is not on port 8000.

## Requirements and agent workflow

Read [AGENTS.md](AGENTS.md) for module homes, shared Claude Code/Codex conventions and the feature workflow. [docs/requirements/](docs/requirements/) contains the local requirements register, course template, traceability and document exports. The [prototype](docs/prototype/spms_ui.html) is the visual reference.

`srs.md` and `implementation-plan.md` are local exports of the SRS and the plan (2026-10-17); their diagrams are not exported. Do not invent missing criteria or assignments. Re-export the local documents whenever their sources change. Approved CR-02 already sets reservation holds to 10 minutes and TC-06 expiry to minute 11; CR-01 monthly passes are not approved.
