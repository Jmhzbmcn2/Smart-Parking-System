# SPMS Sprint 2 Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Deliver the Sprint 2 backlog (SP-4.1, SP-3.1, SP-3.2, SP-4.2, SP-2.2.1, SP-2.2.2, T-02, T-03), so that UC-02 (reservation) and UC-03 (exit with payment) run end to end with mock devices and a mock payment gateway.

**Architecture:**
- The exit gate no longer closes a session directly. It computes the fee, creates a pending payment and waits.
- A successful payment (QR mock or cash) closes the session and opens the barrier.
- Each session keeps the price version that was current at entry.
- Reservations expire lazily: every read of slot state first releases holds that are past due. No background thread is needed, and the frozen clock can test expiry.

**Tech Stack:** As in Sprint 1. No new runtime dependency.

**Spec:**
- `docs/requirements/srs.md` (acceptance criteria and UC-02, UC-03).
- `docs/requirements/implementation-plan.md` (Sprint 2 scope).
- Workbook `test_cases`: TC-05, 06, 08, 09, 11, 12, 13, 17.
- `AGENTS.md` (conventions; CR-02 is in force).
- Sprint 1 plan `2026-10-17-spms-sprint-1.md` (existing interfaces).

## Global Constraints

- Everything in `AGENTS.md`. Sprint 1 Global Constraints still hold (plate regex, gate IDs, roles, threshold 0.8).
- Money is `int` VND everywhere, including JSON.
- Default price is first 2 h for 20 000 VND, then 10 000 VND per started hour. Billable hours are `max(1, ceil(minutes / 60))`.
- Fee formula, as code (the spec pins it):

  ```python
  hours = max(1, math.ceil(minutes / 60))
  fee = first_price if hours <= first_hours else first_price + (hours - first_hours) * per_hour
  ```

- The reservation hold is **10 minutes** (CR-02). A slot is still Reserved at minute 10 and Available at minute 11. The rule is `now > expires_at` releases it.
- The daily report uses the UTC+7 calendar day of `paid_at`.
- Schema changes have no migrations: delete `backend/spms.db` after pulling this sprint. Say so in the README.

## Review Focus

1. A second exit event for a plate whose payment is still pending: reuse the same pending payment, never create a second one (Task 3).
2. An exit timestamp earlier than `entry_at`: HTTP 422, no payment (Task 3).
3. Paying a payment that is already paid: HTTP 409, no second barrier event (Task 4).
4. Reserving a slot that is not Available, or a second active reservation by the same driver: HTTP 409 (Task 6).
5. Changing the price while a session is Active: that session is billed at the old price (Task 2/3, TC-11).

## Rulings (planner's calls)

- **Lazy expiry instead of a scheduled job for SP-2.2.2.** The observable behavior is the same (TC-06 reads the slot state), and the test needs no sleeping thread. Upgrade to a periodic task if a requirement needs an expiry notification.
- **QR code is shown as text.** The payload is `SPMS|<payment_id>|<amount>`, shown with two mock gateway buttons (success, fail) instead of a real QR image. Add a QR library when a real gateway is chosen.
- **Cash payment** (HZ-03 mitigation): an attendant can settle a pending or failed payment as cash. It writes an audit row and opens the barrier.
- **A slot stays Reserved until a sensor reports it occupied, or the hold time ends,** even if the reserving car has already entered. This is one rule, with no special case for a car that parks elsewhere.
- **CI:** GitHub Actions on `windows-latest`, running `npm run check`. Windows is the target platform.

---

### Task 1: CI and Sprint 1 leftovers

**Files:**
- Create: `.github/workflows/check.yml`
- Modify: `AGENTS.md` (remove "no GitHub remotes or push" from the scaffold rule; add "CI runs `npm run check` on push and pull request")

