# Smart Parking Management System

SPMS is a CSE703095 Requirements Engineering course project using FastAPI, SQLite, React, Vite and shadcn/ui. This scaffold contains a health API and a Driver / Gate / Admin shell; parking features are not implemented yet.

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

## Requirements and agent workflow

Read [AGENTS.md](AGENTS.md) for module homes, shared Claude Code/Codex conventions and the feature workflow. [docs/requirements/](docs/requirements/) contains the local requirements register, course template, traceability and document exports. The [prototype](docs/prototype/spms_ui.html) is the visual reference.

Both `srs.md` and `implementation-plan.md` are currently **EXPORT PENDING** placeholders because the source connector was unavailable. Full SRS content and most sprint assignments remain unverified; use the local workbook and scaffold design for the information they contain, and do not invent missing criteria or assignments. Re-export the local documents whenever their sources change. Approved CR-02 already sets reservation holds to 10 minutes and TC-06 expiry to minute 11; CR-01 monthly passes are not approved.
