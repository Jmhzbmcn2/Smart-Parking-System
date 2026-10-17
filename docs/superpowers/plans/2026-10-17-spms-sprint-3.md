# SPMS Sprint 3 Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Deliver the Sprint 3 backlog: SP-2.3, SP-3.3, T-04 (NFR-04), T-05 (NFR-05), T-06 (all test cases plus the Excel update), and T-08 (demo prep). The final demo on 30/11 must cover UC-01, UC-02 and UC-03. All evidence the final report needs must be in the repo.

**Architecture:**
- The slot suggestion is a pure ordering over available slots.
- Invoices go to a file outbox by default, and to SMTP only when it is configured.
- Personal data is encrypted with deterministic AES-SIV (256-bit) through a SQLAlchemy column type. Equality lookups and the unique Active-plate index keep working.
- HTTPS uses a local self-signed certificate.

**Tech Stack:** As before, plus `cryptography` (backend runtime; AES-SIV and certificate generation) and `openpyxl` (backend dev group; Excel update script).

**Spec:**
- `docs/requirements/srs.md`.
- `docs/requirements/implementation-plan.md` (Sprint 3 scope).
- Workbook `test_cases` TC-07, TC-10, TC-18, sheet `nfrs`, sheet `hazards` HZ-04.
- `AGENTS.md` (NFR-04 rule: field-level encryption via a column type in `core/`, plus HTTPS).
- Sprint 2 plan for the existing interfaces.

## Global Constraints

- Everything in `AGENTS.md` and the Sprint 1–2 Global Constraints.
- Scope cut order if time runs short, from the plan's risk table: drop SP-3.3 first, then SP-2.3. Never drop T-04, T-06 or T-08.
- Encryption covers personal data: every `plate` column (`parking_sessions`, `gate_events`, `reservations`, `audit_log`) and `users.username`. Passwords stay scrypt hashes; tokens stay random.
- The data key comes from env `SPMS_DATA_KEY` (base64, 64 bytes, for AES-256-SIV). If the variable is unset, the backend creates `backend/.data_key` on first start and reuses it. `.data_key`, `*.pem` and `backend/outbox/` are git-ignored.
- After pulling T-04, delete `backend/spms.db`: existing rows are plaintext. Say so in the README.

## Review Focus

1. A lookup by plate after encryption (the active session, a duplicate entry with 409, a reservation per driver) must still work. It needs deterministic encryption, and tests must cover it (Task 3).
2. The DB file must not contain the plate in plaintext. A test reads the raw SQLite file or column (Task 3).
3. No free slot is left when a suggestion is requested: return `null`, not an error (Task 1).
4. A wrong or missing device key on `/api/lpr-events` and `/api/sensor-events`: 401 (Task 4).
5. Logout must make the token unusable on the server (Task 4).

## Rulings (planner's calls)

- **"Gần lối vào" means the lowest ordering `(floor, zone, number)`.** Entry is at floor 1, zone A, slot 01. TC-07 (T1-A-01 occupied, then suggest T1-A-02) matches this. Replace it with a distance table if the real layout differs.
- **A reservation wins over the suggestion.** If the entering plate holds a reservation, the suggestion is that reserved slot.
- **Invoice email goes to a file outbox** (`backend/outbox/<payment_id>.eml`, built with the stdlib `email` package). It uses SMTP only when `SPMS_SMTP_HOST` is set. TC-10 is verified by the outbox file's timestamp ≤ 5 min after `paid_at`.
- **Deterministic AES-SIV instead of AES-GCM with a separate hash column.** It is one column, and lookups and the unique index keep working. The leak is equality only (the same plate gives the same ciphertext); this is accepted for the course scope and noted in the report.
- **Device authentication is a shared key header `X-Device-Key`** (env `SPMS_DEVICE_KEY`, default `dev-device-key`). The mocks send it.
- **TC-18 stays Not Run:** it needs the camera vendor and 500 labeled images (implementation plan risk table).
- **T-05 and T-07 are human or buffer work.** This plan prepares the T-05 materials only. T-07 (bug buffer, 16 h) has no tasks.