- [ ] **Step 1:** Write the workflow. Trigger on `push` and `pull_request` to `main`, using `windows-latest`. Steps:
  - `actions/checkout`, then `astral-sh/setup-uv`, then `actions/setup-node` (Node 22, npm cache on `frontend/package-lock.json`).
  - `uv sync --directory backend`.
  - `npm ci` in `frontend`.
  - `npm run check`.
- [ ] **Step 2:** Push the branch. Expected: the workflow run is green on GitHub.
- [ ] **Step 3:** Commit `ci: run npm run check on GitHub Actions`.

### Task 2: SP-4.1 price table

**Files:**
- Create: `backend/app/modules/billing/{models,schemas,service,router}.py`
- Modify: `backend/app/main.py` (register the billing module, seed the price), `backend/app/modules/sessions/models.py` (`ParkingSession.price_id`), `backend/app/modules/sessions/service.py` (snapshot at entry)
- Test: `backend/tests/test_billing.py`

**Interfaces:**
- Produces: `Price(id, first_hours: int, first_price: int, per_hour: int, created_at, created_by: str)`. The newest row is current.
- Produces: `billing.service.seed_price(db)` (idempotent default 2/20000/10000), `current_price(db) -> Price`, and `fee(minutes: int, price: Price) -> int`.
- Produces: `ParkingSession.price_id: int` (FK `prices.id`), set at entry to `current_price(db).id`.
- Produces:
  - `GET /api/prices/current` (any logged-in role).
  - `GET /api/prices` (admin; newest first).
  - `POST /api/prices {first_hours >= 1, first_price >= 0, per_hour >= 0}` (admin, 201). It writes an audit row with `action="price_change"`, `gate_id="-"`, and a reason that describes the old and new values.

- [ ] **Step 1:** Write the failing tests:
  - `test_fee_rounds_up_started_hours` (parametrised: 0 min = 20000, 60 = 20000, 120 = 20000, 121 = 30000, 190 = 40000).
  - `test_tc11_new_price_applies_to_new_sessions_only`: this test uses the billing in Task 3, so for now assert only that each session's `price_id` comes from entry time. Task 3 extends it to fees.
  - `test_tc13_driver_gets_403_on_price_admin`: driver gets 403 on `POST /api/prices` and on `GET /api/prices`.
  - `test_price_change_is_audited`.
- [ ] **Step 2:** Run the tests. Expected: FAIL.
- [ ] **Step 3:** Implement.
- [ ] **Step 4:** Run `npm run check`. Expected: pass.
- [ ] **Step 5:** Commit `feat(SP-4.1): versioned price table`.

### Task 3: SP-3.1 fee at the exit gate (SP-1.3 payment check)

**Files:**
- Modify: `backend/app/modules/billing/{models,service}.py`, `backend/app/modules/sessions/{models,schemas,service}.py`
- Test: `backend/tests/test_billing.py`, `backend/tests/test_sessions.py`

**Interfaces:**
- Produces: `Payment(id, session_id FK, gate_id, amount: int, status: "pending" | "paid" | "failed", method: "qr" | "cash" | None, created_at, paid_at: datetime | None)`.
- Produces: `billing.service.open_payment(db, session, gate_id) -> Payment`. It returns the existing pending or failed payment of the session if there is one; otherwise it creates a pending payment for `fee(minutes(session.entry_at, session.exit_at), session.price)`. Minutes are whole minutes, truncated.
- Changes `handle_plate` at an `OUT-` gate:
  - Set `session.exit_at = at`; the status stays `active`.
  - Call `open_payment`.
  - Event `action="payment_required"`, `payment_id` set, and `barrier_opened_at=None`.
  - Raise `InvalidExitTime` (422) when `at < session.entry_at`.
- Produces: `GateEvent.payment_id: int | None`, and the matching field in `GateEventOut`. New action values: `"payment_required"` and `"payment_failed"`.
- Produces: `GET /api/payments/{id}` (staff) returns `{id, session_id, plate, gate_id, amount, status, method, qr_payload}`, where `qr_payload = f"SPMS|{id}|{amount}"`.

