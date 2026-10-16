# SPMS Codebase Scaffold Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** A git monorepo for SPMS where backend and frontend run with one command each, one command runs every check, and every requirement ID has a documented home, so later features go straight to code.

**Architecture:** `backend/` is a uv-managed FastAPI app with a small `core/` (config, db, clock) and one example module (`health`). `frontend/` is a Vite + React + TypeScript app with Tailwind and shadcn/ui, proxying `/api` to the backend. Root holds docs, agent instructions (`AGENTS.md`, `CLAUDE.md` → `@AGENTS.md`), and a script-only `package.json`.

**Tech Stack:** Python 3.13, uv, FastAPI, SQLAlchemy 2.0, pytest, ruff · Node 22, Vite, React, TypeScript, Tailwind CSS v4, shadcn/ui, ESLint.

**Spec:** `docs/superpowers/specs/2026-10-17-spms-codebase-scaffold-design.md`

## Global Constraints

- Platform: Windows 11; every documented command must work from both PowerShell and Git Bash.
- No feature code, no per-requirement stubs, no failing placeholder tests.
- Business code never calls `datetime.now()`; it calls `app.core.clock.now()`. Time zone UTC+7.
- Money is integer VND.
- Test names that cover a test case start with `test_tc<NN>_`.
- Commit messages: Conventional Commits; feature commits put the requirement ID in scope, e.g. `feat(SP-3.1): …`. Scaffold commits use `chore(scaffold): …`.
- Root `package.json` has scripts only, no dependencies.
- Library versions: latest stable at build time.
- `.mcp.json` (shadcn MCP) stays at the repo root unchanged.
- Agents' requirement sources are files in the repo, never claude.ai links.

## Review Focus

1. **Relative SQLite path:** starting the backend from the repo root or from `backend/` must use the same DB file `backend/spms.db`, never create a stray `spms.db` at the root. → test in Task 2 (`test_default_database_url_points_into_backend`).
2. **Clock override leaking between tests:** a test that freezes time must not leave later tests frozen. → test in Task 2 (`test_clock_unfrozen_after_fixture`).
3. **Naive datetimes:** `now()` must return a timezone-aware value at +07:00, frozen or not. → tests in Task 2.
4. **Backend down while frontend runs:** the shell must render and show the API as offline, not a blank page. → manual check in Task 3, Step 7.
5. **Excel lock file in the first commit:** `~$SPMS_requirements.xlsx` must never be committed. → check in Task 1, Step 6.

---

## File Map

| Path | Responsibility | Task |
|---|---|---|
| `.gitignore` | ignore venv, node_modules, dist, `spms.db`, `~$*`, caches | 1 |
| `docs/requirements/*` | course deliverables + Markdown exports agents read | 1 |
| `docs/prototype/spms_ui.html` | visual reference | 1 |
| `backend/pyproject.toml` | uv project, deps, ruff + pytest config | 2 |
| `backend/app/core/config.py` | settings from env vars | 2 |
| `backend/app/core/clock.py` | `now()` in UTC+7, overridable | 2 |
| `backend/app/core/db.py` | engine, session dependency, `Base`, `init_db` | 2 |
| `backend/app/modules/health/router.py` | example module, `GET /api/health` | 2 |
| `backend/app/main.py` | app factory wiring | 2 |
| `backend/tests/conftest.py` | `client`, `frozen_clock` fixtures | 2 |
| `frontend/**` | Vite app, shell with 3 tabs, `lib/api.ts` | 3 |
| `package.json` | `dev:be`, `dev:fe`, `check` | 4 |
| `AGENTS.md`, `CLAUDE.md`, `README.md` | agent + human instructions | 4 |
| `docs/requirements/traceability.md` | requirement → module → page → TC → status | 4 |

---

### Task 1: Repository and requirement documents

**Files:**
- Create: `.gitignore`, `docs/requirements/srs.md`, `docs/requirements/implementation-plan.md`
- Copy: `SPMS_requirements.xlsx` → `docs/requirements/SPMS_requirements.xlsx`; `true (2).xlsx` → `docs/requirements/course-template.xlsx`
- Move: `spms_ui.html` → `docs/prototype/spms_ui.html`
- Keep: `docs/superpowers/specs/…`, `docs/superpowers/plans/…`, `.mcp.json`

**Interfaces:**
- Produces: `docs/requirements/srs.md` and `implementation-plan.md`, read by Task 4's `traceability.md` and by agents later.

- [ ] **Step 1: `git init` at `C:\Users\VUDUYLINH\PycharmProjects\Parking`, default branch `main`.**

- [ ] **Step 2: Write `.gitignore`** with at least: `.venv/`, `__pycache__/`, `.pytest_cache/`, `.ruff_cache/`, `node_modules/`, `dist/`, `*.db`, `~$*`, `.env`, `.idea/`.

