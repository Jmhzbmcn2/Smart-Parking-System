from sqlalchemy import func, select
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


class UnknownSlot(Exception):
    """No slot has this ID."""


def set_occupied(db: Session, slot_id: str, occupied: bool) -> Slot:
    """Sensor event. Idempotent: the status is set, never counted."""
    slot = db.get(Slot, slot_id)
    if slot is None:
        raise UnknownSlot(slot_id)
    if occupied:
        slot.status = "occupied"
    elif slot.status == "occupied":  # a "free" report never cancels a reservation hold
        slot.status = "available"
    db.commit()
    return slot


def list_slots(db: Session, floor: int | None, zone: str | None, status: str | None) -> list[Slot]:
    query = select(Slot).order_by(Slot.id)
    for column, value in ((Slot.floor, floor), (Slot.zone, zone), (Slot.status, status)):
        if value is not None:
            query = query.where(column == value)
    return list(db.scalars(query))


def summary(db: Session) -> list[dict[str, int | str]]:
    rows = db.execute(
        select(
            Slot.floor,
            Slot.zone,
            func.count().filter(Slot.status == "available").label("free"),
            func.count().label("total"),
        )
        .group_by(Slot.floor, Slot.zone)
        .order_by(Slot.floor, Slot.zone)
    )
    return [row._asdict() for row in rows]
