# SPMS codebase scaffold — design

Date: 2026-10-17
Status: approved

## Intent

The Smart Parking Management System (SPMS) is a course project for CSE703095 (Requirements Engineering). Requirements are already specified:

- SRS: https://claude.ai/code/artifact/aa272cea-9945-440d-9b30-452de8ead248
- Requirements register: `SPMS_requirements.xlsx` (course template, 13 sheets)
- Implementation plan (3 sprints, backlog, architecture): https://claude.ai/code/artifact/8c780454-ef4a-492d-a3f5-7cb73ff9e8b8
- Clickable UI prototype: `spms_ui.html`

The user will build features by working with **Claude Code and Codex** in the same repo, often switching between them. The scaffold exists so that, from then on, a request like "implement SP-3.1" can go straight to code: the agent knows where the code lives, which test case to satisfy, how to run checks, and what to update afterwards, without asking.

## Goals

1. A monorepo that runs: backend and frontend both start with one command each, and one command runs every check.
2. Every requirement ID (SP-x.x, IF-0x) has a fixed home: a backend module and, where it has UI, a frontend page. The mapping is written down in the repo.
3. One instruction file shared by Claude Code and Codex, so the two agents follow the same rules.
4. A documented feature workflow: requirement → test from its TC → code → check → update traceability.
5. The course deliverables move into the repo, under version control.

## Non-goals

- No feature is implemented. No per-requirement stubs, no placeholder endpoints, no failing tests for future work (the user chose "skeleton and conventions only").
- No real device integration. LPR camera, slot sensor, and payment gateway are mocked later, when their requirements are built (IF-01, SP-2.1, SP-3.2).
- No Docker, deployment, or cloud hosting.
- No GitHub remote or push in this step.

## Anti-goals (failure even if it technically works)

- An agent has to guess where a feature's code goes, or puts the same concern in two places.
- `AGENTS.md` and `CLAUDE.md` give different instructions.
- The skeleton does not start or its check command fails on a clean clone.
- Over-built scaffolding: abstractions, base classes, or folders that no requirement needs yet.

## Constraints

- Windows 11, shell is PowerShell and Git Bash. Commands in docs must work in both, or both forms must be given.
- Installed: Python 3.13, uv 0.7, Node 22 / npm 10, git 2.39, gh 2.89.
- `.mcp.json` already registers the shadcn MCP server (`cmd /c npx shadcn@latest mcp`). Keep it at the repo root.
- Business rules come from the SRS: currency VND, time zone UTC+7, Vietnamese plate format such as `30A-123.45`, 2 floors × 2 zones × 50 slots = 200 slots, slot ID format `T1-A-05`.
- The folder `C:\Users\VUDUYLINH\PycharmProjects\Parking` is not a git repo yet.

## Decisions made by the user

- Stack from the implementation plan: Python FastAPI backend, SQLite database, React + Vite + shadcn/ui frontend, mock scripts for external devices.
- Agents doing the work: Claude Code and Codex.
- Scaffold depth: skeleton and conventions only.

## Design

### Repository layout

```
Parking/
├── AGENTS.md                 # the one instruction file (Codex reads it natively)
├── CLAUDE.md                 # one line: @AGENTS.md
├── README.md                 # human quick start
├── package.json              # root scripts only: dev:be, dev:fe, check
├── .gitignore
├── .mcp.json                 # shadcn MCP (already exists)
├── docs/
│   ├── requirements/
│   │   ├── SPMS_requirements.xlsx
│   │   ├── course-template.xlsx      # renamed from "true (2).xlsx"
│   │   ├── srs.md                    # Markdown export of the SRS doc
│   │   ├── implementation-plan.md    # Markdown export of the plan doc
│   │   └── traceability.md           # requirement → module → page → TC → status
│   ├── prototype/spms_ui.html
│   └── superpowers/{specs,plans}/
├── backend/
│   ├── pyproject.toml        # uv project
│   ├── app/
│   │   ├── main.py           # FastAPI app, mounts module routers under /api
│   │   ├── core/
│   │   │   ├── config.py     # settings from environment variables
│   │   │   ├── db.py         # SQLAlchemy engine, session dependency, Base
│   │   │   └── clock.py      # now() in UTC+7, overridable in tests
│   │   └── modules/
│   │       └── health/       # the one example module, shows the pattern
│   │           └── router.py # GET /api/health
│   └── tests/
│       ├── conftest.py       # TestClient, in-memory DB, frozen clock fixture
│       └── test_health.py
└── frontend/
    ├── package.json          # Vite + React + TypeScript + Tailwind + shadcn
    ├── components.json       # shadcn config
    ├── vite.config.ts        # proxy /api → http://localhost:8000
    └── src/
        ├── main.tsx, App.tsx # app shell: header + tabs Driver / Gate / Admin
        ├── lib/api.ts        # small fetch wrapper for /api
        ├── components/ui/    # shadcn components, added on demand
        └── pages/{driver,gate,admin}/  # one empty page each
```

### Module map (the "fixed home" for each requirement)

Backend modules are created under `backend/app/modules/<name>/` the first time one of their requirements is built. The map lives in `AGENTS.md` and `docs/requirements/traceability.md`.

