import pytest

from app.modules.billing.models import Price
from app.modules.billing.service import fee
from tests.test_sessions import post_lpr, sessions

DEFAULT = Price(first_hours=2, first_price=20000, per_hour=10000)


@pytest.mark.parametrize(
    ("minutes", "expected"),
    [(0, 20000), (60, 20000), (120, 20000), (121, 30000), (190, 40000)],
)
def test_fee_rounds_up_started_hours(minutes, expected):
    assert fee(minutes, DEFAULT) == expected


def set_price(client, headers, **values):
    body = {"first_hours": 2, "first_price": 20000, "per_hour": 10000} | values
    return client.post("/api/prices", json=body, headers=headers)


def test_tc11_new_price_applies_to_new_sessions_only(client, login, frozen_clock):
    post_lpr(client, plate="30A-111.11")
    assert set_price(client, login(client, "admin"), per_hour=15000).status_code == 201
    post_lpr(client, plate="30A-222.22")
    by_plate = {s["plate"]: s for s in sessions(client, login)}
    assert by_plate["30A-111.11"]["price_id"] != by_plate["30A-222.22"]["price_id"]


def test_tc13_driver_gets_403_on_price_admin(client, login):
    headers = login(client, "driver")
    assert set_price(client, headers).status_code == 403
    assert client.get("/api/prices", headers=headers).status_code == 403


def test_price_current_any_role(client, login):
    response = client.get("/api/prices/current", headers=login(client, "driver"))
    assert response.status_code == 200
    assert response.json()["per_hour"] == 10000
    assert client.get("/api/prices/current").status_code == 401


def test_price_list_newest_first_and_validated(client, login):
    admin = login(client, "admin")
    assert set_price(client, admin, first_hours=0).status_code == 422
    assert set_price(client, admin, per_hour=-1).status_code == 422
    set_price(client, admin, per_hour=12000)
    rows = client.get("/api/prices", headers=admin).json()
    assert [r["per_hour"] for r in rows] == [12000, 10000]
    assert rows[0]["created_by"] == "admin"


def test_price_change_is_audited(client, login, frozen_clock):
    admin = login(client, "admin")
    set_price(client, admin, per_hour=15000)
    [row] = client.get("/api/audit-log", headers=admin).json()
    assert row["action"] == "price_change"
    assert row["gate_id"] == "-"
    assert "10000" in row["reason"] and "15000" in row["reason"]


T_IN = "2026-10-19T08:00:00+07:00"
T_OUT = "2026-10-19T11:10:00+07:00"  # 3 h 10 min later


def exit_gate(client, plate="30A-123.45", timestamp=T_OUT):
    return post_lpr(client, plate=plate, gate="OUT-1", timestamp=timestamp)


def payment_of(client, login, response):
    payment_id = response.json()["payment_id"]
    result = client.get(f"/api/payments/{payment_id}", headers=login(client, "attendant"))
    assert result.status_code == 200
    return result.json()


def test_tc08_fee_3h10m_is_40000(client, login, frozen_clock):
    post_lpr(client)
    payment = payment_of(client, login, exit_gate(client))
    assert payment["amount"] == 40000
    assert payment["status"] == "pending"
    assert payment["qr_payload"] == f"SPMS|{payment['id']}|40000"
    assert payment["plate"] == "30A-123.45"


def test_tc11_fee_uses_price_at_entry(client, login, frozen_clock):
    post_lpr(client, plate="30A-111.11")
    set_price(client, login(client, "admin"), per_hour=15000)
    post_lpr(client, plate="30A-222.22")
    a = payment_of(client, login, exit_gate(client, plate="30A-111.11"))
    b = payment_of(client, login, exit_gate(client, plate="30A-222.22"))
    assert (a["amount"], b["amount"]) == (40000, 50000)


def test_exit_creates_pending_payment_and_keeps_barrier_closed(client, login, frozen_clock):
    post_lpr(client)
    body = exit_gate(client).json()
    assert body["action"] == "payment_required"
    assert body["barrier_opened_at"] is None
    [session] = sessions(client, login)
    assert session["status"] == "active"


