from datetime import datetime, timedelta

PLATE = "30A-123.45"
T0 = "2026-10-19T08:00:00+07:00"


def post_lpr(client, plate=PLATE, gate="IN-1", confidence=0.95, timestamp=T0):
    return client.post(
        "/api/lpr-events",
        json={"plate": plate, "confidence": confidence, "gate_id": gate, "timestamp": timestamp},
    )


def events(client, login):
    return client.get("/api/gate-events", headers=login(client, "attendant")).json()


def sessions(client, login, status=None):
    params = {"status": status} if status else {}
    response = client.get("/api/sessions", params=params, headers=login(client, "attendant"))
    return response.json()


def test_tc15_lpr_event_valid_returns_201(client, login, frozen_clock):
    response = post_lpr(client)
    assert response.status_code == 201
    assert len(events(client, login)) == 1


def test_tc01_entry_creates_active_session(client, login, frozen_clock):
    post_lpr(client)
    active = sessions(client, login, "active")
    assert len(active) == 1
    assert active[0]["plate"] == PLATE
    assert datetime.fromisoformat(active[0]["entry_at"]) == datetime.fromisoformat(T0)


def test_tc02_barrier_opens_within_3s(client, frozen_clock):
    body = post_lpr(client).json()
    opened = datetime.fromisoformat(body["barrier_opened_at"])
    received = datetime.fromisoformat(body["received_at"])
    assert timedelta(0) <= opened - received <= timedelta(seconds=3)


# test_tc03_exit_closes_session moved to test_billing.py: exit now waits for payment (Sprint 2).


def test_duplicate_entry_409(client, login, frozen_clock):
    post_lpr(client)
    assert post_lpr(client).status_code == 409
    assert len(sessions(client, login)) == 1
    assert len(events(client, login)) == 1


def test_exit_without_session_404(client, login, frozen_clock):
    assert post_lpr(client, gate="OUT-1").status_code == 404
    assert events(client, login) == []


def test_naive_timestamp_422(client, login, frozen_clock):
    assert post_lpr(client, timestamp="2026-10-19T08:00:00").status_code == 422
    assert sessions(client, login) == []


def test_unknown_gate_422(client, frozen_clock):
    assert post_lpr(client, gate="SIDE-1").status_code == 422


def test_low_confidence_marks_manual_required(client, login, frozen_clock):
    response = post_lpr(client, confidence=0.6)
    assert response.status_code == 201
    body = response.json()
    assert body["action"] == "manual_required"
    assert body["barrier_opened_at"] is None
    assert sessions(client, login) == []


def test_invalid_plate_marks_manual_required(client, login, frozen_clock):
    body = post_lpr(client, plate="???").json()
    assert body["action"] == "manual_required"
    assert sessions(client, login) == []


def test_plate_is_normalized(client, login, frozen_clock):
    post_lpr(client, plate=" 30a-123.45 ")
    assert post_lpr(client).status_code == 409


def test_gate_events_requires_staff_role(client, login):
    assert client.get("/api/gate-events").status_code == 401
    assert client.get("/api/gate-events", headers=login(client, "driver")).status_code == 403


def test_device_key_required_401(client, frozen_clock):
    from fastapi.testclient import TestClient

    from app.core.config import DEVICE_KEY
    from app.main import app

    bare = TestClient(app)  # no X-Device-Key header, unlike the `client` fixture
    lpr = {"plate": PLATE, "confidence": 0.95, "gate_id": "IN-1", "timestamp": T0}
    sensor = {"slot_id": "T1-A-05", "occupied": True}
    mock = {"success": True}
    for path, body in (
        ("/api/lpr-events", lpr),
        ("/api/sensor-events", sensor),
        ("/api/payments/1/mock", mock),
    ):
        assert bare.post(path, json=body).status_code == 401, path
        wrong = bare.post(path, json=body, headers={"X-Device-Key": "wrong"})
        assert wrong.status_code == 401, path
    right = {"X-Device-Key": DEVICE_KEY}
    assert bare.post("/api/lpr-events", json=lpr, headers=right).status_code == 201
    assert bare.post("/api/sensor-events", json=sensor, headers=right).status_code == 200
    assert bare.post("/api/payments/999/mock", json=mock, headers=right).status_code == 404
