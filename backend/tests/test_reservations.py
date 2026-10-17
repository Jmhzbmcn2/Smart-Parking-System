from datetime import datetime

import pytest
from sqlalchemy import select
from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import Session

from app.core import clock
from app.modules.auth.models import User
from app.modules.auth.service import hash_password
from app.modules.reservations.models import Reservation
from app.modules.reservations.service import HOLD

PLATE = "30A-123.45"


def reserve(client, headers, slot_id="T1-A-05", plate=PLATE):
    return client.post(
        "/api/reservations", json={"slot_id": slot_id, "plate": plate}, headers=headers
    )


def slot_status(client, headers, slot_id="T1-A-05"):
    rows = client.get("/api/slots", params={"floor": 1, "zone": "A"}, headers=headers).json()
    return next(s["status"] for s in rows if s["id"] == slot_id)


def my_reservation(client, headers):
    response = client.get("/api/reservations/me", headers=headers)
    assert response.status_code == 200
    return response.json()


def at(minute):
    return datetime(2026, 10, 19, 8, minute, tzinfo=clock.TZ)


def test_tc05_reservation_sets_slot_reserved(client, login, frozen_clock):
    driver = login(client, "driver")
    response = reserve(client, driver)
    assert response.status_code == 201
    assert datetime.fromisoformat(response.json()["expires_at"]) == at(10)
    assert slot_status(client, driver) == "reserved"
    assert my_reservation(client, driver)["slot_id"] == "T1-A-05"


def test_tc06_reservation_expires_at_minute_11(client, login, engine, frozen_clock):
    driver = login(client, "driver")
    reserve(client, driver)
    frozen_clock(at(10))  # CR-02: still held at minute 10
    assert slot_status(client, driver) == "reserved"
    frozen_clock(at(11))
    assert slot_status(client, driver) == "available"
    assert my_reservation(client, driver) is None
    with Session(engine) as db:
        assert db.scalars(select(Reservation.status)).all() == ["expired"]


def test_reserve_taken_slot_409(client, login, frozen_clock):
    client.post("/api/sensor-events", json={"slot_id": "T1-A-05", "occupied": True})
    assert reserve(client, login(client, "driver")).status_code == 409


def test_second_active_reservation_409(client, login, frozen_clock):
    driver = login(client, "driver")
    reserve(client, driver)
    assert reserve(client, driver, slot_id="T1-A-06").status_code == 409
    assert slot_status(client, driver, "T1-A-06") == "available"


def test_can_reserve_again_after_expiry(client, login, frozen_clock):
    driver = login(client, "driver")
    reserve(client, driver)
    frozen_clock(at(11))
    assert reserve(client, driver, slot_id="T1-A-06").status_code == 201


def test_cancel_frees_slot(client, login, frozen_clock):
    driver = login(client, "driver")
    reserve(client, driver)
    assert client.delete("/api/reservations/me", headers=driver).status_code == 204
    assert slot_status(client, driver) == "available"
    assert my_reservation(client, driver) is None
    assert client.delete("/api/reservations/me", headers=driver).status_code == 404


def test_attendant_cannot_reserve_403(client, login, frozen_clock):
    assert reserve(client, login(client, "attendant")).status_code == 403


def test_reserve_unknown_slot_404_and_bad_plate_422(client, login, frozen_clock):
    driver = login(client, "driver")
    assert reserve(client, driver, slot_id="T9-Z-99").status_code == 404
    assert reserve(client, driver, plate="???").status_code == 422
    assert my_reservation(client, driver) is None


def test_reserved_slot_not_counted_free(client, login, frozen_clock):
    driver = login(client, "driver")
    before = client.get("/api/slots/summary", headers=driver).json()[0]["free"]
    reserve(client, driver)
    after = client.get("/api/slots/summary", headers=driver).json()[0]["free"]
    assert (before, after) == (50, 49)
    frozen_clock(at(11))
    assert client.get("/api/slots/summary", headers=driver).json()[0]["free"] == 50


def test_sensor_free_report_keeps_slot_reserved(client, login, frozen_clock):
    driver = login(client, "driver")
    reserve(client, driver)
    client.post("/api/sensor-events", json={"slot_id": "T1-A-05", "occupied": False})
    assert slot_status(client, driver) == "reserved"


def test_expiry_keeps_slot_a_sensor_marked_occupied(client, login, frozen_clock):
    driver = login(client, "driver")
    reserve(client, driver)
    client.post("/api/sensor-events", json={"slot_id": "T1-A-05", "occupied": True})
    frozen_clock(at(11))
    assert slot_status(client, driver) == "occupied"


def test_slot_list_filters_and_requires_login(client, login):
    assert client.get("/api/slots").status_code == 401
    rows = client.get(
        "/api/slots",
        params={"floor": 2, "zone": "B", "status": "available"},
        headers=login(client, "driver"),
    ).json()
    assert len(rows) == 50
    assert {(r["floor"], r["zone"]) for r in rows} == {(2, "B")}


def test_two_drivers_cannot_hold_same_slot(client, login, engine, frozen_clock):
    with Session(engine) as db:
        db.add(User(username="driver2", password_hash=hash_password("driver2123"), role="driver"))
        db.commit()
    assert reserve(client, login(client, "driver")).status_code == 201
    assert reserve(client, login(client, "driver2"), plate="30A-999.99").status_code == 409
    # The database refuses a second active hold even if the application check is bypassed.
    with Session(engine) as db:
        now = clock.now()
        db.add(
            Reservation(
                slot_id="T1-A-05",
                plate="30A-999.99",
                username="driver2",
                created_at=now,
                expires_at=now + HOLD,
            )
        )
        with pytest.raises(IntegrityError):
            db.commit()