- [ ] **Step 3: Copy the two xlsx files and move `spms_ui.html`** to the paths above. Copy, do not move, the xlsx: Excel may hold them open. Leave the root originals; the user deletes them after closing Excel.

- [ ] **Step 4: Export the two claude.ai docs to Markdown** with the Claude Docs connector (`export`, Markdown) and save them:
  - SRS doc id `aa272cea-9945-440d-9b30-452de8ead248` → `docs/requirements/srs.md`
  - Plan doc id `8c780454-ef4a-492d-a3f5-7cb73ff9e8b8` → `docs/requirements/implementation-plan.md`

  Diagrams do not export as text. Where the SRS requirement-tree diagram sat, add an indented list of the tree (SP → SP-1..SP-4 → leaves, with SP-2.2 → SP-2.2.1, SP-2.2.2). Where the plan's diagrams sat, add one line each describing the architecture and the sprint dates (S1 19/10–1/11, S2 2/11–15/11, S3 16/11–29/11, final demo 30/11). Put a first line in each file: `Exported from <claude.ai link> on 2026-10-17. Re-export when the doc changes.`

- [ ] **Step 5: Verify**

Run: `git status --short`
Expected: lists `.gitignore`, `.mcp.json`, `docs/`; does **not** list `~$SPMS_requirements.xlsx`; root `SPMS_requirements.xlsx` and `true (2).xlsx` appear as untracked (add them to `.gitignore` as `/SPMS_requirements.xlsx` and `/true (2).xlsx` so the root copies never get committed).

- [ ] **Step 6: Commit**

```bash
git add .gitignore .mcp.json docs
git commit -m "chore(scaffold): add requirement docs and prototype"
```

---

### Task 2: Backend skeleton

**Files:**
- Create: `backend/pyproject.toml`, `backend/app/__init__.py`, `backend/app/main.py`, `backend/app/core/__init__.py`, `backend/app/core/config.py`, `backend/app/core/clock.py`, `backend/app/core/db.py`, `backend/app/modules/__init__.py`, `backend/app/modules/health/__init__.py`, `backend/app/modules/health/router.py`
- Test: `backend/tests/conftest.py`, `backend/tests/test_core.py`, `backend/tests/test_health.py`

**Interfaces:**
- Produces (later feature modules rely on these exact names):
  - `app.core.clock.TZ: datetime.tzinfo` — fixed offset UTC+7
  - `app.core.clock.now() -> datetime` — aware, in `TZ`; returns the frozen value when set
  - `app.core.clock.freeze(at: datetime | None) -> None` — `None` unfreezes
  - `app.core.config.BACKEND_DIR: pathlib.Path`, `app.core.config.DATABASE_URL: str` — env `SPMS_DATABASE_URL`, default `sqlite:///<BACKEND_DIR>/spms.db`
  - `app.core.db.Base` (SQLAlchemy `DeclarativeBase`), `engine`, `SessionLocal`, `get_db() -> Iterator[Session]`, `init_db() -> None`
  - `app.main.app: FastAPI`; module routers mounted with prefix `/api`
  - pytest fixtures: `client: TestClient` (in-memory SQLite, `get_db` overridden), `frozen_clock` → callable `set_time(at: datetime)`, starts frozen at `2026-10-19 08:00 +07:00`, unfreezes on teardown

- [ ] **Step 1: Create the uv project** in `backend/`: `uv init --app --no-readme --python 3.13`, then `uv add "fastapi[standard]" sqlalchemy` (quote the extra; PowerShell treats `[` specially) and `uv add --dev pytest ruff`. Delete the generated `main.py`/`hello.py`. In `pyproject.toml` set `[tool.pytest.ini_options] testpaths = ["tests"]` and `pythonpath = ["."]`, and `[tool.ruff] line-length = 100`.

- [ ] **Step 2: Write the failing tests** in `backend/tests/test_core.py`:

```python
from datetime import datetime, timedelta
from app.core import clock, config


def test_now_is_aware_in_utc_plus_7():
    assert clock.now().utcoffset() == timedelta(hours=7)


def test_freeze_returns_fixed_time(frozen_clock):
    assert clock.now() == datetime(2026, 10, 19, 8, 0, tzinfo=clock.TZ)
    frozen_clock(datetime(2026, 10, 19, 11, 10, tzinfo=clock.TZ))
    assert clock.now().hour == 11 and clock.now().minute == 10


def test_clock_unfrozen_after_fixture():
    # runs after test_freeze_returns_fixed_time; must see real time again
    assert abs(clock.now() - datetime.now(clock.TZ)) < timedelta(seconds=5)


def test_default_database_url_points_into_backend():
    assert config.DATABASE_URL == f"sqlite:///{(config.BACKEND_DIR / 'spms.db').as_posix()}"
    assert config.BACKEND_DIR.name == "backend"
```