def test_repeat_exit_reuses_pending_payment(client, login, frozen_clock):
    post_lpr(client)
    first = exit_gate(client).json()["payment_id"]
    second = exit_gate(client, timestamp="2026-10-19T12:00:00+07:00").json()["payment_id"]
    assert first == second
    assert payment_of(client, login, exit_gate(client))["amount"] == 40000


def test_exit_before_entry_422(client, login, frozen_clock):
    post_lpr(client)
    response = exit_gate(client, timestamp="2026-10-19T07:59:00+07:00")
    assert response.status_code == 422
    [session] = sessions(client, login)
    assert session["exit_at"] is None
    events = client.get("/api/gate-events", headers=login(client, "attendant")).json()
    assert [e["action"] for e in events] == ["entered"]


def test_payment_requires_staff(client, login):
    assert client.get("/api/payments/1").status_code == 401
    assert client.get("/api/payments/1", headers=login(client, "driver")).status_code == 403
    assert client.get("/api/payments/999", headers=login(client, "attendant")).status_code == 404


def start_exit(client):
    post_lpr(client)
    return exit_gate(client).json()["payment_id"]


def mock_pay(client, payment_id, success):
    return client.post(f"/api/payments/{payment_id}/mock", json={"success": success})


def gate_events(client, login):
    return client.get("/api/gate-events", headers=login(client, "attendant")).json()


def test_tc09_failed_qr_keeps_barrier_closed(client, login, frozen_clock):
    payment_id = start_exit(client)
    response = mock_pay(client, payment_id, False)
    assert response.status_code == 200
    assert response.json()["status"] == "failed"
    newest = gate_events(client, login)[0]
    assert newest["action"] == "payment_failed"
    assert newest["barrier_opened_at"] is None
    assert sessions(client, login)[0]["status"] == "active"


def test_tc03_exit_closes_session(client, login, frozen_clock):
    payment_id = start_exit(client)
    response = mock_pay(client, payment_id, True)
    assert response.status_code == 200
    assert (response.json()["status"], response.json()["method"]) == ("paid", "qr")
    [session] = sessions(client, login)
    assert session["status"] == "closed"
    assert session["exit_at"] is not None
    newest = gate_events(client, login)[0]
    assert newest["action"] == "exited"
    assert newest["barrier_opened_at"] is not None
    assert newest["gate_id"] == "OUT-1"


def test_failed_qr_can_be_retried(client, login, frozen_clock):
    payment_id = start_exit(client)
    mock_pay(client, payment_id, False)
    assert mock_pay(client, payment_id, True).json()["status"] == "paid"
    assert sessions(client, login)[0]["status"] == "closed"


def test_pay_twice_409(client, login, frozen_clock):
    payment_id = start_exit(client)
    mock_pay(client, payment_id, True)
    before = len(gate_events(client, login))
    assert mock_pay(client, payment_id, True).status_code == 409
    assert mock_pay(client, payment_id, False).status_code == 409
    cash = client.post(f"/api/payments/{payment_id}/cash", headers=login(client, "attendant"))
    assert cash.status_code == 409
    assert len(gate_events(client, login)) == before


def test_mock_unknown_payment_404(client):
    response = mock_pay(client, 999, True)
    assert response.status_code == 404
    assert response.json()["detail"] == "Payment not found"


def test_cash_after_failed_qr_closes_and_audits(client, login, frozen_clock):
    payment_id = start_exit(client)
    mock_pay(client, payment_id, False)
    response = client.post(f"/api/payments/{payment_id}/cash", headers=login(client, "attendant"))
    assert response.status_code == 200
    assert (response.json()["status"], response.json()["method"]) == ("paid", "cash")
    assert sessions(client, login)[0]["status"] == "closed"
    assert gate_events(client, login)[0]["barrier_opened_at"] is not None
    [row] = client.get("/api/audit-log", headers=login(client, "admin")).json()
    assert (row["action"], row["username"], row["reason"]) == (
        "cash_payment",
        "attendant",
        "Thu tiền mặt",
    )


def test_driver_cannot_pay_cash_403(client, login, frozen_clock):
    payment_id = start_exit(client)
    response = client.post(f"/api/payments/{payment_id}/cash", headers=login(client, "driver"))
    assert response.status_code == 403
