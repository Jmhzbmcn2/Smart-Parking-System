# SPMS agent guide

SPMS (Smart Parking Management System) is a CSE703095 Requirements Engineering course project: a FastAPI/SQLite backend with React, Vite and shadcn/ui frontend for parking entry/exit, slots, reservations, billing and administration. This repository currently contains only a runnable skeleton and conventions; build requirements incrementally in their fixed homes. The course domain uses UTC+7, integer VND, Vietnamese plates such as `30A-123.45`, and 200 slots across 2 floors × 2 zones × 50 slots, with IDs such as `T1-A-05`.

## Sources of truth

- [docs/requirements/srs.md](docs/requirements/srs.md): local SRS export (2026-10-17) with the acceptance criteria; the requirement-tree diagram is not exported.
- [docs/requirements/SPMS_requirements.xlsx](docs/requirements/SPMS_requirements.xlsx): local requirements register; read `requirements`, `nfrs`, `change_requests`, `test_cases` and `test_case_analysis` for the applicable requirement, criteria and test steps.
- [docs/requirements/traceability.md](docs/requirements/traceability.md): fixed module/page homes, TC mapping and implementation status.
- [docs/requirements/implementation-plan.md](docs/requirements/implementation-plan.md): local plan export (2026-10-17) with the backlog and sprint mapping; diagrams are not exported.
- [Scaffold design](docs/superpowers/specs/2026-10-17-spms-codebase-scaffold-design.md): repository structure and cross-cutting conventions, including explicitly known CR-02/T-04 scheduling.

Agents use local files, never depend on claude.ai links. Re-export `srs.md` and `implementation-plan.md` whenever their source documents change. Use only the information in local sources; do not invent missing criteria, backlog or sprint assignments. Approved change requests override older requirement/test text: CR-02 is already in force.

## Commands

Run from the repository root in PowerShell or Git Bash; start each development server in its own terminal. If PowerShell blocks `npm.ps1`, use `npm.cmd` in place of `npm`.

| Command | Purpose |
|---|---|
| `npm run dev:be` | FastAPI development server on port 8000; `GET /api/health` returns `{"status":"ok"}` |
| `npm run dev:fe` | Vite development server on port 5173; `/api` proxies to `http://localhost:8000` |
| `npm run check` | Backend Ruff and pytest; frontend ESLint, TypeScript (`tsc -b`) and Vite build |

## Repository layout

```text
Parking/
  AGENTS.md                 Shared instructions for Codex and Claude Code
  CLAUDE.md                 Imports AGENTS.md
  README.md                 Human quick start
  package.json              Root scripts only
  .gitignore
  .mcp.json                 Root shadcn MCP configuration
  docs/
    requirements/           Register, course-template.xlsx, exports, traceability
    prototype/spms_ui.html  Visual reference
    superpowers/specs/      Binding scaffold design
    superpowers/plans/      Implementation tasks
  backend/
    pyproject.toml, uv.lock
    app/
      main.py               FastAPI app and /api routers
      core/                 config.py, db.py, clock.py
      modules/health/       router.py; only example module implemented
    tests/                  conftest.py, test_core.py, test_health.py
  frontend/
    package.json, package-lock.json, components.json, vite.config.ts
    src/
      main.tsx, App.tsx     Driver / Gate / Admin shell
      lib/api.ts           Shared /api fetch wrapper
      components/ui/       shadcn components added as needed
      pages/driver/        Empty driver page
      pages/gate/          Empty gate page
      pages/admin/         Empty admin page
```

## Module map

Create backend modules under `backend/app/modules/<name>/` when first needed. Page names refer to `frontend/src/pages/<name>/`; login and guards are future auth work. Mock device scripts go in `backend/mocks/` when IF-01, SP-2.1 or SP-3.2 are built.

| Backend module | Requirements | Frontend page |
|---|---|---|
| `sessions` | SP-1.1, SP-1.2, SP-1.3, IF-01, IF-02 | gate |
| `slots` | SP-2.1, SP-2.3; sensor events | driver |
| `reservations` | SP-2.2.1, SP-2.2.2 | driver |
| `billing` | SP-3.1, SP-3.2, SP-3.3, SP-4.1 | gate, admin |
| `reports` | SP-4.2 | admin |
| `auth` | SP-4.3 | login; guards all pages |
| `audit` | SP-4.4 | admin |