- [ ] **Step 1:** Write the failing tests:
  - `test_tc08_fee_3h10m_is_40000`: entry 08:00, exit 11:10; the payment amount is 40000.
  - Extend `test_tc11_...`: session A enters, admin sets `per_hour=15000`, session B enters. Both stay 3 h 10 min. A pays 40000, B pays 50000.
  - `test_exit_creates_pending_payment_and_keeps_barrier_closed`.
  - `test_repeat_exit_reuses_pending_payment`.
  - `test_exit_before_entry_422`.
  - Update `test_tc03_exit_closes_session`: it now finishes in Task 4, so mark it as moved there.
- [ ] **Step 2:** Run the tests. Expected: FAIL.
- [ ] **Step 3:** Implement. Keep `minutes` and `fee` pure functions in `billing/service.py`. Avoid circular imports: `sessions.service` imports `billing.service`; `billing.service` never imports `sessions`.
- [ ] **Step 4:** Run `npm run check`. Expected: pass.
- [ ] **Step 5:** Commit `feat(SP-3.1): fee and pending payment at exit`.

### Task 4: SP-3.2 mock QR payment and cash fallback

**Files:**
- Modify: `backend/app/modules/billing/{schemas,router}.py`, `backend/app/modules/sessions/service.py`
- Test: `backend/tests/test_billing.py`, `backend/tests/test_sessions.py`

**Interfaces:**
- Produces: `sessions.service.complete_exit(db, payment, method: str) -> GateEvent`:
  - Marks the payment `paid` with `paid_at=clock.now()` and `method`.
  - Sets the session to `closed`.
  - Adds an `"exited"` GateEvent at `payment.gate_id` with `barrier_opened_at=clock.now()`.
  - Flushes only; the caller commits.
- Produces: `POST /api/payments/{id}/mock {success: bool}`. There is no auth, because it stands in for the gateway callback. It returns 200 with the payment.
  - On success it calls `complete_exit(..., "qr")`.
  - On fail it sets the status to `failed` and adds a `"payment_failed"` GateEvent (no barrier).
  - A payment that is already paid gives 409.
- Produces: `POST /api/payments/{id}/cash` (staff). It calls `complete_exit(..., "cash")` plus an audit row (`action="cash_payment"`, reason `"Thu tiền mặt"`) in one commit. A payment that is already paid gives 409.
- Mock: `backend/mocks/payment.py <payment_id> --success | --fail` (stdlib only).

- [ ] **Step 1:** Write the failing tests:
  - `test_tc09_failed_qr_keeps_barrier_closed`: the newest event is `payment_failed`, there is no barrier opening, and the session is still active.
  - `test_tc03_exit_closes_session`: exit, mock success, then the session is `closed`, `exit_at` is set, and an `exited` event has a barrier opening.
  - `test_pay_twice_409`.
  - `test_cash_after_failed_qr_closes_and_audits`.
  - `test_driver_cannot_pay_cash_403`.
- [ ] **Step 2:** Run the tests. Expected: FAIL.
- [ ] **Step 3:** Implement.
- [ ] **Step 4:** Run `npm run check`. Expected: pass.
- [ ] **Step 5:** Commit `feat(SP-3.2): mock QR payment with cash fallback`.

### Task 5: SP-4.2 daily revenue report

**Files:**
- Create: `backend/app/modules/reports/{schemas,service,router}.py`
- Modify: `backend/app/main.py`
- Test: `backend/tests/test_reports.py`

**Interfaces:**
- Produces: `GET /api/reports/daily?date=YYYY-MM-DD` (admin). The date defaults to today in UTC+7. It returns `{date, paid_count, total, by_method: {qr, cash}}`, summing payments whose `paid_at` falls in that day in UTC+7.

