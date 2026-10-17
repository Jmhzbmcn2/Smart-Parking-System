from datetime import datetime

import pytest

from tests.test_sessions import PLATE, post_lpr, sessions


def audit_log(client, login):
    return client.get("/api/audit-log", headers=login(client, "admin")).json()


def manual_open(client, headers, reason="Khách trả tiền mặt", gate="OUT-1"):
    return client.post(
        "/api/barrier/manual-open", json={"gate_id": gate, "reason": reason}, headers=headers
    )


def test_tc14_manual_open_writes_one_log(client, login, frozen_clock):
    response = manual_open(client, login(client, "attendant"))
    assert response.status_code == 201
    [row] = audit_log(client, login)
    assert row["username"] == "attendant"
    assert row["action"] == "manual_open"
    assert row["reason"] == "Khách trả tiền mặt"
    assert datetime.fromisoformat(row["at"]) == datetime.fromisoformat("2026-10-19T08:00:00+07:00")


def test_tc16_low_confidence_then_manual_entry(client, login, frozen_clock):
    assert post_lpr(client, confidence=0.6).json()["action"] == "manual_required"
    response = client.post(
        "/api/gate/manual-entry",
        json={"gate_id": "IN-1", "plate": PLATE},
        headers=login(client, "attendant"),
    )
    assert response.status_code == 201
    assert response.json()["source"] == "manual"
    assert len(sessions(client, login, "active")) == 1
    [row] = audit_log(client, login)
    assert row["action"] == "manual_entry"
    assert row["plate"] == PLATE


def test_tc13_driver_gets_403_on_admin_page(client, login):
    response = client.get("/api/audit-log", headers=login(client, "driver"))
    assert response.status_code == 403


def test_audit_log_requires_admin(client, login):
    assert client.get("/api/audit-log").status_code == 401
    assert client.get("/api/audit-log", headers=login(client, "attendant")).status_code == 403


def test_manual_open_requires_reason_422(client, login):
    headers = login(client, "attendant")
    assert manual_open(client, headers, reason="").status_code == 422
    assert manual_open(client, headers, reason="   ").status_code == 422
    assert audit_log(client, login) == []


def test_driver_cannot_manual_open_403(client, login):
    assert manual_open(client, login(client, "driver")).status_code == 403
    assert audit_log(client, login) == []


def test_manual_entry_invalid_plate_422_no_log(client, login, frozen_clock):
    response = client.post(
        "/api/gate/manual-entry",
        json={"gate_id": "IN-1", "plate": "abc"},
        headers=login(client, "attendant"),
    )
    assert response.status_code == 422
    assert audit_log(client, login) == []


def test_manual_entry_duplicate_409_no_log(client, login, frozen_clock):
    post_lpr(client)
    response = client.post(
        "/api/gate/manual-entry",
        json={"gate_id": "IN-1", "plate": PLATE},
        headers=login(client, "attendant"),
    )
    assert response.status_code == 409
    assert audit_log(client, login) == []


def test_manual_entry_rolls_back_when_audit_fails(client, login, frozen_clock, monkeypatch):
    from app.modules.audit import service as audit_service

    def broken_record(*args, **kwargs):
        raise RuntimeError("audit store down")

    headers = login(client, "attendant")
    monkeypatch.setattr(audit_service, "record", broken_record)
    with pytest.raises(RuntimeError):
        client.post("/api/gate/manual-entry", json={"gate_id": "IN-1", "plate": PLATE}, headers=headers)
    monkeypatch.undo()
    assert sessions(client, login, "active") == []
    assert audit_log(client, login) == []