and `backend/tests/test_health.py`:

```python
def test_health_ok(client):
    r = client.get("/api/health")
    assert r.status_code == 200
    assert r.json() == {"status": "ok"}
```

(`test_default_database_url_points_into_backend` assumes `SPMS_DATABASE_URL` is unset in the test run.)

- [ ] **Step 3: Run the tests to verify they fail**

Run: `cd backend && uv run pytest -q`
Expected: errors on `ModuleNotFoundError: No module named 'app'` / missing fixtures.

- [ ] **Step 4: Implement `core/config.py`, `core/clock.py`, `core/db.py`.**
  - `BACKEND_DIR = Path(__file__).resolve().parents[2]`.
  - `clock` keeps a module-level `_frozen: datetime | None`; `now()` returns `_frozen` or `datetime.now(TZ)`; `freeze()` raises `ValueError` for a naive datetime.
  - `db`: `create_engine(DATABASE_URL, connect_args={"check_same_thread": False})`, `SessionLocal = sessionmaker(engine, autoflush=False)`, `get_db` yields a session and closes it, `init_db` runs `Base.metadata.create_all(engine)`.

- [ ] **Step 5: Implement `modules/health/router.py` and `main.py`.**
  - `router = APIRouter(tags=["health"])` with `GET /health` → `{"status": "ok"}`.
  - `main.py`: `app = FastAPI(title="SPMS", lifespan=…)` where the lifespan calls `init_db()`; `app.include_router(health.router, prefix="/api")`.

- [ ] **Step 6: Implement `tests/conftest.py`.**
  - `client`: engine `sqlite://` with `StaticPool`, `Base.metadata.create_all` on it, `app.dependency_overrides[get_db]` yielding sessions from it; `TestClient(app)` used **without** the lifespan touching the file DB (construct `TestClient(app)` outside a `with` block, or override `init_db`), clear overrides on teardown.
  - `frozen_clock`: `clock.freeze(datetime(2026, 10, 19, 8, 0, tzinfo=clock.TZ))`, yield `clock.freeze`, then `clock.freeze(None)`.

- [ ] **Step 7: Run tests and lint**

Run: `cd backend && uv run pytest -q && uv run ruff check .`
Expected: `5 passed`; ruff `All checks passed!`. Confirm no `spms.db` was created by the test run (`ls backend/*.db` finds nothing).

- [ ] **Step 8: Smoke-run the server from the repo root**

Run: `uv run --directory backend fastapi dev app/main.py`, then `curl http://localhost:8000/api/health`
Expected: `{"status":"ok"}`; file `backend/spms.db` exists; no `spms.db` at repo root. Stop the server.

- [ ] **Step 9: Commit**

```bash
git add backend
git commit -m "chore(scaffold): add FastAPI backend skeleton"
```

---

### Task 3: Frontend skeleton

**Files:**
- Create: `frontend/` via Vite `react-ts` template; then `frontend/vite.config.ts`, `frontend/tsconfig.json`, `frontend/tsconfig.app.json`, `frontend/src/index.css`, `frontend/components.json`, `frontend/src/lib/utils.ts` (shadcn), `frontend/src/lib/api.ts`, `frontend/src/App.tsx`, `frontend/src/pages/driver/DriverPage.tsx`, `frontend/src/pages/gate/GatePage.tsx`, `frontend/src/pages/admin/AdminPage.tsx`
- Delete: template demo assets and `App.css`

**Interfaces:**
- Consumes: `GET /api/health` → `{"status": "ok"}` (Task 2).
- Produces:
  - `src/lib/api.ts`: `export async function api<T>(path: string, init?: RequestInit): Promise<T>` — prefixes `/api`, sends/accepts JSON, throws `ApiError` (`status: number`, `message: string`) on non-2xx or network failure.
  - Pages: default exports `DriverPage`, `GatePage`, `AdminPage`, each rendering its title and the requirement IDs it will host (Driver: SP-2.1, SP-2.2.1, SP-2.2.2, SP-2.3 · Gate: SP-1.1–1.3, IF-01, IF-02, SP-3.1, SP-3.2 · Admin: SP-4.1, SP-4.2, SP-4.4).
  - Import alias `@/` → `src/`.

- [ ] **Step 1: Scaffold** with `npm create vite@latest frontend -- --template react-ts`, `cd frontend && npm install`.

- [ ] **Step 2: Add Tailwind v4 and the alias.** `npm install tailwindcss @tailwindcss/vite` and `npm install -D @types/node`; add the Tailwind plugin and `resolve.alias { "@": path.resolve(__dirname, "./src") }` in `vite.config.ts`; add `"baseUrl": "."` and `"paths": { "@/*": ["./src/*"] }` to both `tsconfig.json` and `tsconfig.app.json`; replace `src/index.css` with `@import "tailwindcss";`.

