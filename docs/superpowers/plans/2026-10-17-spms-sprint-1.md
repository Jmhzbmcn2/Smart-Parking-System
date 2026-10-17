# SPMS Sprint 1 Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Deliver the Sprint 1 backlog (T-01, IF-01, SP-1.1, SP-1.2, SP-1.3, SP-2.1, SP-4.3, SP-4.4, IF-02) so that the entry/exit flow of UC-01 and UC-03 (without payment) runs end to end with mock devices.

**Architecture:** Each requirement lives in its fixed module from `AGENTS.md`. Device events arrive over REST from mock scripts in `backend/mocks/`. One service function in `sessions` handles a plate at a gate; LPR events and manual entry both call it. The frontend polls the backend; it does not use WebSocket (see Rulings).

**Tech Stack:** FastAPI, SQLAlchemy 2.x, SQLite, pytest, React + Vite + shadcn/ui, Vitest (added in Task 7).

**Spec:** `docs/requirements/srs.md` (acceptance criteria), `docs/requirements/implementation-plan.md` (backlog, Sprint 1 scope), `docs/requirements/SPMS_requirements.xlsx` sheet `test_cases` (TC steps), `AGENTS.md` (conventions). The scaffold design remains binding for structure.

## Global Constraints

- Follow `AGENTS.md` exactly: module homes, `router.py`/`service.py`/`models.py`/`schemas.py`, `app.core.clock.now()`, integer VND, `test_tc<NN>_` names, `npm run check` green before each commit.
- Commit per task: `feat(<ID>): ...` with the main requirement ID in scope; docs-only commits use `docs: ...`.
- Plate format: `^\d{2}[A-Z][A-Z0-9]?-\d{3}\.?\d{2}$` after `strip().upper()`; example `30A-123.45`.
- Slot IDs: `T{floor}-{zone}-{nn:02d}`, floors 1–2, zones A–B, nn 01–50 (200 slots).
- Confidence threshold: `confidence < 0.8` means manual entry (IF-02).
- Gate IDs: `IN-<n>` is an entry gate, `OUT-<n>` is an exit gate. Anything else is HTTP 422.
- Roles: `driver`, `attendant`, `admin`.
- Device endpoints (`/api/lpr-events`, `/api/sensor-events`) have no authentication in Sprint 1; T-04 adds it.
- No payment, fee, reservation or WebSocket code in this sprint.

## Review Focus

1. The same plate arrives twice at an entry gate while its session is Active: no second session, no barrier opening; HTTP 409 (Task 4).
2. A plate arrives at an exit gate with no Active session: no barrier opening; HTTP 404 (Task 4).
3. A timestamp without a timezone: HTTP 422, never stored as a naive datetime (Task 4).
4. A sensor event for an unknown slot ID, or for a slot already in the reported state: 404, or no double counting (Task 6).
5. An expired or wrong token on a protected endpoint: 401, not 500 (Task 3).

## Rulings (planner's calls)

- **Polling instead of WebSocket for SP-2.1.** The criterion is ≤ 5 s; a 3 s poll meets it with no extra infrastructure. The implementation plan's risk table names this fallback. Upgrade if the class demo requires real time.
- **IF-02 "no event for 5 s".** There is no vehicle-detected signal without a camera, so the 5 s timeout has no trigger. The manual entry form is always available on the Gate page; it also opens automatically for a `manual_required` event.
- **SP-1.3 closes sessions without payment.** TC-03's precondition "đã thanh toán" belongs to Sprint 2 (SP-3.1, SP-3.2). Sprint 2 adds the payment check before closing.
- **TC-13 runs against `GET /api/audit-log`.** The price page (SP-4.1) is Sprint 2. Sprint 2 adds a second TC-13 assertion on the price endpoint.
- **Tokens:** opaque `secrets.token_urlsafe(32)` stored on the user row, passwords hashed with `hashlib.scrypt`. No JWT library.
- **CI in T-00 is skipped.** The scaffold design forbids a GitHub remote in this phase; `npm run check` is the gate.