- [ ] **Step 1:** Write the failing tests:
  - `test_tc12_report_total_equals_paid_sessions`: 5 sessions are paid with different amounts on 2026-10-19, and the total equals their sum. Add one more payment at 2026-10-20 00:05+07; it must not be counted. Add one pending payment; it must not be counted.
  - `test_report_day_boundary_is_utc_plus_7`: a payment at 2026-10-19 23:30+07 (which is 16:30Z) belongs to 2026-10-19.
  - `test_report_admin_only_403`.
- [ ] **Step 2:** Run the tests. Expected: FAIL.
- [ ] **Step 3:** Implement. Compute the day bounds in UTC+7 and compare them against stored UTC values through `AwareDateTime`.
- [ ] **Step 4:** Run `npm run check`. Expected: pass.
- [ ] **Step 5:** Commit `feat(SP-4.2): daily revenue report`.

### Task 6: SP-2.2.1 and SP-2.2.2 reservations (CR-02)

**Files:**
- Create: `backend/app/modules/reservations/{models,schemas,service,router}.py`
- Modify: `backend/app/modules/slots/{models,service,router}.py` (status `"reserved"`, list endpoint, `summary` calls expiry first), `backend/app/main.py`
- Test: `backend/tests/test_reservations.py`

**Interfaces:**
- Produces: `HOLD = timedelta(minutes=10)` in `reservations/service.py`, with a comment citing CR-02.
- Produces: `Reservation(id, slot_id FK, plate, username, created_at, expires_at, status: "active" | "expired")`.
- Produces: `reservations.service.expire_due(db) -> int`. It sets `status="expired"` on active reservations with `now > expires_at`, and sets their slot back to `available` if it is still `reserved`.
  - `slots.service.summary` and the slot list call it first.
  - The function lives in `reservations` and is imported by the slots router. The slots service must not import reservations; the router does the call.
- Produces:
  - `POST /api/reservations {slot_id, plate}` (driver, 201). It needs an `available` slot and no active reservation for the same username; otherwise 409. An unknown slot gives 404, an invalid plate 422.
  - `GET /api/reservations/me` (driver) returns the active reservation or `null`.
  - `DELETE /api/reservations/me` (driver, 204) cancels it and frees the slot.
- Produces: `GET /api/slots?floor=&zone=&status=` (logged-in) returns `[{id, floor, zone, status}]`.

- [ ] **Step 1:** Write the failing tests, with the clock frozen at 2026-10-19 08:00+07:
  - `test_tc05_reservation_sets_slot_reserved`: T1-A-05 becomes `reserved`, and `expires_at` is 08:10.
  - `test_tc06_reservation_expires_at_minute_11`: at 08:10 the slot is still reserved; at 08:11 it is available and the reservation is `expired`.
  - `test_reserve_taken_slot_409`, `test_second_active_reservation_409`, `test_cancel_frees_slot`, `test_attendant_cannot_reserve_403`.
  - `test_reserved_slot_not_counted_free`: the summary `free` drops by 1.
- [ ] **Step 2:** Run the tests. Expected: FAIL.
- [ ] **Step 3:** Implement.
- [ ] **Step 4:** Run `npm run check`. Expected: pass.
- [ ] **Step 5:** Commit `feat(SP-2.2.1): 10-minute slot reservation with lazy expiry`.

### Task 7: Frontend for payment, price, report and reservation

**Files:**
- Modify: `frontend/src/pages/gate/GatePage.tsx`, `frontend/src/pages/admin/AdminPage.tsx`, `frontend/src/pages/driver/DriverPage.tsx`, `frontend/src/lib/gate.ts`
- Create: `frontend/src/lib/money.ts` + `money.test.ts` (`formatVnd(n) -> "40.000 ₫"`), `frontend/src/lib/reservation.ts` + test (`secondsLeft(expiresAt, now) -> number`, never negative)