---

### Task 0: Sprint 2 leftover, one active reservation per slot

**Files:**
- Modify: `backend/app/modules/reservations/models.py`, `backend/app/modules/reservations/service.py`
- Test: `backend/tests/test_reservations.py`

- [ ] **Step 1:** Write the failing test `test_two_drivers_cannot_hold_same_slot`. It adds a second demo user directly in the test DB (role `driver`), lets driver 1 reserve T1-A-05, and expects driver 2 to get 409. Then it inserts a second active `Reservation` row for T1-A-05 straight through the session and expects `IntegrityError`.
- [ ] **Step 2:** Run the test. Expected: the direct insert does not raise, so the test fails.
- [ ] **Step 3:** Add `Index("uq_active_slot", "slot_id", unique=True, sqlite_where=text("status = 'active'"))` to `Reservation`, using the same pattern as `uq_active_plate` in `sessions/models.py`. Map an `IntegrityError` at commit in `reserve` to `SlotNotAvailable`.
- [ ] **Step 4:** Run `npm run check`. Expected: pass. Delete `backend/spms.db`.
- [ ] **Step 5:** Commit `fix(SP-2.2.1): unique active reservation per slot`.

### Task 1: SP-2.3 suggest the nearest free slot

**Files:**
- Modify: `backend/app/modules/slots/service.py`, `backend/app/modules/sessions/{service,schemas}.py`, `frontend/src/pages/gate/GatePage.tsx`
- Test: `backend/tests/test_slots.py`

**Interfaces:**
- Produces: `slots.service.suggest(db) -> str | None`, the first `available` slot ordered by `floor`, `zone`, then the numeric part.
- Produces: `GateEvent.suggested_slot: str | None`, set on `entered` events. The plate's reserved slot comes first, otherwise `suggest(db)`.
- Gate page: show "Gợi ý: T1-A-02" on the newest `entered` event.

- [ ] **Step 1:** Write the failing tests: `test_tc07_suggests_slot_nearest_entrance` (T1-A-01 occupied, then T1-A-02), `test_suggest_none_when_full`, and `test_reserved_plate_gets_its_reserved_slot`.
- [ ] **Step 2:** Run the tests. Expected: FAIL.
- [ ] **Step 3:** Implement. The tests already pin the ordering; sort with `int(id[-2:])`, not a string compare.
- [ ] **Step 4:** Run `npm run check`. Expected: pass.
- [ ] **Step 5:** Commit `feat(SP-2.3): suggest nearest free slot on entry`.

### Task 2: SP-3.3 e-invoice by email

**Files:**
- Create: `backend/app/modules/billing/invoice.py`
- Modify: `backend/app/modules/billing/router.py`, `.gitignore`, `frontend/src/pages/gate/GatePage.tsx`
- Test: `backend/tests/test_billing.py`

**Interfaces:**
- Produces: `POST /api/payments/{id}/invoice {email: EmailStr}`. It is open, because the driver uses it at the exit kiosk. It returns 202 `{sent_at, path | null}`. The payment must be `paid`, otherwise 409.
- Produces: `billing.invoice.send(payment, session, email) -> datetime`.
  - The invoice contains the plate, entry, exit, billable hours, amount (VND), method and payment ID.
  - It writes `backend/outbox/<id>.eml`, or sends via SMTP (host/port/user/password from env).
  - Use `pydantic`'s `EmailStr` only if `email-validator` is already installed (it comes with `fastapi[standard]`); otherwise use a plain `str` with `@` validation.

- [ ] **Step 1:** Write the failing tests:
  - `test_tc10_invoice_within_5_minutes`: write to a temporary outbox via `monkeypatch.setenv`; the file exists, it contains the amount `40.000`, and `sent_at - paid_at <= 5 min`.
  - `test_invoice_unpaid_409`.