---

### Task 1: Sync requirement docs

**Files:**
- Modify: `docs/requirements/srs.md`, `docs/requirements/implementation-plan.md` (already re-exported in the working tree; review and commit)
- Modify: `docs/requirements/traceability.md`, `AGENTS.md`, `README.md`
- Modify: `frontend/vite.config.ts`, `frontend/src/lib/api.ts`, `docs/superpowers/specs/2026-10-17-spms-codebase-scaffold-design.md`

- [ ] **Step 1:** In `traceability.md`, fill the Sprint column from `implementation-plan.md` section 3 (Sprint 1: SP-1.1, SP-1.2, SP-1.3, SP-2.1, SP-4.3, SP-4.4, IF-01, IF-02; Sprint 2: SP-4.1, SP-3.1, SP-3.2, SP-4.2, SP-2.2.1, SP-2.2.2; Sprint 3: SP-2.3, SP-3.3). Remove every "EXPORT PENDING" and "Pending plan export" sentence in `traceability.md`, `AGENTS.md` and `README.md`. Keep the requirement tree; mark it as the source for the unexported diagram.
- [ ] **Step 2:** `vite.config.ts`: replace `__dirname` with `import.meta.dirname`. `api.ts`: set `Content-Type: application/json` only when `typeof init?.body === 'string'` and the header is absent. Spec: `Status: approved`.
- [ ] **Step 3:** Run `npm run check`. Expected: pass, and the Vite `__dirname` warning is gone.
- [ ] **Step 4:** Commit `docs: export SRS and plan, fill sprint mapping`.

### Task 2: T-01 data model and seed

**Files:**
- Create: `backend/app/modules/slots/models.py`, `backend/app/modules/slots/service.py`
- Create: `backend/app/modules/auth/models.py`, `backend/app/modules/auth/service.py`
- Modify: `backend/app/main.py` (lifespan seeds after `init_db()`), `backend/tests/conftest.py` (client fixture seeds)
- Test: `backend/tests/test_slots.py`, `backend/tests/test_auth.py`

**Interfaces:**
- Produces: `Slot(id: str PK, floor: int, zone: str, status: str)`; status values `"available" | "occupied"`.
- Produces: `User(id: int PK, username: str unique, password_hash: str, role: str, token: str | None unique)`.
- Produces: `slots.service.seed_slots(db: Session) -> None` and `auth.service.seed_users(db: Session) -> None`. Both are idempotent.
- Produces: `auth.service.hash_password(pw: str) -> str` and `verify_password(pw: str, stored: str) -> bool` (scrypt, random 16-byte salt, stored as `salt_hex$hash_hex`).
- Demo users: `admin/admin123` (admin), `attendant/attendant123` (attendant), `driver/driver123` (driver).

- [ ] **Step 1:** Write the failing tests:
  - `test_seed_creates_200_slots`: after seeding, the count is 200, `T1-A-01` and `T2-B-50` exist, and all are `available`.
  - `test_seed_is_idempotent`: seeding twice still gives 200 slots and 3 users.
  - `test_password_hash_roundtrip`: `verify_password("x", hash_password("x"))` is True, and `verify_password("y", ...)` is False.
- [ ] **Step 2:** Run `uv run --directory backend pytest -q`. Expected: FAIL, modules missing.
- [ ] **Step 3:** Implement the models and seeds. Import the model modules in `app/main.py` before `init_db()` so `create_all` sees them. The `client` fixture calls both seeds on its in-memory DB.
- [ ] **Step 4:** Run `npm run check`. Expected: pass.
- [ ] **Step 5:** Commit `feat(T-01): add slot and user tables with seed`.

### Task 3: SP-4.3 login and role guard

**Files:**
- Create: `backend/app/modules/auth/router.py`, `backend/app/modules/auth/schemas.py`
- Modify: `backend/app/modules/auth/service.py`, `backend/app/main.py`
- Test: `backend/tests/test_auth.py`

