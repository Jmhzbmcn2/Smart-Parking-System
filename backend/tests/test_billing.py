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
