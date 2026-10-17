from sqlalchemy import func, select, update
from sqlalchemy.orm import Session

from app.modules.slots.models import Slot
from app.modules.slots.service import seed_slots


def test_seed_creates_200_slots(db):
    seed_slots(db)
    assert db.scalar(select(func.count()).select_from(Slot)) == 200
    assert db.get(Slot, "T1-A-01") is not None
    assert db.get(Slot, "T2-B-50") is not None
    assert db.scalar(select(func.count()).select_from(Slot).where(Slot.status != "available")) == 0


def summary(client, login, user="driver"):
    response = client.get("/api/slots/summary", headers=login(client, user))
    assert response.status_code == 200
    return response.json()


def sensor(client, slot_id, occupied):
    return client.post("/api/sensor-events", json={"slot_id": slot_id, "occupied": occupied})


def floor_free(rows, floor):
    return sum(r["free"] for r in rows if r["floor"] == floor)


def test_tc04_free_count_matches_sensor(client, login, engine):
    free = {f"T1-B-{n:02d}" for n in range(31, 51)}
    with Session(engine) as db:
        db.execute(
            update(Slot).where(Slot.floor == 1, Slot.id.not_in(free)).values(status="occupied")
        )
        db.commit()
    rows = summary(client, login)
    assert floor_free(rows, 1) == 20
    response = sensor(client, "T1-B-31", True)
    assert response.status_code == 200
    assert response.json() == {"slot_id": "T1-B-31", "status": "occupied"}
    assert floor_free(summary(client, login), 1) == 19


def test_summary_shape(client, login):
    rows = summary(client, login)
    assert [(r["floor"], r["zone"], r["free"], r["total"]) for r in rows] == [
        (1, "A", 50, 50),
        (1, "B", 50, 50),
        (2, "A", 50, 50),
        (2, "B", 50, 50),
    ]


def test_sensor_unknown_slot_404(client):
    response = sensor(client, "T9-Z-99", True)
    assert response.status_code == 404
    assert response.json()["detail"] == "Unknown slot"


def test_sensor_repeat_event_no_double_count(client, login):
    sensor(client, "T1-A-05", True)
    sensor(client, "T1-A-05", True)
    assert floor_free(summary(client, login), 1) == 99
    sensor(client, "T1-A-05", False)
    sensor(client, "T1-A-05", False)
    assert floor_free(summary(client, login), 1) == 100


def test_summary_requires_login_401(client):
    assert client.get("/api/slots/summary").status_code == 401


def enter(client, plate="30A-123.45"):
    body = {
        "plate": plate,
        "confidence": 0.95,
        "gate_id": "IN-1",
        "timestamp": "2026-10-19T08:00:00+07:00",
    }
    response = client.post("/api/lpr-events", json=body)
    assert response.status_code == 201
    return response.json()


def test_tc07_suggests_slot_nearest_entrance(client, frozen_clock):
    assert enter(client, "30A-111.11")["suggested_slot"] == "T1-A-01"
    sensor(client, "T1-A-01", True)
    assert enter(client, "30A-222.22")["suggested_slot"] == "T1-A-02"


def test_suggestion_orders_by_number_not_text(client, engine, frozen_clock):
    with Session(engine) as db:
        db.execute(update(Slot).where(Slot.id < "T1-A-10").values(status="occupied"))
        db.commit()
    assert enter(client)["suggested_slot"] == "T1-A-10"


def test_suggest_none_when_full(client, engine, frozen_clock):
    with Session(engine) as db:
        db.execute(update(Slot).values(status="occupied"))
        db.commit()
    body = enter(client)
    assert body["action"] == "entered"
    assert body["suggested_slot"] is None


def test_reserved_plate_gets_its_reserved_slot(client, login, frozen_clock):
    reserved = client.post(
        "/api/reservations",
        json={"slot_id": "T1-A-05", "plate": "30A-123.45"},
        headers=login(client, "driver"),
    )
    assert reserved.status_code == 201
    assert enter(client, "30A-123.45")["suggested_slot"] == "T1-A-05"
    assert enter(client, "30A-222.22")["suggested_slot"] == "T1-A-01"


def test_exit_event_has_no_suggestion(client, frozen_clock):
    enter(client)
    body = {
        "plate": "30A-123.45",
        "confidence": 0.95,
        "gate_id": "OUT-1",
        "timestamp": "2026-10-19T09:00:00+07:00",
    }
    assert client.post("/api/lpr-events", json=body).json()["suggested_slot"] is None
