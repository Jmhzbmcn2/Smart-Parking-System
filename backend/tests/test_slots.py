from sqlalchemy import func, select

from app.modules.slots.models import Slot
from app.modules.slots.service import seed_slots


def test_seed_creates_200_slots(db):
    seed_slots(db)
    assert db.scalar(select(func.count()).select_from(Slot)) == 200
    assert db.get(Slot, "T1-A-01") is not None
    assert db.get(Slot, "T2-B-50") is not None
    assert db.scalar(select(func.count()).select_from(Slot).where(Slot.status != "available")) == 0