- [ ] **Step 1:** Write the failing Vitest tests for `formatVnd` and `secondsLeft`.
- [ ] **Step 2:** Run `npm --prefix frontend run test`. Expected: FAIL.
- [ ] **Step 3:** Gate page: when the newest event is `payment_required` or `payment_failed`, show a payment card with the plate, the amount, the QR payload in a monospaced box, and three buttons: "Mô phỏng thành công", "Mô phỏng thất bại" and "Thu tiền mặt". Add the new action names to the event table.
- [ ] **Step 4:** Admin page: add three sections:
  - The current price with a form to change it.
  - A daily report with a date input, showing the total and the counts by method.
  - The existing audit log.
- [ ] **Step 5:** Driver page:
  - Keep the summary grid.
  - Add a slot picker (floor/zone select, then a list of available slot IDs) and a plate input, with a "Giữ chỗ" button.
  - Show the active reservation with an mm:ss countdown and a cancel button.
- [ ] **Step 6:** Run `npm run check`. Expected: pass.
- [ ] **Step 7:** Commit `feat(SP-3.2): payment, price, report and reservation UI`.

### Task 8: T-02 performance test TC-17 (NFR-01)

**Files:**
- Create: `backend/mocks/perf_tc17.py`
- Create: `docs/testing/tc17-results.md`

**Interfaces:**
- Script: `uv run --directory backend python mocks/perf_tc17.py [--url ...] [--n 100]`.
  - Sends `n` entry events with distinct valid plates, generated as `30A-{100+i:03d}.{i%100:02d}`, one after another.
  - For each event, measures the client-side time from send to a response with `barrier_opened_at` set.
  - Prints the count, mean, p95 (nearest-rank) and max in ms, and exits non-zero if p95 > 3000 ms.
  - Stdlib only.
- It runs against a throwaway DB: `SPMS_DATABASE_URL=sqlite:///perf.db` (give both PowerShell and Git Bash forms in the doc).

- [ ] **Step 1:** Write a pytest `test_p95_nearest_rank` for the percentile helper, importing it from the script module (guard the script body with `if __name__ == "__main__":`).
- [ ] **Step 2:** Implement the script.
- [ ] **Step 3:** Start the backend on a throwaway DB, run the script, and paste the real output, machine description and date into `tc17-results.md`. This is the evidence for report section 6.2.
- [ ] **Step 4:** Run `npm run check`. Expected: pass.
- [ ] **Step 5:** Commit `test(NFR-01): TC-17 gate latency script and results`.

### Task 9: T-03 end-to-end test and sprint close-out

**Files:**
- Create: `backend/tests/test_e2e.py`
- Modify: `docs/requirements/traceability.md`, `README.md` (mock payment usage, "delete spms.db after pulling Sprint 2")

- [ ] **Step 1:** Write `test_e2e_uc02_uc01_uc03`. It goes through the HTTP API only, with the clock frozen and advanced:
  1. The driver reserves T1-A-05.
  2. The car enters at IN-1. The sensor reports T1-A-05 occupied.
  3. At +3 h 10 min the car exits at OUT-1. The first mock payment fails, and the barrier stays closed.
  4. A second mock payment succeeds. The session is closed, the barrier is open, and the slot is freed by the sensor.
  5. The admin daily report shows 40000.

  This is the evidence for report section 8.3.
- [ ] **Step 2:** Run `npm run check`. Expected: pass.
- [ ] **Step 3:** Set traceability status to `Done` for SP-4.1, SP-3.1, SP-3.2, SP-4.2, SP-2.2.1 and SP-2.2.2. Change SP-1.3 to `Done` (remove the Sprint 2 note) and SP-4.3 to `Done` (TC-13 now also covers the price page). Add a T-02 note to NFR-01: "TC-17 measured, see docs/testing/tc17-results.md".
- [ ] **Step 4:** Commit `docs: close Sprint 2 traceability`.
- [ ] **Step 5:** The user updates the Excel `test_cases` sheet for TC-03, 05, 06, 08, 09, 11, 12, 13 and 17 at the sprint review.