- [ ] **Step 2:** Run the tests. Expected: FAIL.
- [ ] **Step 3:** Implement. Gate page: after a successful payment, show an email input with a "Gửi hóa đơn" button.
- [ ] **Step 4:** Run `npm run check`. Expected: pass.
- [ ] **Step 5:** Commit `feat(SP-3.3): email invoice via outbox or SMTP`.

### Task 3: T-04 encryption at rest (NFR-04)

**Files:**
- Create: `backend/app/core/crypto.py`
- Modify: every model with a `plate` column, `auth/models.py` (`username`), `backend/pyproject.toml` (`cryptography`), `.gitignore`
- Test: `backend/tests/test_crypto.py`

**Interfaces:**
- Produces: `core.crypto.EncryptedString(TypeDecorator[str])`. Bind does `AESSIV(key).encrypt(value.encode(), None)` and stores base64 text; the result value decrypts.
- Produces: `core.crypto.load_key() -> bytes`, which reads `SPMS_DATA_KEY` or `backend/.data_key` and creates it if missing. Tests set a fixed key through an env fixture in `conftest.py`.

- [ ] **Step 1:** Write the failing tests:
  - `test_plate_not_stored_in_plaintext`: after an entry, `SELECT plate FROM parking_sessions` on the raw connection does not contain `30A-123.45`.
  - `test_roundtrip_and_lookup_still_work`: run all existing session tests unchanged (this is the regression).
  - `test_same_plate_same_ciphertext`: the duplicate-entry 409 still holds.
  - `test_username_encrypted`.
- [ ] **Step 2:** Run the tests. Expected: FAIL on the plaintext assertions.
- [ ] **Step 3:** Implement, then apply the column type to the listed columns.
- [ ] **Step 4:** Run `npm run check`. Expected: pass, with all earlier tests unchanged.
- [ ] **Step 5:** Commit `feat(NFR-04): field-level AES-256-SIV encryption of personal data`.

### Task 4: T-04 HTTPS, device key and logout (NFR-04, HZ-04)

**Files:**
- Create: `backend/mocks/make_cert.py` (self-signed `localhost` certificate via `cryptography`; writes `backend/certs/{key,cert}.pem`)
- Modify:
  - root `package.json`: add `dev:be:https`, running `uv run --directory backend uvicorn app.main:app --port 8443 --ssl-keyfile certs/key.pem --ssl-certfile certs/cert.pem`.
  - `frontend/vite.config.ts`: when env `SPMS_HTTPS=1`, proxy to `https://localhost:8443` with `secure: false`.
  - `backend/app/modules/{sessions,slots,billing}/router.py`: add the device key dependency to the device endpoints.
  - `auth/router.py`: add `POST /api/auth/logout`.
  - The mocks: send the `X-Device-Key` header.
- Test: `backend/tests/test_auth.py`, `backend/tests/test_sessions.py`

**Interfaces:**
- Produces: `core.config.DEVICE_KEY` and a `require_device` dependency (missing or wrong header gives 401). It applies to `/api/lpr-events`, `/api/sensor-events` and `/api/payments/{id}/mock`.
- Produces: `POST /api/auth/logout` (logged-in, 204), which sets `user.token = None`. The frontend logout calls it before clearing local storage.
- TLS: Python's `ssl` default server context already refuses below TLS 1.2. Document how to verify it with `curl -k --tlsv1.1 --tls-max 1.1 https://localhost:8443/api/health` (expected: failure).

- [ ] **Step 1:** Write the failing tests: `test_device_key_required_401`, `test_logout_invalidates_token`. Update `post_lpr` and the sensor helpers to send the key.
- [ ] **Step 2:** Run the tests. Expected: FAIL.
- [ ] **Step 3:** Implement. Record the TLS check output in `docs/testing/nfr04-inspection.md`, together with a checklist of encrypted columns (the NFR-04 verification method is Inspection).
- [ ] **Step 4:** Run `npm run check`. Expected: pass.
- [ ] **Step 5:** Commit `feat(NFR-04): HTTPS dev server, device key, server-side logout`.

