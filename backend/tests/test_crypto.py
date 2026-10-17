import pytest
from sqlalchemy import create_engine, text
from sqlalchemy.orm import Session

from app.core.db import Base
from app.modules.sessions.service import handle_plate
from tests.test_sessions import PLATE, post_lpr

PLATE_COLUMNS = [
    ("parking_sessions", "plate"),
    ("gate_events", "plate"),
    ("reservations", "plate"),
    ("audit_log", "plate"),
]


def raw(engine, table, column):
    with engine.connect() as connection:
        return [r[0] for r in connection.execute(text(f"SELECT {column} FROM {table}"))]


def test_plate_not_stored_in_plaintext(client, login, engine, frozen_clock):
    post_lpr(client)  # parking_sessions and gate_events
    driver = login(client, "driver")
    client.post(
        "/api/reservations", json={"slot_id": "T1-A-05", "plate": "30A-222.22"}, headers=driver
    )
    client.post(
        "/api/gate/manual-entry",
        json={"gate_id": "IN-1", "plate": "30A-333.33"},
        headers=login(client, "attendant"),
    )  # audit_log
    for table, column in PLATE_COLUMNS:
        values = raw(engine, table, column)
        assert values, table
        assert not any("30A" in v or "." in v for v in values if v), (table, values)


def test_username_encrypted_but_login_works(client, login, engine):
    values = raw(engine, "users", "username")
    assert len(values) == 3
    assert not any(name in v for v in values for name in ("admin", "attendant", "driver"))
    assert login(client, "admin")  # lookup by encrypted username still matches


def test_username_copies_encrypted(client, login, engine, frozen_clock):
    driver = login(client, "driver")
    client.post(
        "/api/reservations", json={"slot_id": "T1-A-05", "plate": "30A-222.22"}, headers=driver
    )
    assert client.get("/api/reservations/me", headers=driver).status_code == 200
    attendant = login(client, "attendant")
    client.post(
        "/api/gate/manual-entry", json={"gate_id": "IN-1", "plate": "30A-333.33"}, headers=attendant
    )
    admin = login(client, "admin")
    price = {"first_hours": 2, "first_price": 25000, "per_hour": 10000}
    assert client.post("/api/prices", json=price, headers=admin).status_code == 201
    for table, column in [
        ("reservations", "username"),
        ("audit_log", "username"),
        ("prices", "created_by"),
    ]:
        values = raw(engine, table, column)
        assert values, table
        assert not any(name in v for v in values for name in ("admin", "attendant", "driver")), (
            table
        )


def test_same_plate_same_ciphertext(client, login, engine, frozen_clock):
    post_lpr(client)
    assert post_lpr(client).status_code == 409  # equality lookup and unique index still work
    post_lpr(client, gate="OUT-1")
    # gate_events holds the plate twice (entry and exit), always the same ciphertext.
    values = raw(engine, "gate_events", "plate")
    assert len(values) == 2 and len(set(values)) == 1


def test_stored_plate_decrypts_in_responses(client, login, frozen_clock):
    post_lpr(client)
    [session] = client.get("/api/sessions", headers=login(client, "attendant")).json()
    assert session["plate"] == PLATE


def test_database_file_does_not_contain_the_plate(tmp_path):
    path = tmp_path / "spms.db"
    engine = create_engine(f"sqlite:///{path}")
    Base.metadata.create_all(engine)
    from app.core import clock
    from app.modules.billing.service import seed_price
    from app.modules.slots.service import seed_slots

    with Session(engine) as db:
        seed_slots(db)
        seed_price(db)
        handle_plate(db, "IN-1", PLATE, clock.now(), "manual", None)
        db.commit()
    engine.dispose()
    data = path.read_bytes()
    assert PLATE.encode() not in data
    # "-" and "." are outside the base64 alphabet, so no ciphertext can contain these by chance.
    assert b"30A-" not in data and b"123.45" not in data


def test_key_from_env_must_be_64_bytes(monkeypatch):
    from app.core import crypto

    monkeypatch.setenv("SPMS_DATA_KEY", "AAAA")
    with pytest.raises(ValueError):
        crypto.load_key()


def test_missing_key_is_created_once_and_reused(monkeypatch, tmp_path):
    from app.core import crypto

    key_file = tmp_path / ".data_key"
    monkeypatch.delenv("SPMS_DATA_KEY", raising=False)
    monkeypatch.setenv("SPMS_DATA_KEY_FILE", str(key_file))
    first = crypto.load_key()
    assert key_file.exists() and len(first) == 64
    assert crypto.load_key() == first
