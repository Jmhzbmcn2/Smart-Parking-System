from datetime import datetime

from app.core import clock

PLATE = "30A-123.45"


def at(hour, minute):
    return datetime(2026, 10, 19, hour, minute, tzinfo=clock.TZ)


def test_e2e_uc02_uc01_uc03(client, login, frozen_clock):
    """Reserve, enter, exit with a failed then a successful payment, daily report."""
    driver, attendant, admin = (login(client, u) for u in ("driver", "attendant", "admin"))

    def slot_status():
        rows = client.get("/api/slots", params={"floor": 1, "zone": "A"}, headers=driver).json()
        return next(s["status"] for s in rows if s["id"] == "T1-A-05")

    def newest_event():
        return client.get("/api/gate-events", headers=attendant).json()[0]

    def lpr(gate, when):
        body = {"plate": PLATE, "confidence": 0.95, "gate_id": gate, "timestamp": when.isoformat()}
        return client.post("/api/lpr-events", json=body)

    # UC-02: the driver reserves T1-A-05 at 08:00.
    reserved = client.post(
        "/api/reservations", json={"slot_id": "T1-A-05", "plate": PLATE}, headers=driver
    )
    assert reserved.status_code == 201
    assert slot_status() == "reserved"

    # UC-01: the car enters at IN-1 and the sensor reports the slot occupied.
    entry = lpr("IN-1", at(8, 0))
    assert entry.status_code == 201 and entry.json()["barrier_opened_at"] is not None
    client.post("/api/sensor-events", json={"slot_id": "T1-A-05", "occupied": True})
    assert slot_status() == "occupied"

    # UC-03: 3 h 10 min later the car reaches OUT-1; the first QR payment fails.
    frozen_clock(at(11, 10))
    exit_event = lpr("OUT-1", at(11, 10)).json()
    assert exit_event["action"] == "payment_required"
    payment = client.get(f"/api/payments/{exit_event['payment_id']}", headers=attendant).json()
    assert payment["amount"] == 40000
    client.post(f"/api/payments/{payment['id']}/mock", json={"success": False})
    assert newest_event()["action"] == "payment_failed"
    assert newest_event()["barrier_opened_at"] is None

    # The second payment succeeds: the session closes and the barrier opens.
    paid = client.post(f"/api/payments/{payment['id']}/mock", json={"success": True})
    assert paid.json()["status"] == "paid"
    assert newest_event()["action"] == "exited"
    assert newest_event()["barrier_opened_at"] is not None
    [session] = client.get("/api/sessions", headers=attendant).json()
    assert session["status"] == "closed"

    # The sensor frees the slot; the admin report shows the day's revenue.
    client.post("/api/sensor-events", json={"slot_id": "T1-A-05", "occupied": False})
    assert slot_status() == "available"
    report = client.get("/api/reports/daily", params={"date": "2026-10-19"}, headers=admin).json()
    assert (report["total"], report["paid_count"]) == (40000, 1)