**Interfaces:**
- Produces: `POST /api/auth/login {username, password}` returns 200 `{token, username, role}`; bad credentials return 401. Each login issues a new token, which replaces the old one.
- Produces: `GET /api/auth/me` returns `{username, role}`.
- Produces: `auth.router.current_user` (dependency: `Authorization: Bearer <token>`; missing or unknown token gives 401) and `require_role(*roles: str)`, which returns a dependency that gives 403 when the role is not allowed and otherwise returns the `User`.
- Produces: test helper `login(client, username) -> dict[str, str]` in `conftest.py`, which returns the auth header for a demo user.

- [ ] **Step 1:** Write the failing tests: `test_login_returns_token_and_role`, `test_login_wrong_password_401`, `test_me_without_token_401`, `test_me_with_stale_token_401` (log in twice; the first token is now invalid).
- [ ] **Step 2:** Run the tests. Expected: FAIL with 404.
- [ ] **Step 3:** Implement.
- [ ] **Step 4:** Run `npm run check`. Expected: pass.
- [ ] **Step 5:** Commit `feat(SP-4.3): login and role guard`.

### Task 4: IF-01, SP-1.1, SP-1.2, SP-1.3 gate pipeline

**Files:**
- Create: `backend/app/modules/sessions/{models,schemas,service,router}.py`
- Create: `backend/mocks/lpr.py`
- Modify: `backend/app/main.py`
- Test: `backend/tests/test_sessions.py`

**Interfaces:**
- Produces: `GateEvent(id, gate_id, plate: str | None, confidence: float | None, source: "lpr" | "manual", received_at, action: str, session_id: int | None, barrier_opened_at: datetime | None)`. `action` is one of `"entered" | "exited" | "manual_required"`.
- Produces: `ParkingSession(id, plate, entry_at, exit_at: datetime | None, status: "active" | "closed")`.
- Produces: `sessions.service.handle_plate(db, gate_id: str, plate: str, at: datetime, source: str, confidence: float | None) -> GateEvent`. It runs entry or exit by gate prefix, opens the barrier (sets `barrier_opened_at = clock.now()`), and raises `PlateConflict` (409) or `NoActiveSession` (404). Task 5 reuses it.
- Produces: `POST /api/lpr-events {plate, confidence: 0..1, gate_id, timestamp: AwareDatetime}` returns 201 with a `GateEvent` JSON. A low confidence or an invalid plate format is stored as `manual_required` with no session or barrier, and still returns 201 (IF-01: a valid request returns 201).
- Produces: `GET /api/gate-events?limit=20` (attendant, admin) returns the newest events first.
- Produces: `GET /api/sessions?status=active` (attendant, admin).
- Mock: `uv run --directory backend python mocks/lpr.py 30A-123.45 --gate IN-1 --confidence 0.95 [--url http://localhost:8000]`. It uses stdlib `urllib` only, prints the response, and sets the timestamp to the current UTC+7 time.

- [ ] **Step 1:** Write the failing tests, freezing the clock at 2026-10-19 08:00+07:
  - `test_tc15_lpr_event_valid_returns_201`: POST a valid event; response 201; one row from `GET /api/gate-events`.
  - `test_tc01_entry_creates_active_session`: plate `30A-123.45` at `IN-1`; one active session with that plate and `entry_at` equal to the event timestamp.
  - `test_tc02_barrier_opens_within_3s`: `barrier_opened_at - received_at <= 3 s`.
  - `test_tc03_exit_closes_session`: entry, then advance the clock 1 h, then exit at `OUT-1`; the session is `closed` and `exit_at` is set.
  - `test_duplicate_entry_409`, `test_exit_without_session_404`, `test_naive_timestamp_422`, `test_unknown_gate_422`.
  - `test_low_confidence_marks_manual_required`: confidence 0.6 gives 201 with `action == "manual_required"`, no session and `barrier_opened_at is None`.
