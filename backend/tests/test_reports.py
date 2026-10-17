from datetime import datetime, timedelta

from app.core import clock
from tests.test_billing import exit_gate, mock_pay
from tests.test_sessions import post_lpr


def pay_session(client, index, hours, paid_at, method="qr", login=None):
    """Enter `hours` before `paid_at`, exit, then settle the payment at `paid_at`."""
    plate = f"30A-{100 + index}.{index:02d}"
    clock.freeze(paid_at - timedelta(hours=hours))
    entry_ts = (paid_at - timedelta(hours=hours)).isoformat()
    post_lpr(client, plate=plate, timestamp=entry_ts)
    payment_id = exit_gate(client, plate=plate, timestamp=paid_at.isoformat()).json()["payment_id"]
    clock.freeze(paid_at)
    if method == "qr":
        mock_pay(client, payment_id, True)
    else:
        client.post(f"/api/payments/{payment_id}/cash", headers=login(client, "attendant"))
    return payment_id


def day(d, h=9, m=0):
    return datetime(2026, 10, d, h, m, tzinfo=clock.TZ)


def report(client, login, date=None):
    params = {"date": date} if date else {}
    return client.get("/api/reports/daily", params=params, headers=login(client, "admin"))


def test_tc12_report_total_equals_paid_sessions(client, login, frozen_clock):
    hours = [1, 3, 4, 2, 5]  # 20000, 30000, 40000, 20000, 50000
    for i, h in enumerate(hours):
        pay_session(client, i, h, day(19, 9 + i))
    expected = 20000 + 30000 + 40000 + 20000 + 50000
    pay_session(client, 10, 3, datetime(2026, 10, 20, 0, 5, tzinfo=clock.TZ))  # next day
    # A pending payment: exits but never pays.
    clock.freeze(day(19, 20))
    post_lpr(client, plate="30A-999.99", timestamp=day(19, 18).isoformat())
    exit_gate(client, plate="30A-999.99", timestamp=day(19, 20).isoformat())
    body = report(client, login, "2026-10-19").json()
    assert body == {
        "date": "2026-10-19",
        "paid_count": 5,
        "total": expected,
        "by_method": {"qr": expected, "cash": 0},
    }


def test_report_day_boundary_is_utc_plus_7(client, login, frozen_clock):
    # 23:30+07 on the 19th is 16:30Z, still the 19th in UTC+7.
    pay_session(client, 1, 1, datetime(2026, 10, 19, 23, 30, tzinfo=clock.TZ))
    assert report(client, login, "2026-10-19").json()["total"] == 20000
    assert report(client, login, "2026-10-20").json()["total"] == 0
    assert report(client, login, "2026-10-18").json()["paid_count"] == 0


def test_report_splits_cash_and_defaults_to_today(client, login, frozen_clock):
    pay_session(client, 1, 1, day(19, 9))
    pay_session(client, 2, 3, day(19, 10), method="cash", login=login)
    body = report(client, login).json()  # frozen clock: today is 2026-10-19
    assert body["date"] == "2026-10-19"
    assert body["by_method"] == {"qr": 20000, "cash": 30000}
    assert body["paid_count"] == 2


def test_report_admin_only_403(client, login):
    assert client.get("/api/reports/daily").status_code == 401
    for user in ("driver", "attendant"):
        response = client.get("/api/reports/daily", headers=login(client, user))
        assert response.status_code == 403
