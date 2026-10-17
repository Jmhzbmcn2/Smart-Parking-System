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