- [ ] **Step 2:** Run the tests. Expected: FAIL.
- [ ] **Step 3:** Implement. Business time comes from the event `timestamp` for `entry_at`/`exit_at`, and from `clock.now()` for `received_at`/`barrier_opened_at`.
- [ ] **Step 4:** Run `npm run check`. Expected: pass. Start `npm run dev:be` and run the mock once; expected output: a 201 response.
- [ ] **Step 5:** Commit `feat(IF-01): LPR event pipeline with entry, exit and barrier`.

### Task 5: SP-4.4 audit log and IF-02 manual entry

**Files:**
- Create: `backend/app/modules/audit/{models,schemas,service,router}.py`
- Modify: `backend/app/modules/sessions/router.py`
- Test: `backend/tests/test_audit.py`

**Interfaces:**
- Consumes: `handle_plate`, `require_role`, `login`.
- Produces: `AuditLog(id, at, username, action: "manual_open" | "manual_entry", gate_id, reason: str, plate: str | None)` and `audit.service.record(db, user, action, gate_id, reason, plate=None) -> AuditLog`.
- Produces: `POST /api/barrier/manual-open {gate_id, reason: non-empty}` (attendant, admin) returns 201. It writes exactly one audit row; the barrier is a mock, so no session change.
- Produces: `POST /api/gate/manual-entry {gate_id, plate}` (attendant, admin) calls `handle_plate(source="manual")` plus one audit row with `action="manual_entry"` and `reason="LPR không chắc chắn"`. It returns 201 with the `GateEvent`.
- Produces: `GET /api/audit-log?limit=50` (admin only) returns the newest rows first.

- [ ] **Step 1:** Write the failing tests:
  - `test_tc14_manual_open_writes_one_log`: attendant manual-open with reason `Khách trả tiền mặt`; the log has exactly 1 row with username, `at` = frozen time, and the reason.
  - `test_tc16_low_confidence_then_manual_entry`: LPR confidence 0.6 gives `manual_required`; attendant manual entry with the same plate creates an active session and 1 audit row.
  - `test_tc13_driver_gets_403_on_admin_page`: a driver token on `GET /api/audit-log` gives 403.
  - `test_manual_open_requires_reason_422`.
  - `test_driver_cannot_manual_open_403`.
- [ ] **Step 2:** Run the tests. Expected: FAIL.
- [ ] **Step 3:** Implement.
- [ ] **Step 4:** Run `npm run check`. Expected: pass.
- [ ] **Step 5:** Commit `feat(SP-4.4): audit log, manual barrier and manual plate entry`.

### Task 6: SP-2.1 slot availability backend

**Files:**
- Create: `backend/app/modules/slots/{schemas,router}.py`, `backend/mocks/sensor.py`
- Modify: `backend/app/modules/slots/service.py`, `backend/app/main.py`
- Test: `backend/tests/test_slots.py`

**Interfaces:**
- Produces: `POST /api/sensor-events {slot_id, occupied: bool}` returns 200 `{slot_id, status}`; unknown slot gives 404. A repeated event for the same state is a no-op.
- Produces: `GET /api/slots/summary` (any logged-in role) returns `[{floor, zone, free, total}]`, ordered by floor then zone, 4 rows.
- Mock: `uv run --directory backend python mocks/sensor.py T1-A-05 --occupied` (`--free` to release). Uses stdlib only.

- [ ] **Step 1:** Write the failing tests:
  - `test_tc04_free_count_matches_sensor`: set floor 1 so that 20 slots are free, send one `occupied` event, then the floor 1 rows sum to 19 free.
  - `test_sensor_unknown_slot_404`.
  - `test_sensor_repeat_event_no_double_count`.
  - `test_summary_requires_login_401`.
- [ ] **Step 2:** Run the tests. Expected: FAIL.
- [ ] **Step 3:** Implement.
- [ ] **Step 4:** Run `npm run check`. Expected: pass.
- [ ] **Step 5:** Commit `feat(SP-2.1): sensor events and slot availability`.

### Task 7: Frontend login and role-based tabs (SP-4.3 UI)