## Module file convention

- `router.py`: HTTP endpoints, mounted under `/api` in `app/main.py`.
- `service.py`: business rules, with no FastAPI imports.
- `models.py`: SQLAlchemy tables.
- `schemas.py`: Pydantic request/response schemas.

Create only the files each module needs.

## Cross-cutting rules

- Windows 11 is the target. Every documented command must work in both PowerShell and Git Bash, or give both forms. Shell chains inside npm scripts run through npm; PowerShell 5.1 commands must be separate lines.
- Keep the scaffold at skeleton and conventions only: no feature code, per-requirement stubs or failing placeholder tests. Add only the feature being implemented in a feature session.
- Business code calls `app.core.clock.now()`, never `datetime.now()` directly. Values must be timezone-aware at UTC+7, including frozen values. Tests freeze or advance the clock without leaking overrides to later tests.
- Money is integer VND, never float.
- Use pytest. Tests covering a TC start with `test_tc<NN>_`, for example `test_tc08_fee_3h10m_is_40000`. Put module tests in `backend/tests/test_<module>.py`.
- Use SQLAlchemy 2.x with SQLite at `backend/spms.db`, irrespective of the startup directory; create tables via `Base.metadata.create_all` at startup. Tests use an in-memory database. No Alembic migrations yet; add them when moving to PostgreSQL.
- Commit messages use Conventional Commits; feature commits include the requirement ID in scope, for example `feat(SP-3.1): calculate parking fee`. Scaffold commits use `chore(scaffold): ...`.
- NFR-04 (T-04): personal data (every `plate` column and `users.username`) is encrypted with `core/crypto.py` `EncryptedString` (deterministic AES-256-SIV, so equality lookups and unique indexes still work). Use that column type for any new personal-data column. The key comes from `SPMS_DATA_KEY` or `backend/.data_key`. HTTPS is served by `npm run dev:be:https`.
- CR-02 is Approved: reservation hold is **10 minutes**, and TC-06 checks expiry at minute **11**. This overrides the workbook's older 15/16-minute wording, including TC-05. CR-02 is scheduled with SP-2.2.1 in Sprint 2. CR-01 monthly passes remain Under Review: do not build them.
- Root `package.json` has scripts only, `private: true`, and no dependencies. Use latest stable library versions compatible with the stack when adding dependencies; keep installs and lockfiles reproducible. The existing TypeScript version follows the stable ESLint integration's supported range.
- Keep `.mcp.json` at the repository root unchanged. Do not add Docker, deployment or cloud hosting. CI runs `npm run check` on push and pull request (`.github/workflows/check.yml`).
- Preserve original root workbooks while Excel may hold them open; the versioned copies live under `docs/requirements/`. Ignore Excel `~$*` lock files; never commit them.

## Feature workflow

1. Look up the requirement in `docs/requirements/traceability.md`: module, page and test cases.
2. Read its acceptance criteria and test steps in the local SRS or workbook `requirements` / `test_cases` sheets, plus applicable approved changes. If required information is absent from the exports and local workbook, do not guess it.
3. Write tests for its TC first and see them fail for the expected missing behavior.
4. Implement in the mapped module and page, creating only the files needed.
5. Run `npm run check` until it passes.
6. Update the requirement's implementation status in `docs/requirements/traceability.md`.
7. Commit with `feat(<ID>): ...`.

Update the Excel `test_cases` sheet's status, actual result, executor and date at the **end of each sprint**, not per feature (plan task T-06).

## Frontend rules

Use shadcn components via the shadcn MCP, adding components on demand. Pages call the backend only through `frontend/src/lib/api.ts` (`api<T>(path, init?)`, with `ApiError` for HTTP failures). Use [docs/prototype/spms_ui.html](docs/prototype/spms_ui.html) as the visual reference. Keep the shell usable when the backend is unavailable and display the API as offline. Add Vitest with the first frontend logic that has branches; the current frontend check is lint, type check and build.