- [ ] **Step 3: Add the dev proxy** in `vite.config.ts`: `server: { port: 5173, proxy: { "/api": "http://localhost:8000" } }`.

- [ ] **Step 4: Initialise shadcn** with `npx shadcn@latest init` (accept defaults, base color neutral), then `npx shadcn@latest add tabs badge`.

- [ ] **Step 5: Write `lib/api.ts`, the three pages, and `App.tsx`.** The shell is a header ("SPMS" + an API status badge) and shadcn `Tabs` with Driver / Gate / Admin. On mount, `App` calls `api<{status: string}>("/health")`: badge shows `API: online` on success and `API: offline` on `ApiError`. No router library.

- [ ] **Step 6: Run the frontend checks**

Run: `cd frontend && npm run lint && npm run build`
Expected: no lint errors, no type errors, `dist/` built.

- [ ] **Step 7: Manual check, both backend states.** Start `npm run dev` in `frontend/` with the backend stopped: page renders with three tabs and `API: offline`. Start the backend (Task 2 Step 8 command) and reload: `API: online`.

- [ ] **Step 8: Commit**

```bash
git add frontend
git commit -m "chore(scaffold): add React + shadcn frontend skeleton"
```

---

### Task 4: Root commands, agent instructions, traceability

**Files:**
- Create: `package.json`, `AGENTS.md`, `CLAUDE.md`, `README.md`, `docs/requirements/traceability.md`

**Interfaces:**
- Consumes: backend commands (Task 2), frontend commands (Task 3), `srs.md` and the xlsx (Task 1).
- Produces: `npm run dev:be`, `npm run dev:fe`, `npm run check`; the instruction file every later feature session reads.

- [ ] **Step 1: Write root `package.json`** (`"private": true`, no dependencies) with scripts:
  - `dev:be`: `uv run --directory backend fastapi dev app/main.py`
  - `dev:fe`: `npm --prefix frontend run dev`
  - `check:be`: `uv run --directory backend ruff check . && uv run --directory backend pytest -q`
  - `check:fe`: `npm --prefix frontend run lint && npm --prefix frontend run build` (the Vite template's `build` script is already `tsc -b && vite build`; keep it that way)
  - `check`: `npm run check:be && npm run check:fe`

  (Note: `uv run --directory` changes into `backend/` so `ruff check .` and pytest's `testpaths` resolve there; confirm in Step 5.)

- [ ] **Step 2: Write `docs/requirements/traceability.md`** with three tables:
  - Functional + interface requirements: `ID | Title | Priority | Sprint | Backend module | Frontend page | Test cases | Status`. Rows for all 16 IDs, module/page from the spec's module map, sprint from `implementation-plan.md`, TCs from the xlsx `test_case_analysis` sheet, Status `Not started`.
  - NFRs: `ID | Target | Verified by | Status`, values from the spec ("verified by" column).
  - Change requests: `CR | Status | Effect on build` — CR-02 Approved: hold is 10 minutes, TC-06 checks minute 11; CR-01 Under Review: do not build.

- [ ] **Step 3: Write `AGENTS.md`** containing, in this order: one-paragraph project summary; source-of-truth list (`docs/requirements/srs.md`, `SPMS_requirements.xlsx`, `traceability.md`; never claude.ai links); the three commands; repo layout (the spec's tree, short); module map table; module file convention (`router.py` / `service.py` / `models.py` / `schemas.py`, create only what is needed, `service.py` has no FastAPI imports); the Global Constraints of this plan (clock, VND integers, TC test naming, commit format, no encryption before T-04, CR-02 = 10 min); the 7-step feature workflow from the spec; frontend rules (shadcn via MCP, calls only through `src/lib/api.ts`, prototype as visual reference).

- [ ] **Step 4: Write `CLAUDE.md`** with exactly `@AGENTS.md`, and `README.md` with prerequisites (Python 3.13, uv, Node 22), install (`uv sync --directory backend`, `npm --prefix frontend install`), the three commands, and links to `AGENTS.md` and `docs/requirements/`.

- [ ] **Step 5: Run the full check from both shells**

Run (PowerShell, repo root): `npm run check`
Run (Git Bash, repo root): `npm run check`
Expected: both pass — `5 passed`, ruff clean, lint/tsc/build clean.

- [ ] **Step 6: Commit**

```bash
git add package.json AGENTS.md CLAUDE.md README.md docs/requirements/traceability.md
git commit -m "chore(scaffold): add root commands, agent guide, traceability"
```

- [ ] **Step 7: Clean-clone verification**

Run in a temp directory: `git clone <repo path> spms-check && cd spms-check && uv sync --directory backend && npm --prefix frontend install && npm run check`
Expected: passes with no file outside the repo needed. Delete the temp clone.