### Task 5: T-05 usability test kit (NFR-05)

**Files:**
- Create: `docs/testing/nfr05-usability.md`

- [ ] **Step 1:** Write the kit:
  - The task given to each driver: "Đặt chỗ một slot trống ở tầng 1".
  - Start and stop points: from the logged-in Driver tab to a visible countdown.
  - A results table with 3 rows: participant (initials), first time using the app (yes/no), seconds, success, and comments. Pass means every time ≤ 60 s.
  - A short consent note.
- [ ] **Step 2:** Commit `docs(NFR-05): usability test kit`. The user runs the sessions and fills in the table.

### Task 6: T-06 run every test case and update the Excel workbook

**Files:**
- Create: `backend/mocks/update_test_cases.py`
- Modify: `backend/pyproject.toml` (dev group: `openpyxl`), `docs/requirements/traceability.md`

**Interfaces:**
- Script: `uv run --directory backend python mocks/update_test_cases.py --junit report.xml --executor "<name>" [--date 2026-11-28]`.
  - It reads the pytest JUnit XML and maps each `test_tc<NN>_*` result to `TC-<NN>`. A TC passes only if all its tests pass.
  - It writes `status` (`Pass` / `Fail`), `actual_result` (`"Automated: <k> test(s) passed"` or the first failure message), `executed_by` and `executed_date` into `docs/requirements/SPMS_requirements.xlsx` sheet `test_cases`. Dates are ISO strings, matching the sheet.
  - It does not touch TCs that have no automated test. TC-17 comes from `tc17-results.md`. TC-18 stays Not Run, and so do the manual ones; the user fills those in.
  - It never edits other sheets or headers.
- pytest: `uv run --directory backend pytest -q --junitxml=report.xml`.

- [ ] **Step 1:** Write a pytest `test_tc_id_mapping`: `test_tc08_fee_3h10m_is_40000` maps to `TC-08`, and a non-TC test maps to `None`.
- [ ] **Step 2:** Implement. Run the script on a copy of the workbook first and diff the sheet by printing it, then on the real file.
- [ ] **Step 3:** Set every implemented requirement in `traceability.md` to `Done`, and every NFR to its verification result (NFR-01 measured, NFR-02 Not Run, NFR-03/06 Analysis written in report, NFR-04 Inspection doc, NFR-05 kit). Add a coverage line: "TC-01–TC-17 automated or measured; TC-18 Not Run (vendor)".
- [ ] **Step 4:** Run `npm run check`. Expected: pass.
- [ ] **Step 5:** Commit `test(T-06): update test_cases from automated results`.

### Task 7: T-08 demo script and report evidence

**Files:**
- Create: `docs/demo.md`
- Modify: `README.md`

- [ ] **Step 1:** Write `docs/demo.md`, a 10-minute script for 30/11 with exact commands:
  - Reset the DB, start both servers, log in as the three roles.
  - UC-02: reserve.
  - UC-01: `mocks/lpr.py`, sensor, suggestion. The low-confidence case leads to manual entry.
  - UC-03: exit, failed QR, cash or a successful QR, invoice.
  - Admin: report, price change, audit log.
  - Close with the `npm run check` output.
- [ ] **Step 2:** Add an "Evidence for the final report" list to `docs/demo.md`. It maps each report section to its repo source:
  - 6.2: `tc17-results.md`.
  - 7.1: `traceability.md`.
  - 7.2: pytest/Vitest output and the Excel sheet.
  - 7.3: `change_requests` and CR-02 in the code.
  - 8.1: the `hazards` sheet and the HZ mitigations implemented (HZ-02 manual entry, HZ-03 cash, HZ-04 encryption).
  - 8.3: `test_e2e.py`.
- [ ] **Step 3:** Rehearse the script once on a clean clone. Fix anything that fails, under T-07 buffer.
- [ ] **Step 4:** Commit `docs(T-08): demo script and report evidence map`.