| Backend module | Requirements | Frontend page |
|---|---|---|
| `sessions` | SP-1.1, SP-1.2, SP-1.3, IF-01, IF-02 | gate |
| `slots` | SP-2.1, SP-2.3 (and sensor events) | driver |
| `reservations` | SP-2.2.1, SP-2.2.2 | driver |
| `billing` | SP-3.1, SP-3.2, SP-3.3, SP-4.1 | gate, admin |
| `reports` | SP-4.2 | admin |
| `auth` | SP-4.3 | login, guards all pages |
| `audit` | SP-4.4 | admin |

Mock device scripts go in `backend/mocks/` when IF-01 / SP-2.1 / SP-3.2 are built.

`traceability.md` also has:

- **NFR rows** with a "verified by" column: NFR-01 by TC-17 (a timing script, not part of `npm run check`), NFR-02 by TC-18 (depends on the camera vendor; stays Not Run), NFR-03 and NFR-06 by analysis, NFR-04 by inspection, NFR-05 by demonstration.
- **NFR-04 (encryption)** is plan task T-04 in Sprint 3: field-level encryption of personal-data columns (plates, accounts) through a SQLAlchemy column type in `core/`, plus HTTPS. Agents do not add encryption before T-04. The plain SQLite setup in `core/db.py` does not block this.
- **A change-request section.** CR-02 is Approved: the reservation hold is **10 minutes**, not 15. SP-2.2.1 is built with 10 minutes and TC-06 checks expiry at minute 11 (the plan schedules CR-02 together with SP-2.2.1 in Sprint 2). CR-01 (monthly pass) is Under Review and not to be built.

Inside a module, the files are `router.py` (HTTP), `service.py` (business rules, no FastAPI imports), `models.py` (SQLAlchemy tables), `schemas.py` (Pydantic). A module creates only the files it needs.

### Cross-cutting rules (written in AGENTS.md)

- **Time:** business code never calls `datetime.now()` directly; it calls `app.core.clock.now()`. Tests freeze or advance it. Reason: TC-06 (reservation expires at minute 11 after CR-02) and TC-08 (3 h 10 min fee) need controlled time.
- **Source of requirements for agents:** `docs/requirements/srs.md` and the xlsx. Codex cannot open claude.ai links, so agents never depend on them. When the SRS doc changes on claude.ai, re-export `srs.md`.
- **Money:** integer VND, never float.
- **Tests:** pytest. A test that covers a test case is named after it, for example `test_tc08_fee_3h10m_is_40000`. Each test file sits in `backend/tests/` and is named after its module.
- **Database:** SQLAlchemy 2.0 with SQLite file `backend/spms.db`; tables created with `Base.metadata.create_all` at startup. Tests use an in-memory database.
- **Requirement IDs everywhere:** commit messages use Conventional Commits with the ID in scope, for example `feat(SP-3.1): calculate parking fee`.
- **Frontend:** UI components come from shadcn via the shadcn MCP; pages call the backend only through `src/lib/api.ts`. The prototype `docs/prototype/spms_ui.html` is the visual reference.

### Feature workflow (written in AGENTS.md)

1. Look up the requirement in `docs/requirements/traceability.md`: module, page, test cases.
2. Read its acceptance criteria and test case steps (SRS or the `requirements` / `test_cases` sheets).
3. Write the test(s) for its TC first and see them fail.
4. Implement in the mapped module (and page).
5. Run `npm run check` until it passes.
6. Update the requirement's status in `traceability.md`.
7. Commit with `feat(<ID>): …`.

Updating the Excel `test_cases` sheet (status, actual result, executor, date) is done at the end of each sprint, not per feature (task T-06 in the plan).

### Commands

| Command (from repo root) | Does |
|---|---|
| `npm run dev:be` | `uv run fastapi dev app/main.py` in `backend/`, port 8000 |
| `npm run dev:fe` | Vite dev server in `frontend/`, port 5173 |
| `npm run check` | backend: `ruff check` + `pytest`; frontend: `eslint` + `tsc -b` + `vite build` |

Root `package.json` holds scripts only, no dependencies.

### Done means

- The xlsx files are **copied** (not moved) into `docs/requirements/`, because Excel may hold them open; the originals at the root are removed only after the user closes Excel. `.gitignore` excludes `~$*` lock files.
- `git init`, first commit contains everything above.
- On a clean clone: `uv sync` in backend and `npm install` in frontend, then `npm run check` passes.
- `npm run dev:be` serves `GET /api/health` → `{"status": "ok"}`; `npm run dev:fe` shows the shell with three empty tabs and calls `/api/health` through the proxy.

## Builder's calls (not decided by the user)

- Exact library versions (latest stable at build time).
- No Alembic migrations yet; add when moving to PostgreSQL.
- No frontend unit-test runner yet (Vitest gets added with the first frontend logic that has branches); the frontend check is lint + type check + build.
- Settings read from environment variables with defaults in `config.py`; no `pydantic-settings` dependency.
- Wording and depth of `AGENTS.md` and `README.md`.
- SRS and implementation plan exported to Markdown in the repo as the agents' source (Codex cannot read claude.ai links).
- NFRs tracked in `traceability.md` with a "verified by" column; NFR-04 encryption deferred to plan task T-04.
- CR-02 treated as in force (10-minute hold); CR-01 not built.
- Excel files copied, not moved, while Excel may have them open.