**Files:**
- Create: `frontend/src/pages/login/LoginPage.tsx`, `frontend/src/lib/auth.ts`, `frontend/src/lib/auth.test.ts`
- Modify: `frontend/src/lib/api.ts`, `frontend/src/App.tsx`, `frontend/package.json` (Vitest, `test` script), root `package.json` (`check:fe` runs `npm --prefix frontend run test` before build)

**Interfaces:**
- Produces: `auth.ts`: `getSession(): {token, username, role} | null`, `saveSession(s)`, `clearSession()` (localStorage, wrapped in try/catch), and `tabsFor(role): ('driver'|'gate'|'admin')[]` with driver → `['driver']`, attendant → `['gate', 'driver']`, admin → `['admin', 'gate', 'driver']`.
- Produces: `api.ts` adds `Authorization: Bearer` when a session exists. On a 401 it clears the session and dispatches `window` event `spms:logout`.
- Uses shadcn `card`, `input`, `button`, `label` (add via the shadcn MCP or `npx shadcn@latest add`).

- [ ] **Step 1:** Write the failing Vitest test `tabsFor` with all 3 roles.
- [ ] **Step 2:** Run `npm --prefix frontend run test`. Expected: FAIL.
- [ ] **Step 3:** Implement. If there is no session, show the login page. Otherwise show the header with the username, a logout button and the API badge, and only the tabs from `tabsFor`.
- [ ] **Step 4:** Run `npm run check`. Expected: pass. Manual check: log in as each demo user and see the right tabs.
- [ ] **Step 5:** Commit `feat(SP-4.3): login page and role-based tabs`.

### Task 8: Frontend pages for Gate, Driver and Admin

**Files:**
- Modify: `frontend/src/pages/gate/GatePage.tsx`, `frontend/src/pages/driver/DriverPage.tsx`, `frontend/src/pages/admin/AdminPage.tsx`
- Use shadcn `table`, `dialog` as needed. Follow `docs/prototype/spms_ui.html` for layout.

**Interfaces:**
- Consumes: `GET /api/gate-events`, `POST /api/gate/manual-entry`, `POST /api/barrier/manual-open`, `GET /api/slots/summary`, `GET /api/audit-log`.

- [ ] **Step 1:** Build the Gate page:
  - Poll the event feed every 2 s.
  - Show a barrier badge: "Mở" when the newest event's `barrier_opened_at` is within 5 s.
  - Show the manual entry form (gate select `IN-1`/`OUT-1`, plate input with the plate regex check). It opens automatically when the newest event is `manual_required`.
  - Add a manual-open button with a required reason.
- [ ] **Step 2:** Build the Driver page: a free/total per floor and zone grid, polled every 3 s.
- [ ] **Step 3:** Build the Admin page: an audit log table (time in UTC+7, user, action, gate, reason).
- [ ] **Step 4:** Run `npm run check`. Expected: pass. Manual demo with both dev servers:
  - `mocks/lpr.py 30A-123.45 --gate IN-1` makes the feed show "entered" and the barrier "Mở".
  - `--confidence 0.6` opens the manual form.
  - `mocks/sensor.py T1-A-05 --occupied` makes the Driver count drop within 5 s.
  - A manual open appears in the Admin log.
- [ ] **Step 5:** Commit `feat(SP-1.1): gate, driver and admin pages`.

### Task 9: Sprint 1 close-out

**Files:**
- Modify: `docs/requirements/traceability.md`, `README.md` (add a mock usage section)

- [ ] **Step 1:** Set the Status column to `Done` for SP-1.1, SP-1.2, SP-1.3, SP-2.1, SP-4.3, SP-4.4, IF-01 and IF-02. Note on SP-1.3 "payment check added in Sprint 2", and on SP-4.3 "TC-13 re-checked on price page in Sprint 2".
- [ ] **Step 2:** Run `npm run check` from the root and keep the output for the sprint report.
- [ ] **Step 3:** Commit `docs: close Sprint 1 traceability`.
- [ ] **Step 4:** Excel `test_cases` update for TC-01–04 and TC-13–16 (status, actual_result, executed_by, executed_date) is done by the user at the sprint review (plan task T-06), not by the agent.
