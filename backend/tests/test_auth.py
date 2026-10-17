from sqlalchemy import func, select

from app.modules.auth.models import User
from app.modules.auth.service import hash_password, seed_users, verify_password
from app.modules.slots.models import Slot
from app.modules.slots.service import seed_slots


def test_seed_is_idempotent(db):
    for _ in range(2):
        seed_slots(db)
        seed_users(db)
    assert db.scalar(select(func.count()).select_from(Slot)) == 200
    assert db.scalar(select(func.count()).select_from(User)) == 3


def test_password_hash_roundtrip():
    stored = hash_password("x")
    assert verify_password("x", stored)
    assert not verify_password("y", stored)


def test_login_returns_token_and_role(client):
    response = client.post("/api/auth/login", json={"username": "admin", "password": "admin123"})
    assert response.status_code == 200
    body = response.json()
    assert body["username"] == "admin"
    assert body["role"] == "admin"
    assert body["token"]


def test_login_wrong_password_401(client):
    response = client.post("/api/auth/login", json={"username": "admin", "password": "nope"})
    assert response.status_code == 401


def test_me_without_token_401(client):
    assert client.get("/api/auth/me").status_code == 401


def test_me_with_token_returns_role(client, login):
    response = client.get("/api/auth/me", headers=login(client, "attendant"))
    assert response.status_code == 200
    assert response.json() == {"username": "attendant", "role": "attendant"}


def test_me_with_stale_token_401(client, login):
    first = login(client, "driver")
    login(client, "driver")
    assert client.get("/api/auth/me", headers=first).status_code == 401


def test_logout_invalidates_token(client, login):
    headers = login(client, "driver")
    assert client.get("/api/auth/me", headers=headers).status_code == 200
    assert client.post("/api/auth/logout", headers=headers).status_code == 204
    assert client.get("/api/auth/me", headers=headers).status_code == 401


def test_logout_requires_login(client):
    assert client.post("/api/auth/logout").status_code == 401
