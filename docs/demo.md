# SPMS demo script (30/11, 10 minutes)

Two terminals for the servers, one for the mock devices, one browser window. Plate used throughout: `30A-123.45`. Payment IDs are 1, 2, ... in the order they are created on a fresh database.

## 0. Before the demo (not timed)

Stop any running backend, then reset the database (it is recreated and seeded on the next start):

```text
PowerShell:  Remove-Item backend\spms.db -ErrorAction SilentlyContinue
Git Bash:    rm -f backend/spms.db
```

Terminal 1: `npm run dev:be`. Terminal 2: `npm run dev:fe`. Open `http://localhost:5173`.
Optional HTTPS variant (NFR-04): see [nfr04-inspection.md](testing/nfr04-inspection.md). Mock devices send `X-Device-Key` already.

## 1. Roles (1 min)

Log in as `driver` / `driver123`: only the Driver tab. Log out. Log in as `attendant` / `attendant123`: Gate tab. Log out. Log in as `admin` / `admin123`: all tabs. Say: roles are enforced on the server (SP-4.3, TC-13); logout invalidates the token.

## 2. UC-02 reserve a slot (1 min)

Log in as `driver`. The free counts show 50 per zone. Pick floor 1, zone A, click a slot (for example `T1-A-05`), type `30A-123.45`, click "Giữ chỗ". The card "Your reservation" shows the slot and a 10:00 countdown (CR-02: hold is 10 minutes). Say: after 10 minutes the slot is released (TC-06, checked at minute 11).

## 3. UC-01 vehicle entry (2 min)

Log in as `attendant`, open the Gate tab. In terminal 3 (repository root):

```text
uv run --directory backend python mocks/lpr.py 30A-123.45 --gate IN-1 --confidence 0.95
```

The event row shows `entered`, the barrier opens, and the badge "Gợi ý" shows the reserved slot `T1-A-05` (SP-2.3: a plate's own reservation wins, otherwise the nearest free slot). Park it with the sensor:

```text
uv run --directory backend python mocks/sensor.py T1-A-05 --occupied
```

Switch to the Driver tab: the free count for floor 1 zone A drops. Low confidence (HZ-02, IF-02):

```text
uv run --directory backend python mocks/lpr.py 51F-678.90 --gate IN-1 --confidence 0.6
```

The Gate page asks for manual entry. Use "Manual plate entry" with `51F-678.90`. Say: no automatic charge on an unsure read.

## 4. UC-03 exit and payment (3 min)

```text
uv run --directory backend python mocks/lpr.py 30A-123.45 --gate OUT-1
```

The event is `payment_required`, the barrier stays closed, and the payment card shows the fee (minimum 20.000 VND for the first 2 hours; fee rules TC-08). Failed QR first (TC-09, HZ-03):

```text
uv run --directory backend python mocks/payment.py 1 --fail
```

The card shows "QR payment failed", the barrier is still closed. Then pay: click "Mô phỏng thành công", or use "Thu tiền mặt" as the fallback when the gateway is down (HZ-03). The session closes and the barrier opens. In the "Hóa đơn điện tử" card, type any email and click "Gửi hóa đơn". The invoice file appears as `backend/outbox/1.eml` (SP-3.3; set `SPMS_SMTP_HOST` to send real mail). Optional: `uv run --directory backend python mocks/payment.py 2 --success` for the second car.

## 5. Admin (2 min)

Log in as `admin`. "Daily revenue": the total equals the paid sessions (TC-12). "Price": change the first-two-hours price, click "Save price"; say new prices apply only to new sessions (TC-11). Audit log: first, as `attendant` on the Gate tab, use "Manual barrier open" with a reason (required). Then, as `admin`, the "Audit log" table on the Admin tab shows one new row with user, time and reason (SP-4.4, TC-14).

## 6. Close (1 min)

```text
npm run check
```

Show: Ruff and pytest pass (about 100 tests), ESLint, `tsc -b` and Vitest/build pass. Say: tests are named `test_tc<NN>_...` and map to the test cases in the workbook (`backend/mocks/update_test_cases.py` writes the results).

## If something goes wrong

| Problem | Fix |
|---|---|
| Login fails or the server crashes on start with old data | Stop the backend, reset the database (section 0), restart. |
| Mock prints 401 | Device key mismatch: unset `SPMS_DEVICE_KEY` or set it to the same value for the backend and the mock. |
| Mock cannot connect | Add `--url http://127.0.0.1:8000` (the `localhost` IPv6 fallback can be slow on Windows). |
| `npm` blocked in PowerShell | Use `npm.cmd`. |

## Evidence for the final report

| Report section | Source in this repository |
|---|---|
| 6.2 Performance (NFR-01) | [testing/tc17-results.md](testing/tc17-results.md) and `backend/mocks/perf_tc17.py` |
| 7.1 Traceability | [requirements/traceability.md](requirements/traceability.md) |
| 7.2 Test results | `npm run check` output (pytest and Vitest) and the `test_cases` sheet in [requirements/SPMS_requirements.xlsx](requirements/SPMS_requirements.xlsx) |
| 7.3 Change requests | `change_requests` sheet; CR-02 is in force: 10-minute hold in `backend/app/modules/reservations/`, TC-05 and TC-06 tests |
| 8.1 Hazards | `hazards` sheet; HZ-02 manual entry at low confidence (TC-16), HZ-03 cash fallback (`/payments/{id}/cash`), HZ-04 encryption and device key ([testing/nfr04-inspection.md](testing/nfr04-inspection.md)). HZ-01 (barrier sensor) is out of scope: no hardware. |
| 8.3 End-to-end flow | `backend/tests/test_e2e.py` |
| NFR-05 usability | [testing/nfr05-usability.md](testing/nfr05-usability.md) (sessions run by the team) |
| NFR-02 LPR accuracy | TC-18 Not Run: needs the camera vendor's sample set |
