from sqlalchemy.orm import Session

from app.modules.slots.models import Slot


def seed_slots(db: Session) -> None:
    """Create the 200 slots (2 floors x 2 zones x 50) that do not exist yet."""
    for floor in (1, 2):
        for zone in ("A", "B"):
            for n in range(1, 51):
                slot_id = f"T{floor}-{zone}-{n:02d}"
                if db.get(Slot, slot_id) is None:
                    db.add(Slot(id=slot_id, floor=floor, zone=zone))
    db.commit()
