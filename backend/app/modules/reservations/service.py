from datetime import timedelta

from sqlalchemy import select
from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import Session

from app.core import clock
from app.modules.reservations.models import Reservation
from app.modules.sessions.service import PLATE_RE, InvalidPlate, normalize_plate
from app.modules.slots.models import Slot
from app.modules.slots.service import UnknownSlot

# CR-02 (Approved): the hold is 10 minutes, not the SRS's old 15. It is still held at
# minute 10 and released at minute 11 (TC-06).
HOLD = timedelta(minutes=10)


class SlotNotAvailable(Exception):
    """The slot is reserved or occupied."""


class AlreadyReserved(Exception):
    """The driver already has an active reservation."""


class NoReservation(Exception):
    """The driver has no active reservation."""


def expire_due(db: Session) -> int:
    """SP-2.2.2: release holds past due. Called before any read of slot state."""
    due = db.scalars(
        select(Reservation).where(
            Reservation.status == "active", Reservation.expires_at < clock.now()
        )
    ).all()
    for reservation in due:
        reservation.status = "expired"
        _release(db, reservation)
    db.commit()
    return len(due)


def _release(db: Session, reservation: Reservation) -> None:
    slot = db.get(Slot, reservation.slot_id)
    if slot is not None and slot.status == "reserved":  # a sensor-occupied slot stays occupied
        slot.status = "available"


def active_for(db: Session, username: str) -> Reservation | None:
    return db.scalar(
        select(Reservation).where(Reservation.username == username, Reservation.status == "active")
    )


def reserve(db: Session, username: str, slot_id: str, plate: str) -> Reservation:
    plate = normalize_plate(plate)
    if not PLATE_RE.match(plate):
        raise InvalidPlate(plate)
    slot = db.get(Slot, slot_id)
    if slot is None:
        raise UnknownSlot(slot_id)
    if active_for(db, username) is not None:
        raise AlreadyReserved(username)
    if slot.status != "available":
        raise SlotNotAvailable(slot_id)
    now = clock.now()
    reservation = Reservation(
        slot_id=slot_id, plate=plate, username=username, created_at=now, expires_at=now + HOLD
    )
    slot.status = "reserved"
    db.add(reservation)
    try:
        db.commit()
    except IntegrityError as exc:  # a concurrent request took the slot first
        db.rollback()
        raise SlotNotAvailable(slot_id) from exc
    return reservation


def cancel(db: Session, username: str) -> None:
    reservation = active_for(db, username)
    if reservation is None:
        raise NoReservation(username)
    reservation.status = "cancelled"
    _release(db, reservation)
    db.commit()
